# wow-agent

> **Terminal Coding Agent for Everyone**  
> 一个简单、开放、可扩展的终端 AI 编程助手

**中文** | **English**

---

## 为什么是 wow-agent？

传统 AI 编程流程往往变成：

```
用户 → 复制代码 → 问 AI → 自己修改 → 再问 AI → 无限循环
```

wow-agent 改变这个循环，让 AI 直接参与真实的开发流程：

```
用户给目标 → AI 规划 → 调用工具执行 → 验证结果 → 完成
```

它不是聊天工具，而是**能在真实代码库里工作的 AI 编程伙伴**。

---

## 为什么选择 wow-agent？

| 核心差异 | 传统工具 | wow-agent |
|---------|---------|-----------|
| **模型自由** | 绑定单一商家/模型 | **任意 OpenAI 兼容 API** + 本地模型（Ollama/LM Studio） |
| **运行环境** | 依赖特定 IDE/云端 | **纯终端**，本地运行，数据完全掌控 |
| **架构支持** | 仅 x86 | **原生 ARM64**（Jetson Orin NX 实测，边缘设备可用） |
| **安全性** | AI 直接执行命令 | **三重安全层**：断网沙盒 + 外传拦截 + 高危二次确认 + 一键回滚 |
| **可扩展性** | 封闭生态 | **MCP 生态** + 自定义工具 + 子代理架构 |

> **一句话**：wow-agent 让你拥有模型选择权、环境控制权、安全决策权。

---

## 架构概览：四层设计

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: Agent Brain (智能核心)                     │
│  ├─ 任务规划 · 状态机 · 子代理协作                    │
└─────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────┐
│  Layer 2: Developer Tools (开发工具)                 │
│  ├─ 文件 CRUD / Diff / Undo / 代码索引               │
└─────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────┐
│  Layer 3: Model Ecosystem (模型生态)                │
│  ├─ 云端：DeepSeek/Qwen/OpenAI/Gemini/...           │
│  └─ 本地：Ollama / LM Studio                        │
└─────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────┐
│  Layer 4: Safety System (安全系统)                   │
│  ├─ 断网沙盒 · 外传拦截 · 高危二次确认 · 撤销/回滚   │
└─────────────────────────────────────────────────────┘
```

| 层级 | 核心能力 | 关键技术点 |
|------|---------|-----------|
| **Agent Brain** | 任务拆解、状态机、子代理 | planning→executing→verifying→done/failed 状态机 |
| **Dev Tools** | 文件操作、Diff/Undo、代码索引 | AST 解析 Python 符号表、增量索引、Diff 可视化 |
| **Model Eco** | 云端/本地统一接入 | 16+ 服务商 + Ollama/LM Studio，`/model` 在线拉取列表 |
| **Safety** | 沙盒/外传拦截/确认/回滚 | `unshare -n` 网络隔离、外传拦截、高危二次确认、`/undo` |

---

## 快速开始

### 安装（需 [uv](https://docs.astral.sh/uv/)）

```bash
# Ubuntu / Debian / WSL
cd wow-agent && curl -LsSf https://astral.sh/uv/install.sh | sh && uv sync && uv run wow

