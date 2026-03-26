#!/usr/bin/env python3
"""
vsezol marketplace — MCP setup installer.

Reads mcp_template.json, shows available MCP servers,
lets the user pick which ones to install, asks for missing values,
and merges them into Claude Desktop config.

Usage:
    python3 install.py                        # interactive mode
    python3 install.py --list                  # list available MCPs
    python3 install.py --install gitlab context7  # install specific MCPs
"""

import json
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
    print(f"\n💾 Saved: {path}")


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


def is_cloud_connector(server_config: dict) -> bool:
    """Check if this is a cloud connector (has url, no command)."""
    return "url" in server_config and "command" not in server_config


def list_servers(template: dict):
    servers = template.get("mcpServers", {})
    claude_config = load_json(CLAUDE_CONFIG_PATH)
    print("\n📦 Available MCP servers:\n")
    for name, config in servers.items():
        meta = config.get("_meta", {})
        desc = meta.get("description", "—")
        note = meta.get("note", "")
        placeholders = find_placeholders(config)
        placeholder_str = ", ".join(placeholders) if placeholders else "none"
        already = " [installed]" if name in claude_config.get("mcpServers", {}) else ""
        cloud = " [cloud connector]" if is_cloud_connector(config) else ""
        print(f"  • {name}{already}{cloud}")
        print(f"    {desc}")
        if note:
            print(f"    ℹ️  {note}")
        else:
            print(f"    Required data: {placeholder_str}")
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
    print(f"\n🔧 Configuring {server_name}:")
    for ph in placeholders:
        hint = prompts.get(ph, ph)
        while True:
            val = input(f"  {hint}: ").strip()
            if val:
                values[ph] = val
                break
            print("  ⚠️  Value cannot be empty")
    return values


def install_servers(template: dict, server_names: list[str], interactive: bool = True):
    servers = template.get("mcpServers", {})
    claude_config = load_json(CLAUDE_CONFIG_PATH)

    if "mcpServers" not in claude_config:
        claude_config["mcpServers"] = {}

    installed = []
    skipped = []
    cloud_connectors = []

    for name in server_names:
        if name not in servers:
            print(f"  ❌ {name} — not found in template, skipping")
            skipped.append(name)
            continue

        server_config = servers[name]

        # Cloud connectors can't be installed via config — guide user to UI
        if is_cloud_connector(server_config):
            meta = server_config.get("_meta", {})
            note = meta.get("note", "Connect via Claude Settings → Connectors")
            cloud_connectors.append((name, note))
            continue

        if check_already_installed(claude_config, name):
            if interactive:
                answer = input(f"\n  ⚠️  {name} is already installed. Overwrite? [y/N]: ").strip().lower()
                if answer != "y":
                    print(f"  ⏭  {name} — skipped")
                    skipped.append(name)
                    continue
            else:
                print(f"  ⏭  {name} — already installed, skipping")
                skipped.append(name)
                continue

        values = prompt_values(name, server_config) if interactive else {}

        filled = fill_placeholders(server_config, values)
        cleaned = clean_meta(filled)

        # Check for unfilled placeholders
        remaining = find_placeholders(cleaned)
        if remaining:
            print(f"  ⚠️  Unfilled fields remaining: {', '.join(remaining)}")
            if interactive:
                for ph in remaining:
                    val = input(f"  {ph}: ").strip()
                    if val:
                        values[ph] = val
                filled = fill_placeholders(server_config, values)
                cleaned = clean_meta(filled)

        claude_config["mcpServers"][name] = cleaned
        installed.append(name)
        print(f"  ✅ {name} — added")

    if installed:
        save_json(CLAUDE_CONFIG_PATH, claude_config)
        print(f"\n✅ Installed: {', '.join(installed)}")
        print("🔄 Restart Claude for changes to take effect")
    else:
        print("\n📭 Nothing installed")

    if cloud_connectors:
        print(f"\n☁️  Cloud connectors (connect manually):")
        for name, note in cloud_connectors:
            print(f"  • {name} — {note}")

    if skipped:
        print(f"⏭  Skipped: {', '.join(skipped)}")


def interactive_mode(template: dict):
    servers = template.get("mcpServers", {})
    claude_config = load_json(CLAUDE_CONFIG_PATH)

    print("\n🚀 vsezol marketplace — MCP server installer\n")
    print("Choose servers to install (space-separated), or 'all' for everything:\n")

    for i, (name, config) in enumerate(servers.items(), 1):
        meta = config.get("_meta", {})
        desc = meta.get("description", "")
        already = " [installed]" if check_already_installed(claude_config, name) else ""
        cloud = " [cloud]" if is_cloud_connector(config) else ""
        print(f"  {i}. {name} — {desc}{already}{cloud}")

    print()
    choice = input("Numbers or names (e.g. 1 3 or gitlab context7): ").strip()

    if not choice:
        print("Nothing selected.")
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
                print(f"  ⚠️  '{part}' not found, skipping")

    if selected:
        install_servers(template, selected, interactive=True)


def main():
    parser = argparse.ArgumentParser(description="vsezol marketplace — MCP installer")
    parser.add_argument("--list", action="store_true", help="List available MCP servers")
    parser.add_argument("--install", nargs="+", metavar="NAME", help="Install specific MCP servers")
    parser.add_argument("--template", type=str, help="Path to template (default: mcp_template.json)")
    args = parser.parse_args()

    template_path = Path(args.template) if args.template else TEMPLATE_PATH
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
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
