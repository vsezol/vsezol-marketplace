---
name: setup
description: >
  Installs MCP servers from a template into Claude Desktop config. Shows available servers,
  asks the user for missing credentials, and merges everything into the config.
  Use this skill when the user wants to: set up MCP, add a new MCP server,
  install infrastructure, setup mcp, "connect gitlab/slack/atlassian", "configure environment",
  "what MCPs can I add", install mcp servers, bootstrap dev environment.
---

# Setup — MCP Infrastructure Installer

This skill manages the installation of MCP servers into Claude Desktop. It uses a template `mcp_template.json` containing server configs with `{{PLACEHOLDER}}` values for secrets and settings.

## How it works

The template defines available MCP servers. Each server has a `_meta` field with a description and prompt hints telling the user what data is needed and where to find it. Servers without placeholders (like context7) can be installed without any user input.

Some servers are **cloud connectors** (Slack, Atlassian) — they connect via Claude's MCP registry UI, not via local npx. The setup skill should guide the user to the Settings → Connectors page for these.

## Mode 1: Via skill (Claude executes)

When the user asks to set up MCP through chat:

1. Read the template `setup/mcp_template.json` from the marketplace
2. Read the current Claude Desktop config: `~/Library/Application Support/Claude/claude_desktop_config.json`
3. Show the user which servers are available — mark which are already installed
4. Ask which ones they want to install
5. For each selected server, find `{{...}}` placeholders and ask the user for values using hints from `_meta.prompts`
6. Fill placeholders, remove `_meta`, and add the config to `mcpServers` in the Claude config
7. For cloud connectors (servers with `url` field and `_meta.note`), inform the user they need to connect via Claude Settings → Connectors
8. Save the config
9. Remind to restart Claude

## Mode 2: Via CLI (user runs directly)

```bash
# Interactive mode — shows list, asks what to install
python3 setup/scripts/install.py

# List available servers
python3 setup/scripts/install.py --list

# Install specific servers
python3 setup/scripts/install.py --install gitlab context7
```

## Adding a new MCP to the template

Add an entry to `mcp_template.json`:

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
      "MY_API_KEY": "Where to get this key (e.g. Settings → API Keys)"
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