# Windows (PowerShell，实验性)
cd wow-agent; irm https://astral.sh/uv/install.ps1 | iex
$env:Path += ";$env:USERPROFILE\.local\bin"
uv sync; uv run wow
```

之后每次启动：

```bash
uv run wow        # 或 .venv/bin/wow
```

> 首次启动会引导配置服务商和 API Key，写入 `~/.wow-agent.env`（权限 600）

---

## 核心功能一览

### 🤖 Agent Brain（智能核心）
- **任务树 + 状态机**：自动拆解多步任务，`planning → executing → verifying → done/failed`
- **子代理**：干净上下文调研代码，只回结论，不污染主上下文；`/review` 三级代码审查
- **状态机**：`planning → executing → verifying → done/failed` 自动流转

### 🛠 Developer Tools
- **文件操作**：读/写/改/删/搜索，`code_index` 一次扫描生成 Python 符号表
- **Diff & Undo**：彩色 Diff 可视化、单步 `/undo`、整轮失败整轮回滚、快照跨重启有效
- **代码索引**：AST 解析 Python 符号表，增量更新，`code_index` 先查索引再精读

### 🤝 Model Ecosystem
| 类型 | 支持 |
|------|------|
| 云端 | DeepSeek / Qwen / Kimi / GLM / SiliconFlow / 豆包 / 混元 / MiniMax / OpenRouter / Groq / Mistral / Grok / OpenAI / Gemini / OpenCode Zen |
| 本地 | Ollama / LM Studio（无需 Key）|
| 免费档 | OpenCode Zen 免费档（含 ox alpha `x-preview-f-free`）|

### 🛡 Safety System
- **断网沙盒**：`unshare -n` 网络命名空间隔离，不可用时降级代理黑洞
- **外传拦截**：`curl POST` / `scp` / `git push` / `npm publish` 等自动拦截
- **高危二次确认**：`rm -rf /`、`mkfs`、`dd`、`fork bomb`、`shutdown`、`chmod -R 777 /` 等强制二次确认
- **一键回滚**：`/undo` 单步撤销，任务失败可整轮回滚

---

## 配置

配置文件：`~/.wow-agent.env`（权限 600）

```bash
WOW_API_KEY=          # API Key
WOW_BASE_URL=         # API Base URL
WOW_MODEL=            # 模型 ID
WOW_SAFE_MODE=1       # 0 关闭沙盒
WOW_MAX_ITER=40       # 最大迭代轮数
WOW_AUTO_COMPACT=55000 # 自动压缩阈值
WOW_LANGUAGE=en       # en/zh，默认 en
WOW_MODEL_CTX=128000  # 模型上下文长度（用于上下文估算）
WOW_CELL_ASPECT=2.0   # 终端字符宽高比（logo 缩放用）
WOW_UPLOAD_GUARD=1    # 外传防护开关
```

MCP Server 配置：`~/.wow-agent/mcp.json`

```json
{
  "servers": {
    "fs": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-fs", "/tmp"]}
  }
}
```

---

## 快速上手

```text
$ wow
Enter auto mode? y/N    # y = 免逐步确认（高危/外传仍需批准）
> 帮我看看这个项目的结构
```

常用交互：
- `!<命令>`：不经模型直接跑 shell（如 `!git status`）
- `/`：模糊补全命令，`/help` 查看全部

| 命令 | 说明 |
|------|------|
| `/model` | 切换服务商/模型向导；`/model <id>` 快速切换 |
| `/status` | 会话状态：上下文、任务进度、可撤销改动 |
| `/compact [要求]` | 手动压缩历史 |
| `/mem save/use/rm/list/new` | 长期记忆管理 |
| `/resume` | 恢复历史会话 |
| `/undo` | 撤销最近修改；任务失败可整轮回滚 |
| `/review [路径]` | 只读代码审查：🔴高风险 / 🟡建议 / 🟢优化 |
| `/language [en\|zh]` | 切换语言（默认英文，支持交互式菜单） |
| `/safe` | 开/关安全模式 |
| `/clear` `/exit` | 清空对话 / 退出 |

---

## 开发与测试

```bash
uv sync                      # 安装依赖
uv run python tests_smoke.py # 冒烟测试（离线）
uv run python tests_e2e.py   # 端到端模拟（假 LLM，离线）
```

---

## 参与贡献

欢迎任何形式的贡献！

- 🌐 **新模型/服务商适配** —— `config.py` 扩展 `PROVIDERS`
- 🎨 **UI/UX 改进** —— `ui.py` / `tui.py`（若恢复）
- 🔧 **新工具开发** —— `tools.py` 扩展 `TOOLS_SCHEMA` + `execute`
- 🐛 **Bug 修复 / 文档完善** —— Issues / PRs 欢迎

提交前请跑通测试：

```bash
uv run python tests_smoke.py
uv run python tests_e2e.py
```

---

## License

[MIT](LICENSE) © uuzjw

> **独立开发**，与同名同姓的开源项目无关。  
> 问题反馈请到 [GitHub Issues](https://github.com/uuzjw/wow-agent/issues)。