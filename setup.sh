#!/bin/bash
set -e

cd "$(dirname "$0")"

# Clean up any stale git state from sandbox
rm -rf .git

# Init fresh repo
git init -b main
git add README.md marketplace.json daily-standup/SKILL.md send-tg-msg/SKILL.md

git commit -m "feat: init vsezol marketplace with daily-standup and send-tg-msg skills

- daily-standup: collects Jira, GitLab, Slack activity and sends report to Telegram
- send-tg-msg: sends messages to Telegram via Bot API
- marketplace.json: registry of available skills

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# Create GitHub repo and push
gh repo create vsezol-marketplace --public --source=. --remote=origin --push

echo ""
echo "✅ Done! Repo: https://github.com/$(gh api user --jq .login)/vsezol-marketplace"
echo ""
echo "Remove this script:"
echo "  rm setup.sh"
