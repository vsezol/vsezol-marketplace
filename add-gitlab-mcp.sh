#!/bin/bash
set -e

CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Create config if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
  mkdir -p "$(dirname "$CONFIG_FILE")"
  echo '{}' > "$CONFIG_FILE"
fi

python3 -c "
import json, sys

config_path = '$CONFIG_FILE'

with open(config_path, 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

if 'gitlab' in config.get('mcpServers', {}):
    print('⚠️  gitlab MCP уже есть в конфиге, обновляю...')

config['mcpServers']['gitlab'] = {
    'command': 'npx',
    'args': ['-y', '@zereight/mcp-gitlab'],
    'env': {
        'GITLAB_PERSONAL_ACCESS_TOKEN': 'AYgUfIUsEQGyqNLU41fqn286MQp1OjFzCA.01.0y1fi2df5',
        'GITLAB_API_URL': 'https://gitlab.thetradingpit.com/api/v4'
    }
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print('✅ GitLab MCP добавлен в ' + config_path)
print('🔄 Перезапусти Claude чтобы изменения вступили в силу')
"
