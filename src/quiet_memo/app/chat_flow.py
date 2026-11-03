from __future__ import annotations

import time
from dataclasses import dataclass
from functools import partial
from threading import Event

from textual.widgets import Input, Static

from ..llm import ChatModelError, GenerationCancelled
from ..infra.diagnostics import record_event
from .chat_widgets import ASSISTANT_NAME, ChatReply


def _is_undo_line(line: str) -> bool:
    text = line.strip()
    return text.startswith("/") and text.split(" ", 1)[0].lower() == "/undo"


@dataclass
class _QueuedLine:
    """等待期提交的全局 FIFO 项；执行时按 session_id 从磁盘新鲜加载会话。"""

    session_id: str
    line: str


class ChatFlowMixin:
    """LLM 请求调度与流式渲染：忙碌态解耦、全局 FIFO 排队、切走切回的流式续播。

    依赖 ChatApp 的 runtime/sessions/service、busy 三态字段与 `_begin_ask`/`_end_ask`
    等生命周期方法；提交路由规则见 `_submit_during_ask`。
    """

    # 等待 LLM 期间可直接执行的导航/只读命令；其余提交（消息与命令）进全局 FIFO。
    SAFE_COMMANDS = frozenset({
        "/new", "/sessions", "/exit", "/quit", "/help", "/model",
        "/status", "/topics", "/summary", "/pending", "/git",
    })

    # ---------- 提交与调度 ----------

    def _ask_in_current_view(self) -> bool:
        """请求的会话是否就是当前正在查看的会话（尚未绑定时按当前视图处理）。"""
        if self._ask_in_flight is None:
            return True
        return self.runtime.has_session and self.runtime.current.id == self._ask_in_flight

    def _bind_ask_session(self, session_id: str) -> None:
        # on_session 先于一切 delta/事件回调投递，这里补齐首条消息的会话绑定。
        if self._ask_active and self._ask_in_flight is None:
            self._ask_in_flight = session_id

    def _bind_ask_user_message(self, message_id: str) -> None:
        if self._ask_active:
            self._ask_user_message_id = message_id

    def _submit_during_ask(self, line: str) -> None:
        # 等待期提交：/undo 是即时控制命令，必须先于 SAFE/FIFO 判定。
        command = line.split(" ", 1)[0].lower() if line.startswith("/") else ""
        if command == "/undo":
            self._request_undo()
            return
        # 其余导航/只读命令立即执行；普通消息按提交顺序进全局 FIFO，
        # 完成后逐条执行——意图排队接续，绝不静默丢弃，也不并发第二个请求。
        if line.startswith("/") and command in self.SAFE_COMMANDS:
            self._command(line)
            return
        if not self.runtime.has_session:
            # /new 后尚未发过消息：先落一个会话文件，排队任务才有绑定目标。
            self.runtime.ensure_session()
        session_id = self.runtime.session.id
        self._queue.append(_QueuedLine(session_id=session_id, line=line))
        self._refresh_queue()

    def _refresh_queue(self) -> None:
        panel = self.query_one("#send-queue", Static)
        panel.display = bool(self._queue)
        lines = [f"Queued ({len(self._queue)}) · sent automatically in order"]
        for index, item in enumerate(self._queue[:3], 1):
            lines.append(f"{index}. {item.line[:100]}")
        if len(self._queue) > 3:
            lines.append(f"+{len(self._queue) - 3} more")
        panel.update("\n".join(lines))

    def _stop_generation(self) -> None:
        if not self._ask_active or self._cancel_generation is None:
            return
        self._cancel_generation.set()
        self._progress_phase = "Stopping"
        self._render_model_status()
        self.query_one("#input").focus()

    def _request_undo(self) -> None:
        """生成期间的 /undo：立即取消，不进入 FIFO；撤销在 Worker 退出后执行。"""
        if not self._ask_active:
            self._undo_message()
            return
        if self._undo_requested:
            self.notify("Undo already in progress.")
            return
        self._undo_requested = True
        self._undo_target_session_id = self._ask_in_flight
        self._undo_target_message_id = self._ask_user_message_id
        # 旧版本可能把 /undo 排进 FIFO；这里一次性清掉，避免撤销后再次执行。
        self._purge_queued_undo()
        if self._cancel_generation is not None:
            self._cancel_generation.set()
        self._progress_phase = "Stopping"
        self._render_model_status()
        self.query_one("#input").focus()
        self.notify("Stopping generation and undoing this turn…")

    def _purge_queued_undo(self) -> None:
        kept = [item for item in self._queue if not _is_undo_line(item.line)]
        removed = len(self._queue) - len(kept)
        self._queue = kept
        self._refresh_queue()
        if self._pending_command and _is_undo_line(self._pending_command.line):
            self._pending_command = None
            removed += 1
        if removed:
            self.notify(f"Discarded {removed} queued /undo.")

    def _finish_undo(
        self,
        session_id: str | None,
        user_message_id: str | None = None,
        error: str | None = None,
    ) -> None:
        """Worker 已退出后执行撤销；不启动新请求，也不自动发送旧队列。"""
        self._progress_phase = "Undoing"
        self._render_model_status()
        target_sid = (
            self._undo_target_session_id
            or session_id
            or self._ask_in_flight
        )
        target_mid = user_message_id or self._undo_target_message_id
        restored: str | None = None
        undo_failed = False
        # 没有绑定到具体用户消息时绝不回退撤销上一轮：那可能是请求落盘前的
        # 失败，撤销更早的对话会破坏用户上下文。
        if target_sid and target_mid:
            try:
                # 始终从磁盘加载目标会话：后台 Worker 的写入可能晚于切回时
                # 载入的内存对象，直接用当前对象会看不到刚追加的用户消息。
                target_session = self.runtime.sessions.load(target_sid)
                restored = self.runtime.undo(
                    target_session, message_id=target_mid
                )
            except Exception as exc:
                undo_failed = True
                record_event("undo.failed", exc)
                self.notify(f"Undo failed: {exc}")
        if error:
            record_event("chat.failed", error)
            self.notify(f"Request failed before undo: {error}")
        if restored is None and not undo_failed:
            self.notify("No generated turn to undo.")

        current_id = self.runtime.current.id if self.runtime.has_session else None
        if restored is not None and target_sid:
            # 按会话保存待回填，后台撤销互不覆盖；同一会话的新撤销覆盖
            # 尚未应用的旧文本（旧回合已撤销，输入框未被占用）。
            self._pending_undo_restore[target_sid] = restored
            if current_id == target_sid and not self._navigation_busy:
                self._flush_undo_refresh()
            elif current_id != target_sid:
                # 后台会话：不修改当前视图与输入框；切回目标会话时再回填。
                self.notify("Generation stopped and message undone in background session")
        self._heal_current_session(target_sid)
        self.refresh_sessions()
        self.refresh_pending()
        self._end_ask()
        queued_count = len(self._queue)
        self._queue_paused_after_undo = restored is not None and bool(self._queue)
        self._undo_requested = False
        self._undo_target_session_id = None
        self._undo_target_message_id = None
        self.update_status()
        if self._queue_paused_after_undo:
            self.notify(
                f"{queued_count} queued message(s) paused after undo; "
                "they resume after your next reply."
            )
        else:
            # 撤销失败/无目标时不能把 FIFO 永久留在暂停状态；Worker 已退出，
            # 可安全接续队列（成功后 pause 分支不会走到这里）。
            if queued_count:
                self.notify(f"{queued_count} queued message(s) resumed.")
            self._drain_pending_intent()

    def _apply_undo_view(self, session_id: str, text: str) -> bool:
        """目标会话就是当前视图：从磁盘重载，清除已撤销回合并回填原文。"""
        if not self.runtime.has_session or self.runtime.current.id != session_id:
            return False
        try:
            self.runtime.session = self.runtime.sessions.load(session_id)
        except Exception as exc:
            record_event("session.reload_failed", exc)
        self._clear_chat()
        self.build_transcript()
        self.refresh_sessions()
        self.update_status()
        widget = self.query_one("#input", Input)
        # 用户已在输入框写了新内容时不能静默覆盖；保留待回填，
        # 等之后带回填会话且输入为空时再应用。
        if widget.value.strip() and widget.value != text:
            self.notify(
                "Undo text not restored: the input has unsent text. "
                "It will be restored when you return with an empty input."
            )
            return False
        widget.value = text
        widget.cursor_position = len(text)
        widget.focus()
        return True

    def _flush_undo_refresh(self) -> None:
        """切换完成后消费当前会话对应的回填；其他会话的待回填保持不变。"""
        if not self._pending_undo_restore:
            return
        current_id = self.runtime.current.id if self.runtime.has_session else None
        if current_id is None:
            return
        text = self._pending_undo_restore.get(current_id)
        if text is None:
            return
        if self._apply_undo_view(current_id, text):
            self._pending_undo_restore.pop(current_id, None)

    def _finish_cancelled(
        self,
        session_id: str | None = None,
        user_message_id: str | None = None,
    ) -> None:
        if self._undo_requested:
            self._finish_undo(session_id, user_message_id)
            return
        sid = session_id or self._ask_in_flight
        if self._ask_in_current_view():
            content = self._stream_buffer + "\n\n*(generation stopped by user)*"
            if self._stream_widget is not None:
                self._finalize_stream_segment(content)
            else:
                self.add_card("Generation stopped by user")
        else:
            self.notify("Generation stopped in background session")
        self._heal_current_session(sid)
        self.refresh_sessions()
        self.refresh_pending()
        self._end_ask()
        self.update_status()
        self._drain_pending_intent()

    def _start_ask(self, line: str, session_id: str | None = None) -> None:
        self._cancel_generation = Event()
        stamp = time.strftime("%H:%M")
        # 用户气泡只渲染进它所属会话的视图；后台任务不串入当前视图。
        if session_id is None or not self.runtime.has_session or session_id == self.runtime.current.id:
            self.add_user_turn(line, stamp)
        else:
            self.notify("Running queued task in background session")
        self._begin_ask(session_id)
        self._stream_stamp = stamp
        self.run_worker(
            partial(self._ask_work, line, stamp, session_id),
            group="ask",
            thread=True,
            exclusive=True,
            exit_on_error=False,
        )

    def _dispatch_queue(self) -> None:
        if self.busy or not self._queue:
            return
        item = self._queue.pop(0)
        self._refresh_queue()
        if item.line.startswith("/"):
            # 排队的命令按命令分发，不能当聊天消息发给模型；会话归属见
            # _run_queued_command——不能拿当前查看的会话顶替提交时的会话。
            self._run_queued_command(item)
            self._drain_pending_intent()
            return
        self._start_ask(item.line, item.session_id)

    def _run_queued_command(self, item: _QueuedLine) -> None:
        """排队命令绑定提交时的会话：目标不是当前会话时先切回再执行。

        切换完成后由 _after_session_switch → _drain_pending_intent 消费
        _pending_command；目标已删除或损坏时提示并跳过，继续处理后续队列。
        """
        current_id = self.runtime.current.id if self.runtime.has_session else None
        if current_id == item.session_id:
            self._command(item.line)
            return
        try:
            self.runtime.sessions.load(item.session_id)
        except Exception as exc:
            record_event("queue.failed", exc)
            self.notify("Queued command skipped: session no longer available")
            return
        self._pending_command = item
        self._switch_session(item.session_id)

    def _ui(self, fn, *args) -> None:
        try:
            self.call_from_thread(fn, *args)
        except RuntimeError:
            pass  # 界面已退出：丢弃收尾回调，避免淹没退出流程。

    def _ask_work(self, line: str, stamp: str, session_id: str | None) -> None:
        started = time.monotonic()
        # 回调先捕获 Worker 实际绑定的会话与用户消息 ID；UI 字段可能被切换/竞态影响。
        bound: dict[str, str | None] = {
            "session_id": session_id,
            "user_message_id": None,
        }

        def bind_session(s) -> None:
            bound["session_id"] = s.id
            self.call_from_thread(self._bind_ask_session, s.id)

        def bind_user_message(message_id: str) -> None:
            bound["user_message_id"] = message_id
            self.call_from_thread(self._bind_ask_user_message, message_id)

        try:
            session = None
            if session_id and not (
                self.runtime.has_session and self.runtime.session.id == session_id
            ):
                # 后台任务执行时从磁盘新鲜加载，不跨切换复用内存对象（对象会过期）。
                session = self.runtime.sessions.load(session_id)
            reply = self.runtime.ask(
                line,
                session=session,
                on_session=bind_session,
                on_user_message=bind_user_message,
                on_event=lambda event: self.call_from_thread(self.add_event, event),
                on_delta=lambda delta: self.call_from_thread(self._stream_append, stamp, delta),
                on_progress=lambda phase: self.call_from_thread(self._progress_update, phase),
                cancel=self._cancel_generation,
            )
        except GenerationCancelled:
            self._ui(
                self._finish_cancelled,
                bound["session_id"],
                bound["user_message_id"],
            )
            return
        except ChatModelError as exc:
            record_event("chat.failed", exc)
            self._ui(
                self._finish_error, str(exc),
                bound["session_id"], bound["user_message_id"],
            )
            return
        except Exception as exc:  # 界面不因单轮失败退出
            record_event("chat.failed", exc)
            self._ui(
                self._finish_error, f"Request failed: {exc}",
                bound["session_id"], bound["user_message_id"],
            )
            return
        elapsed = time.monotonic() - started
        meta = [f"{reply.steps} steps", f"{reply.estimated_tokens} tok"]
        if reply.usage.cost_usd:
            meta.append(f"${reply.usage.cost_usd:.4f}")
        meta.append(f"{elapsed:.1f}s")
        self._ui(
            self._finish_reply, reply.content, stamp, " · ".join(meta),
            bound["session_id"], bound["user_message_id"],
        )

    # ---------- 流式渲染：帧合并更新，完成/中断后收尾 ----------

    def _stream_append(self, stamp: str, delta: str) -> None:
        self._progress_phase = "Streaming"
        self._stream_buffer += delta
        if not self._ask_in_current_view():
            return  # 请求在后台会话：内容留在 buffer，切回时重放。
        chat = self._chat()
        if self._stream_widget is None:
            chat.mount(Static(f"{ASSISTANT_NAME} · {stamp}", classes="who-ai"))
            self._stream_widget = ChatReply("", classes="reply")
            chat.mount(self._stream_widget)
        if not self._stream_flush_scheduled:
            self._stream_flush_scheduled = True
            self.call_after_refresh(self._stream_flush)

    def _stream_flush(self) -> None:
        self._stream_flush_scheduled = False
        if self._stream_widget is not None:
            self._stream_widget.update(self._stream_buffer)
            self._scroll_end()

    def _finalize_stream_segment(self, content: str) -> None:
        """就地定稿当前可见的活跃段；后台会话没有挂载控件，无需处理。"""
        if self._stream_widget is not None:
            self._stream_widget.update(content)
            self._stream_widget = None
        self._stream_flush_scheduled = False

    def _replay_stream(self) -> None:
        """切回生成中的会话：磁盘重建负责已完成轮次，这里只补挂尚未落盘的活跃段。"""
        if not self._stream_buffer:
            return
        chat = self._chat()
        chat.mount(Static(f"{ASSISTANT_NAME} · {self._stream_stamp}", classes="who-ai"))
        self._stream_widget = ChatReply(self._stream_buffer, classes="reply")
        chat.mount(self._stream_widget)
        self._scroll_end()

    def add_event(self, event: str) -> None:
        if self._stream_buffer:
            # 工具事件在两轮生成之间：先就地定稿当前段（已完成段随 assistant 记录落盘），
            # 后续 delta 另起一段，否则最终回复会覆盖工具前的正文，事件顺序也会颠倒。
            self._finalize_stream_segment(self._stream_buffer)
            self._stream_buffer = ""
        memo = event.startswith(("Saved", "Corrected", "Deleted"))
        # 事件卡只进当前视图；后台请求的事件由磁盘 tool 记录在切回时重建。
        if self._ask_in_current_view():
            self._chat().mount(
                Static(f"✓ {event}" if memo else event, classes="event-card memo" if memo else "event-card")
            )
            self._scroll_end()

    # ---------- 回合收尾 ----------

    def _heal_current_session(self, session_id: str | None) -> None:
        """后台写入期间用户可能切走再切回，内存对象会落后于磁盘：完成后从磁盘刷新。"""
        if not session_id or not self.runtime.has_session or self.runtime.current.id != session_id:
            return
        try:
            self.runtime.session = self.runtime.sessions.load(session_id)
        except Exception as exc:
            record_event("session.reload_failed", exc)
            pass  # 会话文件异常时保留内存对象，后续操作各自报错。

    def _finish_reply(
        self,
        content: str,
        stamp: str,
        meta: str,
        session_id: str | None,
        user_message_id: str | None = None,
    ) -> None:
        if self._undo_requested:
            # 用户已要求撤销：自然完成与取消竞争时只撤销一次，不保留最终回复。
            self._finish_undo(session_id, user_message_id)
            return
        sid = session_id or self._ask_in_flight
        in_view = sid is None or (
            self.runtime.has_session and self.runtime.current.id == sid
        )
        if in_view:
            if self._stream_widget is not None:
                # 流式已实时渲染正文：就地定稿并补 meta/分隔线，不再重复挂载。
                self._finalize_stream_segment(content or "(empty reply)")
                chat = self._chat()
                if meta:
                    chat.mount(Static(meta, classes="meta"))
                chat.mount(Static("", classes="divider"))
                self._scroll_end()
            else:
                self.add_assistant_turn(content, stamp, meta)
        else:
            # 后台完成：不动当前视图；回复已落盘，切回时从磁盘重建。
            self.notify("Reply ready in background session")
        self._heal_current_session(sid)
        self.refresh_sessions()  # 首条消息会创建会话，侧栏需要随之出现
        self.refresh_pending()
        self.update_status()
        self._end_ask()
        self._drain_pending_intent()

    def _finish_error(
        self,
        message: str,
        session_id: str | None = None,
        user_message_id: str | None = None,
    ) -> None:
        if self._undo_requested:
            self._finish_undo(session_id, user_message_id, error=message)
            return
        sid = session_id or self._ask_in_flight
        in_view = sid is None or (
            self.runtime.has_session and self.runtime.current.id == sid
        )
        if in_view:
            if self._stream_widget is not None:
                # 中途断流：保留已生成的半截并显式标注，不静默吞掉。
                interrupted = self._stream_buffer + "\n\n*(generation interrupted)*"
                self._finalize_stream_segment(interrupted)
                self._chat().mount(Static("", classes="divider"))
                self._scroll_end()
            self.add_card(message)
        else:
            self.notify(f"Background request failed: {message}")
        self._heal_current_session(sid)
        self.refresh_sessions()
        self._end_ask()
        # 通用失败出口：压缩/导入/切换失败走这里时还要释放导航忙。
        self._end_navigation()
        if self._pending_command:
            # 切回目标会话失败：挂起的命令失去目标上下文，丢弃而非误伤当前会话。
            self.notify("Queued command dropped: session switch failed")
            self._pending_command = None
        self._drain_pending_intent()

    def _plan_is_current(self) -> bool:
        """last_plan 属于别的会话时不得污染当前视图的上下文用量显示。"""
        runtime = self.runtime
        if runtime.last_plan_session is None:
            return True
        return runtime.has_session and runtime.last_plan_session == runtime.current.id
