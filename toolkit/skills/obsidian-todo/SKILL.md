---
name: obsidian-todo
description: >
  Manage todos in Obsidian vault. Read, add, toggle, edit, and review daily/monthly/yearly todo lists.
  Use this skill when the user asks to: show my todos, add a todo, check off a task, what do I need to do today,
  todo list, mark task done, "what's left for today", show progress, daily tasks, toggle task,
  summary, create today's todo, edit todo, what did I do today.
argument-hint: "[action] [date or scope]"
---

# Obsidian Todos

Manage todo lists in the user's Obsidian vault. Uses the `obsidian` CLI and follows the `obsidian` skill safety rules.

## Arguments

- `$0` — **action** (optional). One of: `show`, `add`, `toggle`, `edit`, `summary`, `progress`, `create`. If omitted, defaults to `show` for today.
- `$1` — **date or scope** (optional). Date like `today`, `yesterday`, `2026-03-25`, or scope like `month`, `year`. Defaults to today.

Examples:
- `/obsidian-todo` — show today's todos
- `/obsidian-todo show yesterday`
- `/obsidian-todo add "Сделать ревью MR" TTP`
- `/obsidian-todo toggle "Кардио 40 мин+"`
- `/obsidian-todo summary` — human-readable summary of today
- `/obsidian-todo progress month`
- `/obsidian-todo create` — create today's daily todo from template

## Vault structure

### Hierarchy: Year → Month → Day

The user maintains a **three-level todo hierarchy** in `todos/`:

| Level | File example | Naming pattern | Content |
|-------|-------------|----------------|---------|
| **Year** | `todos/2026.md` | `{YYYY}.md` | Yearly goals grouped by category: Finances, Work, Development, Health, Hobbies, etc. |
| **Month** | `todos/March 2026.md` | `{Month} {YYYY}.md` | Monthly goals and targets, more specific than yearly |
| **Day** | `todos/27 March 26.md` | `{day} {Month} {YY}.md` | Daily tasks with checkboxes |

Additional files:
- `todos/$$$GRIND$$$.md` — long-term strategy with phases and deadlines
- `todos/investments.md` — investment tracking and deposit records
- `todos/strategies/` — canvas and strategy files
- `todos/old/` — archived daily files from previous months

### Daily file format

Daily files follow a consistent structure with **sections**:

```markdown
**Main:**
- [ ] Контроль питания
- [ ] Кардио 40 мин+
- [ ] English
- [ ] Ловушка счастья! > 10 мин

**Evening:**
- [ ] Прополоскать горло > 1 мин!
- [ ] Помыть лицо пеной
- [ ] Выпить таблетки

Тренировка:
- [ ] Подтягивания -> Брусья -> Приседания
- [ ] Лодочка 2 мин
- [ ] Пресс 2 мин
- [ ] Шея 3 мин

TTP
- [ ] Work task description

TD
- [ ] Work task description

LT
- [ ] Work task description
```

**Sections explained:**
- **Main** — core daily habits and personal tasks
- **Evening** — evening routine (skincare, meds)
- **Тренировка** — workout plan (pullups, planks, abs, neck)
- **TTP**, **TD**, **LT** — work tasks for different companies/projects
- Lines starting with `//` — comments/notes, not tasks
- Lines starting with `TODO:` + numbered items — longer-term reminders, not daily checkboxes

### Template

New daily files are created from the template at `__templates/daily.md`. This template contains the standard sections with placeholder tasks. When creating a new daily file, always use this template.

### Todo syntax

- `- [ ]` — pending task
- `- [x]` — completed task
- `**Section:**` or `Section:` — section headers
- `// comment` — notes/comments (not tasks)
- `TODO:` + numbered list — reminders carried between days

### Date resolution

To convert a date to a daily file name:
```bash
# For a specific date (macOS)
DAY=$(date -j -f "%Y-%m-%d" "2026-03-27" +%-d)
MONTH=$(date -j -f "%Y-%m-%d" "2026-03-27" +%B)
YY=$(date -j -f "%Y-%m-%d" "2026-03-27" +%y)
FILE_NAME="$DAY $MONTH $YY"
# Result: "27 March 26"

# For today
FILE_NAME="$(date +%-d) $(date +%B) $(date +%y)"

# For yesterday
FILE_NAME="$(date -v-1d +%-d) $(date -v-1d +%B) $(date -v-1d +%y)"
```

