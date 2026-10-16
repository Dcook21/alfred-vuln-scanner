import json
import os
import datetime


def append_alert(path: str, changes: dict, notes: list) -> None:
    """Append one alert record to the history file, for the dashboard to read."""
    history = load_alerts(path)
    history.append({
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "changes": changes,
        "notes": notes,
    })
    # Keep the file from growing unbounded — last 200 alerts is plenty for a dashboard.
    history = history[-200:]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)


def load_alerts(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)
