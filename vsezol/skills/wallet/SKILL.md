---
name: wallet
description: >
  Interact with personal finances via Wallet (BudgetBakers) API. Query transactions, accounts,
  budgets, goals, categories, and spending analytics. All operations are read-only.
  Use this skill when the user asks to: check my balance, show expenses, spending analysis,
  how much did I spend, budget status, savings goals, transactions, "my finances",
  "what's my balance", show accounts, recurring payments, monthly spending.
argument-hint: "[query about finances]"
---

# Wallet — Personal Finance via Direct API

Query personal financial data from BudgetBakers Wallet via direct HTTP API. **All operations are read-only.**

## How it works

This skill calls the Wallet API directly via `curl` JSON-RPC — no MCP server needed.

### Authentication

Read the JWT token from secrets:

```bash
WALLET_TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.claude/secrets.json'))['WALLET_TOKEN'])")
```

If `WALLET_TOKEN` is missing from secrets, tell the user to run `/vsezol:setup secrets` and add it (get from BudgetBakers Wallet → Settings → Integrations → generate token).

### Making API calls

All calls use JSON-RPC POST to `https://mcp.wallet.budgetbakers.com/`:

```bash
curl -s -X POST "https://mcp.wallet.budgetbakers.com/" \
  -H "Authorization: Bearer $WALLET_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"METHOD_NAME","arguments":{ARGS}},"id":1}'
```

Response structure: `result.structuredContent` contains the data. Parse with `python3 -c "import sys,json; ..."` or `jq`.

## API Methods

### get_accounts

List bank accounts and wallets. Returns: id, name, accountType, currencyCode, archived, initialBalance, recordStats.

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Filter by IDs (comma-separated) |
| name | string | Filter by name (`eq.` or `contains.` prefix) |
| accountType | string | Filter: general/cash/current/credit/savings/bonus/insurance/investment/loan/mortgage/overdraft |
| currencyCode | string | Filter by currency (e.g. `USD`, `EUR`) |
| bankAccountNumber | string | Filter by bank account number (`eq.` or `contains.` prefix) |
| archived | string | Filter by archived status (pass as filter, not boolean) |
| budgetId | string | Filter accounts belonging to a budget |
| createdAt | array | Timestamp range: `["gte.2024-01-01T00:00:00Z"]` |
| updatedAt | array | Timestamp range |
| limit | integer | Max results (default 200) |
| offset | integer | Pagination offset |

### get_records

Retrieve transactions with filters. Returns: id, accountId, amount, baseAmount, recordDate, recordType (expense/income), category, labels, payee, payer, note.

| Parameter | Type | Description |
|-----------|------|-------------|
| accountId | string | Filter by account ID |
| recordDate | array | Date range: `["gte.2024-01-01", "lt.2024-02-01"]` |
| categoryId | string | Filter by category ID |
| labelId | string | Filter by label ID |
| contactId | string | Filter by contact ID |
| amount | array | Amount range: `["gte.100", "lte.500"]` |
| baseAmount | array | Base amount range (in reference currency) |
| createdAt | array | Timestamp range |
| updatedAt | array | Timestamp range |
| note | string | Filter by note (`eq.` or `contains.` prefix, `eq-i.`/`contains-i.` for case-insensitive) |
| payee | string | Filter expenses by payee (`eq.` or `contains.` prefix) |
| payer | string | Filter income by payer (`eq.` or `contains.` prefix) |
| fields | string/array | Select fields: `"amount,recordDate,category.name"` |
| sortBy | string | Sort: `+recordDate`, `-amount`. Comma-separated for multi-sort |
| limit | integer | Max results (default 200, max 400) |
| offset | integer | Pagination offset |

### get_records_by_id

Fetch specific records by ID. Returns full record details.

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | **Required.** Record IDs (comma-separated) |
| limit | integer | Max results |
| offset | integer | Pagination offset |

### get_records_aggregation

Aggregate records with flexible grouping. Best for analytics queries.

| Parameter | Type | Description |
|-----------|------|-------------|
| groupBy | array | **Required.** Fields: `month`, `week`, `day`, `year`, `category.id`, `category.name`, `accountId`, `recordType`, `paymentType`, `recordState`, `currency` |
| compute | object | **Required.** `{"baseAmount": ["sum","avg","min","max","median"], "amount": ["sum",...], "recordDate": ["min","max"], "count": true}` |
| accountId | string | Filter by account ID |
| recordDate | array | Date range filter |
| categoryId | string | Filter by category |
| labelId | string | Filter by label |
| amount | array | Amount range filter |
| baseAmount | array | Base amount range filter |
| note | string | Filter by note |
| payee | string | Filter by payee |
| payer | string | Filter by payer |
| limit | integer | Max results (default 200, max 2000) |
| offset | integer | Pagination offset |