For monthly: `$(date +%B) $(date +%Y)` → `March 2026`
For yearly: `$(date +%Y)` → `2026`

## Actions

### show — Display todos

Read and display the todo file. Default: today's daily file.

```bash
obsidian read file="{file name}"
```

Scope shortcuts:
- `show` or `show today` → today's daily file
- `show yesterday` → yesterday's daily file
- `show month` → current monthly file
- `show year` → current yearly file
- `show 2026-03-25` → specific date's daily file

Output the content as-is, preserving formatting.

### create — Create a new daily todo

Create today's daily file from the `__templates/daily.md` template.

Workflow:
1. Read the template: `obsidian read file="daily"` (from `__templates/`)
2. Check if today's file already exists: `obsidian read file="{today file name}"`
3. If it exists — warn the user and do NOT overwrite
4. If it doesn't exist — create it:
   ```bash
   obsidian create name="{day} {Month} {YY}" path="todos/" content="{template content}" silent
   ```

### add — Add a new todo

Add a new task to a daily file. The user may specify a section.

**Without section** — append to the end:
```bash
obsidian append file="{file name}" content="- [ ] {task text}"
```

**With section** (e.g. "add to TTP", "add to Evening") — insert the task under that section:
1. Read the file
2. Find the section header
3. Insert `- [ ] {task text}` after the last task in that section
4. Write back: `obsidian create name="{file name}" path="todos/" overwrite silent content="{updated}"`

This counts as **adding** content — no confirmation needed.

### toggle — Toggle a checkbox

Toggle a task between `- [ ]` and `- [x]`. **No confirmation needed.**

The user can specify tasks by:
- Exact text: `toggle "Кардио 40 мин+"`
- Partial match: `toggle "кардио"` (case-insensitive search)
- Multiple tasks: `toggle "кардио" "english"` (toggle several at once)

Workflow:
1. Read the file
2. Find matching task(s)
3. If exactly one match — toggle it
4. If multiple matches — show them and ask which one(s)
5. If no match — show all pending tasks and ask
6. Write back with `obsidian create name="{file name}" path="todos/" overwrite silent content="{updated}"`

### edit — Edit a task or section

Modify existing task text or section content. Follows `obsidian` skill safety rules:

- **Adding new content** — safe, no confirmation
- **Changing task text** — requires confirmation (show old → new)
- **Removing tasks** — requires confirmation
- **Toggling checkboxes** — safe, no confirmation (use `toggle` action)

### summary — Human-readable summary

Generate a natural-language summary of the day. Default: today.

Workflow:
1. Read the daily file
2. Count tasks per section: done vs total
3. Output a **readable summary** like:

```
Сегодня (27 March):

Main: 2 из 4 сделано. Осталось: Контроль питания, Ловушка счастья.
Evening: ничего не сделано (3 задачи).
Тренировка: всё сделано!
TTP: 1 из 2. Осталось: Таска по show account id.
TD: сделано! Допинал задачу до ревью.
LT: 1 из 2. Осталось: Влить интеграцию с контрактами.

Итого: 8 из 15 (53%). Осталось 7 задач.
```

The summary should be **plain language**, easy to scan. List remaining tasks by name so the user knows exactly what's left.

### progress — Progress across scopes

Show completion stats. Can operate on day, month, or year level.

- `progress` or `progress today` — today's daily file stats
- `progress month` — read monthly file, count done/total
- `progress year` — read yearly file, count done/total

Output format:
```
March 2026 — прогресс:

Finances: 3 из 6 (50%)
  Осталось:
  - To have expenses <= $2800
  - Разобраться че делать с ИП
  - To handle with 3 jobs during all month

Здоровье: 4 из 8 (50%)
  Осталось:
  - Подтягивания 14/16
  - Приседания 40
  ...

Общий прогресс: 15 из 28 (54%)
```

## Safety rules

Inherits all safety rules from the `obsidian` skill:
- **Never delete files**
- **Appending new todos — always safe, no confirmation needed**
- **Toggling checkboxes — always safe, no confirmation needed**
- **Removing or replacing existing text — requires user confirmation**
- **Creating new daily files from template — always safe**

## Error handling

- If today's daily file doesn't exist — offer to create it from `__templates/daily.md`
- If `obsidian` CLI is not available — inform the user to enable it in Obsidian Settings > General > Advanced, and add `~/bin` to PATH
- If a task to toggle is not found — show available tasks and ask which one
- If a section is not found — show available sections and ask
