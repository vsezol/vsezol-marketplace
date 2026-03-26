# vsezol marketplace

Personal skill marketplace for Claude Cowork.

## Skills

| Skill | Description |
|-------|-------------|
| `vsezol:daily-standup` | Daily standup report: Jira + GitLab + Slack → Telegram |
| `vsezol:send-tg-msg` | Send messages to Telegram via Bot API |
| `vsezol:setup` | Install MCP servers (GitLab, Slack, Atlassian, Context7) into Claude Desktop config |

## Usage

```
/vsezol:daily-standup thetradingpit
/vsezol:send-tg-msg REDACTED_CHAT_ID Hello!
/vsezol:setup
```

## MCP servers in template

| Server | Type | Description |
|--------|------|-------------|
| gitlab | Local (npx) | GitLab MCP — merge requests, issues, commits |
| slack | Cloud connector | Slack MCP — messages, channels, search |
| atlassian | Cloud connector | Atlassian MCP — Jira issues, Confluence pages |
| context7 | Local (npx) | Context7 MCP — up-to-date library documentation |

## Quick setup

```bash
python3 ~/projects/pet/vsezol-marketplace/setup/scripts/install.py
```
