# wow-agent 开发进度存档

> 更新时间: 2026-08-25 | 状态: v0.5.3 Agent 可靠性四件套
> 恢复方式: 对 AI 说「继续对话」，让它读本文件了解上下文

## 项目定位
对标 Claude Code / opencode 的终端编码 agent，运行在 Jetson Orin NX (ARM64)。
Python 3.10+ / uv 管理；依赖 openai / httpx[socks] / prompt_toolkit / rich。
GitHub: https://github.com/uuzjw/wow-agent（MIT）
声明: 独立开发，与同名开源项目无关（README 顶部 + 全部 .py 版权头已加，v0.5.2 后提交）

## v0.5.3 新增（可靠性四件套）
1. **read_file 分块读取** (`tools.py`)：offset/limit 参数；返回头部元信息
   （总行数/当前区间/续读 offset=...），大文件不再一次吞爆上下文
2. **提示词强化** (`agent.py` system_prompt)：工具失败必须先析因再换法
   （同法连败两次禁原样硬试）；声称完成前强制回读验证 + 跑测试/import 冒烟
3. **循环检测** (`agent.py` run_turn + _call_sig)：同签名调用连续 3 次同结果
   → 注入系统警告逼模型换思路；签名 JSON 规范化（键排序）防参数序误判，
   警告后计数归零
4. **记忆防污染** (`memory.py` + `cli.py`)：/mem save 同名记忆自动更新旧条目；
   超 MAX_MEMS=30 条自动清理最旧并提示

## v0.5.2 新增（ox alpha 兼容性 + 上手体验）
1. **半截输出不残留**：Live 改 transient 渲染，流式中途断线重试时自动丢弃
   半截回答（text_discard），不再出现"半截+完整"两份重复内容
2. **SDK 隐形重试收编**：make_client 统一构造 OpenAI 客户端，max_retries=0 +
   超时收紧（connect 10s / read 90s），退避完全由 run_turn 控制并带指数回退
   （1/2/4/8s），免费档上游卡死不再一次调用挂几分钟；cli/subagent 共用
3. **纯空白回复修复**：模型返回全空白 content 也按空回复处理重试，
   不再静默"成功"
4. **401 根因防线**：/model 向导把服务商说明提到输 key 之前；已知前缀
   key 归属校验（OpenRouter/OpenAI/Groq/Gemini/Anthropic 填错家会拦下确认）；
   fetch_models 在线验 key，失败明确告警"key 可能无效"；401 报错给出去哪拿
   正确 key 的指引（Zen → opencode.ai/auth）
5. **断网沙盒回归**：v0.3 的 unshare -n / 代理黑洞沙盒曾在重构中丢失导致
   /safe 必崩，已恢复；/safe 现为安全模式总开关（沙盒+外传批准一起切）
6. **UI 修复**：tool_result 双重打印 bug（每次工具输出渲染两遍）
7. **README + LICENSE(MIT) + GitHub 发布**：uv 一条命令安装路径已实测

## v0.5.0 已有 ✅
1. **圆角输入框**：`╭─ wow · 服务商/模型 ─╮ │ ❯ ╰─ 模式·任务·/help ─╯`，
   自绘边框（prompt_toolkit bottom_toolbar 在部分环境不渲染，弃用）；
   盒子随提交留在滚动记录里形成对话气泡
2. **Banner 面板化**：WOW logo + 版本/模型信息装进 ROUNDED Panel
3. **工具卡片图标**：$ bash › read + write ± edit * glob ~ grep = plan @ agent
4. **状态线**：`────── ✻ 8.1s · ctx≈365 tok ──────`
5. **ox alpha 兼容**：免费档上游间歇 network_error（实测成功率~1/3），run_turn
   自动重试 6 次（单轮~91%）；空回复明确报错不再静默；思考过程显示已思考字数
6. **Zen 预置清洗**：剔除实测坏模型（deepseek-v4-flash-free/muse-spark-contributor），
   实测工具调用通过的免费模型排前（hy3/nemotron 系/laguna）

