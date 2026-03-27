---
name: setup
description: >
  Installs MCP servers, configures secrets, and sets up tools for the vsezol marketplace.
  Shows available servers, asks for missing credentials, and merges into
  both Claude Desktop config and Claude Code config.
  Also manages secrets (API tokens, chat IDs) stored in ~/.vsezol-marketplace/secrets.json.
  Can set up Obsidian CLI for vault interaction.
  Use this skill when the user wants to: set up MCP, add a new MCP server,
  install infrastructure, configure secrets, add telegram token, setup mcp,
  "connect gitlab/slack/atlassian", "configure environment", bootstrap dev environment,
  setup obsidian, configure obsidian cli.
argument-hint: "[action: install | secrets | obsidian | list]"
---

# Setup — MCP, Secrets & Tools Installer

This skill manages three things:
1. **MCP servers** — installs them into **both** Claude Desktop and Claude Code configs from `mcp_template.json`
2. **Secrets** — stores API tokens and credentials in `~/.vsezol-marketplace/secrets.json`
3. **Tools** — sets up CLI tools like Obsidian CLI

## Environment detection

Setup detects the current environment to prioritize installation and show relevant status.

### Detection method

Run via Bash:
```bash
claude mcp list 2>/dev/null
```

- **If succeeds** → running in **Claude Code CLI**. Highlight Claude Code status, but still offer to install for Desktop too.
- **If fails** → running in **Claude Desktop**. Highlight Desktop status, but still offer to install for Claude Code too.

Use this to:
- Show the **current environment's status first** in status displays
- Default to installing for the **current environment** when the user asks to add a single server
- Still support installing to both targets when the user asks for full setup

## Target configs

MCP servers are installed into **two targets simultaneously**:

| Target | Config location | Method |
|--------|----------------|--------|
| **Claude Desktop** | `~/Library/Application Support/Claude/claude_desktop_config.json` | Direct JSON write |
| **Claude Code** | `~/.claude.json` (user scope) | `claude mcp add --scope user` CLI command |

Cloud connectors (Slack, Atlassian, Figma, Miro) are managed via Claude Settings → Connectors, not via config files.

Custom HTTP connectors (Wallet) require a JWT token and are installed to both Desktop (JSON with `headers`) and Code (`claude mcp add --transport http --header`). For Claude Web — add as custom connector at `claude.ai/settings/connectors` (email auth, no token needed).

## Arguments

- `$0` — **action** (optional): `install`, `secrets`, `obsidian`, or `list`.

Example: `/setup install` or `/setup secrets` or `/setup obsidian`

## Interactive Setup

Use `AskUserQuestion` for all user decisions:

**If no argument is provided**, ask:

```
What would you like to set up?
Options:
1. Install MCP servers (GitLab, Slack, Atlassian, Figma, Miro, Wallet, Context7)
2. Configure secrets (Telegram token, chat ID)
3. Set up Obsidian CLI (symlink + PATH)
4. Full setup (secrets + MCP servers + tools)
```

**When installing MCP servers**, detect the environment first (see "Environment detection"), then show available options with status. Show the **current environment's status prominently**:

```
Current environment: Claude Code CLI
Which MCP servers would you like to install?

Options:                                    Code    Desktop
1. GitLab — repos, MRs, issues (local)     ✓       ✓
2. Atlassian (Jira + Confluence) — cloud    ✓       —
3. Slack — cloud connector                  ✓       —
4. Figma — cloud connector                  —       —
5. Miro — cloud connector                   —       —
6. Wallet — custom HTTP (finances)          ✓       ✗
7. Context7 — library docs (local)          ✓       ✓
8. All servers
```

Legend: ✓ installed, ✗ not installed, — managed via Connectors UI

**When installing GitLab or any server with `{{PLACEHOLDER}}` values**, ask for credentials via `AskUserQuestion`:

First check if the server already has values in existing configs. If values are found, ask whether to reuse them. If not found, ask for each placeholder:

```
Please provide your GitLab Personal Access Token.
(Get one from GitLab → Settings → Access Tokens → read_api scope)
Options:
1. I'll paste it now
2. Skip GitLab for now
```

If the user chooses to paste, use `AskUserQuestion` again to receive the token value.

Then ask for the GitLab URL:

```
What is your GitLab instance URL?
Options:
1. https://gitlab.com (default)
2. I'll enter a custom URL
```

After collecting all values, fill placeholders, strip `_meta`, and write to **both** configs:

1. **Claude Desktop**: merge into `mcpServers` in `claude_desktop_config.json`
2. **Claude Code**: run `claude mcp add --scope user -e KEY=value -- name command args...`

If a server is already installed in one target but not the other, only install to the missing target.

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

Servers fall into three categories with different install methods:

