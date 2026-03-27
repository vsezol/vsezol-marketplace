---
name: mcp-check
description: >
  Health-check for MCP servers. Detects the current environment (Claude Code CLI or Claude Desktop)
  and checks only MCPs configured for that environment. Returns a status report with environment info.
  Designed to run as a sub-agent before other skills that depend on MCP servers.
  Use this skill when: checking MCP status, "are my MCPs working", before running skills
  that need MCP, diagnosing connection issues, "check gitlab/slack/jira connection".
argument-hint: "[mcp names: gitlab jira slack ...]"
---

# MCP Health Check

Runs lightweight probe requests against MCP servers to verify they are connected and responding. **Environment-aware**: detects whether it runs in Claude Code CLI or Claude Desktop and checks only MCPs configured for the current environment.

This skill is designed to be **launched as a sub-agent** (via the Agent tool) before other skills that depend on MCP. It runs in an isolated context and returns the results.

## Arguments

- `$0...$N` — **MCP names** to check, space-separated. Supported: `gitlab`, `jira`, `slack`, `figma`, `miro`, `wallet`, `all`.
- If no arguments — check all MCPs configured in the current environment.

Examples:
- `/mcp-check gitlab jira slack`
- `/mcp-check all`
- `/mcp-check wallet`
- `/mcp-check gitlab`

## Step 1: Detect environment

Before probing, determine which environment the skill is running in.

### Detection method

Run via Bash:
```bash
claude mcp list 2>/dev/null
```

- **If the command succeeds** (exit code 0 and produces output) → you are in **Claude Code CLI**. Parse the output to get the list of configured MCP servers.
- **If the command fails** (command not found, or exit code ≠ 0) → you are in **Claude Desktop**. Read the config file to get the list:
  ```bash
  cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
  ```
  Parse the `mcpServers` keys from the JSON.

Store the detected environment and the set of configured server names for Step 2.

## Step 2: Filter requested MCPs

Compare the requested MCPs (from arguments) against the set of configured servers:

- If a requested MCP is **not configured** in the current environment → report it as `NOT CONFIGURED` (not the same as DOWN — it was never set up).
- If a requested MCP **is configured** → proceed to probe it in Step 3.
- If no arguments were given → only check MCPs that are configured (skip unconfigured ones entirely).

### MCP name → config server name mapping

| Requested name | Config server name(s) | Notes |
|---|---|---|
| `gitlab` | `gitlab` | Local stdio server |
| `jira` | `atlassian` | Cloud connector — also look for `jira` or `atlassian` |
| `slack` | `slack` | Cloud connector |
| `figma` | `figma` | Cloud connector |
| `miro` | `miro` | Cloud connector |
| `wallet` | `wallet` | Custom HTTP server |

**Cloud connectors** (Slack, Atlassian, Figma, Miro) may not appear in local config files because they are managed via Claude's connector UI. For cloud connectors:
- In **Claude Code CLI**: they appear in `claude mcp list` output if connected.
- In **Claude Desktop**: they may NOT appear in `claude_desktop_config.json` (managed separately). If a cloud connector is not in the config, still attempt the probe — it may be connected via the Connectors UI.

## Step 3: Probe configured MCPs

Each MCP has a specific lightweight probe — a simple, fast, read-only request that verifies the connection works.

### GitLab (`mcp__gitlab__*`)

Probe: list projects with minimal response.
```
Call: mcp__gitlab__list_projects
Args: { "per_page": 1, "simple": true }
```
- **UP** if it returns a list (even empty)
- **DOWN** if it throws an error or times out

### Jira / Atlassian (`mcp__claude_ai_Atlassian__*`)

Probe: list accessible resources.
```
Call: mcp__claude_ai_Atlassian__getAccessibleAtlassianResources
Args: {}
```
- **UP** if it returns a list of sites
- **DOWN** if it throws an error or times out

### Slack (`mcp__claude_ai_Slack__*`)

Probe: search with a minimal query.
```
Call: mcp__claude_ai_Slack__slack_search_public_and_private
Args: { "query": "test", "limit": 1 }
```
- **UP** if it returns results (even empty)
- **DOWN** if it throws an error or times out

### Figma (`mcp__figma__*`)

Probe: any lightweight Figma MCP call available. Since Figma MCP is an HTTP cloud connector, attempt any list/read call.
- **UP** if it responds without error
- **DOWN** if it throws an error or times out

### Miro (`mcp__miro__*`)

Probe: any lightweight Miro MCP call available. Since Miro MCP is an HTTP cloud connector, attempt any list/read call.
- **UP** if it responds without error
- **DOWN** if it throws an error or times out

### Wallet / BudgetBakers (`mcp__wallet__*`)

Probe: list accounts (lightweight, read-only).
```
Call: mcp__wallet__get_accounts
Args: {}
```
- **UP** if it returns a list of accounts
- **DOWN** if it throws an error or times out

## Execution

1. **Detect environment** (Claude Code CLI or Claude Desktop) — see Step 1
2. **Get configured MCPs** from the environment's config
3. **Filter** requested MCPs against configured ones — see Step 2
4. Run **all probes in parallel** (use parallel tool calls) for maximum speed — see Step 3
5. Collect results and output a status report

## Output format

```
MCP Health Check (Claude Code CLI):
Configured servers: gitlab, wallet, context7

- GitLab: OK
- Wallet: OK
- Slack: NOT CONFIGURED (not installed in Claude Code CLI — run /vsezol:setup to add)
```

Or for Desktop:

```
MCP Health Check (Claude Desktop):
Configured servers: gitlab, context7

- GitLab: OK
- Wallet: NOT CONFIGURED (not installed in Claude Desktop — run /vsezol:setup to add)
```

Status values:
- **OK** — probe succeeded, MCP is connected and responding
- **DOWN** — MCP is configured but probe failed (error or timeout)
- **NOT CONFIGURED** — MCP is not installed in the current environment

Return the environment name, list of configured servers, and status for each requested MCP.

## How other skills should use this

Other skills (like `daily-standup`, `wallet`) should launch `mcp-check` as a **sub-agent** before starting data collection:

```
Launch Agent with prompt:
  "Run the mcp-check skill to verify these MCPs are available: gitlab jira slack.
   Return the status of each MCP."
```

Then use the result to:
- Skip unavailable sources (don't waste time on failing requests)
- Suggest `/vsezol:setup` for MCPs that are NOT CONFIGURED
- Include a note in the output about which sources were down
- Proceed with available sources only
