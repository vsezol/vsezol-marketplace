#!/usr/bin/env node

import { readFileSync } from "fs";
import { homedir } from "os";
import { join } from "path";

const API_URL = "https://mcp.wallet.budgetbakers.com/";

function loadToken() {
  const secretsPath = join(homedir(), ".claude", "secrets.json");
  try {
    const secrets = JSON.parse(readFileSync(secretsPath, "utf-8"));
    if (!secrets.WALLET_TOKEN) {
      console.error(
        "Error: WALLET_TOKEN not found in secrets.json\nRun /vsezol:setup secrets to add it."
      );
      process.exit(1);
    }
    return secrets.WALLET_TOKEN;
  } catch {
    console.error(
      "Error: Cannot read ~/.claude/secrets.json\nRun /vsezol:setup secrets to configure."
    );
    process.exit(1);
  }
}

async function rpc(token, method, args = {}) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      method: "tools/call",
      params: { name: method, arguments: args },
      id: 1,
    }),
  });
  const data = await res.json();
  if (data.error) {
    throw new Error(`API error: ${data.error.message}`);
  }
  return data.result?.structuredContent ?? {};
}

function fmt(value, decimals = 2) {
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

async function main() {
  const token = loadToken();

  // Fetch accounts and aggregation in parallel
  const [accountsData, aggData] = await Promise.all([
    rpc(token, "get_accounts", { limit: 2000 }),
    rpc(token, "get_records_aggregation", {
      groupBy: ["accountId"],
      compute: { amount: ["sum"], baseAmount: ["sum"], count: true },
      limit: 2000,
    }),
  ]);

  const accounts = (accountsData.accounts ?? []).filter((a) => !a.archived);
  const aggResults = aggData.results ?? [];

  // Build aggregation lookup: accountId -> [{currency, amountSum}]
  const aggByAccount = new Map();
  for (const row of aggResults) {
    const id = row.accountId;
    if (!aggByAccount.has(id)) aggByAccount.set(id, []);
    aggByAccount.get(id).push({
      currency: row.currency ?? null,
      amountSum: row.amountSum ?? 0,
      baseAmountSum: row.baseAmountSum ?? 0,
    });
  }

  // Infer account currency from its aggregation data or name
  function inferCurrency(account) {
    const id = account.id;
    const init = account.initialBalance;
    if (init?.currencyCode) return init.currencyCode;

    // Check aggregation rows for non-null currency
    const rows = aggByAccount.get(id) ?? [];
    for (const r of rows) {
      if (r.currency) return r.currency;
    }

    // Fallback: guess from account name
    const name = account.name.toUpperCase();
    for (const c of ["GEL", "USD", "EUR", "RUB", "KZT", "TRY", "CNY", "LKR"]) {
      if (name.includes(c)) return c;
    }
    return "???";
  }

  // Compute balances
  const balances = [];
  for (const acc of accounts) {
    const cur = inferCurrency(acc);
    const initVal = acc.initialBalance?.value ?? 0;
    const rows = aggByAccount.get(acc.id) ?? [];

    let total = initVal;
    for (const r of rows) {
      // Add rows matching account currency or with null currency (transfers)
      if (r.currency === cur || r.currency === null) {
        total += r.amountSum;
      }
    }

    balances.push({
      name: acc.name,
      type: acc.accountType,
      currency: cur,
      balance: Math.round(total * 100) / 100,
    });
  }

  // Group by currency
  const byCurrency = new Map();
  for (const b of balances) {
    if (!byCurrency.has(b.currency)) byCurrency.set(b.currency, []);
    byCurrency.get(b.currency).push(b);
  }

  // Sort currencies by total value descending (use baseAmount for rough ordering)
  const currencyOrder = [...byCurrency.keys()].sort((a, b) => {
    const sumA = byCurrency
      .get(a)
      .reduce((s, x) => s + Math.abs(x.balance), 0);
    const sumB = byCurrency
      .get(b)
      .reduce((s, x) => s + Math.abs(x.balance), 0);
    return sumB - sumA;
  });

  // Format output
  const SEPARATOR = "=".repeat(62);
  const THIN_SEP = "-".repeat(54);

  console.log();
  console.log(SEPARATOR);
  console.log("  ACCOUNT BALANCES");
  console.log(SEPARATOR);

  for (const cur of currencyOrder) {
    const accs = byCurrency.get(cur).sort((a, b) => b.balance - a.balance);
    const total = accs.reduce((s, a) => s + a.balance, 0);

    console.log();
    console.log(`  ${cur}`);
    console.log(`  ${THIN_SEP}`);

    for (const a of accs) {
      const tag =
        a.type !== "General" ? ` [${a.type}]` : "";
      const label = (a.name + tag).padEnd(40);
      console.log(`  ${label} ${fmt(a.balance).padStart(12)} ${cur}`);
    }

    console.log(`  ${"".padEnd(40)} ${"-".repeat(12)}`);
    console.log(
      `  ${"TOTAL".padStart(40)} ${fmt(total).padStart(12)} ${cur}`
    );
  }

  console.log();
  console.log(SEPARATOR);
  console.log(
    `  ${accounts.length} active accounts | ${new Date().toISOString().slice(0, 16).replace("T", " ")} UTC`
  );
  console.log(SEPARATOR);
  console.log();
}

main().catch((err) => {
  console.error(`Error: ${err.message}`);
  process.exit(1);
});
