#!/usr/bin/env python3
"""
vsezol marketplace — MCP setup installer.

Reads mcp_template.json, shows available MCP servers,
lets the user pick which ones to install, asks for missing values,
and merges them into both Claude Desktop and Claude Code configs.

Usage:
    python3 install.py                        # interactive mode
    python3 install.py --list                  # list available MCPs
    python3 install.py --install gitlab context7  # install specific MCPs
"""

import json
import sys
import re
import shutil
import subprocess
import argparse
from pathlib import Path

CLAUDE_DESKTOP_CONFIG_PATH = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
TEMPLATE_PATH = Path(__file__).parent.parent / "mcp_template.json"
SECRETS_PATH = Path.home() / ".vsezol-marketplace" / "secrets.json"

SECRETS_SCHEMA = {
    "TELEGRAM_BOT_TOKEN": "Telegram Bot Token (get from @BotFather in Telegram)",
    "TELEGRAM_CHAT_ID": "Default Telegram chat/user ID for notifications",
}


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


def get_claude_code_servers() -> set[str]:
    """Get list of MCP servers installed in Claude Code."""
    claude_cli = shutil.which("claude")
    if not claude_cli:
        return set()
    try:
        result = subprocess.run(
            [claude_cli, "mcp", "list"],
            capture_output=True, text=True, timeout=30,
        )
        servers = set()
        for line in result.stdout.splitlines():
            # Format: "name: command - status"
            if ":" in line:
                name = line.split(":")[0].strip()
                if name and not name.startswith(("claude.ai", "plugin:")):
                    servers.add(name)
        return servers
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return set()


def list_servers(template: dict):
    servers = template.get("mcpServers", {})
    desktop_config = load_json(CLAUDE_DESKTOP_CONFIG_PATH)
    desktop_installed = set(desktop_config.get("mcpServers", {}).keys())
    code_installed = get_claude_code_servers()

    print("\n📦 Available MCP servers:\n")
    for name, config in servers.items():
        meta = config.get("_meta", {})
        desc = meta.get("description", "—")
        note = meta.get("note", "")
        placeholders = find_placeholders(config)
        placeholder_str = ", ".join(placeholders) if placeholders else "none"
        cloud = " [cloud connector]" if is_cloud_connector(config) else ""

        # Show install status for both targets
        in_desktop = name in desktop_installed
        in_code = name in code_installed
        if in_desktop and in_code:
            status = " [Desktop ✓ | Code ✓]"
        elif in_desktop:
            status = " [Desktop ✓ | Code ✗]"
        elif in_code:
            status = " [Desktop ✗ | Code ✓]"
        else:
            status = ""

        print(f"  • {name}{status}{cloud}")
        print(f"    {desc}")
        if note:
            print(f"    ℹ️  {note}")
        else:
            print(f"    Required data: {placeholder_str}")
        print()


def check_already_installed(desktop_config: dict, code_servers: set, server_name: str) -> tuple[bool, bool]:
    """Returns (installed_in_desktop, installed_in_code)."""
    return (
        server_name in desktop_config.get("mcpServers", {}),
        server_name in code_servers,
    )


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


