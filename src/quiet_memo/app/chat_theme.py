"""Textual 主题与布局样式；ChatApp 通过 CSS = APP_CSS 应用。"""
from __future__ import annotations

from rich.theme import Theme

# Scoped to reply rendering; other Rich/CLI output keeps its own theme.
MARKDOWN_THEME = Theme({
    "markdown.h1": "bold #86cfbc not underline",
    "markdown.h2": "bold #8dd8c0 not underline",
    "markdown.h3": "bold #b9acd9 not underline",
    "markdown.h4": "bold #b9acd9 not underline",
    "markdown.h5": "bold #b9acd9 not underline",
    "markdown.h6": "bold #b9acd9 not underline",
    "markdown.link": "#86cfbc underline",
    "markdown.link_url": "#86cfbc underline",
    "markdown.code": "#c3b5e5 on #252525",
    "markdown.block_quote": "#93a9b8",
    "markdown.table.border": "#35485a",
    "markdown.table.header": "bold #c9dce8",
    "markdown.item.bullet": "#86cfbc",
    "markdown.item.number": "#86cfbc",
    "markdown.hr": "#35485a",
})

APP_CSS = """
    /* Evolution: neutral gray surfaces with restrained color accents. */
    $accent: #8dd8c0;
    $secondary: #b7a7d9;
    $warm: #d8ba86;
    $dim: #3a3a3a;
    $muted: #a6a6a6;
    $faint: #818181;
    $panel: #1d1d1d;
    $bg: #171717;
    $scroll-track: #171717;
    $scroll-thumb: #484848;
    $scroll-thumb-hover: #818181;
    $scroll-thumb-active: #999999;

    Screen { background: $bg; }
    /* 统一窄滚动条；新的可滚动组件加 thin-scroll 类即可复用。 */
    .thin-scroll {
        scrollbar-size-vertical: 1;
        scrollbar-size-horizontal: 1;
        scrollbar-background: $scroll-track;
        scrollbar-color: $scroll-thumb;
        scrollbar-color-hover: $scroll-thumb-hover;
        scrollbar-color-active: $scroll-thumb-active;
    }
    #root { width: 1fr; height: 1fr; }
    #sidebar { width: 28; background: #121212; border-right: solid #292929; }
    #sidebar-head { height: 3; align: left middle; }
    #brand { color: $accent; text-style: bold; padding: 0 1; width: 1fr; }
    /* 折叠按钮只留符号，减少侧栏头部的方框噪音 */
    #hide-sidebar { width: 3; height: 3; min-width: 3; padding: 0; background: #121212; color: $faint; border: none; margin-right: 1; content-align: center middle; }
    #hide-sidebar:hover { color: $accent; }
    #show-sidebar { layer: overlay; dock: top; width: 3; height: 3; min-width: 3; padding: 0; background: $bg; color: $faint; border: none; content-align: center middle; display: none; }
    #show-sidebar:hover { color: $accent; }
    #new-session { width: 1fr; height: 3; margin: 0 1 1 1; background: #202020; color: $accent; border: none; content-align: left middle; padding: 0 1; }
    #new-session:hover { background: #292929; color: $accent; }
    /* 列表与 New session 用同一左右外边距；隐藏滚动条，避免出现滚动条时行宽缩 2 格错位 */
    #sessions { width: 1fr; height: 1fr; margin: 0 1; scrollbar-size-vertical: 0; }
    /* ListItem 默认高度跟随子容器（Vertical 是 1fr 会撑满列表），必须钉死 auto */
    #sessions > ListItem { padding: 0 1; height: auto; }
    #sessions > ListItem > Vertical { height: auto; }
    .session-title { color: #d4d4d4; width: 1fr; overflow-x: hidden; text-overflow: ellipsis; }
    .session-meta { color: #8e8e8e; }
    /* 当前会话保留左线作为非颜色标识，低饱和底色区分焦点。 */
    #sessions > ListItem.-highlight { background: #272727; }
    #sessions > ListItem.current { background: #272727; border-left: heavy $accent; }
    #sessions > ListItem.current.-highlight { background: #303030; border-left: heavy $accent; }
    .group-label { color: #8e8e8e; padding: 1 1 0 1; }

    #main { width: 1fr; layers: base overlay; }
    #chat { width: 100%; height: 1fr; padding: 1 0 1 3; }
    /* 右侧留白改由子元素承担，滚动条才能贴在窗口最右侧 */
    #chat > * { margin-right: 2; }
    .who-user { content-align: right top; color: $secondary; width: 1fr; margin-top: 1; }
    .user-turn { width: 1fr; height: auto; align: right top; }
    .bubble { background: #262626; color: #e0e7ef; padding: 0 2; width: auto; max-width: 68%; height: auto; }
    .who-ai { color: $accent; text-style: bold; margin-top: 1; width: 1fr; }
    .reply { color: #d8e1eb; margin: 0; height: auto; }
    /* 工具事件用薄边线和弱底色分组，不与正式回复争夺注意力 */
    .event-card { border-left: solid $dim; background: #1c1c1c; color: $muted; padding: 0 1; width: 1fr; }
    .event-card.memo { border-left: solid $accent; color: #a8d7c6; }
    .meta { color: $faint; width: 1fr; }
    .divider { border-top: solid #303030; height: 1; margin: 1 0; }
    .card { border-left: solid $dim; background: $panel; padding: 0 2; margin: 1 0; color: #d4d4d4; width: 1fr; }
    /* 欢迎区用薄荷色品牌与留白建立层级。 */
    .welcome-brand { color: $accent; text-style: bold; margin: 2 0 0 0; }
    .welcome-line { color: #b2b2b2; }
    .welcome-meta { color: #8e8e8e; margin-top: 1; }
    .welcome-hint { color: #8e8e8e; margin-top: 2; }

    /* 输入框不做焦点整块提亮，避免像额外遮罩；只用边框区分焦点。 */
    #send-queue { display: none; height: auto; max-height: 5; margin: 0 3; padding: 0 1; color: $muted; border-left: solid $dim; }
    #input { margin: 0 3 1 3; background: $panel; background-tint: transparent; border: round #414141; border-title-color: #999999; border-title-align: left; }
    #input:focus { border: round #8dd8c0; border-title-color: #8dd8c0; }
    /* 光标由 BarInput 渲染成竖线；这里只提供前景色，避免默认整格反色块。 */
    #input > .input--cursor {
        background: transparent;
        color: #e0e7ef;
    }
    /* 1 行正文 + 1 行上边框；height:1 会被边框吃掉整个内容区。 */
    #status-row { height: 2; width: 1fr; background: $bg; padding: 0 3; border-top: solid #2d2d2d; }
    #model-status { width: 1fr; height: 1; color: $secondary; overflow-x: hidden; }
    #status { width: auto; max-width: 55%; height: 1; color: $faint; text-align: right; }


    /* 命令面板：浮在输入框上方，只显示命令、参数和一句短语。
       -6 = status 2 行 + 输入框下边距 1 行 + 输入框 3 行；偏移不够会盖住输入框。 */
    #cmd-palette { layer: overlay; dock: bottom; offset-x: 3; offset-y: -6; width: 64; height: auto; max-height: 16; background: $panel; border: round #484848; padding: 0 1; display: none; }
    .cmd-row { width: 1fr; height: 1; padding: 0 1; color: #d1d1d1; }
    .cmd-row.cmd-active { background: #303030; }
    .cmd-usage { color: $accent; }
    .cmd-desc { color: #a3a3a3; }

    PickScreen, SessionPickerScreen, TextInputScreen { align: center middle; background: #0d0d0d 75%; }
    #pick-card { width: 64; height: auto; max-height: 70%; background: $panel; border: round #484848; padding: 1 2; }
    #picker-input, #pick-search, #pick-input { width: 1fr; background: #171717; color: #e0e7ef; border: round #414141; }
    #picker-input:focus, #pick-search:focus, #pick-input:focus { background: #222222; border: round #8dd8c0; }
    #picker-input, #pick-search { margin-bottom: 1; }
    #picker-list { height: auto; max-height: 16; }
    /* 与侧栏一致：SessionItem 内层 Vertical 默认 1fr 会把整行撑满 */
    #picker-list > ListItem { padding: 0 1; height: auto; border-left: heavy transparent; }
    #picker-list > ListItem > Vertical { height: auto; }
    #picker-list > ListItem.-highlight { background: #303030; border-left: heavy $accent; }
    #picker-list > ListItem.current { background: #272727; border-left: heavy $accent; }
    #picker-list > ListItem.current.-highlight { background: #303030; border-left: heavy $accent; }
    .pick-title { color: $accent; text-style: bold; margin-bottom: 1; }
    #pick-list { height: auto; max-height: 18; }
    #pick-list > ListItem { height: auto; }
    #pick-list > ListItem.-highlight { background: #303030; }
    /* 模型列表独立滚动，为小窗口的搜索框和快捷键提示保留空间。 */
    ModelPickerScreen #pick-card { height: 80%; max-height: 90%; max-width: 95%; }
    ModelPickerScreen #pick-list { height: 1fr; min-height: 1; }
    /* Full pending text scrolls independently; decision actions stay visible. */
    #pick-card.has-detail { width: 76; max-width: 90%; height: auto; max-height: 85%; }
    #pick-detail { height: auto; max-height: 30vh; min-height: 1; margin-bottom: 1; padding: 0 1; background: $bg; }
    #pick-detail-text { height: auto; width: 1fr; color: #d8e1eb; }
    #pick-card.has-detail #pick-list { height: auto; max-height: 6; min-height: 3; }
    .pick-hint { color: $warm; margin-top: 1; }
    """
