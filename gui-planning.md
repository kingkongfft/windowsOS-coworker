# Phase 3 — 桌面 GUI 规划（PyQt6）

> Date: 2026-06-29
> Status: Planning ⬜ Pending implementation

---

## 豆包 UI 拆解 → 对应 windowsOS-coworker 实现

```
┌─────────────────────────────────────────────────────────────────┐
│  windowsOS-coworker                              [─][□][✕]      │
├──────────────────┬──────────────────────────────────────────────┤
│                  │           当前会话标题                         │
│  🔍 搜索历史会话  │─────────────────────────────────────────────  │
│                  │                                               │
│  ＋ 新对话        │                                               │
│                  │     ┌─────────────────────────────────┐      │
│  ─────────────── │     │   有什么我能帮你的吗？              │      │
│  历史对话         │     └─────────────────────────────────┘      │
│                  │                                               │
│  • check disk... │   [快捷操作气泡] [磁盘] [内存] [CPU] [进程]    │
│  • kill process  │                                               │
│  • network diag  │                                               │
│  • sfc /scannow  │  ╔══════════════════════════════════════╗    │
│  • ...           │  ║ 🤖  检查磁盘使用情况...               ║    │
│                  │  ╚══════════════════════════════════════╝    │
│                  │  ╔══════════════════════════════════════╗    │
│  ─────────────── │  ║ 👤  C盘使用了 87%，建议清理           ║    │
│  ⚙ 设置           │  ╚══════════════════════════════════════╝    │
│  📊 审计日志      │                                               │
│                  │  ┌──────────────────────────────────────┐    │
│                  │  │ 发消息...                    [发送↑]  │    │
│                  │  │ [⚡快捷] [📋审计] [💾内存] [❓帮助]   │    │
│                  │  └──────────────────────────────────────┘    │
└──────────────────┴──────────────────────────────────────────────┘
```

---

## 完整技术栈

| 层 | 技术 | 用途 |
|---|---|---|
| GUI 框架 | `PyQt6` | 窗口、布局、事件循环 |
| 异步桥接 | `qasync` | 把 asyncio 接入 Qt 事件循环 |
| Markdown 渲染 | `QTextEdit` + 自定义 HTML | 消息气泡渲染 |
| 语法高亮 | `pygments` | 代码块高亮 |
| 数据层 | 现有 `core/memory_store.py` | 历史会话、消息、facts |
| Agent 层 | 现有 `agents/orchestrator.py` | 完全复用 |
| 审批弹窗 | `QDialog` | 替换现有 `core/approval.py` 的 CLI 提示 |

---

## 文件结构规划

```
ui/
├── __init__.py
├── app.py                    ← 入口：QApplication + 主窗口启动
├── main_window.py            ← QMainWindow：左右分栏总布局
│
├── widgets/
│   ├── __init__.py
│   ├── sidebar.py            ← 左侧栏：搜索框 + 新对话按钮 + 历史列表
│   ├── chat_area.py          ← 右侧聊天区：消息滚动区 + 欢迎页
│   ├── message_bubble.py     ← 单条消息气泡（用户/助手两种样式）
│   ├── input_bar.py          ← 底部输入框 + 快捷按钮栏
│   ├── approval_dialog.py    ← MEDIUM/HIGH 风险审批弹窗
│   └── thinking_indicator.py ← "正在思考..." 动画 widget
│
├── styles/
│   ├── theme.py              ← 颜色常量、字体定义（豆包配色）
│   └── main.qss              ← Qt 样式表（CSS-like）
│
├── worker.py                 ← QThread worker：在后台线程跑 Runner.run()
│
└── bridge.py                 ← CLI ↔ GUI 共享层：复用 memory_store、audit_log
```

新增入口文件（项目根）：

```
gui.py                        ← python gui.py 启动 GUI 模式
```

---

## 核心组件设计

### 1. 消息气泡（`message_bubble.py`）

