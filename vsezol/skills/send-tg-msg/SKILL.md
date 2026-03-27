---
name: send-tg-msg
description: >
  Sends a message to Telegram via Bot API. Arguments: chat_id and message text in Markdown format.
  Use this skill when you need to: send a Telegram message, push a notification to TG,
  "send to telegram", "message on telegram", notify telegram, send telegram message.
argument-hint: "[chat_id] [message text]"
---

# Send Telegram Message

Sends a message to Telegram via Bot API.

## Arguments

- `$0` — **chat_id** (optional) — Telegram chat or user ID (numeric). If omitted, reads `TELEGRAM_CHAT_ID` from secrets.
- `$1...` — **message text** in Markdown format.

Example: `/send-tg-msg 123456789 Hello, this is a test message!`

## Interactive Setup

This skill is designed to work silently when secrets are already configured. **Only** use `AskUserQuestion` when required data is missing — never prompt if everything is available.

**If `TELEGRAM_BOT_TOKEN` is missing in secrets**, ask:

```
I need a Telegram Bot Token to send messages.
How would you like to proceed?
Options:
1. I'll provide the token now (get one from @BotFather in Telegram)
2. Run the setup skill to configure all secrets at once
3. Cancel
```

**If `chat_id` is not provided as argument AND `TELEGRAM_CHAT_ID` is missing in secrets**, ask:

```
No chat ID specified. Where should I send the message?
Options:
1. Enter a chat ID manually
2. Save a default chat ID for future use
3. Cancel
```

**If both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (or argument `chat_id`) are available** — skip all questions and send immediately.

## Secrets

This skill requires a Telegram bot token stored in `~/.claude/secrets.json`:

```json
{
  "TELEGRAM_BOT_TOKEN": "your-bot-token-here",
  "TELEGRAM_CHAT_ID": "your-default-chat-id"
}
```

### How to load secrets

Before sending, read the secrets file via bash:

```bash
SECRETS_FILE="$HOME/.claude/secrets.json"

if [ ! -f "$SECRETS_FILE" ]; then
  echo "❌ Secrets file not found: $SECRETS_FILE"
  echo "Run the setup skill or create it manually."
  exit 1
fi

TELEGRAM_BOT_TOKEN=$(python3 -c "import json; print(json.load(open('$SECRETS_FILE'))['TELEGRAM_BOT_TOKEN'])")
TELEGRAM_CHAT_ID=$(python3 -c "import json; print(json.load(open('$SECRETS_FILE')).get('TELEGRAM_CHAT_ID', ''))")
```

If the secrets file doesn't exist or is missing `TELEGRAM_BOT_TOKEN`, use the interactive setup above.

Then save it:
```bash
mkdir -p ~/.claude
python3 -c "
import json, os
path = os.path.expanduser('~/.claude/secrets.json')
data = json.load(open(path)) if os.path.exists(path) else {}
data['TELEGRAM_BOT_TOKEN'] = 'TOKEN_FROM_USER'
data['TELEGRAM_CHAT_ID'] = 'CHAT_ID_FROM_USER'
json.dump(data, open(path, 'w'), indent=2)
print('✅ Saved to', path)
"
```

## How to send

```bash
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
