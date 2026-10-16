# Alfred

Alfred is an autonomous vulnerability scanning agent. He scans a host you own on a schedule, remembers what he saw last time, and reports only what changed.

## What it does

- Runs an nmap service and version scan on a configurable port range, every 6 hours by default.
- Compares each scan to the previous one and flags new open ports, changed service versions and closed ports.
- Sends each change to the Claude API, which returns a severity (low, medium, high), a status, a short note and a suggested fix.
- Writes a heartbeat every 30 seconds so the dashboard shows whether he is online.
- Sends a periodic check-in message, and alerts through an optional Slack-style webhook (they print to the terminal if no webhook is set).
- Serves a dashboard with his status, parameters, last scan, open ports, findings, and a chat box for questions about your scan data.

## Design decisions

- **Read-only.** Alfred observes and advises. He does not exploit findings, modify the target or auto-remediate. Suggested fixes are text for a human to review and run.
- **Single target.** He only scans the host set in `ALFRED_TARGET_HOST`. Only scan systems you own or have written permission to test.
- **Change detection, not repeated reports.** Each run is diffed against a stored baseline, so alerts are new findings only.
- **API access control.** Every API request needs a token (`X-Alfred-Token`), the server refuses to start without one, and the chat endpoint is rate-limited to 10 requests per minute.

## Stack

Python, nmap (python-nmap), APScheduler, FastAPI and uvicorn, the Anthropic API, and a plain HTML/CSS/JS dashboard.

## Setup (macOS)

1. Install nmap: `brew install nmap`
2. Create the environment and install dependencies:
```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
```
3. Set these environment variables (for example in `~/.zshrc`):
```
   export ALFRED_TARGET_HOST=127.0.0.1
   export ALFRED_SCAN_PORTS=1-10000
   export ALFRED_BASELINE_FILE=~/projects/alfred/data/baseline.json
   export ALFRED_ALERTS_FILE=~/projects/alfred/data/alerts.json
   export ALFRED_HEARTBEAT_FILE=~/projects/alfred/data/heartbeat.json
   export ALFRED_API_TOKEN=<any random string, e.g. from: openssl rand -hex 16>
   export ANTHROPIC_API_KEY=<your Anthropic API key>
```
4. Start the agent and the API in two terminals (venv active, variables set):
```
   python agent.py
   uvicorn server:app --port 8000
```
   On macOS, `./start_alfred.sh` starts both. It assumes the repo is at `~/projects/alfred`.
5. Open `index.html` in a browser and enter your `ALFRED_API_TOKEN` when asked.

Your API key and token stay in your environment. They are not stored in this repo.

## Project layout

- `agent.py` runs the scan, heartbeat and check-in schedule.
- `scanner.py` wraps nmap and returns structured results.
- `baseline.py` stores scans and diffs them.
- `classify.py` handles Claude-based triage and the chat answers.
- `server.py` is the FastAPI backend the dashboard reads from.
- `index.html` is the dashboard.
- `config.py` holds all settings and the declared allowed and forbidden actions.
- `heartbeat.py` writes and reads the liveness timestamp.
- `history.py` stores alert history for the dashboard.
- `notify.py` sends alerts to a webhook, or prints them if none is set.
- `Dockerfile` builds an image that runs the scanning agent only. It does not include the API or dashboard.

## Status

Runs locally against the host you configure and has been tested against localhost: scanning, change detection, Claude triage, heartbeat and the dashboard. The check-in message, webhook delivery and the Docker image have not been tested end to end. Deployment to an always-on VPS is planned, not done.
