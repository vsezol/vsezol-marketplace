# vsezol marketplace

Personal skill marketplace for Claude Cowork.

## Skills

| Skill | Description |
|-------|-------------|
| `vsezol:daily-standup` | Ежедневный отчёт перед дейли: Jira + GitLab + Slack → Telegram |
| `vsezol:send-tg-msg` | Отправка сообщений в Telegram через Bot API |

## Usage

```
/vsezol:daily-standup thetradingpit
/vsezol:send-tg-msg REDACTED_CHAT_ID Привет!
```

## Requirements

- **Slack MCP** — connected via Claude MCP registry
- **Atlassian MCP** — connected via Claude MCP registry
- **GitLab MCP** — `@zereight/mcp-gitlab` configured in MCP settings
- **Telegram Bot** — token configured in `send-tg-msg` skill
