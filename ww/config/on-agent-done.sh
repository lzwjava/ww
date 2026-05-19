#!/usr/bin/env bash
# ~/.hermes/agent-hooks/on-agent-done.sh
# macOS notification when Hermes finishes a turn.
# Fired via post_llm_call shell hook — runs after the tool-calling loop completes.

set -euo pipefail

# Read the JSON payload from stdin and extract fields
payload="$(cat -)"

extracted=$(echo "$payload" | python3 -c "
import json, sys
data = json.load(sys.stdin)

# Directory name from cwd
cwd = data.get('cwd', '')
import os
dirname = os.path.basename(cwd) if cwd else 'unknown'

# First 10 chars of user message
extra = data.get('extra', {})
user_msg = extra.get('user_message', '')[:10]

# Conversation history item count
history = extra.get('conversation_history', [])
hist_count = len(history)

print(f'{dirname}|{user_msg}|{hist_count}')
" 2>/dev/null) || extracted="unknown||0"

IFS='|' read -r dirname user_preview hist_count <<< "$extracted"

# Build subtitle
subtitle="msg: ${user_preview}  |  turns: ${hist_count}"

# Send macOS notification (clickable — brings Ghostty to front)
osascript -e "
display notification \"Hermes has completed one turn.\" with title \"Hermes Agent — ${dirname}\" subtitle \"${subtitle}\" sound name \"Glass\"
tell application \"Ghostty\" to activate
" >/dev/null 2>&1 || true

# Silent no-op for the hook system
printf '{}\n'
