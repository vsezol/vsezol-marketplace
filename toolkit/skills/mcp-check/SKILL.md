---
name: mcp-check
description: >
  Health-check for MCP servers. Runs a lightweight probe against each specified MCP
  to verify connectivity. Returns a status report: which MCPs are up and which are down.
  Designed to run as a sub-agent before other skills that depend on MCP servers.
  Use this skill when: checking MCP status, "are my MCPs working", before running skills
  that need MCP, diagnosing connection issues, "check gitlab/slack/jira connection".
argument-hint: "[mcp names: gitlab jira slack ...]"
---

# MCP Health Check

Runs lightweight probe requests against specified MCP servers to verify they are connected and responding. Returns a clear status report.

This skill is designed to be **launched as a sub-agent** (via the Agent tool) before other skills that depend on MCP. It runs in an isolated context and returns the results.

## Arguments

- `$0...$N` — **MCP names** to check, space-separated. Supported: `gitlab`, `jira`, `slack`, `all`.
- If no arguments — check all known MCPs.

Examples:
- `/mcp-check gitlab jira slack`
- `/mcp-check all`
- `/mcp-check gitlab`

## Probe definitions

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

## Execution

1. Parse the argument list to determine which MCPs to check
2. Run **all probes in parallel** (use parallel tool calls) for maximum speed
3. Collect results
4. Output a status report

## Output format

```
MCP Health Check:
- GitLab: OK
- Jira: OK
- Slack: UNAVAILABLE (error: connection timeout)
```

Return the list of available and unavailable MCPs. Skills that call mcp-check as a sub-agent can use this output to decide which data sources to query and which to skip.

## How other skills should use this

Other skills (like `daily-standup`) should launch `mcp-check` as a **sub-agent** before starting data collection:

```
Launch Agent with prompt:
  "Run the mcp-check skill to verify these MCPs are available: gitlab jira slack.
   Return the status of each MCP."
```

Then use the result to:
- Skip unavailable sources (don't waste time on failing requests)
- Include a note in the output about which sources were down
- Proceed with available sources only
