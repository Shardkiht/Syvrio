# 开发交接

## CI 环境与失败修复（2026-11-02）

- 用户指定远程测试环境统一 Debian：演进分支的测试与发布 workflow 均使用 Debian 13 slim 容器、Python 3.12；Ubuntu runner 仅作为 Docker 宿主。安装 Git、CA 证书与 Node 所需 C++ 运行库后再 checkout。保留测试、构建和 CLI help 检查，未修改冻结 main 的 workflow。
- Actions run 41368204299：Ubuntu job 通过；Windows job 在会话切换 UI 测试失败（934 passed、4 skipped、1 failed），CLI help 步骤因前序失败跳过，不是 CLI 启动错误。
- 修复测试同步条件：导航标志结束不代表 Textual 异步移除完成；等待目标会话、导航就绪与实际回复控件状态，并等待完整流式缓冲，保留清空和切回重放断言。局部相关 3 项通过，扩大会话切换/流式/导航回归 18 项通过；uv build 和 qm --help 均通过，YAML 结构校验通过，未调用真实模型或搜索。
- 旧章节中的双平台 CI 描述属于历史，不代表当前演进分支工作流。新 Debian 容器的执行结果须以推送后的 Actions 为准。

## 当前开发分支与冻结约定（2026-11-01）

- **长期远程保留 `main` 与 `feature-memory-evolution`**；历史 `base/chat-stability`、`feature/context-review-recall` 已不在远程，审核期间可存在待清理的短期 PR 分支。删除前的祖先检查记录未独立复核。历史章节中的 base 开发、自动同步 main、提交前默认全量测试均已失效。常规开发应在 evolution 或由其派生的短期任务分支进行；main 保留 GitHub 默认分支身份。
- **后续默认开发分支：`feature-memory-evolution`**。所有新功能、常规问题修复、实验和相应文档工作从此分支（或从它派生的任务分支）开展。执行前确认当前 branch，不在默认的 `main` 上直接开发。
- **`main`：PR #15 合并后冻结展示源码，PR #16 为经授权的发布元数据维护；此后仅用于简历展示、稳定发布与长期维护**。禁止自动将演进分支、历史 `base/chat-stability` 分支向 `main` 同步或合并；只有本人明确点名授权的必要稳定性/安全修复才可走独立修复与受保护分支 PR 流程。
- 历史冻结前源码评审基线为 `main@b016ccbf`，详见 [review-2026-11-01-freeze.md](review-2026-11-01-freeze.md)，不得将其当作当前 HEAD。PR #15 合并提交 `316a030` 对应 `portfolio-2026-11-01`；PR #16 合并提交 `22217c2` 对应 `v0.3.3`。历史 base 同步安排全部作废。
- PR #15 已合并，`portfolio-2026-11-01` 指向 `316a030`；PR #16 已合并，`main` 当前 HEAD 为 `22217c2`，`v0.3.3` Tag 和 GitHub Release 均已存在。两次 PR 的 Windows/Ubuntu CI 均通过。PyPI `0.3.3` 本轮未通过官方发布记录独立复核；原生终端/IME/系统剪贴板仍待人工验收。

- **PR #16 发布维护已同步（2026-11-02）**：本分支通过 `main@22217c2` → `feature-memory-evolution` 单向合并吸收 PR #16 的四处版本变更：`pyproject.toml`、`__init__.py`、`open_websearch.py` 的 MCP clientInfo、`uv.lock`，统一为 `0.3.3`；中英文 README 保留演进功能说明，修正已过期的“尚未同步”描述。合并提交为双父提交，保留 `main` 的完整祖先历史以及本分支原有功能；未将 evolution 反向合入 main。此前 Windows CI 的会话切换异步测试仍应独立复核，合并行为不代表测试已修复。

## 历史接续记录（2026-10-30；不可作为当前入口）

本节保留 2026-10-30 当时的接续快照，不能作为 2026-11-02 的分支 HEAD、发布版本或任务优先级依据；下方均为按时间保留的历史工程记录。后续实现已改变部分旧边界；交接记录不替代当前会话授权。

- 远程目标 `feature-memory-evolution`，本地功能分支 `codex/feature-memory-evolution`；主目录 main 保持独立，不自动合并。当前功能基线 `8b8d507`；main 的命令精简基线 `a7777c0`。
- TUI 默认空闲回顾：补记结束后空闲 60 秒，Dreaming/画像轮转，间隔 300 秒，每次启动自动预算 20 次；配置可关闭，cancel 暂停，resume 恢复。进程退出后无守护任务。预算耗尽不会由 resume 自动补满，手动执行使用单独预算。
- 画像跨全部当前有效事实提炼，兼容中文与自定义主题；事实展示只纳入常见主题及有效画像推断引用的来源。仅已确认且来源与本轮召回相关的画像推断注入上下文。Dreaming 推断仍仅供审查。
- TUI 会话入口仅 /sessions；/resume、/recall、/remember 已删除，Agent recall/memorize 与 CLI 管理功能保留。
- 检索重跑已完成，两分支基础三路检索命中率一致；完整汇总及方法在 [评测说明](../evals/README.md)。固定合成题集与模型生成真实题集分开统计，不能把生成题集当人工金标准，也不能与旧题集成绩直接作涨跌比较。
- 时间有效期探针中 evolution 排除过期/未来事实，main 未实现该筛选。无个人记忆意图的通用问题仍常得到非空结果，下一步优先评估召回门控；本轮未验证最终回答是否误用记忆，不能声称已有无关记忆拒答能力。
- 两边固定记忆解析/裁决均 24/24；evolution 上下文对照 5 例均通过。最近功能全量回归 600 passed。真实数据、查询、来源ID、模型输出和本机配置均只在本地忽略目录，不写入交接文件或提交。
- 本次文档核对提交前全量回归 600 passed（281.52 秒），git diff --check 通过；仅更新文档，未改产品行为。
- 建议后续先做后台状态/配置交互与召回门控评测；复杂时序重排、推断情绪和跨客户端主动召回仍未完成。功能待办按 GitHub Issues 维护。

发布历史日期：2026-10-29。代码版本 `0.3.2`，发行标记使用 `v0.3.2`；基础功能参照 `444fe0f`，文件导入与模型选择界面参照 `bef5199`。包版本、锁文件与 MCP 客户端标识保持一致；远端发布结果以 GitHub Release、Actions 与 PyPI 为准。

更新日期：2026-10-31。代码版本 `0.3.2`，发行标记使用 `v0.3.2`；基础功能参照 `444fe0f`，文件导入与模型选择界面参照 `bef5199`。包版本、锁文件与 MCP 客户端标识保持一致；远端发布结果以 GitHub Release、Actions 与 PyPI 为准。

## 搜索质量优化（2026-10-31，base/chat-stability）

按《联网搜索质量优化实施方案》分阶段完成 P0（Phase 0-3），逐阶段提交：Phase 0/1 `d3ec502`、Phase 2 `79ccbb0`、Phase 3 `87a66fd`。

- 离线基准：`evals/web_search_eval.py`（33 条合成查询、固定候选池、PoolTransport mock；`--save/--compare/--json`），基线快照 `evals/web_search_baseline.json`。合成数据零个人信息，可公开提交。
- QueryAnalysis（`infra/search/quality.py`）：core/context/intent 三层分离——core 只来自原始查询并决定相关性；context 低权重消歧（0.5/0.25），不能单独令结果通过质量门控；时间词（今天/最新/latest…）与事件词（发布/官宣/更新…）不进 core。拉丁词元词边界匹配（`tibo` 不命中 `tibonacci`），CJK 按受控停用词/时间/事件词表轻量切分并保留短语序，≥4 字片段补二元词元；无高置信实体时 `ambiguous=True`。
- 渐进式搜索 + QualityGate：每次请求向上游拉 `fetch_limit = min(30, max(10, limit*3))` 条，进统一 `CandidatePool`（URL 去重、www. 宿主归一、保留各引擎名次证据与更完整标题/摘要）。早停条件：≥2 条标题级强命中，或单条标题覆盖全部 core 词，或单实体导航型查询 1 条强命中；都不满足才继续变体/候补引擎。低相关候选收尾时原样返回并附提示，核心词命中路径按成功语义缓存，零核心命中路径短缓存。
- 超时预算：`SearchQuery.timeout` 由 router 按剩余预算下发（`round(remaining,3)`），HTTP transport 逐请求生效、MCP transport 取 `min(self.timeout, timeout)`；预算计时仍用 `time.perf_counter`。
- 确定性 ranker：`ScoreBreakdown` 逐特征贡献（标题核心 3/词元、摘要 1/词元、全核心覆盖 +2、intent 0.5/词、context 0.5/0.25、引擎内名次 1.2/0.6/0.3、跨引擎交叉 +1.0/+1.5、时效查询有 published +0.3）；平分保持首次入池顺序；无日期不伪造。
- engine 归属：`_map_result` 逐条读取 daemon 的 `engine`/`source` 字段，router 只回填空值（不再一律覆盖成槽位引擎）；daemon `partialFailures` 有部分结果时转成结构化 `SearchFailure`（`provider.last_partial_failures` 通道），不再静默吞掉。
- 缓存键升到 v7（排序策略变化即换键）；低相关候选短缓存、核心命中正常 TTL、失败永不入缓存的政策不变。
- 质量对比（同一固定候选池 vs 基线）：nDCG@5 0.7387→0.8944（+21% 相对），Success@5 0.5455→0.7273，P@5 0.1879→0.2364，误接受率 0.1515→0.0606；平均请求数 1.48→2.30（弱命中查询按设计多试候补，强命中仍单请求早停）。全量 653 测试绿。
- 遗留（P1 待办）：`SearchQuery.lang/freshness` 是否被 open-websearch daemon 支持尚未核实，透传前先验证；`SearchDiagnostics` 结构化诊断未做；模糊实体泛匹配误接受（如 se5「wjx-handler ai」命中 handler/ai 泛词）为词法门控的已知边界，按任务书不引入 LLM rerank。

