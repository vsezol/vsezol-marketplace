#!/bin/bash
# ──────────────────────────────────────────────────────────────
# clean-history.sh — Remove exposed secrets from git history
#
# Uses git-filter-repo to replace sensitive tokens with
# a placeholder string in ALL past commits.
#
# Prerequisites:
#   pip install git-filter-repo --break-system-packages
#
# Usage:
#   cd /path/to/vsezol-marketplace
#   bash setup/scripts/clean-history.sh
#
# After running:
#   git push origin main --force
# ──────────────────────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "$0")/../.." rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# ── Check git-filter-repo is installed ──
if ! command -v git-filter-repo &>/dev/null; then
  echo "❌ git-filter-repo not found. Install it first:"
  echo "   pip install git-filter-repo"
  exit 1
fi

# ── Tokens to scrub ──
# Add any exposed tokens here, one per line: OLD_VALUE→REPLACEMENT
REPLACEMENTS_FILE=$(mktemp)
cat > "$REPLACEMENTS_FILE" <<'TOKENS'
REDACTED_TELEGRAM_BOT_TOKEN==>REDACTED_TELEGRAM_BOT_TOKEN
REDACTED_CHAT_ID==>REDACTED_CHAT_ID
TOKENS

echo "🔍 Scrubbing secrets from git history..."
echo "   Repo: $REPO_ROOT"
echo ""

git filter-repo --replace-text "$REPLACEMENTS_FILE" --force

rm -f "$REPLACEMENTS_FILE"

echo ""
echo "✅ History cleaned!"
echo ""
echo "Next steps:"
echo "  1. Re-add the remote:  git remote add origin git@github.com:vsezol/vsezol-marketplace.git"
echo "  2. Force-push:         git push origin main --force"
echo "  3. Revoke the old Telegram bot token via @BotFather (/revoke command)"
echo "  4. Create a new token and save it:  python3 setup/scripts/install.py --secrets"
