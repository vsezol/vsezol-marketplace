---
name: setup
description: >
  Installs MCP servers and configures secrets for the vsezol marketplace.
  Shows available servers, asks for missing credentials, and merges into Claude Desktop config.
  Also manages secrets (API tokens, chat IDs) stored in ~/.vsezol-marketplace/secrets.json.
  Use this skill when the user wants to: set up MCP, add a new MCP server,
  install infrastructure, configure secrets, add telegram token, setup mcp,
  "connect gitlab/slack/atlassian", "configure environment", bootstrap dev environment.
argument-hint: "[action: install | secrets | list]"
---

# Setup — MCP & Secrets Installer

This skill manages two things:
1. **MCP servers** — installs them into Claude Desktop config from `mcp_template.json`
2. **Secrets** — stores API tokens and credentials in `~/.vsezol-marketplace/secrets.json`

## Arguments

- `$0` — **action** (optional): `install`, `secrets`, or `list`.

Example: `/setup install` or `/setup secrets`

## Interactive Setup

Use `AskUserQuestion` for all user decisions:

**If no argument is provided**, ask:

```
What would you like to set up?
Options:
1. Install MCP servers (GitLab, Slack, Atlassian, Context7)
2. Configure secrets (Telegram token, chat ID)
3. Show available MCP servers and their status
4. Full setup (secrets + MCP servers)
```

**When installing MCP servers**, show available options:

```
Which MCP servers would you like to install?
Options:
1. GitLab — access to repos, MRs, issues
2. Context7 — library documentation lookup
3. Atlassian (Jira + Confluence) — cloud connector, connect via Settings → Connectors
4. Slack — cloud connector, connect via Settings → Connectors
5. All local servers (GitLab + Context7)
```

**When configuring secrets**, ask one at a time:

```
Let's configure your secrets.
Do you have a Telegram Bot Token? (Get one from @BotFather in Telegram)
Options:
1. Yes, I'll paste it now
2. Skip for now
```

Then:

```
Do you have a Telegram Chat ID for notifications?
(Send /start to your bot, then check https://api.telegram.org/bot<TOKEN>/getUpdates)
Options:
1. Yes, I'll paste it now
2. Skip for now
```

## Secrets management

Secrets are stored locally at `~/.vsezol-marketplace/secrets.json` and never committed to git. Other skills (like `send-tg-msg`) read from this file.

### Supported secrets

| Key | Description | Used by |
|-----|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token from @BotFather | send-tg-msg, daily-standup |
| `TELEGRAM_CHAT_ID` | Default Telegram chat/user ID for notifications | send-tg-msg, daily-standup |

### How to configure secrets (via skill)

When the user asks to set up secrets or when a skill reports missing secrets:

1. Read `~/.vsezol-marketplace/secrets.json` (create if missing)
2. Check which secrets are present and which are missing
3. For each missing secret, ask the user to provide the value with a clear hint
4. Save the updated secrets file

```bash
mkdir -p ~/.vsezol-marketplace
# Read or create secrets
python3 -c "
import json, os
path = os.path.expanduser('~/.vsezol-marketplace/secrets.json')
data = json.load(open(path)) if os.path.exists(path) else {}
# ... update values ...
json.dump(data, open(path, 'w'), indent=2)
os.chmod(path, 0o600)  # restrict permissions
"
```

### How to configure secrets (via CLI)

```bash
python3 setup/scripts/install.py --secrets
```

## MCP server installation

### Template

The template `mcp_template.json` defines available MCP servers with `{{PLACEHOLDER}}` values. Each server has a `_meta` field with description and prompt hints.

Some servers are **cloud connectors** (Slack, Atlassian) — they connect via Claude's MCP registry UI, not via local npx.

### Mode 1: Via skill (Claude executes)

1. Read `setup/mcp_template.json` from the marketplace
2. Read `~/Library/Application Support/Claude/claude_desktop_config.json`
3. Show which servers are available and which are already installed
4. Ask which ones to install
5. For each server, find `{{...}}` placeholders and ask for values
6. Fill placeholders, remove `_meta`, add to config
7. For cloud connectors, guide user to Settings → Connectors
8. Save config and remind to restart Claude

### Mode 2: Via CLI

```bash
python3 setup/scripts/install.py              # interactive
python3 setup/scripts/install.py --list        # list servers
python3 setup/scripts/install.py --install gitlab context7  # install specific
python3 setup/scripts/install.py --secrets     # configure secrets only
```

## Adding a new MCP to the template

```json
"server-name": {
  "command": "npx",
  "args": ["-y", "@package/name"],
  "env": {
    "API_KEY": "{{MY_API_KEY}}"
  },
  "_meta": {
    "description": "What this server does",
    "prompts": {
      "MY_API_KEY": "Where to get this key"
    }
  }
}
```

Rules:
- Placeholders: `{{NAME}}` — uppercase letters and underscores
- `_meta.description` — short server description
- `_meta.prompts` — maps placeholder → human-readable hint
- `_meta.note` — optional install note (e.g. for cloud connectors)
- `_meta` is stripped on install and never written to Claude config
