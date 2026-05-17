# CareGuide — Claude Session Context

## Environment

- **Model:** runs in Anthropic cloud
- **Harness:** runs locally on Windows (`C:\Users\scott\`)
- **Working branch:** `claude/implement-careguide-build-3Gk3V`
- **Project root:** `C:\Users\scott\code\careguide`
- **All projects live at:** `C:\Users\scott\code\[project-name]`

---

## Obsidian REST API

Obsidian runs locally with the Local REST API plugin active. Use this to read project notes, build docs, and avoid re-explaining context every session.

**Endpoints:**
- HTTP: `http://127.0.0.1:27123`
- HTTPS: `https://127.0.0.1:27124`

**Auth:** API key is in the environment as `OBSIDIAN_API_KEY`. Pass it as:
```
Authorization: Bearer $OBSIDIAN_API_KEY
```

**Fetch a note:**
```bash
curl -s "http://127.0.0.1:27123/vault/[note-name].md" \
  -H "Authorization: Bearer $OBSIDIAN_API_KEY"
```

**Search notes:**
```bash
curl -s "http://127.0.0.1:27123/search/simple/?query=[term]&contextLength=200" \
  -H "Authorization: Bearer $OBSIDIAN_API_KEY"
```

**List vault root:**
```bash
curl -s "http://127.0.0.1:27123/vault/" \
  -H "Authorization: Bearer $OBSIDIAN_API_KEY"
```

### Project Notes Convention

Every project has a build doc in Obsidian named `[project-name]_build`. Always check this at the start of a session for context, decisions, and architecture. Example:

```bash
curl -s "http://127.0.0.1:27123/vault/polaris_build.md" \
  -H "Authorization: Bearer $OBSIDIAN_API_KEY"
```

---

## MCP Servers

Configured in `~/.claude/settings.json` under `enabledMcpjsonServers`:

| Server | Purpose |
|--------|---------|
| `mcp-obsidian` | Obsidian vault access (when available in session) |
| `polaris` | Command center project — see `C:\Users\scott\code\polaris` |

If MCP tools aren't loading in a session, fall back to the Obsidian REST API directly via `curl`.

---

## Global Claude Settings (`~/.claude/settings.json`)

Key settings already configured:
- `model`: sonnet
- `defaultMode`: bypassPermissions
- `enabledPlugins`: `codex@openai-codex`
- `enabledMcpjsonServers`: mcp-obsidian, polaris
- `env`: `ECC_HOOK_PROFILE=minimal`, `OBSIDIAN_API_KEY` (add this)

**UserPromptSubmit hook:** triggers `/project-initiation` skill when you type "new project". If this hook errors, check that `$input` isn't used as a variable name in the PowerShell command — it's reserved. Use `$raw` instead.

---

## Plugins

**Codex (`codex@openai-codex`):**
- Installed at: `C:\Users\scott\.claude\plugins\cache\openai-codex\codex\1.0.4\`
- Works in: **CLI only** (`claude` in terminal)
- Commands: `/codex:review`, `/codex:setup`, `/codex:status`, `/codex:result`
- Does **not** load in desktop app or web sessions — plugin system not supported there
- MCP version: not yet built (planned)

---

## CareGuide Project

**Stack:** HTML/JS frontend · FastAPI backend · Firebase/Firestore · Claude API

**Key files:**
- `build.html` — system map (all pages, roles, services)
- `registries.html` — collections, claims, and endpoint registries
- `firestore.rules` — security rules
- `firestore.indexes.json` — composite indexes
- `api/main.py` — FastAPI entry point
- `api/routers/` — one file per domain
- `docs/contracts/` — feature contracts
- `docs/registries/` — collections.md, claims.md, endpoints.md

**API base URL (production):**
`https://careguide-api-658340465706.us-central1.run.app`

**Known issues to address:**
- `POST /ai/intake` — endpoint missing, caller exists in `intake.html:548` (critical)
- `intake_data` collection — written but never read (orphan)
- `aiConversations` collection — rule exists, no code uses it (dead)
- `profession` and `beta` claims — set but never checked (orphans)
- Practitioner-side reader UI for `family_messages` — not yet built
- `/family-groups/{id}/revoke` — endpoint exists, no UI calls it yet

---

## Session Start Checklist

1. Check Obsidian for `[project]_build` note via REST API
2. Check `build.html` and `registries.html` for current system state
3. Check `docs/contracts/` for any active feature contracts
4. Review recent git log: `git log --oneline -10`
