import os
from pathlib import Path

ENV_FILE = Path.home() / ".wow-agent.env"

PROVIDERS = {
    "zen": {
        "name": "OpenCode Zen",
        "base_url": "https://opencode.ai/zen/v1",
        "note": ("key 在 opencode.ai/auth 获取；x-preview-f-free 即 ox alpha"
                 "（免费档上游间歇抽风，wow 会自动重试；以下免费模型均已实测"
                 "支持工具调用）"),
        "models": [
            "x-preview-f-free",
            "hy3-free",
            "nemotron-3-ultra-free",
            "nemotron-3.5-lightning-free",
            "laguna-s-2.1-free",
            "big-pickle",
            "mimo-v2.5-free",
            "kimi-k2.7-code",
            "glm-5.2",
            "qwen3.6-plus",
            "claude-sonnet-5",
            "gpt-5.3-codex",
            "grok-4.6",
            "minimax-m2.7",
        ],
    },
    "deepseek": {
        "name": "DeepSeek 官方",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "qwen": {
        "name": "阿里百炼 Qwen",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen3-coder-plus", "qwen-max", "qwen-plus", "qwen-turbo"],
    },
    "kimi": {
        "name": "Moonshot Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["kimi-k2.7-code", "kimi-k2.6", "kimi-k2.5", "kimi-k3"],
    },
    "zhipu": {
        "name": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "models": ["glm-5.2", "glm-5.1", "glm-5", "glm-4.6"],
    },
    "siliconflow": {
        "name": "SiliconFlow 硅基流动",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": [
            "deepseek-ai/DeepSeek-V3.1",
            "Qwen/Qwen3-Coder-480B-A35B-Instruct",
        ],
    },
    "doubao": {
        "name": "火山方舟 豆包",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "models": ["doubao-seed-code-preview"],
    },
    "hunyuan": {
        "name": "腾讯混元",
        "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
        "models": ["hunyuan-turbos", "hunyuan-t1"],
    },
    "minimax": {
        "name": "MiniMax",
        "base_url": "https://api.minimax.io/v1",
        "models": ["MiniMax-M2.7", "MiniMax-M2.5"],
    },
    "openrouter": {
        "name": "OpenRouter（聚合 400+ 模型）",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "anthropic/claude-sonnet-5",
            "openai/gpt-5.3-codex",
            "deepseek/deepseek-chat",
        ],
    },
    "groq": {
        "name": "Groq（极速推理）",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile"],
    },
    "mistral": {
        "name": "Mistral",
        "base_url": "https://api.mistral.ai/v1",
        "models": ["mistral-large-latest", "codestral-latest"],
    },
    "xai": {
        "name": "xAI Grok",
        "base_url": "https://api.x.ai/v1",
        "models": ["grok-4.6", "grok-code-fast-1"],
    },
    "openai": {
        "name": "OpenAI 官方",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-5.3-codex", "gpt-5.4-mini", "gpt-5o"],
    },
    "gemini": {
        "name": "Google Gemini（OpenAI 兼容）",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": ["gemini-3.7-flash", "gemini-3.1-pro"],
    },
    "ollama": {
        "name": "Ollama 本地（无需 key）",
        "base_url": "http://localhost:11434/v1",
        "models": ["qwen3:8b", "qwen2.5-coder:7b"],
    },
    "lmstudio": {
        "name": "LM Studio 本地（无需 key）",
        "base_url": "http://localhost:1234/v1",
        "models": [],
    },
}


def fetch_models(base_url, key, timeout=8):
    """从服务商 /models 端点在线拉取模型列表；失败返回 None。"""
    try:
        import httpx
        r = httpx.get(
            base_url.rstrip("/") + "/models",
            headers={"Authorization": f"Bearer {key}"} if key else {},
            timeout=timeout)
        data = r.json().get("data") or []
        return [m["id"] for m in data
                if isinstance(m, dict) and m.get("id")]
    except Exception:
        return None


MODEL_ALIASES = {
    "ox": "x-preview-f-free",
    "ox-alpha": "x-preview-f-free",
}

ALIAS_DISPLAY = {}
for _a, _m in MODEL_ALIASES.items():
    ALIAS_DISPLAY.setdefault(_m, []).append(_a)


def resolve_model(name):
    """把 ox / ox-alpha 这类别名解析成真实模型 ID，其余原样返回。"""
    n = str(name).strip()
    return MODEL_ALIASES.get(n.lower()) or \
        MODEL_ALIASES.get(n.lower().replace(" ", "-")) or n


def _load_dotenv():
    for candidate in (Path.cwd() / ".env", ENV_FILE):
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

API_KEY = os.environ.get("WOW_API_KEY", "")
BASE_URL = os.environ.get("WOW_BASE_URL", PROVIDERS["deepseek"]["base_url"])
MODEL = os.environ.get("WOW_MODEL", PROVIDERS["deepseek"]["models"][0])
MAX_ITER = int(os.environ.get("WOW_MAX_ITER", "40"))
AUTO_COMPACT = int(os.environ.get("WOW_AUTO_COMPACT", "55000"))
SUB_ITER = int(os.environ.get("WOW_SUB_ITER", "10"))
UPLOAD_GUARD = os.environ.get("WOW_UPLOAD_GUARD", "1").lower() not in (
    "0", "false", "no")


def set_upload_guard(v):
    global UPLOAD_GUARD
    UPLOAD_GUARD = bool(v)


def apply(key=None, base_url=None, model=None):
    global API_KEY, BASE_URL, MODEL
    if key is not None:
        API_KEY = key
    if base_url is not None:
        BASE_URL = base_url
    if model is not None:
        MODEL = model


def save_env(updates):
    lines = (
        ENV_FILE.read_text(encoding="utf-8").splitlines()
        if ENV_FILE.exists() else []
    )
    out, seen = [], set()
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k = s.split("=", 1)[0].strip()
            if k in updates:
                out.append(f"{k}={updates[k]}")
                seen.add(k)
                continue
        out.append(line)
    for k, v in updates.items():
        if k not in seen:
            out.append(f"{k}={v}")
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    try:
        os.chmod(ENV_FILE, 0o600)
    except OSError:
        pass
