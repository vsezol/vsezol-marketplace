---
name: obsidian
description: >
  Read, create, and edit Obsidian vault notes via the built-in Obsidian CLI.
  Use this skill when the user asks to: read a note, create a note, edit a note, append to a note,
  search notes, "open obsidian", "write in obsidian", "add to my notes", find notes, update a note.
argument-hint: "[action] [file-name]"
---

# Obsidian Notes

Interact with notes in the user's Obsidian vault via the built-in `obsidian` CLI. Requires Obsidian to be running with CLI enabled in Settings > General > Advanced.

## Arguments

- `$0` — **action** (optional). One of: `read`, `create`, `append`, `edit`, `search`. If omitted, infer from context.
- `$1` — **file name or search query** (optional). Wikilink-style name (no path or extension needed).

Examples:
- `/obsidian read "March 2026"`
- `/obsidian create "New Note"`
- `/obsidian search "investments"`
- `/obsidian append "27 March 26" "- [ ] New task"`

## Vault info

- Vault name: `vsezol`
- Vault path: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/vsezol/`

## Safety rules

These rules are **non-negotiable** and must be followed at all times:

1. **Never delete files.** The `obsidian` CLI has no delete command, and you must never remove files via bash either.
2. **Appending new content is always safe** — do it freely without asking.
3. **Deleting or replacing existing content requires explicit user confirmation** via `AskUserQuestion` before proceeding. Always show what will be removed.
4. **Toggling checkboxes (`- [ ]` ↔ `- [x]`) is always safe** — do it freely without asking.
5. **Creating new files is always safe** — do it freely.
6. **Never overwrite a file** unless the user explicitly confirms. Use `obsidian create ... silent overwrite` only with confirmation.

## CLI reference

### Read a note
```bash
obsidian read file="Note Name"
obsidian read path="folder/note.md"
```

### Create a note
```bash
obsidian create name="New Note" content="# Title\n\nBody text" silent
obsidian create name="New Note" path="folder/" content="Hello" silent
```
Use `silent` to prevent the note from opening in Obsidian. Use `overwrite` only with explicit user confirmation.

### Append to a note
```bash
obsidian append file="Note Name" content="New line of text"
```
For multiline content use `\n` for newline and `\t` for tab.

### Search notes
```bash
obsidian search query="search term" limit=10
```

### Daily notes
```bash
obsidian daily:read
obsidian daily:append content="- [ ] New task"
```

### Properties
```bash
obsidian property:set name="status" value="done" file="Note Name"
```

### Tasks
```bash
obsidian tasks daily todo
obsidian tasks file="Note Name" todo
```

### Tags and backlinks
```bash
obsidian tags sort=count counts
obsidian backlinks file="Note Name"
```

### Vault targeting
All commands target the most recently focused vault by default. To target a specific vault:
```bash
obsidian vault="vsezol" read file="Note Name"
```

## Editing content

When the user asks to edit existing text (not append), follow this workflow:

1. **Read** the current note content first with `obsidian read`.
2. **Show the user** what you plan to change — the old text and the new text.
3. **If adding new content** (append) — proceed without asking.
4. **If toggling checkboxes** — proceed without asking.
5. **If removing or replacing existing content** — ask the user for confirmation first using `AskUserQuestion`:
   ```
   I'm about to change this in "Note Name":

   Remove: <old text>
   Replace with: <new text>

   Proceed?
   Options:
   1. Yes, apply the change
   2. No, cancel
   ```
6. Apply the change. Since the CLI has no inline-edit command, use `obsidian read` to get content, modify it, and `obsidian create ... overwrite silent` to save.

## Error handling

- If `obsidian` command is not found — inform the user they need to enable CLI in Obsidian Settings > General > Advanced
- If a note is not found — suggest searching for it or creating a new one
- Never fail silently — always inform about problems