def add_to_claude_code(name: str, server_config: dict) -> bool:
    """Add an MCP server to Claude Code via `claude mcp add --scope user`."""
    claude_cli = shutil.which("claude")
    if not claude_cli:
        print(f"  ⚠️  Claude CLI not found, skipping Claude Code install for {name}")
        return False

    cmd = [claude_cli, "mcp", "add", "--scope", "user"]

    # Collect env vars
    env_vars = server_config.get("env", {})
    for key, val in env_vars.items():
        cmd.extend(["--env", f"{key}={val}"])

    # Separator, then name and command
    cmd.append("--")
    cmd.append(name)
    cmd.append(server_config["command"])
    cmd.extend(server_config.get("args", []))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True
        else:
            print(f"  ⚠️  Claude Code: {result.stderr.strip()}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def remove_from_claude_code(name: str) -> bool:
    """Remove an MCP server from Claude Code before re-adding."""
    claude_cli = shutil.which("claude")
    if not claude_cli:
        return False
    try:
        subprocess.run(
            [claude_cli, "mcp", "remove", "--scope", "user", name],
            capture_output=True, text=True, timeout=15,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def install_servers(template: dict, server_names: list[str], interactive: bool = True):
    servers = template.get("mcpServers", {})
    desktop_config = load_json(CLAUDE_DESKTOP_CONFIG_PATH)
    code_servers = get_claude_code_servers()

    if "mcpServers" not in desktop_config:
        desktop_config["mcpServers"] = {}

    installed_desktop = []
    installed_code = []
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

        in_desktop, in_code = check_already_installed(desktop_config, code_servers, name)
        both_installed = in_desktop and in_code

        if both_installed:
            if interactive:
                answer = input(f"\n  ⚠️  {name} is installed in both Desktop & Code. Overwrite? [y/N]: ").strip().lower()
                if answer != "y":
                    print(f"  ⏭  {name} — skipped")
                    skipped.append(name)
                    continue
            else:
                print(f"  ⏭  {name} — already installed in both, skipping")
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

        # Install to Claude Desktop
        if not in_desktop or both_installed:
            desktop_config["mcpServers"][name] = cleaned
            installed_desktop.append(name)

        # Install to Claude Code
        if not in_code or both_installed:
            if in_code:
                remove_from_claude_code(name)
            if add_to_claude_code(name, cleaned):
                installed_code.append(name)

        targets = []
        if name in installed_desktop:
            targets.append("Desktop")
        if name in installed_code:
            targets.append("Code")
        if targets:
            print(f"  ✅ {name} — added to {' + '.join(targets)}")

    if installed_desktop:
        save_json(CLAUDE_DESKTOP_CONFIG_PATH, desktop_config)

    if installed_desktop or installed_code:
        print(f"\n✅ Installed:")
        if installed_desktop:
            print(f"   Claude Desktop: {', '.join(installed_desktop)}")
        if installed_code:
            print(f"   Claude Code:    {', '.join(installed_code)}")
        if installed_desktop:
            print("🔄 Restart Claude Desktop for changes to take effect")
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
    desktop_config = load_json(CLAUDE_DESKTOP_CONFIG_PATH)
    code_servers = get_claude_code_servers()

    print("\n🚀 vsezol marketplace — MCP server installer\n")
    print("Installs to both Claude Desktop and Claude Code.\n")
    print("Choose servers to install (space-separated), or 'all' for everything:\n")

    for i, (name, config) in enumerate(servers.items(), 1):
        meta = config.get("_meta", {})
        desc = meta.get("description", "")
        in_desktop, in_code = check_already_installed(desktop_config, code_servers, name)
        if in_desktop and in_code:
            status = " [Desktop ✓ | Code ✓]"
        elif in_desktop:
            status = " [Desktop ✓ | Code ✗]"
        elif in_code:
            status = " [Desktop ✗ | Code ✓]"
        else:
            status = ""
        cloud = " [cloud]" if is_cloud_connector(config) else ""
        print(f"  {i}. {name} — {desc}{status}{cloud}")

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


def configure_secrets():
    """Interactive secrets configuration."""
    secrets = load_json(SECRETS_PATH)

    print("\n🔐 vsezol marketplace — secrets configuration\n")
    print(f"Secrets file: {SECRETS_PATH}\n")

    updated = False
    for key, hint in SECRETS_SCHEMA.items():
        current = secrets.get(key, "")
        masked = f"{current[:4]}...{current[-4:]}" if len(current) > 8 else ("(empty)" if not current else current)
        print(f"  {key}: {masked}")
        new_val = input(f"    {hint}\n    New value (Enter to keep current): ").strip()
        if new_val:
            secrets[key] = new_val
            updated = True
            print(f"    ✅ Updated")
        print()

    if updated:
        SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
        save_json(SECRETS_PATH, secrets)
        SECRETS_PATH.chmod(0o600)
        print(f"✅ Secrets saved to {SECRETS_PATH}")
    else:
        print("📭 No changes made")


def main():
    parser = argparse.ArgumentParser(description="vsezol marketplace — MCP installer")
    parser.add_argument("--list", action="store_true", help="List available MCP servers")
    parser.add_argument("--install", nargs="+", metavar="NAME", help="Install specific MCP servers")
    parser.add_argument("--secrets", action="store_true", help="Configure secrets (API tokens, etc.)")
    parser.add_argument("--template", type=str, help="Path to template (default: mcp_template.json)")
    args = parser.parse_args()

    if args.secrets:
        configure_secrets()
        return

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
