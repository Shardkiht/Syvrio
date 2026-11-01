from __future__ import annotations

import threading
import time
from functools import partial

from rich.markup import escape


class ChatReflectionMixin:
    """回顾 worker 不占聊天 busy；取消令牌在主线程创建，覆盖尚未启动的任务。"""

    def _start_auto_reflection(self) -> None:
        self._reflection_last_activity = time.monotonic()
        self._reflection_next = 0.0
        self._reflection_remaining = self.service.config.chat.reflect_request_budget
        self._reflection_mode = "dream"
        self._reflection_paused = False
        self.set_interval(5, self._auto_reflection_tick)

    def _reflection_activity(self) -> None:
        self._reflection_last_activity = time.monotonic()

    def _auto_reflection_tick(self) -> None:
        config = self.service.config.chat
        now = time.monotonic()
        if (not config.auto_reflect or self._reflection_paused or not getattr(self, "_reflection_ready", False)
            or self.busy or getattr(self, "_reflection_pending", False) or self._reflection_remaining <= 0
            or now < self._reflection_next or now - self._reflection_last_activity < config.reflect_idle_seconds):
            return
        from textual.widgets import Input
        if self.query_one("#input", Input).value.strip() or len(self.screen_stack) > 1:
            return
        self._reflection_next = now + config.reflect_interval_seconds
        self._reflection_pending = True
        self._reflection_cancel = threading.Event()
        mode = self._reflection_mode
        self._reflection_mode = "profile" if mode == "dream" else "dream"
        # 每轮只发一次；缺少新材料时引擎不调用模型，也不消耗预算。
        self.run_worker(partial(self._auto_reflection_work, mode, self._reflection_cancel),
                        thread=True, group="reflection", exit_on_error=False)

    def _auto_reflection_work(self, mode: str, token: threading.Event) -> None:
        try:
            result = self.service.reflection.run(mode, 1, cancel_event=token)
            self.call_from_thread(self._after_auto_reflection, result, None)
        except Exception:
            self.call_from_thread(self._after_auto_reflection, None, "Automatic reflection failed; progress preserved.")

    def _after_auto_reflection(self, result, error: str | None) -> None:
        self._reflection_pending = False
        self._reflection_next = time.monotonic() + self.service.config.chat.reflect_interval_seconds
        if result is not None:
            self._reflection_remaining -= result.requests
            error = result.error
            if result.proposed:
                self.notify(f"Background reflection proposed {result.proposed} inferences. Review with /inferences.")
        else:
            self._reflection_remaining -= 1
        if error:
            self.notify(error)

    def _reflection_command(self, mode: str, argument: str) -> None:
        if argument == "resume":
            self._reflection_paused = False
            self.add_card("Automatic reflection resumed; it will continue when idle.")
            return
        if argument == "cancel":
            self._reflection_paused = True
            token = getattr(self, "_reflection_cancel", None)
            if token is not None:
                token.set()
            self.service.reflection.cancel()
            self.add_card("Cancellation requested; stopping after the active request returns without publishing its candidates.")
            return
        if argument == "status":
            running = "running" if getattr(self, "_reflection_pending", False) else "idle"
            enabled = self.service.config.chat.auto_reflect and not getattr(self, "_reflection_paused", False)
            self.add_card(f"Reflection {running}; automatic reflection {'enabled' if enabled else 'paused/disabled'}; remaining request budget {getattr(self, '_reflection_remaining', 0)}.")
            return
        if mode == "profile" and not argument:
            self.run_worker(self._profile_work, thread=True, group="profile-view", exit_on_error=False)
            return
        if mode == "profile" and argument.split()[0] != "refresh":
            self.add_card("Use /profile to view the profile; /profile refresh [0–20] generates proposals.")
            return
        value = argument.removeprefix("refresh").strip() if mode == "profile" else argument
        try:
            budget = int(value) if value else 1
            if not 0 <= budget <= 20:
                raise ValueError
        except ValueError:
            self.add_card("Usage: /dream [0–20|cancel|status], /profile [refresh [0–20]|cancel|status]")
            return
        if getattr(self, "_reflection_pending", False):
            self.add_card("Reflection is already running. Use /dream cancel to cancel.")
            return
        self._reflection_cancel = threading.Event()
        self._reflection_pending = True
        self.add_card(f"Background reflection started: at most {budget} model requests. You can continue chatting or switch sessions.")
        self.run_worker(partial(self._reflection_work, mode, budget, self._reflection_cancel),
                        thread=True, group="reflection", exit_on_error=False)

    def _profile_work(self) -> None:
        try:
            items = self.service.reflection.profile()
            labels = {"active": "Fact", "hypothesis": "Proposed inference", "confirmed": "Confirmed inference"}
            text = "\n".join(f"[{labels.get(item.status, item.status)}] {item.text}\nSources: {', '.join(item.source_ids)}" for item in items)
            text = text or "No profile yet. Save preferences, goals or habits; /profile refresh can generate proposals."
            text += "\nCorrect or forget facts using the existing controls; review inferences in /inferences."
        except Exception:
            text = "Could not read the profile. Check local memory and inference logs."
        self.call_from_thread(self.add_card, escape(text))

    def _reflection_work(self, mode: str, budget: int, token: threading.Event) -> None:
        try:
            result = self.service.reflection.run(mode, budget, cancel_event=token)
            message = (f"Reflection {'cancelled' if result.cancelled else 'complete'}: requests {result.requests}, "
                       f"proposed {result.proposed}, remaining {result.remaining} batches.")
            if result.error:
                message += f"\n{result.error}"
            if result.proposed:
                message += "\nView and review with /inferences."
        except Exception:
            message = "Reflection failed; local progress preserved. Check the job log before retrying."
        self.call_from_thread(self._after_reflection, message)

    def _after_reflection(self, message: str) -> None:
        self._reflection_pending = False
        self.add_card(escape(message))

    def on_unmount(self) -> None:
        token = getattr(self, "_reflection_cancel", None)
        if token is not None:
            token.set()
        self.service.reflection.cancel()