## 免费联网搜索增强（2026-10-31，base/chat-stability）

- 引擎候补链：首选引擎空结果、结果与查询核心词不相关或命中过弱（质量门控未达标）或请求失败时，按 `search.fallback_engines`（默认 baidu→duckduckgo→sogou）自动降级，最多 `search.max_engines`（3）个引擎，共享 `search.timeout_budget`（25s）超时预算且单次请求超时不超过剩余预算；显式 `search_engine` 保持单次请求语义不变。引擎回退只对声明 `engines` 能力的 provider 生效（OpenWebSearchProvider 两种 transport 均已声明），provider 级降级顺序保留。
- 查询变体：`search`/MCP `search` 新增 `context` 参数（对话中确认的专有名词，最多 5 个）；原始查询无有效结果时确定性派生最多 2 个变体（追加 context 词项，不改写原拼写），不调用 LLM。
- 缓存分级：真空结果短缓存 5 分钟、「今天/最新/latest」类时效查询成功结果 10 分钟、低相关候选 10 分钟；任何上游失败一律不入缓存。`SearchCache.set` 支持按条目覆盖 TTL（不超过实例 TTL）；键版本见上方"搜索质量优化"（当前 v7）。
- 结果处理：统一候选池去重合并后按确定性 ranker 排序截断（见上方"搜索质量优化"）；`SearchResult.engine` 记录实际来源引擎并进入 payload；零核心命中时如实提示"候补引擎未找到…以下为候选"。
- 工具上限：search 工具 limit 硬上限 10→15（schema 同步）；默认值仍来自 `search.max_results`。
- 计时注意：Windows `time.monotonic` 分辨率约 15.6ms，搜索预算计时用 `time.perf_counter`，勿改回。
- 已知上游限制：open-websearch 无验证码识别（上游弹验证码表现为空结果或跑题内容）；bing 对小众英文账号（如 thsottiaux）可能返回无关内容，依赖 baidu 候补兜底；baidu 返回的是跳转链接（baidu.com/link?url=...，QM 不主动解析，需经 fetch_web）；fetch_web 偶发 daemon HTTP 502。真实冒烟 7 条查询对比与 LLM 端到端在 be6d632 前后完成（冒烟脚本在系统临时目录，不入库）。

## 多厂商搜索适配（Phase B，2026-10-31，base/chat-stability）

- 外部厂商：`baidu_search`（qianfan，双鉴权头可配置待冒烟定夺）、`tavily`、`exa`（type 固定 auto）、`you`（X-API-Key，日期字段未核实保持 None）、`volcengine`（global/custom 双模式）。注册表在 `router._EXTERNAL_PROVIDERS`，Key 走环境变量（如 `BAIDU_SEARCH_API_KEY`），未配置 Key 静默跳过；适配器全部经 `http_client.JsonApiClient`（非 2xx 一律抛 `ProviderError`，错误 detail 只含状态码不回传响应体）。全部 MockTransport 测试覆盖，真实冒烟未做。
- 请求预算：`search.max_requests`（默认 9）为一次搜索跨所有 provider 共享的请求次数上限；查询变体只在第一家 provider 上执行。耗尽时返回池内最佳候选并附截断提示，该结果**不写入缓存**（缓存会丢截断提示，下次搜索应重新请求）。`ProviderErrorKind.BUDGET_EXHAUSTED` 表示本地预算耗尽，与厂商账户配额 `QUOTA`（402 等）严格区分。
- 交叉来源统计：`CandidatePool` 排名证据为 `(provider, engine, rank)` 三元组，corroboration 按 distinct (provider, engine) 计数——外部厂商 engine 为空时凭 provider 身份参与统计；`SearchResult.engine` 语义不变（上游引擎名）。
- 火山引擎 Query 官方上限 100 字符：超限抛 `ProviderError(BAD_RESPONSE)`，不静默截断。
- 待办（v1.2 方案卡 09-14）：独立 FetchRouter 与四家 Fetch 适配、`qm setup` 搜索 Key 菜单、配额保护、文档同步；五家统一受控真实冒烟（每家 ≤10 次）待授权执行，冒烟后固化 Baidu 鉴权头、You.com 日期字段、火山 Custom NeedContent 的真实行为。
- FetchRouter（卡 09）：抓取调度从 `SearchRouter.fetch` 抽到 `infra/search/fetch_router.py`，SearchRouter 保留兼容入口内部委托；新增 `[fetch]` 配置（`providers`，默认 `["open_websearch"]`，与 search.providers 独立，旧配置缺省即原行为）；agent 的 `fetch_web` 工具名/参数/返回结构不变，显式注入 search_router 的旧 DI 路径保留。
- 四家 Fetch（卡 10）：`TavilyFetchProvider`（/extract，Bearer，单 URL Basic）、`ExaFetchProvider`（/contents，x-api-key，body 恰为 {urls, text:true}）、`YouFetchProvider`（/v1/contents，X-API-Key，{urls, formats:["markdown"]}，响应形状二手资料待冒烟）、`VolcengineFetchProvider`（/search_api/fetch，字段名按 Search 同族约定待冒烟）。正文经 `truncate_fetch_content`（base.py）截断；空正文/失败抛 ProviderError 由 FetchRouter 回退。注册表 `fetch_router._EXTERNAL_FETCH_PROVIDERS`，Key 环境变量与对应 Search 相同。
- Key 读取（卡 11）：`config.read_api_key`（env 优先、Keyring 回退）统一供 search/fetch registry 与 setup 使用；`qm setup` 顶层分「模型与 LLM」/「搜索与网页抓取」两个向导（providers.py 的 run_setup/_run_llm_setup/run_search_setup），官方厂商不自动启用、无 Key 拒绝启用，TOML 不落 Key。测试用假 ask + 假 questionary + 假 keyring 脚本化交互。
- 额度限制（卡 12）：`infra/search/usage.py` 的 `UsageLimiter`（`search.usage_limits.<provider>`：period daily/monthly + max_calls，max_calls<=0 视为不限制）；Search/Fetch 同厂商共用一个计数池，计数在实际发起请求前记账（失败保守计数），状态在 vault `.quiet-memo/usage.json` 原子落盘，读前按 mtime 重载以兼容两个路由实例；达上限的失败分类是 `quota`（detail 注明本地上限，与厂商配额语义一致但 detail 可区分）。setup 启用官方厂商时询问每日上限（默认 20）。本地计数不是服务商账单上限。
- 集成与冒烟（卡 13）：`tests/test_multi_provider.py` 覆盖五 Search + 四 Fetch 注册矩阵、Search/Fetch 顺序独立、无 Key 不注册不发请求、search/fetch_web 工具协议、冒烟脚本 dry/live（假件注入）；`scripts/smoke_search_apis.py` 默认 dry 零请求，`--live` 才对单一厂商发 ≤max-requests（默认 1）次真实请求，报告脱敏。真实网络冒烟仍未执行，待验证：百度鉴权头、You.com Contents 响应形状、火山 Fetch 字段名与 Custom NeedContent、各家 count 上限。

## 忙碌态解耦与会话一致性（2026-10-31，分支 base/chat-stability）

