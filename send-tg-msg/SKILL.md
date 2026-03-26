---
name: send-tg-msg
description: >
  Sends a message to Telegram via Bot API. Arguments: chat_id and message text in Markdown format.
  Use this skill when you need to: send a Telegram message, push a notification to TG,
  "send to telegram", "message on telegram", notify telegram, send telegram message.
---

# Send Telegram Message

Sends a message to Telegram via Bot API.

## Arguments

Format: `<chat_id> <message text>`

- **chat_id** — Telegram chat or user ID (numeric). Default: `REDACTED_CHAT_ID`
- **text** — message content in Markdown format

Example: `REDACTED_CHAT_ID Hello, this is a test message!`

## Configuration

- **Bot Token:** `REDACTED_TELEGRAM_BOT_TOKEN`

## How to send

Use bash + curl:

```bash
TELEGRAM_BOT_TOKEN="REDACTED_TELEGRAM_BOT_TOKEN"
CHAT_ID="<chat_id from argument>"
MESSAGE="<text from argument>"

curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "parse_mode=Markdown" \
  --data-urlencode "text=${MESSAGE}"
```

## Limitations and error handling

- Max Telegram message length is **4096 characters**. If text is longer, split into multiple messages and send sequentially.
- If the API returns a Markdown parsing error, retry with `parse_mode=HTML` or without parse_mode.
- If the API is unreachable, inform the user and offer to save the text to a file.
- Always check the API response — `"ok": true` means success.