**Key concepts:**
- `baseAmount` = converted to user's reference currency (RUB) — safe to sum across currencies
- `amount` = original transaction currency — auto-adds `currency` to groupBy
- Expenses are **negative**, income is **positive**

### get_categories

Get transaction categories. Returns: id, name, color, iconName, archived, enabled.

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Filter by IDs |
| name | string | Filter by name (`eq.` or `contains.` prefix) |
| budgetId | string | Filter categories in a budget |
| createdAt | array | Timestamp range |
| updatedAt | array | Timestamp range |
| limit | integer | Max results |
| offset | integer | Pagination offset |

### get_budgets

View budget plans. Returns: id, name, amount, currencyCode, type, startDate, endDate, categories, labels, accountIds.

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Filter by IDs |
| name | string | Filter by name (`eq.` or `contains.` prefix) |
| currencyCode | string | Filter by currency |
| labelId | string | Filter by label |
| accountId | string | Filter by account |
| categoryId | string | Filter by category |
| createdAt | array | Timestamp range |
| updatedAt | array | Timestamp range |
| limit | integer | Max results |
| offset | integer | Pagination offset |

### get_goals

Financial savings goals. Returns: id, name, targetAmount, initialAmount, desiredDate, state (active/paused/reached).

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Filter by IDs |
| name | string | Filter by name (`eq.` or `contains.` prefix) |
| note | string | Filter by note |
| createdAt | array | Timestamp range |
| updatedAt | array | Timestamp range |
| limit | integer | Max results |
| offset | integer | Pagination offset |

### get_standing_orders

Recurring/scheduled transactions. Returns: id, name, amount, currencyCode, frequency, nextOccurrence, accountId, categoryId, payee/payer.

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Filter by IDs |
| name | string | Filter by name (`eq.` or `contains.` prefix) |
| currencyCode | string | Filter by currency |
| labelId | string | Filter by label |
| createdAt | array | Timestamp range |
| updatedAt | array | Timestamp range |
| limit | integer | Max results |
| offset | integer | Pagination offset |

### get_labels

Custom labels for tagging transactions. Returns: id, name, color, archived.

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Filter by IDs |
| name | string | Filter by name (`eq.` or `contains.` prefix) |
| recordId | string | Filter labels on a specific record |
| budgetId | string | Filter labels on a budget |
| standingOrderId | string | Filter labels on a standing order |
| recordRuleId | string | Filter labels on a record rule |
| createdAt | array | Timestamp range |
| updatedAt | array | Timestamp range |
| limit | integer | Max results |
| offset | integer | Pagination offset |

### get_record_rules

Automatic categorization rules. Returns: id, name, pattern, categoryId, labelIds, accountId, priority.

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Filter by IDs |
| name | string | Filter by name (`eq.` or `contains.` prefix) |
| labelId | string | Filter by label |
| createdAt | array | Timestamp range |
| updatedAt | array | Timestamp range |
| limit | integer | Max results |
| offset | integer | Pagination offset |

## Common queries

| User asks | How to handle |
|-----------|--------------|
| "What's my balance?" | `get_accounts` (non-archived) + `get_records_aggregation` by accountId to compute balances. **Or use `/vsezol:balance` for precise calculation.** |
| "How much did I spend this month?" | `get_records` with `recordDate: ["gte.YYYY-MM-01", "lt.YYYY-MM+1-01"]` |
| "Spending by category" | `get_records_aggregation` with `groupBy: ["category.name"]`, `compute: {"baseAmount": ["sum"], "count": true}` |
| "Budget status" | `get_budgets` |
| "Savings goals" | `get_goals` |
| "Recurring payments" | `get_standing_orders` |
| "Spending trends" | `get_records_aggregation` with `groupBy: ["month"]` |

## Output guidelines

- Present data in **clear, readable format** — tables for accounts/budgets, lists for transactions
- Always show **currency** with amounts
- For spending analysis, include **totals and percentages**
- Keep summaries concise
- If the user asks in Russian, respond in Russian

## Safety

- **Read-only**: API cannot modify any data
- **Privacy**: Do not store financial data to files unless user explicitly asks
- **No guessing**: If no data returned, say so — do not fabricate