- **历史流程（已废止，不得执行）**：当时基础修复使用 `base/` 前缀，再分别合入 main 与 evolution。现行开发仅在 evolution（或其短期派生分支）；禁止自动向冻结 main 同步。
- 等待 LLM 期间输入保持可用、会话切换立即执行；等待期提交（消息与 /命令）进入全局 FIFO 队列，按提交顺序执行且任意时刻至多一个请求（并发第二个请求会被 exclusive worker 协作取消且 runtime.ask 无重入保护，故只能排队）；导航/只读命令（/new、/sessions、/exit 等）等待期直接执行。旧的全局 busy 布尔拆为 navigation_busy 与 ask_active 两态，输入框只在导航期间禁用。
- 数据一致性：`runtime.ask` 支持显式 session 并新增 on_session 回调；`_auto_recall`/`_flush_memories` 显式绑定请求会话，不再读 self.current；`last_plan` 带 session 标识，状态栏不串会话；后台任务执行时从磁盘新鲜加载会话对象，完成后若目标是当前会话则 reload 治愈内存快照；切走/新建时对生成中的会话延迟打 closed/distill_deferred 标记（保证排在最后的 assistant 记录之后）；生成期间跳过后台补沉淀，留给启动补记；删除守卫拒绝删除生成中或被队列引用的会话——物理删除后后台追加会原路重建僵尸文件（已用临时库脚本实证）。
- 切回生成中的会话：磁盘重建负责已完成轮次，界面只重放未落盘的活跃段（已完成段必然已随 assistant 记录落盘，天然去重）。
- 输入光标：原生光标仅用于支持 DECSCUSR 的终端（WT_SESSION/WT_PROFILE_ID/TERM_PROGRAM，conhost 退回自绘）；`on_resize` 重算 app.cursor_position，修复布局变化（折叠侧栏、窗口缩放）后硬件光标停在旧坐标的问题。rich 宽度表与终端在 emoji/歧义宽度字符上的渲染差异仍需真实 PowerShell 人工验证，headless 测试无法覆盖。
- 测试：新增 10 个回归（跨会话全局 FIFO 验收场景、等待期输入可用、立即切换、流式重放、关闭标记顺序、删除守卫、补沉淀跳过、光标终端门控与重算等）；同步修稳两个既有负载抖动测试——启动补记可能晚于测试打点触发 refresh_sessions（干扰计数与点击旧控件），driver.write 全量捕获会被帧渲染写入污染 `writes[-1]` 断言。
- 验证：全量 `uv run pytest` 592 passed 连续两轮；分支未合并、未推送。

## 环境变量污染事件与抓取超时（2026-10-31）

- **污染事件**：`QUIET_MEMO_CONFIG`/`QUIET_MEMO_VAULT` 曾被 `setx` 持久化进 Windows 用户注册表（本应只在手动测试启动器进程内注入），导致此后所有新进程（含 TUI 会话）加载测试配置与测试 vault，期间的会话沉淀写入了测试库。已从注册表删除这两个变量。教训：多环境隔离只能用进程级环境变量或启动器包装，禁止 `setx` 等持久化写入；已在运行的长驻程序需重启才脱离旧环境。
- **数据处置**：污染窗口期写入测试库的沉淀按用户决定留在测试库，不抢救、不回滚。定位（2026-10-31 拍板）：本地一切（vault、本地 personal-memory 克隆）按测试环境对待，当前记忆标准源是远程 personal-memory 仓库，终态 vault 单源化未到。
- **抓取超时**：真实网络排查确认抓取目标站响应 24-42 秒且上游间歇 502，原默认 `search.fetch_timeout=25s` 会先于上游掐断约一半尝试；默认提升至 45s，config 数据类、加载 fallback、setup 模板、示例配置、双语 README 与测试同步（`6c24553`）。已有配置文件若显式写 25.0 需手动改为 45.0；未写该键则自动获得新默认。
- **搜索侧结论**：当次 search 失败为 Bing 间歇 TLS 失败后回退 Baidu 撞验证码，属上游瞬时问题，未改代码；daemon 日志中 request-filtering-agent 的 CIDR 告警是已捕获的良性警告（即此前记录的上游地址族比较问题）。
- fetch_timeout 相关提交未经本轮本地全量回归（由用户直接提交推送），以 CI 双矩阵结果为准；后续改动仍遵循"全量 pytest 绿了才提交"。

## 检索评测重跑（2026-10-30）

- main 已完成合成库与真实库三路检索评测：456 条合成记忆/27 个固定用例，882 条真实有效事实/24 个模型生成问题。合成题集为固定用例；真实题集由模型生成，不属于人工标注金标准。
- 基准结果：合成 keyword/vector/hybrid 的 MRR@10 为 0.722/0.913/0.913；真实三路为 0.889/0.814/0.842，真实 Hit@5 均为 95.8%。固定记忆解析与裁决用例 24/24。
- 有效期探针中 main 仍返回过期和未来事实，时间过滤尚未实现；无个人记忆意图的通用问题仍会得到非空结果，尚未验证最终回答是否误用。后续优先评估召回门控。
- 私有题集、逐题明细和原始耗时只在本地忽略目录，不写入交接文件或提交；本次未修改产品代码或个人库。方法与完整结果见 `evals/README.md`。

## 0.3.2 发布核对

- 版本覆盖 `pyproject.toml`、`__init__.py`、`uv.lock` 根包与联网搜索 MCP 客户端标识；新增功能说明已同步双语 README，Release 汇总从 `v0.3.1.1` 以来的变更。
- 本地已构建 wheel 与源码包，检查版本、`documents` extra 和新增模块均正确，未包含本地配置、vault、会话、缓存或虚拟环境。
- 启动自动提交和补沉淀的 UI 测试改为等待后台任务完成再验证，不再依赖固定刷新次数或短时轮询；功能断言保持原样。
- 发布前全量：`uv run --frozen --offline --extra documents pytest -q`，536 passed；`uv lock --check --offline` 通过。双平台 CI 和 PyPI 发布状态需通过远端记录核对。
- Release published 触发 `.github/workflows/workflow.yml` 自动测试、构建并通过 OIDC 发布 PyPI；仅推送版本提交或标签不会发布。

## 模型与供应商选择界面

- `/model` 列表仅展示模型，供应商操作不再作为模型条目混排。模型面板底部提示 `Ctrl+P` 打开独立管理菜单（添加 / 更新 Key / 移除），`Ctrl+R` 刷新，`Ctrl+N` 输入自定义模型名；管理菜单按 Esc 返回模型列表。
- `ModelPickerScreen` 复用现有选择器，单独约束模型列表高度，为搜索框和快捷键提示留空间。`ChatApp` 仅在模型选择器中重定向 Ctrl+P，其他界面仍使用 Textual 原命令面板。后台模型列表刷新仍校验原选择器身份，不能覆盖已打开的供应商管理界面。
- 本次只调整界面编排，保留配置、凭据存储与模型切换逻辑；使用隔离 UI 测试验证，不再消耗真实模型请求。
- 验证：模型选择、供应商管理、返回、快捷键、后台刷新隔离及两种窗口尺寸均通过。早期界面分类回归出现过现有启动自动 Git 提交用例超时，相关 12 项复测通过；提交前最终全量 `uv run --frozen --offline --extra documents pytest -q` 为 536 passed。若再次遇到后台 Git 时序波动，应先检查任务实际完成状态。

## 文件分析与导入

- 用户可粘贴/拖入绝对文件路径并用自然语言要求分析或导入记忆。带空格路径需引号，拖放路径转换取决于终端。仅本条用户消息中显式给出的支持格式文件可用；不沿用历史消息或文件内路径授权，不开放目录读取。
- Agent 工具 `read_file` 按字符游标分页并限制输出 token；`import_file` 每次抽取一块，默认 dry-run，用户明确要求写入长期记忆时才设 apply。返回下一块游标，步数用尽须说明未完成。预览和实际导入都会产生模型抽取请求，用户应了解费用。
- `/import <path> [--apply]` 与 CLI `qm import` 支持当前层目录；TUI 在 worker 运行，默认预览，失败释放 busy 并接续待切换意图。只读取/分析文件不会自动把全文作为个人记忆存储。
- `infra/documents.py` 读取常见文本，复杂格式复用 MarkItDown 可选 `documents` extra；20 MiB 文件上限，未启用插件、云端解析、OCR 或音视频转写。JSON/JSONL 保留原始角色和时间信息，不承诺专用客户端语义适配或跨块完整性。
- `agent/file_tools.py` 隔离文件路径与本轮解析缓存；文件内容脱敏后进入模型工具结果，导入保留文件名及块编号。工具只提供给内置 Agent，不扩展对外 MCP server。
- 新行为使用合成文件、固定抽取和假模型验证。2026-10-29 经授权使用 Spark 做了两轮共 10 次真实请求（达到本轮上限），分别验证显式指定工具、只提供路径与自然语言意图的 read_file / import_file 链路，以及助手建议未被误写为用户事实；保留独立测试库及会话，不读取个人库。不继承本轮调用预算，后续真实测试须按当前授权执行。最终测试记录以本轮实际结果为准。
- 文件导入初轮全量验证为 530 passed；合并模型选择界面优化后的提交前最终全量为 536 passed。真实本地转换覆盖 HTML、DOCX、XLSX、PPTX，其他格式通过统一适配契约测试，不能当作每一种真实文件均已验证。已有两处异步界面测试改为等待目标状态；命令面板按最长用法计算列宽。新增解析依赖已安装到项目环境，日常启动器使用当前项目源码；相关功能纳入 0.3.2。