| Type | Examples | Claude Desktop | Claude Code |
|------|----------|---------------|-------------|
| **Local (stdio)** | GitLab, Context7, filesystem, git | JSON merge into `claude_desktop_config.json` | `claude mcp add --scope user` |
| **Cloud connector** | Slack, Atlassian, Figma, Miro | Settings → Connectors UI | Settings → Connectors UI |
| **Custom HTTP** | Wallet | JSON merge with `"type": "http"` | `claude mcp add --scope user --transport http` |

### Mode 1: Via skill (Claude executes)

1. Read `setup/mcp_template.json` from the marketplace
2. Read both configs:
   - `~/Library/Application Support/Claude/claude_desktop_config.json` (Claude Desktop)
   - Run `claude mcp list` to check Claude Code servers
3. Show which servers are available and their status in **both** targets
4. Ask which ones to install
5. For each server, find `{{...}}` placeholders and ask for values via `AskUserQuestion`
6. Fill placeholders, remove `_meta`
7. Install based on server type:

**For local (stdio) servers** (have `command` field — e.g. GitLab, Context7, filesystem, git):
- **Claude Desktop**: merge into `mcpServers` in `claude_desktop_config.json`:
  ```json
  "server-name": {
    "command": "npx",
    "args": ["-y", "@package/name"],
    "env": { "KEY": "value" }
  }
  ```
- **Claude Code**: run CLI command:
  ```bash
  claude mcp add --scope user -e KEY=value -- <name> <command> <args...>
  ```
  If already exists, first run `claude mcp remove --scope user <name>`

**For custom HTTP servers** (have `url` field but no `command` — e.g. Wallet):

Wallet requires a **JWT token** from the Wallet app: Settings → Integrations → generate token.
Ask the user for this token via `AskUserQuestion` before installing.

- **Claude Desktop**: merge into `mcpServers` in `claude_desktop_config.json`:
  ```json
  "wallet": {
    "type": "http",
    "url": "https://mcp.wallet.budgetbakers.com/",
    "headers": {
      "Authorization": "Bearer <JWT_TOKEN>"
    }
  }
  ```
- **Claude Code**: run CLI command:
  ```bash
  claude mcp add --scope user --transport http --header "Authorization: Bearer <JWT_TOKEN>" wallet https://mcp.wallet.budgetbakers.com/
  ```
- **Claude Web** (claude.ai): go to `claude.ai/settings/connectors` → "Add custom connector" → name: `Wallet`, URL: `https://mcp.wallet.budgetbakers.com`. Auth via email code (no token needed for web).
- Token can be revoked anytime from Wallet Settings → Integrations. All access is read-only.

**For cloud connectors** (Slack, Atlassian, Figma, Miro — have `_meta.note` mentioning "cloud connector"):
- Cannot be installed via config files — guide user to Settings → Connectors in Claude Desktop/Code/Web UI

8. After installing, remind to **restart Claude Desktop** (Claude Code picks up changes immediately)

### Mode 2: Via CLI

```bash
python3 setup/scripts/install.py              # interactive (installs to both)
python3 setup/scripts/install.py --list        # list servers (shows status in both)
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

## Obsidian CLI setup

The `obsidian` and `obsidian-todo` skills require the Obsidian CLI to be available in PATH. This setup is **optional** — only ask the user if they want it.

**When the user picks Obsidian setup (or full setup)**, ask:

```
Do you want to set up the Obsidian CLI?
(Required for obsidian and obsidian-todo skills)
Options:
1. Yes, set it up
2. No, skip
```

If yes, run the following steps:

### Step 1: Check Obsidian is installed

```bash
ls /Applications/Obsidian.app/Contents/MacOS/Obsidian
```

If not found — inform the user to install Obsidian from https://obsidian.md/download.

### Step 2: Create symlink

```bash
mkdir -p ~/bin
ln -sf /Applications/Obsidian.app/Contents/MacOS/Obsidian ~/bin/obsidian
```

### Step 3: Add `~/bin` to PATH

Check if `~/bin` is already in the user's shell config:

```bash
grep -q 'HOME/bin\|~/bin' ~/.zshrc 2>/dev/null
```

If not present, append:

```bash
echo '' >> ~/.zshrc
echo '# Obsidian CLI and other local binaries' >> ~/.zshrc
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
```

### Step 4: Verify CLI works

```bash
export PATH="$HOME/bin:$PATH"
obsidian help 2>&1 | head -5
```

If the output contains "Command line interface is not enabled" — inform the user:

```
Obsidian CLI is installed but not enabled.
Please open Obsidian → Settings → General → Advanced → enable "Command line interface".
```

### Step 5: Confirm

Tell the user:
- Symlink created at `~/bin/obsidian`
- PATH updated in `~/.zshrc` (restart terminal or run `source ~/.zshrc`)
- The `obsidian` and `obsidian-todo` skills are now ready to use
