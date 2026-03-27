---
name: balance
description: >
  Show a summary of all account balances across currencies. Runs a Node.js script that fetches
  data from Wallet API and computes precise balances (initialBalance + sum of transactions).
  Use this skill when the user asks to: check balance, how much money, show balances,
  account summary, net worth, total across accounts, "how much do I have".
argument-hint: "[optional: currency filter e.g. USD, or 'all']"
---

# Balance — Account Balance Summary

Computes and displays precise account balances by running a Node.js script. Uses math (not LLM) for accuracy.

## How to use

Run the balance script:

```bash
node /Users/vsezol/projects/pet/vsezol-marketplace/vsezol/skills/balance/balance.mjs
```

The script:
1. Reads `WALLET_TOKEN` from `~/.claude/secrets.json`
2. Fetches all accounts from Wallet API
3. Fetches aggregated transaction sums per account
4. Computes `balance = initialBalance + sum(transactions)` for each active account
5. Outputs a formatted summary grouped by currency

If `WALLET_TOKEN` is missing, the script prints an error suggesting `/vsezol:setup secrets`.

## Output

The script outputs a formatted text table to stdout. Present it directly to the user — no further processing needed.

## Error handling

- If the script fails with a token error — suggest running `/vsezol:setup secrets` to add `WALLET_TOKEN`
- If no accounts found — relay the message as-is
