---
name: daily-standup
description: >
  Generates a daily standup report by collecting activity from Jira, GitLab, and Slack
  for the previous working day, then sends it to Telegram. Takes a company name as argument.
  Use this skill when the user asks to: prepare a standup report, summarize what was done yesterday,
  daily standup, daily report, "what did I do yesterday", morning status update.
argument-hint: "[company-name]"
---

# Daily Standup Report

Collects user activity from three sources — **Jira**, **GitLab**, and **Slack** — for the previous working day, formats a standup report, and sends it to Telegram.

## Argument

`$0` — **company name** (e.g. `thetradingpit`). Used to find the correct Jira site and GitLab projects.

## Interactive Setup

Before starting data collection, use `AskUserQuestion` to clarify missing details:

**If no company argument is provided**, ask:

```
Which company should I prepare the report for?
Options:
1. thetradingpit
2. Other (specify)
```

**After collecting data, before sending**, ask:

```
Report is ready. How should I deliver it?
Options:
1. Send to Telegram (default chat)
2. Send to Telegram (specify chat ID)
3. Just show the report here, don't send
```

## Steps

### Step 1: Determine target date

Determine the **calendar date of the previous working day** — not a time range, but a specific date. This is important due to timezone issues: binding to 00:00–23:59 is unreliable.

Logic:
- Today is Tuesday–Friday → target date = yesterday (e.g. today is March 26 → take March 25)
- Today is Monday → target date = Friday (skip the weekend)

Calculate via bash:
```bash
DOW=$(date +%u)  # 1=Mon, 7=Sun
if [ "$DOW" -eq 1 ]; then
  TARGET_DATE=$(date -d "3 days ago" +%Y-%m-%d 2>/dev/null || date -v-3d +%Y-%m-%d)
else
  TARGET_DATE=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
fi
echo "$TARGET_DATE"
```

All queries below filter **by this exact date**, not by relative "-1d" or timestamps.

### Step 2: Collect data from Jira (Atlassian MCP)

Use Atlassian MCP tools (connected via config):

1. Call `getAccessibleAtlassianResources` to find the company site (match by argument — company name).
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
4. If available — check push/commit activity via `list_projects` and related tools

### Step 4: Collect data from Slack (Slack MCP)

Use Slack MCP tools (connected via config):

1. Call `slack_search_public_and_private` with query `from:me on:YYYY-MM-DD` (substitute TARGET_DATE)
2. Filter for key discussions — channels where the user was actively participating
3. For each discussion briefly describe the topic and decisions

### Step 5: Format the report

Compose the report in **Russian** using this format:

```
🗓 Дейли-отчёт за [date]

📋 Jira:
• [PROJ-123] Issue title — status
• [PROJ-456] Another issue — In Progress → Done

💻 GitLab:
• MR !789 "MR title" — merged (project-name)
• MR !790 "Another MR" — opened (project-name)

💬 Slack:
• #channel-name — discussed topic X, decided Y
• #another-channel — answered question about Z

🎯 Summary: 1-2 sentence recap of what was accomplished.
```

If there's no data from a source — write "no activity for this date", don't skip the section.

### Step 6: Send to Telegram

Use the `send-tg-msg` skill to deliver the report. It will read the chat ID and bot token from `~/.vsezol-marketplace/secrets.json`. If no chat_id is configured there, ask the user.

Always send the report, even if data is scarce — "low activity" is better than silence.

## Error handling

- If an MCP source is unavailable — collect data from the rest and note which source was down
- If Telegram API is unreachable — save the report to a file and notify the user
- Never fail silently — always inform about problems
