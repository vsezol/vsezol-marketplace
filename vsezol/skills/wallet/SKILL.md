---
name: wallet
description: >
  Interact with personal finances via Wallet (BudgetBakers) MCP. Query transactions, accounts,
  budgets, goals, categories, and spending analytics. All operations are read-only.
  Use this skill when the user asks to: check my balance, show expenses, spending analysis,
  how much did I spend, budget status, savings goals, transactions, "my finances",
  "what's my balance", show accounts, recurring payments, monthly spending.
argument-hint: "[query about finances]"
---

# Wallet — Personal Finance via MCP

Query personal financial data from BudgetBakers Wallet via MCP. **All operations are read-only** — no transactions, accounts, or settings can be modified.

## Prerequisites

Wallet MCP must be connected **in the current environment**. The MCP may be installed in Claude Code CLI but not in Claude Desktop, or vice versa.

## Available MCP tools

All tools are prefixed with `mcp__wallet__`.

### Core financial data

| Tool | Description |
|------|-------------|
| `get_records` | Retrieve transactions with filters for date range, category, account, labels, and amount |
| `get_records_by_id` | Fetch full details of a specific transaction (notes, labels, attachments) |
| `get_accounts` | List all accounts with current balances, currencies, and account types |
| `get_categories` | Get the full category tree including custom categories and subcategories |

### Analytics

| Tool | Description |
|------|-------------|
| `get_records_aggregation` | Aggregate spending by category, time period, or account — ideal for trend analysis |

### Planning

| Tool | Description |
|------|-------------|
| `get_budgets` | View all budgets with spent/remaining amounts, periods, and category assignments |
| `get_goals` | Track savings goals with progress, target amounts, and deadlines |
| `get_standing_orders` | List recurring transactions and upcoming scheduled payments |

### Organization

| Tool | Description |
|------|-------------|
| `get_labels` | Retrieve custom labels used for tagging and organizing transactions |
| `get_record_rules` | View automation rules for automatic transaction categorization |

## Common queries

When the user asks about finances, map their request to the right tool(s):

| User asks | Tools to use |
|-----------|-------------|
| "What's my balance?" / "How much money do I have?" | `get_accounts` |
| "How much did I spend this month?" | `get_records` with date range filter for current month |
| "Show spending by category" | `get_records_aggregation` grouped by category |
| "What are my biggest expenses?" | `get_records` sorted by amount, or `get_records_aggregation` |
| "Budget status" / "Am I over budget?" | `get_budgets` |
| "How are my savings goals going?" | `get_goals` |
| "What recurring payments do I have?" | `get_standing_orders` |
| "Show transactions for groceries" | `get_records` filtered by category |
| "Spending trends over last 3 months" | `get_records_aggregation` by time period |
| "What categories do I use?" | `get_categories` |

## Output guidelines

- Present financial data in a **clear, readable format** — tables for accounts/budgets, lists for transactions
- Always show **currency** with amounts
- For spending analysis, include **totals and percentages**
- When showing transactions, group by date or category for readability
- For budget status, clearly show **spent vs limit** and whether over/under budget
- Keep summaries concise — the user wants quick answers, not raw data dumps
- If the user asks in Russian, respond in Russian

## Safety

- **Read-only**: Wallet MCP cannot modify any data. There is no risk of accidental changes.
- **Privacy**: Financial data is personal. Do not store, cache, or save financial data to files unless the user explicitly asks.
- **No guessing**: If a query returns no data, say so — do not fabricate financial information.

## Error handling

- If Wallet MCP is not connected in the current environment — suggest running `/vsezol:setup wallet` and specify which environment needs it (Claude Code CLI or Claude Desktop)
- If a tool returns an error — inform the user and suggest checking their Wallet token in Settings → Integrations
- If no data matches filters — say "no transactions found for this period/category" rather than failing silently
