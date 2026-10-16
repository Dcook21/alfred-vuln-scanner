import json
import os
import datetime


def write_heartbeat(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"last_seen": datetime.datetime.now(datetime.timezone.utc).isoformat()}, f)


def read_heartbeat(path: str) -> dict:
    if not os.path.exists(path):
        return {"last_seen": None}
    with open(path, "r") as f:
        return json.load(f)
