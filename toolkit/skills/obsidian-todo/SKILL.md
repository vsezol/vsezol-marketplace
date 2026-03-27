---
name: obsidian-todo
description: >
  Manage todos in Obsidian vault. Read, add, toggle, and review daily/monthly/yearly todo lists.
  Use this skill when the user asks to: show my todos, add a todo, check off a task, what do I need to do today,
  todo list, mark task done, "what's left for today", show progress, daily tasks, toggle task.
argument-hint: "[action] [date or file]"
---

# Obsidian Todos

Manage todo lists in the user's Obsidian vault. Uses the `obsidian` CLI and follows the `obsidian` skill safety rules.

## Arguments

- `$0` — **action** (optional). One of: `show`, `add`, `toggle`, `progress`. If omitted, defaults to `show` for today.
- `$1` — **date or file** (optional). Date like `today`, `yesterday`, `2026-03-25`, or a file name like `March 2026`, `2026`. Defaults to today's daily file.

Examples:
- `/obsidian-todo` — show today's todos
- `/obsidian-todo show yesterday`
- `/obsidian-todo add "Сделать ревью MR"`
- `/obsidian-todo toggle "Кардио 40 мин+"`
- `/obsidian-todo progress month`

## Vault structure

Todos live in the `todos/` folder of the vault:

| File | Purpose |
|------|---------|
| `todos/27 March 26.md` | Daily todos — named as `{day} {Month} {YY}` |
| `todos/March 2026.md` | Monthly goals — named as `{Month} {YYYY}` |
| `todos/2026.md` | Yearly goals |
| `todos/$$$GRIND$$$.md` | Long-term strategy notes |
| `todos/investments.md` | Investment tracking |
| `todos/strategies/` | Strategy-specific files |

### Daily file naming convention

Files are named `{day} {Month} {YY}.md` — e.g. `27 March 26` for March 27, 2026.

To resolve a date to a file name:
```bash
# For today
DAY=$(date +%-d)
MONTH=$(date +%B)
YY=$(date +%y)
FILE_NAME="$DAY $MONTH $YY"
# Result: "27 March 26"
```

### Todo format

Todos use standard Obsidian checkbox syntax:
- `- [ ]` — unchecked (pending)
- `- [x]` — checked (done)

Sections are separated by headers like `**Main:**`, `**Evening:**`, or bare labels like `TD`, `LT`, `TTP`.

Comments use `//` prefix — these are notes, not tasks.

## Actions

### show — Display todos

Read and display the todo file for the specified date/scope.

```bash
obsidian read file="{file name}"
```

Output the content as-is, preserving formatting. Optionally summarize progress (X of Y done).

### add — Add a new todo

Append a new todo item to the specified file. Always append — never rewrite.

```bash
obsidian append file="{file name}" content="- [ ] {task text}"
```

If the user specifies a section (e.g. "add to TTP" or "add to Evening"), read the file first, then use `obsidian create ... overwrite silent` to insert the task in the right section. This counts as adding content, not removing — no confirmation needed.

### toggle — Toggle a checkbox

Toggle a specific task between `- [ ]` and `- [x]`. **No confirmation needed** — checkboxes are always safe to toggle.

Workflow:
1. Read the file with `obsidian read`
2. Find the task by matching the text
3. Toggle `- [ ]` → `- [x]` or `- [x]` → `- [ ]`
4. Write back with `obsidian create name="{file name}" path="todos/" overwrite silent content="{updated content}"`

If the task text is ambiguous (matches multiple lines), ask the user which one.

### progress — Show progress summary

Read the specified file and summarize:
- Total tasks vs completed
- Pending tasks grouped by section
- Completion percentage

For `progress month` — read the monthly file (e.g. `March 2026`).
For `progress year` — read the yearly file (e.g. `2026`).
For `progress` with no argument — read today's daily file.

Output a clear, readable summary.

## Safety rules

Inherits all safety rules from the `obsidian` skill:
- **Never delete files**
- **Appending new todos — always safe, no confirmation needed**
- **Toggling checkboxes — always safe, no confirmation needed**
- **Removing or replacing existing content — requires user confirmation**
- **Creating new daily files — always safe**

## Error handling

- If today's daily file doesn't exist — offer to create it (optionally copying structure from the previous day's file)
- If `obsidian` CLI is not available — inform the user to enable it in Obsidian settings
- If a task to toggle is not found — show available tasks and ask which one
