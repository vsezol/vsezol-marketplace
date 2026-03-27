---
name: daily-standup
description: >
  Generates a daily standup report by collecting activity from Jira, GitLab, and Slack
  for the previous working day. Outputs the report as text. Optionally sends to Telegram with --tg flag.
  Use this skill when the user asks to: prepare a standup report, summarize what was done yesterday,
  daily standup, daily report, "what did I do yesterday", morning status update.
argument-hint: "[company-name] [YYYY-MM-DD] [--tg]"
---

# Daily Standup Report

Collects user activity from three sources — **Jira**, **GitLab**, and **Slack** — for the previous working day and formats a standup report. By default outputs the report as text. With `--tg` flag, also sends it to Telegram.

## Arguments

- `$0` — **company name** (optional, e.g. `thetradingpit`). Used to filter the correct Jira site and GitLab projects. If omitted, collect data from **all** configured sources without filtering by company.
- `$1` — **date** (optional, format `YYYY-MM-DD`). The date to generate the report for. If omitted, uses the previous working day.
- `--tg` — (optional flag, can appear anywhere in arguments). If present, also send the report to Telegram via the `send-tg-msg` skill.

## Interactive Setup

This skill is designed to run autonomously (e.g. on a schedule) without user interaction. **Never ask the user which company to use** — if no company argument is provided, simply query all configured MCP sources (Jira, GitLab, Slack) without filtering by company name.

**Delivery**: by default the report is only output as text. If `--tg` flag is present, also send to Telegram using the `send-tg-msg` skill (reads secrets from `~/.claude/secrets.json`). Only ask the user about Telegram credentials if `--tg` is used and secrets are missing.

## Steps

### Step 1: Determine target date

If a date argument (`$1`) is provided in `YYYY-MM-DD` format, use it directly as `TARGET_DATE`.

Otherwise, determine the **calendar date of the previous working day**:
- Today is Tuesday–Friday → target date = yesterday
- Today is Monday → target date = Friday (skip the weekend)

Calculate via bash:
```bash
if [ -n "$DATE_ARG" ]; then
  TARGET_DATE="$DATE_ARG"
else
  DOW=$(date +%u)  # 1=Mon, 7=Sun
  if [ "$DOW" -eq 1 ]; then
    TARGET_DATE=$(date -d "3 days ago" +%Y-%m-%d 2>/dev/null || date -v-3d +%Y-%m-%d)
  else
    TARGET_DATE=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
  fi
fi
echo "$TARGET_DATE"
```

All queries below filter **by this exact date**, not by relative "-1d" or timestamps.

### Step 2: Collect data from Jira (Atlassian MCP)

Use Atlassian MCP tools (connected via config):

1. Call `getAccessibleAtlassianResources` to list available sites. If a company argument was provided, match by name. If no argument — use the first available site (or query all sites).
2. Use `searchJiraIssuesUsingJql` with date-bound JQL:
   - `assignee = currentUser() AND updated >= "YYYY-MM-DD" AND updated < "YYYY-MM-DD+1" ORDER BY updated DESC`
   - Where `YYYY-MM-DD` is `TARGET_DATE` and `YYYY-MM-DD+1` is the next day
   - Example: if TARGET_DATE = 2026-03-25, then `updated >= "2026-03-25" AND updated < "2026-03-26"`
3. For each issue collect: key (PROJ-123), title, current status, and if possible — status transitions

### Step 3: Collect data from GitLab (GitLab MCP)

Use GitLab MCP tools (`@zereight/mcp-gitlab`, connected via config):

1. Call `my_issues` or `list_issues` with `updated_after=TARGET_DATE` and `updated_before=TARGET_DATE+1`
2. Call `list_merge_requests` with `updated_after=TARGET_DATE` and `updated_before=TARGET_DATE+1`, scope=all — find MRs the user opened, updated, or merged on that exact date
3. For each MR collect: number, title, status (opened/merged/closed), project
4. Call `list_events` with `action=pushed`, `after=TARGET_DATE-1` (day before), `before=TARGET_DATE+1` (day after) to get push events for the exact target date. Note: the API uses exclusive boundaries, so to include events on 2026-03-25 use `after=2026-03-24` and `before=2026-03-26`
5. For each push event collect: project name, branch, number of commits. This captures work pushed to branches that don't have a merge request yet

### Step 4: Collect data from Slack (Slack MCP)

Use Slack MCP tools (connected via config):

1. Call `slack_search_public_and_private` with query `from:me on:YYYY-MM-DD` (substitute TARGET_DATE)
2. Filter for key discussions — channels where the user was actively participating
3. For each discussion briefly describe the topic and decisions

### Step 5: Format the report

Compose the report in **Russian** using this format:

```
Daily Report {Company (if specified)} {Date}

Jira:
- {human-readable task description: what was done and current status}
- {human-readable task description}

Gitlab:
- {human-readable activity description: what was done, in which project, why}
- {human-readable activity description}

Slack:
- {human-readable activity description: what was discussed, what was decided}
- {human-readable activity description}

Summary:
{2-4 sentences in natural language, as if you're telling a colleague at standup what you did yesterday. Focus on WHAT was accomplished and WHY, not ticket numbers or technical IDs. Should be easy to read aloud at a daily meeting. Avoid listing raw numbers, hashes, or MR IDs here — use plain human language.}
```

**Formatting rules:**
- Each bullet point should be a clear, self-contained sentence — not a raw ticket key or MR number
- Jira: include the ticket key (e.g. PROJ-123) but lead with a meaningful description, e.g. "Fixed validation on signup form (PROJ-123, Done)"
- GitLab: describe what was done, not just "MR opened". E.g. "Opened MR for refactoring auth middleware in bms" or "Pushed fixes for email templates to feature branch in web-app"
- Slack: summarize the discussion topic and outcome, not just the channel name
- Summary: write it as if speaking at a standup — natural, concise, no jargon dump. A non-technical PM should understand it
- If there's no data from a source — write "no activity", don't skip the section

### Step 6: Output the report

**Always** output the formatted report as text in the conversation — this is the primary delivery method.

### Step 7: Send to Telegram (only if `--tg` flag is present)

If the `--tg` flag was passed in arguments, **additionally** send the report to Telegram using the `send-tg-msg` skill. It reads the chat ID and bot token from `~/.claude/secrets.json`. If secrets are already configured, send immediately without asking the user. Only use `AskUserQuestion` if secrets are missing.

If `--tg` is not present — skip this step entirely.
