#!/bin/zsh
# Starts Alfred: the scanning agent (background) and the API (foreground).
# Scripts don't auto-load ~/.zshrc (only interactive shells do), so load it explicitly.
source ~/.zshrc

if [ -z "$ALFRED_API_TOKEN" ]; then
  echo "ALFRED_API_TOKEN is still not set after loading ~/.zshrc — check that the line is actually in that file."
  exit 1
fi

cd ~/projects/alfred
source venv/bin/activate

echo "Starting agent..."
python agent.py &
AGENT_PID=$!

echo "Starting API on port 8000..."
uvicorn server:app --port 8000

# If uvicorn exits (Ctrl+C), kill the agent too instead of leaving it orphaned.
kill $AGENT_PID 2>/dev/null