## v0.4.0 已有 ✅
1. **服务商扩容到 16 家** (`config.py`)：OpenCode Zen / DeepSeek / 阿里百炼 Qwen /
   Kimi / 智谱 GLM / SiliconFlow / 火山方舟豆包 / 腾讯混元 / MiniMax / OpenRouter /
   Groq / Mistral / xAI Grok / OpenAI / Google Gemini(OpenAI兼容) / Ollama / LM Studio
2. **OpenCode Zen 支持**：base_url https://opencode.ai/zen/v1；
   **ox alpha = 模型 ID `x-preview-f-free`**（免费档）；另有 big-pickle、
   deepseek-v4-flash-free、kimi-k2.7-code 等 64 个模型；key 在 opencode.ai/auth 获取
3. **/model 向导升级**：关键词过滤（输 zen/kimi 直接筛）+ 在线拉取 /v1/models 真实
   模型列表（fetch_models，失败静默回退静态预设）+ LM Studio 走 /models 探测 +
   模型列表超 40 个分页显示；/model <id> 快速切换补全含全部预置模型

## v0.3.0 已有 ✅
1. **任务树 todo_write** (`todo.py` + `ui.py`)：模型多步任务先建计划（parent 父子层级、
   priority 优先级、note 思路/进展），流式回答时左侧实时渲染任务面板（✓/▶/○ + [H][M][L]），
   底栏显示 ☑n/m；清单按会话持久化到 ~/.wow-agent/todos/
2. **只读子代理 task** (`subagent.py`)：全新干净上下文调研代码，禁 write/edit/task，
   工具轨迹一行式展示，报告 ≤8000 字回填主线——主上下文不被文件内容污染
3. **全局长期记忆 /mem** (`memory.py`)：跨目录可用。save(压缩当前对话为摘要)/use N 注入
   /rm N /list /new；存 ~/.wow-agent/memory/
4. **启动 y/N 自主模式**：y = 免逐步确认 + shell 断网沙盒 + 每轮工具执行后实时存档；
   回车 = 每条命令确认（y/n/a 三选）
5. **断网沙盒** (`tools.py`)：默认开启（WOW_SAFE_MODE=0 关）。优先 unshare -n 网络命名
  空间彻底隔离，不可用则降级代理黑洞（127.0.0.1:9）；会话内 /safe 随时开关
6. **高危命令防线**：rm -rf / 、mkfs、dd 写盘、fork bomb、shutdown、chmod -R 777 /、
   git push --force 等 → 无论什么模式强制人工二次确认（force=True 绕过 yolo）
7. **undo 落盘持久化** (`undo.py`)：快照写 ~/.wow-agent/undo/*.json（上限50），崩溃重启
   后照样 /undo；write/edit 前自动存底并渲染彩色 diff
8. 会话 autosave 带 cwd 和 todos（on_progress 每轮触发）；/status、/config 显示沙盒状态

## v0.2.0 已有 ✅
- rich 流式 Markdown + 思考 spinner + 工具卡片（✓/✗ + 耗时 + 截断提示）+ WOW banner
- `/` 命令自动补全（模糊匹配：/cmp → /compact）、/model 参数补全、/mem 子补全、底部状态栏
- 核心循环 40 轮上限、6 基础工具、--yolo、!shell 直通、/compact 手动+超 55k tok 自动压缩
- est_tokens 中英文混合估算；/resume 恢复会话（含任务树）

## 测试状态
- ✅ tests_smoke.py（含 Zen 在线拉模型 64 个验证、16 家服务商结构校验）+ tests_e2e.py 全过
- ✅ 真实 API：DeepSeek 多步任务自纠错验证通过（写错字→自己发现→重写→双重复核）
- ✅ 全局 wow 已重装为 v0.4.0

## 用户环境备忘
- DeepSeek key 生效中（~/.wow-agent.env, chmod 600）
- 本地 Ollama: gemma4:e4b, gemma4-128k:latest
- 注意: 不要把用户 API key 写进任何代码/文档/对话输出

## 下次可选方向（均未开始）
- 任务树与子代理联动（子代理结论自动更新到对应节点 note/progress）
- 并行子代理（同轮派多个 task）
- 权限白名单细化（按命令前缀自动放行）
- README + PyPI 发布
