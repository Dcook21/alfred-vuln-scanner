import os

# Set this to your VPS's public IP or hostname before running.
TARGET_HOST = os.getenv("ALFRED_TARGET_HOST", "CHANGE_ME_TO_YOUR_VPS_IP")

# Port range to scan. 1-1000 covers most common services; widen if needed.
SCAN_PORTS = os.getenv("ALFRED_SCAN_PORTS", "1-1000")

# How often Alfred re-scans, in hours.
SCAN_INTERVAL_HOURS = int(os.getenv("ALFRED_SCAN_INTERVAL_HOURS", "6"))

# Where Alfred stores the last scan, to diff against next time.
BASELINE_FILE = os.getenv("ALFRED_BASELINE_FILE", "/data/baseline.json")

# Where Alfred logs each alert cycle, for the dashboard's history view.
ALERTS_FILE = os.getenv("ALFRED_ALERTS_FILE", "/data/alerts.json")

# Where Alfred writes a liveness timestamp, so the dashboard can tell on/off.
HEARTBEAT_FILE = os.getenv("ALFRED_HEARTBEAT_FILE", "/data/heartbeat.json")

# How often Alfred writes a heartbeat, in seconds — independent of scan interval.
HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("ALFRED_HEARTBEAT_INTERVAL_SECONDS", "30"))

# Declared scope: what Alfred is authorized to do. This is read by the
# dashboard and shown as-is — it is a boundary statement, not a suggestion.
READ_ONLY = True
ALLOWED_ACTIONS = ["scan target", "classify findings", "send alerts", "log history", "answer questions about findings"]
FORBIDDEN_ACTIONS = ["exploit findings", "modify the target", "auto-remediate", "scan targets outside TARGET_HOST"]

# Claude API key, for severity ranking + summaries of new findings.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Optional Slack-style incoming webhook URL. If unset, alerts just log to console.
NOTIFY_WEBHOOK_URL = os.getenv("ALFRED_WEBHOOK_URL")

# Shared secret the dashboard/API must present. Required — the server refuses
# to start without one, so Alfred is never accidentally left open.
API_TOKEN = os.getenv("ALFRED_API_TOKEN")

# How often Alfred sends a check-in message even if nothing changed, in hours.
CHECKIN_INTERVAL_HOURS = int(os.getenv("ALFRED_CHECKIN_INTERVAL_HOURS", "24"))
