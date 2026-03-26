---
name: send-tg-msg
description: >
  Отправляет сообщение в Telegram через Bot API. Аргументы: chat_id и текст сообщения в формате Markdown.
  Используй этот скилл когда нужно: отправить сообщение в Telegram, послать уведомление в ТГ,
  "отправь в телегу", "напиши в телеграм", notify telegram, send telegram message.
---

# Send Telegram Message

Отправляет сообщение в Telegram через Bot API.

## Аргументы

Скилл принимает аргументы в формате: `<chat_id> <текст сообщения>`

- **chat_id** — ID чата или пользователя в Telegram (числовой). Если не передан, используй значение по умолчанию: `REDACTED_CHAT_ID`
- **текст** — содержимое сообщения в формате Markdown

Пример вызова: `REDACTED_CHAT_ID Привет, это тестовое сообщение!`

## Конфигурация

- **Bot Token:** `REDACTED_TELEGRAM_BOT_TOKEN`

## Как отправить

Используй bash + curl:

```bash
TELEGRAM_BOT_TOKEN="REDACTED_TELEGRAM_BOT_TOKEN"
CHAT_ID="<chat_id из аргумента>"
MESSAGE="<текст из аргумента>"

curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "parse_mode=Markdown" \
  --data-urlencode "text=${MESSAGE}"
```

## Ограничения и обработка ошибок

- Максимальная длина сообщения Telegram — **4096 символов**. Если текст длиннее, разбей на несколько сообщений и отправь последовательно.
- Если API возвращает ошибку парсинга Markdown, попробуй отправить с `parse_mode=HTML` или без parse_mode.
- Если API недоступен, сообщи пользователю об ошибке и предложи сохранить текст в файл.
- Всегда проверяй ответ API — поле `"ok": true` означает успех.
