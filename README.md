# wow-agent

终端里的编码 agent —— 对标 Claude Code / opencode 的开源实现。跑在本地终端，
接任意 OpenAI 兼容大模型 API，能读写文件、执行 shell、自建任务计划、派子代理调研代码。

Linux x86_64 / ARM64（Jetson Orin NX 实测）为主场。

## 特性

- **16 家服务商开箱即用**：OpenCode Zen / DeepSeek / Qwen / Kimi / GLM /
  SiliconFlow / 豆包 / 混元 / MiniMax / OpenRouter / Groq / Mistral / Grok /
  OpenAI / Gemini / Ollama / LM Studio，`/model` 向导在线拉取真实模型列表
- **免费可用**：OpenCode Zen 免费档模型（含 ox alpha `x-preview-f-free`），
  key 在 [opencode.ai/auth](https://opencode.ai/auth) 获取；上游波动自动重试
- **任务树计划**：多步任务自动拆解成带优先级/父子层级的清单，流式回答时侧栏实时渲染
- **只读子代理**：干净上下文里调研代码，只回结论，不污染主对话
- **长期记忆**：`/mem save` 把对话压缩成经验摘要，任何目录 `/mem use` 随时调用
- **安全防线**：断网沙盒执行 shell（unshare -n / 代理黑洞）、上传外发命令强制批准、
  高危命令二次确认、AI 改动可 `/undo` 撤销
- **上下文管理**：流式 Markdown 渲染、超长历史自动 LLM 压缩、会话持久化与 `/resume`
- **opencode 式 UI**：圆角输入框、工具调用卡片、彩色 diff、思考过程计数

## 安装

需要 [uv](https://docs.astral.sh/uv/)（没有也没关系，下面的命令会自动装上）。

**Ubuntu / Debian / WSL：**

```bash
cd wow-agent && curl -LsSf https://astral.sh/uv/install.sh | sh && uv sync && uv run wow
```

**Windows（PowerShell，实验性）：**

```powershell
cd wow-agent; irm https://astral.sh/uv/install.ps1 | iex; $env:Path += ";$env:USERPROFILE\.local\bin"; uv sync; uv run wow
```

之后每次启动：

```bash
uv run wow        # 或 .venv/bin/wow
```

## 快速上手

```text
$ wow                 # 或 uv run wow
进入自主模式？ y/N     # y = 命令免逐步确认（高危/外传仍会拦截）
> 帮我看看这个项目的结构
```

- 首次启动会引导配置服务商和 API key，写入 `~/.wow-agent.env`（权限 600）
- `!<命令>` 不经模型直接跑 shell，如 `!git status`
- 输入 `/` 有模糊补全，`/help` 看全部命令

## 常用命令

| 命令 | 说明 |
|---|---|
| `/model` | 切换服务商/模型向导；`/model <id>` 快速切换 |
| `/status` | 会话状态：上下文占用、任务进度、可撤销改动 |
| `/compact [要求]` | 手动压缩历史（超阈值也会自动触发） |
| `/mem save/use/rm/list/new` | 长期记忆管理 |
| `/resume` | 恢复历史会话 |
| `/undo` | 撤销 AI 最近一次文件修改 |
| `/safe` | 开/关安全模式（断网沙盒 + 外传强制批准） |
| `/clear` `/exit` | 清空对话 / 退出 |

## 配置

配置存于 `~/.wow-agent.env`，也可用环境变量覆盖：
`WOW_API_KEY`、`WOW_BASE_URL`、`WOW_MODEL`、`WOW_SAFE_MODE`（0 关沙盒）、
`WOW_MAX_ITER`、`WOW_AUTO_COMPACT`。参考 `.env.example`。

用 Ollama / LM Studio 本地模型无需 key：`/model` 里选对应服务商即可。

## 开发

```bash
uv sync                      # 安装依赖
uv run python tests_smoke.py # 冒烟测试（离线）
uv run python tests_e2e.py   # 端到端模拟（假 LLM，离线）
```

## License

[MIT](LICENSE) © uuzjw