- **用户消息**：右对齐，蓝色背景气泡，圆角
- **助手消息**：左对齐，白色/浅灰背景，带机器人头像
- **Markdown 渲染**：`QLabel` + HTML 转换（标题/加粗/代码块/列表）
- **代码块**：深色背景 + 等宽字体 + 一键复制按钮
- **流式显示**：逐字追加（模拟打字机效果）

### 2. 左侧栏（`sidebar.py`）

- 搜索框过滤历史会话（实时过滤 `memory_store.list_sessions()`）
- 新对话按钮（清空右侧 + 创建新 session）
- 历史列表：每条显示会话第一句话作为标题 + 时间
- 点击任意历史会话 → 右侧加载该会话完整消息历史

### 3. 底部输入栏（`input_bar.py`）

- `QTextEdit` 多行输入，Enter 发送，Shift+Enter 换行
- 快捷按钮：⚡磁盘 / ⚡内存 / ⚡CPU / ⚡进程（预设 prompt）
- 发送按钮动画：发送中变为停止按钮（可中断）

### 4. 审批弹窗（`approval_dialog.py`）

- 替换 `core/approval.py` 的 CLI 提示
- MEDIUM：黄色警告弹窗 + Yes/No 按钮
- HIGH：红色危险弹窗 + 需要输入工具名确认

### 5. 异步工作线程（`worker.py`）

- `QThread` + signals 模式
- `Runner.run()` 在 worker 线程中执行，通过 `pyqtSignal` 把结果推回主线程
- 支持取消（`asyncio.CancelledError`）

---

## 配色方案（豆包风格）

| 元素 | 颜色 |
|---|---|
| 背景（主区域） | `#FFFFFF` 白 |
| 背景（侧边栏） | `#F7F7F8` 浅灰 |
| 用户气泡背景 | `#E8F4FF` 浅蓝 |
| 助手气泡背景 | `#FFFFFF` 白 + 边框 |
| 主题色（按钮/高亮） | `#4D6BFE` 蓝紫 |
| 危险色（HIGH risk） | `#FF4D4F` 红 |
| 警告色（MEDIUM risk） | `#FAAD14` 黄 |
| 文字主色 | `#1A1A1A` 近黑 |
| 文字次色 | `#8A8A8A` 灰 |
| 红色分隔线 | `#FF4D4F` |

---

## 新增依赖

```
PyQt6>=6.7.0
qasync>=0.27.0
pygments>=2.18.0
```

需在 `requirements.txt` 和 `pyproject.toml` 中添加。

---

## 开发顺序（5个迭代）

| 迭代 | 内容 | 可测试里程碑 |
|---|---|---|
| **P3.1** | 骨架窗口：主窗口 + 左右分栏 + QSS 主题 | `python gui.py` 能打开空窗口 |
| **P3.2** | 消息气泡 + 输入栏 + 发送/接收基本流程 | 能发消息、显示回复 |
| **P3.3** | 侧边栏历史列表 + 新对话 + 历史切换 | 能切换历史对话、搜索 |
| **P3.4** | Markdown 渲染 + 代码块高亮 + 打字机效果 | 格式化消息正确显示 |
| **P3.5** | 审批弹窗 + 快捷操作按钮 + 打磨 UI 细节 | 完整替代 CLI 版本 |

---

## CLI 与 GUI 共存策略

- `python main.py` → 继续使用现有 CLI（不改动任何现有代码）
- `python gui.py` → 启动桌面 GUI 版本
- 两者共用同一个 `core/`、`agents/`、`skills/` 层，零重复
- GUI 版本通过 `ui/bridge.py` 替换 `core/approval.py` 的 CLI 交互部分

---

## 与现有代码的关系

```
现有代码（完全不改动）          GUI 新增层
─────────────────────          ──────────────────────
core/memory_store.py   ←───   ui/bridge.py
core/audit_log.py      ←───   ui/bridge.py
core/approval.py       ←───   ui/widgets/approval_dialog.py (override)
agents/orchestrator.py ←───   ui/worker.py
config.py              ←───   ui/app.py
main.py                        (不变，CLI 入口保留)
```

---

## 启动方式总结

```bash
# CLI 模式（现有，不变）
python main.py

# GUI 模式（Phase 3 新增）
python gui.py
```