## 基础版本范围（444fe0f）

本轮实现 [#10](https://github.com/Shardkiht/quiet-memo/issues/10)、[#11](https://github.com/Shardkiht/quiet-memo/issues/11) 的基础部分，并建立 [#14](https://github.com/Shardkiht/quiet-memo/issues/14) 的首批合成解析与裁决回归。未提高包版本，也未发布到 PyPI。

## 已实现

- 独立 `.venv` 与锁定依赖可安装，支持离线缓存；仓库提供 VS Code pytest 发现和调试配置。
- `MemoryContext` 包含可选事件日期、生效起止日期、时间原话、地点类型和显式情绪。日期支持年、月、日精度，检查非法日期和倒置区间。
- 普通抽取与导入使用同一上下文契约。缺少可靠时间锚点时只保留相对时间原话；语气推断不写入情绪事实。
- 上下文写在 Markdown 行尾 `context` JSON 标签中，沿用标签转义，旧格式无需迁移。候选排队、普通确认和 resolved 记录保留上下文；改写后确认及手动更正清除旧上下文。
- 正文和新增上下文共同经过凭据拦截。条目 ID、来源、软删除与替代关系保持现有语义。
- `MemoryService.propose_inference()` 只把假设追加到 `.quiet-memo/inferences.jsonl`，新记录为 `hypothesis`，包含类型、来源 ID 和带时区的生成/更新时间。
- 来源去重且必须是有效事实；同类型、同规范化文本、同证据集合重复登记返回原记录。推断不能支持另一推断，不进入 Markdown 事实库或普通召回。
- `evals/memory_eval.py` 提供固定合成输出的解析、冲突和上下文回归，并通过 `tests/test_memory_eval.py` 接入 pytest/CI；推断边界由独立领域测试覆盖。
- 离线验证发现并修复 token 截断在极小预算下超限的问题；字符估算分支按最终预算截断，tokenizer 分支避免截断产生无效 Unicode。
- 正式增加讯飞 Spark MaaS provider：配置向导、密钥环境变量、模型预设与 OpenAI 兼容调用；适配其采样默认值、输出上限以及 JSON 提示词约束。
- 修复 AI Markdown 回复无法选择复制：保留单控件绘制，通过带文本坐标的 Content 渲染选择高亮；覆盖流式、历史回复与窗口缩放。恢复会话成功不再弹出通知。

## 主要入口

| 文件 | 职责 |
| --- | --- |
| `memory/models.py` | 上下文和推断领域模型、字段校验 |
| `memory/extractor.py` | 普通抽取/导入的上下文契约 |
| `memory/store.py` | `context` 标签的读写与转义 |
| `memory/service.py` | 裁决、确认与推断证据检查 |
| `memory/inference.py` | 独立推断日志的追加和读取 |
| `evals/memory_eval.py` | 离线合成解析与裁决回归 |

以上源码路径相对 `src/quiet_memo/`，评测路径相对仓库根目录。

## 复现与调试

```bash
uv sync --frozen
uv run pytest
uv run pytest -m memory
uv run python evals/memory_eval.py
```

缓存齐全时可使用 `uv sync --frozen --offline`。网络受限环境可以下载与 `uv.lock` 对应的官方 wheel 并校验哈希，再用 `uv pip` 安装到项目 `.venv`；不要用全局包路径替代最终测试环境。共享缓存不可写时，项目默认的 `.cache/uv` 可独立使用。

VS Code 选择 `.venv` 后可从测试面板下断点，或使用 `.vscode/launch.json` 的当前文件/全量配置。不要运行真实 `qm` 会话验证测试：夹具会隔离配置、vault 和凭据，调试测试时也应保留这些护栏。

当前受限 Windows 执行环境禁止回环 TCP，默认 asyncio 在 `socketpair` 初始化时阻塞。测试专用开关 `QUIET_MEMO_TEST_PIPE_LOOP=1` 使用本地管道唤醒 Proactor，保持正常异步调度与跨线程回调；它不改变应用运行时或网络权限。普通终端与 CI 不必启用。当前环境同时用 `UV_FROZEN=true` 避免全局镜像配置触发重新解析依赖，用 `UV_OFFLINE=true` 复用已准备的锁定依赖。

## 本机手动测试

手动测试使用独立虚拟环境与配置，包以 editable 方式指向项目源码；修改保存后重启即可测试。不在交接文档保存本机路径。

测试 vault 是用户指定记忆库的独立副本，拥有自己的 Git 历史，无远程仓库；只复制长期记忆与人设，没有复制旧会话。新会话仅追加到副本的 `sessions/`。启动检查已验证原库文件哈希未变。

启动器通过进程环境变量隔离配置、vault、凭据与 tokenizer 缓存；凭据和个人配置仅存本地，不入库。

## 验证记录

- 本地 Windows / Python 3.12.14，独立 `.venv`，126 个运行/测试依赖符合锁定版本，未借用全局工具环境。
- `uv sync --frozen --offline`：通过。
- `uv run pytest -q -x --tb=short -o faulthandler_timeout=45`：478 passed，147.57 秒；使用上述受限 Windows 测试环境开关。
- `uv run python evals/memory_eval.py`：24/24 通过。
- `git diff --check`：通过。

Spark 真实接口合成数据冒烟：流式回复、带时间/地点的记忆抽取、`read_topic` 工具结果回传均通过，共 4 次请求。当前环境不能由 Python 直接建立网络连接，因此保留项目 LiteLLM/OpenAI 的请求序列化和响应解析，通过本地文件转交已授权网络客户端发送原始请求；这验证了 API 接线和响应形状，未验证普通终端的直连网络或逐帧延迟。测试凭据和冒烟产物均在本地忽略路径；未发送个人记忆。

普通 Windows 事件循环与 Ubuntu 的最终验证以 GitHub Actions 双矩阵结果为准。

## 当前剩余规划

- #10：已补原始消息时区偏移、逐消息抽取锚点与确定的相对日/月/年解析；复杂自然语言时间依赖抽取模型，未知或无时区旧记录不猜测。推断情绪仍待实现。
- #11：已补 CLI/TUI 查看、确认、拒绝、更正、来源失效、追加状态事件和显式损坏尾行恢复。来源审查与操作共用写锁；更正产生新假设，确认不变成事实。合入前保持 Issue 开放。
- #12：已实现事件日期范围、地点、显式情绪筛选，CLI/Agent/MCP 共用服务入口，先筛选再截断；无筛选保留原行为。当前/历史视图与显式演化已在功能分支实现；复杂时序重排仍待完善。
- #14：在程序契约回归之外增加真实模型语义抽取评估、时间演化、无关注入率、过时事实与推断误用指标。任何真实模型冒烟先约定预算。
- Dreaming 与画像基础功能已在独立功能分支实现，仍需长期语义评测与自动调度；跨客户端主动召回继续按 Issue 推进。

用户要求：本轮基础功能验证通过并提交后，另开 feature 分支集中完成较难的后续功能，供用户评估后合入；不得自动合并该 feature 分支。

## 独立功能分支进行中

分支 `codex/feature-memory-evolution` 基于 v0.3.2；主工作目录保持发布版本。用户授权先完成推断审查/来源失效、相对时间/时区、时间地点条件检索。不得自动合并。实现和验证结果以分支实际状态为准；未做真实模型调用。新增 CLI/TUI 推断审查和 recall 筛选参数，MCP/Agent recall 同步筛选。推断确认保持独立，状态追加可追溯；日志损坏时停止写入；CLI --recover-tail 仅显式恢复损坏尾行，保留全部字节并追加恢复标记。推断 TUI 的读写在 worker 执行，失败释放 busy 并接续待切换意图。后续状态见下方增量记录；跨客户端主动召回仍待实现。

开发测试须使用功能分支专属虚拟环境及配置/记忆库；Git worktree 不隔离用户配置，不能直接用默认配置启动功能分支的真实聊天。当前只运行夹具隔离的合成测试；没有读取或迁移个人库，没有真实模型请求。

本分支验证：推断/日期/Agent 专项回归 99 项通过；推断界面正常操作与异常恢复均通过。合成 200 条记忆，关键词条件检索预热后连续 10 次，耗时中位数 26.88 ms、最大 37.65 ms；仅代表本机该合成规模，不代表向量模型或大库性能。最终全量回归 560 passed；随后补充的故障注入与界面复测 23 passed（其中包含新增的两条审计保留用例，不与全量数量简单相加）。git diff --check 通过。所有测试记录与合成评测文件保留在忽略目录，不删除。

推断日志写入失败的边界：事实更正/软删除先保留审计，再同步推断失效；若失效追加失败，下次审查重新校验来源并补记。尾行恢复仅显式执行，不改写原文件。旧版 0.3.2 不理解 revision/recovery 推断事件，功能分支必须使用独立测试库，不能让两个版本共写同一库。本分支独立开发，现有主目录仍为发布版本；提交与推送状态以 Git 记录为准，合并须由用户评估。当时约定每次提交前运行全量测试；现行以 AGENTS.md 的按影响范围选测规则为准。

本次提交前完整回归：562 passed。模型搜索测试改为等待列表的最终可观察状态，保留原筛选断言，避免将异步移除/挂载尚未完成的一帧误判为失败。


## 后续高优先级功能（2026-10-29）

前三项已在 `368d5b3` 提交并推送到 `codex/feature-memory-evolution`，提交前全量 562 passed。用户随后明确授权自行 commit/push 并继续剩余高优先级开发；不授权自动合并主分支或再次发版。以下为该功能分支后续实现，最终提交状态以 Git 为准。

- #12：`qm evolve`、Agent/MCP evolve 区分状态变化与错误更正；当前召回排除已过期/未生效事实，历史日期和完整演化视图使用关键词快照，不污染向量缓存。删除/纠错不会复活前驱。明确分离的有效期不互判冲突，仍保留敏感/低可信候选审查。
- #9：CLI/TUI/MCP profile 从当前偏好、目标、约束、习惯、日程事实和独立画像推断重建；纯查看不调用模型。显式 refresh 产生待审查推断；只有来源相关、已确认的画像可进入聊天，最多 300 tokens。新来源指纹支持稳定 ID 下的手动正文修改失效；旧无指纹推断不能追溯历史编辑。
- #8：CLI dream 与 TUI /dream 显式启动增量回顾。默认一次请求，上限 20，禁用重试/候补模型，单次超时最多 60 秒；窗口至少 2048 tokens。TUI 运行期间可聊天/换会话；支持状态、取消、重启接续，预算 0 可发布已校验缓存而不请求模型。失败保留会话和任务日志，发布前重新校验证据。互斥仅覆盖同服务实例；不支持多个进程并发回顾同一库。
- 新增 `memory/reflection.py` 与 `app/chat_reflection.py`；领域模型仍集中 models.py。`reflection-jobs.jsonl` 追加批次摘要/候选/状态，截断尾行追加恢复标记，中间损坏停止。新推断类型 reflection 与 source_fingerprints、条目标签 change_kind 都不兼容旧版读取；仍须用独立测试库，不与 0.3.2 共写。
- 没有实现无人值守自动调度、原始会话直接回顾、整库所有关系穷举或跨客户端主动召回。既有会话沉淀先产生事实。真实模型语义效果未验证，本轮零真实请求，没有使用个人库。
- `evals/memory_eval.py` 新增合成时间/地点/情绪 Recall@1 与 MRR@5 对照；它验证筛选和历史视图契约，不代表真实用户准确率。新增回归覆盖预算、取消、失败接续、证据失效、画像注入与 TUI 可交互性。
- 中英文 README、命令表、MCP 列表、结构树与 AGENTS 同步更新。Issues 在功能分支验收/合入及剩余范围完成前保持开放。

最终提交前验证：全量 `uv run --frozen --offline --extra documents pytest -q` 为 591 passed（238.48 秒）；使用夹具隔离和测试专用管道事件循环。首轮 589 passed / 1 failed 暴露命令面板嵌套方括号转义问题，已改为直接组合 Content 文本与样式，并在完整复测中通过。画像日志故障不再阻断事实召回与聊天，错误可见。合成上下文评测：baseline Recall@1=0.2、MRR@5=0.5，contextual 均为 1.0；仅 5 个固定合成用例。变更文件的本机路径/凭据模式扫描无命中，git diff --check 通过。全部记录保留在本地忽略目录。此次仅本地 Windows 验证，尚无该提交的跨平台 CI 结论。

## 全项目审查后续

远程分支已由用户改名为 `feature-memory-evolution`，推送必须明确指定目标。审查覆盖 app/agent/memory/retrieval/llm/infra 的主要调用与异常路径；修复候选日志失败导致丢失、损坏向量缓存导致检索异常、缓存清理异常外溢、搜索默认引擎未传递、回顾缺失 proposals 被误判成功。时间写入收回 MemoryService；回顾改用公开服务方法，服务使用可重入写锁保持组合操作一致性。没有新增依赖或读取个人库。

本轮完整回归：594 passed，430.50 秒；git diff --check 通过。仅隔离合成测试，零真实模型请求。测试记录保留；本轮未验证跨平台 CI。

## Spark 真实数据诊断

用户明确授权真实 Vault 只读输入及 Spark 调用；诊断输出单独保存在本地忽略目录，不提交任何条目原文或个人配置。三次真实请求中一次超时、两次成功；复现确认异常类型为请求超时，失败批次保留，重跑后进度推进。原记忆文件哈希一致。画像预设主题无匹配，因此未触发该入口，不宣称画像真实数据验证通过，也未处理完整记忆库。错误分类补充 timeout/validation/storage/request，只记录类别与固定文案，不保存异常原文。

提交前全量回归：595 passed（331.73 秒）。真实数据原文与诊断输出均未暂存，测试和诊断记录保留。

## 自动沉淀定位修正

用户明确要求自动运行：TUI 默认启用 Dreaming/画像空闲轮转，补记结束后开始，空闲 60 秒、间隔 300 秒、每次启动自动请求预算 20；可配置关闭、暂停恢复。后台输出仍须审查，不自动修改事实。此前文档中的“仅手动、自动调度未实现”描述被本节取代。退出进程无后台守护。

自动调度提交前完整回归：597 passed（365.38 秒）；覆盖忙碌延后、暂停/恢复、请求预算耗尽、配置关闭和输入草稿不触发。git diff --check 通过。没有新增真实模型请求或改写个人库。功能仅在 evolution 分支生效，主目录启动器仍指向发布版本。


## TUI 命令精简

按用户要求同步 main 和 evolution：仅保留 /sessions 会话入口，移除 /resume、/recall、/remember 的面板与分发及闲置处理函数。自然语言记忆仍通过 Agent recall/memorize 工具，CLI 管理入口保留。导入完成回调改为按用途命名；中英文 README 同步。

命令精简验证：evolution 全量 598 passed（441.86 秒）。 测试记录保留，git diff --check 通过。

## 简单优先：画像主题兼容

画像提炼移除英文主题白名单，跨全部有效事实筛选；输入带主题帮助理解。画像事实视图仅展示常见中英文主题与有效画像推断引用的来源，拒绝/失效后自定义主题来源不再留在画像；事实本身不变。后续可优先补配置界面与后台进度展示，复杂跨客户端召回继续后置。

画像主题兼容验证：全量 600 passed（385.63 秒）；真实 Vault 只读快照进行一次 Spark 画像请求，正常结束并生成 6 条来源校验通过的待审查候选。仅完成一个批次，不代表整库完成；原始记忆文件哈希未变。原文、候选和诊断文件仅在本地忽略目录保存，不进入提交。

命令精简验证：main 全量 537 passed（375.37 秒）；首轮临时目录缺失导致的准备错误已修复并完整复测。 测试记录保留，git diff --check 通过。

## 搜索基础兼容同步（2026-10-30）

- 搜索与抓取属于两分支共用基础能力，修复同步 main 与 feature-memory-evolution；记忆演化、画像和自动回顾仍仅在功能分支领先，不合并整条功能分支。
- 域名解析默认兼容代理合成 DNS 段 `198.18.0.0/15` 与 `2001:2::/48`，自动启动的搜索 daemon 继承相同 `FAKE_IP_CIDRS`。显式设置覆盖默认值，空值关闭；已有外部 daemon 不自动重启，需手动同步环境。
- 合成 DNS 例外只用于域名解析结果，直接填写非公网 IP 仍拒绝，混合返回中存在其他私网地址仍拒绝，重定向终点继续复验。双语 README 与回归测试同步。
- 开发使用功能分支自己的虚拟环境与空测试库，显式覆盖继承的配置变量；全局命令继续引用 main。开发配置与入口均在忽略目录，不保存个人库或真实凭据。
- 本次验证：main 全量 556 passed；功能分支全量 619 passed。直接公开网页请求返回 HTTP 200，URL 校验通过；未运行经 daemon 的端到端抓取，测试环境未发现可用 npx 或运行中的服务。零模型请求，专属测试临时目录已清理。
- 后续已补齐 Node/npm/npx 与 open-websearch，自动启动改为优先已安装命令，缺失时才回退 npx。真实服务冒烟两分支均返回搜索结果并抓取到公开页面正文，取代上方“尚未验证”的旧边界；测试进程和日志已清理。open-websearch 2.2.0 的混合 IPv4/IPv6 CIDR 比较存在上游问题，本机安装包已修正为同地址族比较；此修补不在 Python 包内，升级上游服务时需复核。
- 安装与命令选择调整后的最终全量回归：main 558 passed，feature-memory-evolution 621 passed；真实搜索/抓取两个分支均通过，零模型请求，测试临时目录均已清理。
- Spark 联网 Agent 真实冒烟：main 2 次请求、feature-memory-evolution 3 次请求，共 5 次，关闭重试和候补模型。该次冒烟只向模型提供联网工具，未覆盖记忆工具与联网工具混合注册的生产场景。两边均由模型选择 search/fetch_web，实际执行搜索与两次网页抓取，工具结果回传后生成带来源链接的回答；使用空临时库，事实写入数为 0。直接抓取覆盖 tibo.cc、Python asyncio 文档、GitHub 仓库页、MDN HTTP 文档、中文维基百科，两个分支均成功；知乎公开主题页远端 HTTP 403，上游服务将其包装为 502，属于远端访问限制而非本地 DNS 拦截。未做浏览器渲染或登录态访问。测试服务已停止，临时会话与日志已清理；本轮未改产品代码。

- 两分支自动召回增加轻量个人话题/连续追问门控，通用问题跳过预取与查询改写；模型主动 recall 保留。规则存在隐式个人意图漏判边界，不将关键词判断视为完整语义分类。


## 请求进度与状态栏

- 发送后立即在模型名称旁显示活动条、阶段和经过秒数；上下文用量独立右对齐。活动条表示忙碌，不代表完成百分比。
- Agent 的可选 on_progress 回调在上下文准备、模型请求及工具执行前通知界面；工具开始与结果分别展示，异常仍走原有收尾释放 busy。
- 两分支同步基础体验；按需召回跳过通用问题，模型自身首字等待仍取决于供应商。
- 最终隔离全量回归（2026-10-31）：main 572 passed，feature-memory-evolution 635 passed；覆盖工具执行前进度、两种窗口宽度、状态栏卸载后的定时刷新。此次界面改动未做真实模型延迟基准，不将加载提示视为模型耗时缩短。


## TUI language and search errors

- Fixed TUI labels and progress are English; model/user content retains its original language.
- Search accepts JSON-encoded engine arrays from model arguments. Empty results with upstream partialFailures now raise an error and are not cached; default Bing HTTP failures fall back to Baidu once, explicit engines remain unchanged.
- Reproduced upstream Bing TLS failure returned in partialFailures with HTTP 200. Live tool smoke on both branches returned three results for default search and JSON-encoded Baidu arguments; temporary vaults removed, no model calls. Cache keys are versioned to bypass legacy false-empty entries.
- Validation: full isolated suite main 580 passed / evolution 643 passed; after the cache-key update, all 81 search tests passed on each branch. Fixed TUI string literals are checked for unintended Chinese text; user and model content are unaffected.


## Windows IME cursor

- Windows interactive TUI input uses a native blinking bar cursor, leaving IME composition placement to the terminal; headless and other platforms retain the painted cursor. Blur/unmount hide the native cursor and reset its shape. Native IME behavior requires manual terminal verification; headless tests only cover cursor control, editing coordinates and cleanup.


## Review follow-up: queued targets and search budget

- Pending commands retain the full session-bound queue item and recheck its target after intervening navigation; synchronous completion resumes FIFO processing. Pending targets are covered by the session deletion guard.
- Search budget exhaustion stops further requests while retaining collected candidates with the existing candidate hint and timeout diagnostics.
- Validation: targeted queue/budget regressions 5 passed; full isolated suite 617 passed. No real model or network requests were used.


## Input caret end spacing

- BarInput removes Textual Input's extra end-of-value scroll cell from the terminal caret coordinate; scrolling retains its existing padding. Empty input and trailing user spaces retain their actual insertion positions. Regression coverage includes Chinese, mixed ASCII/CJK, middle edits and literal trailing spaces.
- Validation: insertion-coordinate cases and native cursor checks passed; full isolated suites base 623 passed, evolution working tree 651 passed. Real terminal/IME rendering remains a manual check.


## Generation cancellation and visible send queue

- Esc stops the active generation, preserving the draft and partial response in the append-only session. Open palettes/modals consume Esc first. TUI streaming uses cancellable async transport inside the worker, including first-token waits; no second request starts until cleanup completes.
- Enter during generation appends to the session-bound FIFO, shown above the input. Completion or cancellation drains it automatically. The queue is process-local, not persisted across exit.
- Active synchronous context preparation/tools finish safely; remaining tools receive cancelled results to keep tool-call pairs valid. Completed writes are not rolled back. UI text remains English.

- Validation: final full isolated suites base/main 632 passed, evolution working tree 672 passed. Installed LiteLLM async stream wiring tested with local mock responses, including repeated requests; cancellation covers first-token waits, partial output, draft preservation and tool-result pairing. No live model/network verification or evaluation-data changes. Evolution retains its pre-existing uncommitted work and memory-specific behavior.


## Search / Fetch final wiring fixes

- Normal Agent tool construction builds FetchRouter independently of SearchRouter; explicit legacy router injection remains supported and its fetch compatibility entry shares the usage limiter.
- Request-count budget is checked before provider quota accounting. Failed dispatched requests still count conservatively.
- Official fetch adapters receive search.fetch_timeout; search adapters retain search.timeout. Setup exposes Fetch only for implemented fetch providers.
- You Contents parses the documented top-level array (https://you.com/docs/api-reference/contents), without livecrawl or additional formats. Search parsing and the shared JSON client remain unchanged.
- Offline comparison against the starting HEAD preserved all search metrics. That offline-only pass made no paid requests; the later authorized real API verification is recorded below.

- Validation: affected provider/setup/usage suite 121 passed; full isolated pytest 775 passed. Offline Search Eval unchanged: P@5 0.2364, Success@5/MRR@5 0.7273, NDCG@5 0.8944, false acceptance 0.0606, requests/query 2.303. Temporary baseline removed; evaluation inputs unchanged.


## Search / Fetch real API smoke follow-up (2026-11-01)

- Authorized smoke used process-local credentials and disposable empty vaults through normal build_tools / AgentRuntime paths. Five official Search providers returned results; Tavily, Exa, You Contents and open-websearch fetched public page content.
- Volcengine Fetch returned HTTP 200 but exposed an incorrect assumed response mapping. The official Fetch documentation and live response agree on Result.Data.StatusCode / ContentText / RedirectedUrl / Title. The adapter now reads those fields, rejects target-page HTTP errors, and preserves router URL checks and existing usage accounting.
- Corrected Volcengine Fetch succeeded through build_tools on a public page. A confirmed Spark Agent run used two model requests, executed Tavily search and fetch_web, then produced a linked answer; the temporary vault contained no memory files. Mock regressions cover the documented response, redirects, truncation, empty content and target HTTP 403/404/500. Official reference: https://docs.volcengine.com/docs/networked-search/doubao-search-web-analysis-fetch?lang=zh
- Smoke scope does not establish all count limits, Custom search behavior, dynamic-page rendering or every target website. Credentials were read only; no user vault or persistent configuration was changed.
- Final validation: provider suite 70 passed; full isolated pytest 778 passed (one existing Pydantic warning). Search Eval retained P@5 0.2364, Success@5/MRR@5 0.7273, NDCG@5 0.8944, false acceptance 0.0606 and requests/query 2.303. Evaluation inputs were unchanged; disposable smoke directories were removed.


## Base synchronization (2026-11-01)

- main fast-forwarded to base/chat-stability c6d8aee. Evolution integrates the same base while retaining its temporal memory, profile and reflection features. Search / Fetch implementation matches base.
- The paused merge was snapshotted and rebuilt against the latest base. Original local README, reflection UI and reflection-test changes remain outside the merge commit. The original preservation stash remains available.
- Adapted the corrupt-profile recall test to use an explicit personal question under the automatic-recall gate; its corruption and fact-retrieval assertions remain unchanged.
- Final isolated full suites: main 778 passed; evolution working tree with retained local edits 841 passed. Both Search Eval runs retain the same quality and request metrics. One intermittent native-cursor test failed during a prior run, passed its focused retry and the final full suite; no product change was made for it. No live API calls or evaluation-data changes were made for synchronization.


## Review follow-up: committed English reflection UI (2026-11-01)

- Committed the reflection UI English labels previously present only in the local working tree; normalized the status line punctuation. No reflection logic or user/model content changed.
- Validation used a disposable archive of the committed evolution tree with only this source fix overlaid, excluding all unrelated local README and reflection-test edits: full pytest 841 passed, one existing dependency warning. The archive was removed after testing.
- Search result-count clamping and loss of low-relevance hints on cache hits were reproduced with synthetic providers during review; left unchanged pending user review. No live API calls or user-vault access.

## Search review fixes (2026-11-01)

- Explicit search limits override the configured default up to 15. Cached result hints are recomputed using the same query analysis, retaining low-relevance warnings without changing cache storage. Regression tests use synthetic providers and verify no second upstream request on cache hits.
- Validation: search suite 242 passed, full base suite 782 passed. Search Eval unchanged. Normal build_tools live smoke returned 15 You results and repeated search used cache without another request; fetch succeeded. Spark Agent completed search/fetch and a linked answer in two model requests. Three You requests were added (five including prior smoke), temporary vault removed; no user vault or persistent credentials changed.


- Evolution review follow-up also pins the profile-test proposal to its intended source ID instead of depending on randomly ordered IDs.
- Final evolution validation: full isolated suite 845 passed, one existing dependency warning; this tested the exact source/test contents prepared for commit, with unrelated README edits stashed. Evolution live build_tools smoke also returned 15 You results, reused cache without another request, and fetched the public example page. Across both environments this follow-up used five You requests (seven including prior smoke) and two Spark model requests. Search Eval unchanged; temporary smoke vaults removed.

## Dual-period usage protection and official quota pauses (2026-11-01)

- Defaults live in config.DEFAULT_USAGE_LIMITS. Local calendar day/month counters are independent and shared by Search/Fetch. UsageLimiter.acquire atomically checks and records under a process-wide path lock; persistence reloads under that lock. Cross-process transactional accounting is intentionally unsupported.
- Legacy TOML overrides defaults; legacy usage windows retain only the known count. The unknown other period is labeled; new requests count in both periods. No invented historical totals. Pauses persist alongside counts; manual resume does not reset usage, and reliable timestamps expire on access.
- Setup quota management shows defaults/effective caps, usage/remaining, unknown historical periods and pause reasons; edits accept zero, reset uses centralized defaults, manual resume clears only official pauses.
- Official evidence checked: Baidu search response contract https://ai.baidu.com/ai-doc/AppBuilder/pmaxd1hvy and AI Search errors https://ai.baidu.com/ai-doc/AppBuilder/4m8sgh88y distinguish QUOTA_USER_DAILY_REQUEST, QUOTA_USER_DAILY_FREE, BILLING_INSUFFICIENT_BALANCE from RATE_LIMIT_*_QPS. The specified local daily 50 is not a claim about official free pricing.
- Tavily https://help.tavily.com/articles/8645538886-understanding-http-errors documents 432 plan / 433 PAYG limits versus ordinary 429. Exa https://exa.ai/docs/admin/error-codes documents 402 NO_MORE_CREDITS / API_KEY_BUDGET_EXCEEDED / TEAM_BUDGET_EXCEEDED; payment-protocol challenges and unknown tags are not persistent quota evidence.
- You https://you.com/docs/using-the-api/error-code-reference and https://about.you.com/resources/web-search-api-authentication-header document keyed 402 Insufficient credits; payment challenges are excluded. Volcengine Fetch https://docs.volcengine.com/docs/networked-search/doubao-search-web-analysis-fetch?lang=zh documents 10406 free quota and 10412 search package exhaustion; no unverified generic Search codes are added.
- Exact account reset instants/timezones were not confirmed by those sources. Recognized provider quota pauses therefore require manual resume, including Baidu daily codes; no midnight/month-start is guessed. The limiter supports expiry for a reliable timestamp when one is supplied. Official pauses are distinct from local cap failures; unknown failures retain fallback without a persistent pause.
- Only safe machine error codes are retained from HTTP failure payloads; full upstream error responses/messages are not exposed. No real API calls, key access or user-vault modifications were performed during offline validation.
- Final offline validation: 817 passed, one existing Pydantic warning. Search Eval retained P@5 0.2364, Success@5/MRR@5 0.7273, NDCG@5 0.8944, false acceptance 0.0606 and requests/query 2.303. Inputs unchanged. Real TUI/API validation is a separate user-approved phase; sessions must remain visible in the shared local test environment.


- Evolution integrates the dual-period quota and official-pause base update while preserving memory-specific configuration and behavior.
- Quota-update merge validation: evolution full isolated pytest 880 passed (one existing dependency warning); search implementation matches main/base bc661bb and Search Eval metrics are unchanged. Unrelated local README edits were excluded from validation and the merge commit. No real API calls were made during synchronization.

## TUI Markdown rendering (2026-11-01)

- Reproduced the quoted-CJK emphasis example with the installed Rich/markdown-it parser: CommonMark punctuation flanking leaves double-star markers literal beside CJK text. Reply-only compatibility adjusts double-star delimiter flags at CJK/punctuation boundaries, preserving markdown-it pairing, code/escapes and full-document reference context. Stored Markdown is untouched.
- Scoped reply styles replace magenta/underlined headings with left-aligned slate-blue/neutral headings. Heading-to-body spacing and code-block vertical padding are reduced; code uses restrained dark syntax styling and preserves source indentation/trailing spaces. Rich continues to handle lists, tables, quotes, rules and terminal link metadata.
- The Content conversion remains the single rendering/selection source. Copy still means rendered display text, including display wrapping, not original Markdown. Exact duplicate ChatReply updates reuse the visual; stream coalescing and session storage are unchanged. No new rendering dependency, model/API call or user-vault access.
- Local visual validation includes Textual SVG screenshots and equivalent Rich before/after PNGs for 80/120/160 columns (reply widths 47/87/127). The synthetic sample uses 39→35 lines at 80 columns, 38→34 at 120/160. Terminal fonts, italic support, soft-wrapped code copying and link activation remain terminal-dependent; no new link interaction or copy mode was added.
- Validation: UI suite 128 passed; focused final Markdown suite 25 passed; full isolated pytest 842 passed with one existing dependency warning. Truecolor Textual screenshots explicitly override process-local NO_COLOR for visual inspection only; 80/120/160-column SVGs confirm slate heading color and no literal emphasis markers in the sample. CJK and existing assistant selection/Ctrl+C tests pass; stored Markdown remains byte-for-byte unchanged. No user configuration, Vault, credentials or APIs were accessed.

- Markdown merge validation: evolution full isolated pytest 905 passed with one existing dependency warning. Reply Markdown rendering/theme match main/base 3dd03ca, while evolution retains its existing command-panel and memory functionality. Local README edits remain outside the merge commit; no real API calls were made for this merge.

## Full pending review content (2026-11-01)

- Pending action review no longer truncates the item to 44 characters. PickScreen accepts optional plain-text detail in an independently scrollable area; the expanded card uses up to 90% width / 85% height with a bounded width. Approval/edit/rejection actions remain below the body.
- Detail mode supports mouse-wheel scrolling and PgUp/PgDn without moving the action selection; other pickers retain their existing layout and bindings. Markup-like content is literal. Pending list rows remain concise summaries; review and edit receive the full original text.
- Synthetic UI regressions cover 80x24, 120x40 and 160x50 layouts, pagination, cancellation, full-text approval, full-text edit defaults and rejection. No API calls, user-vault access or memory/session format changes.
- Validation: focused pending suite 9 passed; full isolated base suite 848 passed with one existing dependency warning. Synthetic rendered SVG checks at all three sizes confirm mouse-wheel scrolling, the final body line and visible action labels. No real APIs or user data were used.
- Pending merge validation: full isolated evolution suite 911 passed with one existing dependency warning. Existing README changes remain unstaged; no real API calls were made.

## Compact pending confirmation (2026-11-01)

- Replaced fixed 85% dialog height with content-driven sizing. Width is capped at 76 columns / 90% of the terminal; the body grows with content up to 30% of terminal height, then scrolls independently. Short confirmations no longer reserve a large empty area; action controls remain visible.
- Regression coverage at 80/120/160 columns verifies one-line bodies remain one line with no scrollbar, while existing full-text pagination and action tests remain unchanged.
- AGENTS.md now records compact, content-driven temporary dialogs as a UI invariant, including bounded scrolling and visible action controls.
- Per user direction, AGENTS.md now requires tests selected by impact instead of automatic full-suite runs before commits/branch synchronization. Pending suite: 12 passed; Markdown suite: 25 passed on rerun. An earlier full run had 850 passed and one Markdown copy/wrapping failure; the repeated full run completed with 851 passed and one existing warning before the cancellation arrived. Subsequent verification is targeted only.


## Final stability fixes and freeze acceptance (2026-11-01)

- F1: validate complete JSON record shapes, retain direct-load errors and original bytes, and log per-file batch errors without aborting healthy session listing or consolidation. Existing torn-tail recovery is unchanged.
- F2: scoped in-memory snapshots compensate ordinary exceptions in manual approve/correct/reject/forget, including partial decision-log writes. Resolution is written before pending removal. Only affected topic/log paths are snapshotted under the existing writer lock; no storage format, durable journal or transaction framework is added. Failed rollback raises both errors. Process kill/power loss and simultaneous writers remain unsupported transaction boundaries, explicitly documented in both READMEs.
- F3: cross-process quota atomicity remains a documented limitation. F4: optional open-websearch latest fallback remains unpinned; no clean upstream version has been verified in this round, so no guessed pin is introduced. F5: exclusive session file creation closes the exists/write race. F6: portfolio tag identifies source independently of package 0.3.2 and its older Release; evaluation data and historical metrics are untouched.
- CI runs Windows/Ubuntu tests, build and CLI help, including pushes to evolution. All local verification uses temporary Vaults, static extractors and fake models. Native terminal IME/clipboard appearance remains a manual acceptance item; headless UI checks do not establish it.
- Build inspection found Hatch's default source archive included an existing untracked local script. The sdist now uses an explicit public project-content allowlist and excludes the entire one-off scripts directory; the local script itself was not opened or changed. Wheel package selection is unchanged.
- User requested the untracked script be moved outside the repository; it was moved with a matching SHA256, without opening its content. The source-archive allowlist remains as a packaging safeguard.
- Full validation exposed an existing Markdown copy assertion using a pre-scrollbar-layout snapshot. The assertion now compares clipboard text to the current rendered width after Ctrl+C; rendering and copy behavior are unchanged.
- Local final acceptance: 871 passed, 4 optional document tests skipped, one existing dependency warning; sync/build and disposable installed-wheel CLI succeeded. Temporary install environments were removed. Manual native terminal checks and remote PR/CI/tag/cleanup remain separate gates.
- Remote main b2057c4 CI failed only its Windows native-input cursor test: the after-refresh focus callback had not fired before inspecting captured writes. The test now waits for the actual cursor-show event with a bounded timeout and retains focus/active-state/sequence assertions; product cursor code is unchanged.
- PR Windows CI exposed another test readiness race: the request-active UI flag precedes worker-side session creation. The queue/cancellation test helper now waits for both an active request and an existing runtime session before dereferencing current; production request/queue behavior is unchanged.
- Dual-platform CLI smoke exposed a real English-Windows redirected-output failure: cp1252 could not encode Chinese help. The CLI entry point configures only non-TTY Windows stdout/stderr to UTF-8 in-process; native console handling and persistent environment stay unchanged. A real subprocess regression forces cp1252:strict and checks UTF-8 help output.


## Evolution absorbs the stable main snapshot

- Merged only main -> evolution after the stable main PR and final-SHA CI passed and the portfolio tag was pushed. Retain temporal retrieval, reflection, inference review/fingerprints and dated-session behavior; no evolution features enter main.
- Conflict resolution preserves inference validation/invalidation in manual correction and soft-delete. Existing evolution tests establish that completed source facts and their audit survive a later inference append failure; subsequent inference reads repair derived status. Accordingly source/audit writes receive main's exception rollback, while inference invalidation remains after that boundary. The existing source-audit failure regression is retained and strengthened; no inference format or commit semantics are changed.
- Shared queue keeps main's rollback and log-before-removal behavior plus evolution's existing log-failure test. Current branch/freeze instructions replace the obsolete base-first workflow; historical evolution planning remains recorded.
- Evolution merge validation: memory-evolution/reflection/inference/context/service suite 125 passed; focused TUI queue/pending/cancel/cursor suite 24 passed. Shared session/queue/Agent/CLI/Markdown regressions also passed before resolving the inference commit-boundary difference, and the affected service paths were rerun in the 125-test group. At that historical checkpoint, main was unchanged after tagging and evolution push CI was still the synchronization gate. Current release/branch status is recorded at the top.

## Evolution 视觉区分（2026-11-02）

TUI 改为深蓝灰面板、薄荷绿焦点/当前会话、淡紫角色/模型标签、暖金快捷键提示；回复 Markdown 同步配色。布局、键位、数据和命令行为保留。配色集中 chat_theme.py，固定 TUI 文案继续英文。只同步 evolution，不修改冻结 main。

视觉验证：相关焦点、当前会话、命令面板、弹窗布局与 Markdown 渲染 40 项通过；合成聊天、命令面板和会话选择器已导出预览，聊天配色已渲染检查。预览仅在本地忽略目录，未使用真实 Vault 或调用服务。主目录日常启动器已使用 evolution，重启即可加载新样式。

## 视觉偏好修正（2026-11-02）

用户明确反馈蓝色背景不好看，改回中性灰：主背景、侧栏、面板、消息气泡、选中行、弹窗与代码底色全部使用灰阶，边框与次要文字同步中性化；仅焦点/当前会话与少量角色标签保留强调色。此前深蓝灰配色已被本节取代。

## 对话界面层级调整（2026-11-02）

用户要求参考终端对话产品的设计，保留灰背景。当前使用单一暖色强调，欢迎内容聚合居中、首条用户消息清除欢迎态；用户内容改为左对齐全宽灰面板，助手与工具事件弱化边框和标签颜色。输入区变为平面面板，用左侧焦点线提示，底部显示模型/上下文/快捷键。保留输入提示上沿位置以兼容 IME。TranscriptView 清理时同时移除 home 样式，历史和实时对话共用排版。新增窄/宽窗口欢迎态转对话回归，旧配色章节仅为历史。未使用真实数据，合成预览仅保存在忽略目录。

界面验证：整组聊天/Markdown 回归首轮 144 passed、1 个会话弹窗弱标记断言失败；恢复当前项灰线与焦点暖线区分后，相关 6 项复测全部通过（含 80/120 列欢迎态转换、输入焦点和命令浮层）。欢迎页、对话页及弹窗均以合成会话导出预览，已检查实际渲染；未调用真实服务或使用参考截图中的内容。git diff --check 通过。

## 强调色确认（2026-11-02）

用户选择石墨灰背景与清晰天蓝强调 #6CB6FF，替换暖色，用于焦点、选中标记、链接及少量品牌文字。标题/正文/角色标签保留灰白，提示恢复灰色；布局不变。此前暖色说明仅为历史。

启动侧栏按用户要求默认收起，Ctrl+B/展开控件保持可用；会话切换不强制修改当前展开状态。

验证：配色相关 31 项通过；整组界面/Markdown 首轮 144 passed，1 个直接点击已隐藏侧栏按钮的旧测试失败。测试显式展开后，相关 5 项复测全部通过。实际天蓝/收起预览已检查，未调用真实服务。

## 首页实用内容与远程失败核对（2026-11-02）

用户提供的旧 Actions run 41384553579 在早期薄荷配色测试失败：当前会话灰标记预期与强调色实现不符，已在后续提交修正。最新 run 41397436953 的 Debian 测试/构建/CLI 均成功，不对旧失败记录反复重跑。

首页改为宽度受限、靠上显示的本地概况、最近三个非空会话、可编辑对话示例。HomePanel worker 读取当前有效事实与待审查数量、会话摘要元信息，UI 线程挂载；标题按纯文本处理。点击会话复用切换逻辑，点击示例只填输入，不自动请求模型。首页移除后忽略迟到结果，读盘失败有提示，窄窗口滚动不遮输入。实现仍在现有 chat_widgets.py，未新增依赖或读取个人库测试；预览仅使用合成资料。

首页验证：聊天界面/Markdown 整组 147 passed（226.70 秒），首批首页与焦点专项 8 passed。合成首页已渲染检查，最近会话和示例在常见窗口可见，窄窗口使用滚动；未调用真实模型/搜索或读取个人库。
