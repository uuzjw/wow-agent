---
title: Add a Model Provider
layout: docs
permalink: /tutorials/add-provider/
eyebrow: Developer Tutorial
description: Connect any OpenAI-compatible endpoint to wow-agent in minutes — presets, headers, model lists and per-provider capabilities.
---

Any endpoint that speaks the OpenAI Chat Completions dialect can be a wow-agent provider. This tutorial adds a fictional provider **NebulaAI**.

## Fastest path: no code at all

For one-off use, skip code — set three env vars:

```bash
# ~/.wow-agent.env
WOW_API_KEY=neb_sk-...
WOW_BASE_URL=https://api.nebula.ai/v1
WOW_MODEL=nebula-coder-large
```

Done. The rest of this tutorial makes it a **first-class provider** with a picker entry and online model listing.

## Step 1 — Add the preset

In `wow_agent/config.py`, extend `PROVIDERS`:

```python
"nebula": {
    "base_url": "https://api.nebula.ai/v1",
    "models": ["nebula-coder-large", "nebula-coder-mini"],
    "default": "nebula-coder-large",
    "api_key_env": "NEBULA_API_KEY",      # where to read the key from
    "capabilities": {
        "streaming": True,
        "tools": True,          # supports function/tool calling
        "vision": False,
        "max_context": 128000,
    },
},
```

Field reference:

| Field | Required | Meaning |
|---|---|---|
| `base_url` | ✔ | OpenAI-compatible root (include `/v1` when required) |
| `models` | ✔ | static fallback list |
| `default` | ✔ | preselected model |
| `api_key_env` | – | env var holding the key |
| `headers` | – | extra headers, `{api_key}` placeholder supported |
| `capabilities` | – | lets the agent adapt behavior (e.g. no tool-calling) |

## Step 2 — Verify

```bash
uv run wow
/model            # NebulaAI should appear in the picker
/model nebula     # quick switch
/model --fetch    # pull live model list from the endpoint (if supported)
```

## Step 3 — Handle quirks (optional)

Some endpoints deviate slightly. Common patches, in `config.py` provider entry:

```python
"headers": {"X-Source": "wow-agent"},          # tracking header
"query_params": {"api-version": "2024-02-01"}, # Azure-style versioning
"wire": {"tool_format": "openai_v1"},          # force a dialect
```

## Step 4 — Contribute it back

1. `uv run python tests_smoke.py` — must stay green
2. Add a line to `PROVIDERS` + a test fixture
3. PR with the provider name as title: `feat(providers): NebulaAI`

See [Contributing](/tutorials/contributing/) for the full workflow.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `401 Unauthorized` | key in wrong env var / not exported |
| `404` on chat | `base_url` missing or over-including `/v1` |
| Tools never called | provider `capabilities.tools` false or dialect mismatch |
| Streaming garbled | set `capabilities.streaming: false` to force plain mode |
