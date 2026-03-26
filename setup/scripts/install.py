#!/usr/bin/env python3
"""
vsezol marketplace — MCP setup installer.

Reads mcp_template.json, shows available MCP servers,
lets the user pick which ones to install, asks for missing values,
and merges them into Claude Desktop config.

Usage:
    python3 install.py                        # interactive mode
    python3 install.py --list                  # list available MCPs
    python3 install.py --install gitlab github # install specific MCPs
"""

import json
import os
import sys
import re
import argparse
from pathlib import Path

CLAUDE_CONFIG_PATH = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
TEMPLATE_PATH = Path(__file__).parent.parent / "mcp_template.json"


def load_json(path: Path) -> dict:
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {}


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Сохранено: {path}")


def find_placeholders(obj) -> list[str]:
    """Recursively find all {{PLACEHOLDER}} patterns in a dict/list/string."""
    placeholders = []
    if isinstance(obj, str):
        placeholders.extend(re.findall(r"\{\{(\w+)\}\}", obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            placeholders.extend(find_placeholders(v))
    elif isinstance(obj, list):
        for item in obj:
            placeholders.extend(find_placeholders(item))
    return list(dict.fromkeys(placeholders))  # unique, preserve order


def fill_placeholders(obj, values: dict):
    """Recursively replace {{PLACEHOLDER}} with actual values."""
    if isinstance(obj, str):
        for key, val in values.items():
            obj = obj.replace(f"{{{{{key}}}}}", val)
        return obj
    elif isinstance(obj, dict):
        return {k: fill_placeholders(v, values) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fill_placeholders(item, values) for item in obj]
    return obj


def clean_meta(server_config: dict) -> dict:
    """Remove _meta field before writing to Claude config."""
    return {k: v for k, v in server_config.items() if k != "_meta"}


def list_servers(template: dict):
    servers = template.get("mcpServers", {})
    print("\n📦 Доступные MCP-серверы:\n")
    for name, config in servers.items():
        meta = config.get("_meta", {})
        desc = meta.get("description", "—")
        placeholders = find_placeholders(config)
        placeholder_str = ", ".join(placeholders) if placeholders else "нет"
        print(f"  • {name}")
        print(f"    {desc}")
        print(f"    Нужные данные: {placeholder_str}")
        print()


def check_already_installed(claude_config: dict, server_name: str) -> bool:
    return server_name in claude_config.get("mcpServers", {})


def prompt_values(server_name: str, server_config: dict) -> dict:
    """Ask user for placeholder values interactively."""
    meta = server_config.get("_meta", {})
    prompts = meta.get("prompts", {})
    placeholders = find_placeholders(server_config)

    if not placeholders:
        return {}

    values = {}
    print(f"\n🔧 Настройка {server_name}:")
    for ph in placeholders:
        hint = prompts.get(ph, ph)
        while True:
            val = input(f"  {hint}: ").strip()
            if val:
                values[ph] = val
                break
            print("  ⚠️  Значение не может быть пустым")
    return values


def install_servers(template: dict, server_names: list[str], interactive: bool = True):
    servers = template.get("mcpServers", {})
    claude_config = load_json(CLAUDE_CONFIG_PATH)

    if "mcpServers" not in claude_config:
        claude_config["mcpServers"] = {}

    installed = []
    skipped = []

    for name in server_names:
        if name not in servers:
            print(f"  ❌ {name} — не найден в шаблоне, пропускаю")
            skipped.append(name)
            continue

        if check_already_installed(claude_config, name):
            if interactive:
                answer = input(f"\n  ⚠️  {name} уже установлен. Перезаписать? [y/N]: ").strip().lower()
                if answer != "y":
                    print(f"  ⏭  {name} — пропущен")
                    skipped.append(name)
                    continue
            else:
                print(f"  ⏭  {name} — уже установлен, пропускаю")
                skipped.append(name)
                continue

        server_config = servers[name]
        values = prompt_values(name, server_config) if interactive else {}

        filled = fill_placeholders(server_config, values)
        cleaned = clean_meta(filled)

        # Check for unfilled placeholders
        remaining = find_placeholders(cleaned)
        if remaining:
            print(f"  ⚠️  Остались незаполненные поля: {', '.join(remaining)}")
            if interactive:
                for ph in remaining:
                    val = input(f"  {ph}: ").strip()
                    if val:
                        values[ph] = val
                filled = fill_placeholders(server_config, values)
                cleaned = clean_meta(filled)

        claude_config["mcpServers"][name] = cleaned
        installed.append(name)
        print(f"  ✅ {name} — добавлен")

    if installed:
        save_json(CLAUDE_CONFIG_PATH, claude_config)
        print(f"\n✅ Установлено: {', '.join(installed)}")
        print("🔄 Перезапусти Claude чтобы изменения вступили в силу")
    else:
        print("\n📭 Ничего не установлено")

    if skipped:
        print(f"⏭  Пропущено: {', '.join(skipped)}")


def interactive_mode(template: dict):
    servers = template.get("mcpServers", {})
    claude_config = load_json(CLAUDE_CONFIG_PATH)

    print("\n🚀 vsezol marketplace — установка MCP-серверов\n")
    print("Выбери серверы для установки (через пробел), или 'all' для всех:\n")

    for i, (name, config) in enumerate(servers.items(), 1):
        meta = config.get("_meta", {})
        desc = meta.get("description", "")
        already = " [установлен]" if check_already_installed(claude_config, name) else ""
        print(f"  {i}. {name} — {desc}{already}")

    print()
    choice = input("Номера или имена (например: 1 3 или gitlab github): ").strip()

    if not choice:
        print("Ничего не выбрано.")
        return

    names = list(servers.keys())

    if choice.lower() == "all":
        selected = names
    else:
        selected = []
        for part in choice.split():
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(names):
                    selected.append(names[idx])
            elif part in servers:
                selected.append(part)
            else:
                print(f"  ⚠️  '{part}' не найден, пропускаю")

    if selected:
        install_servers(template, selected, interactive=True)


def main():
    parser = argparse.ArgumentParser(description="vsezol marketplace — MCP installer")
    parser.add_argument("--list", action="store_true", help="Показать доступные MCP-серверы")
    parser.add_argument("--install", nargs="+", metavar="NAME", help="Установить конкретные MCP-серверы")
    parser.add_argument("--template", type=str, help="Путь к шаблону (по умолчанию: mcp_template.json)")
    args = parser.parse_args()

    template_path = Path(args.template) if args.template else TEMPLATE_PATH
    if not template_path.exists():
        print(f"❌ Шаблон не найден: {template_path}")
        sys.exit(1)

    template = load_json(template_path)

    if args.list:
        list_servers(template)
    elif args.install:
        install_servers(template, args.install, interactive=True)
    else:
        interactive_mode(template)


if __name__ == "__main__":
    main()
