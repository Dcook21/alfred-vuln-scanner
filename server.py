import datetime
import time
import sys

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from baseline import load_baseline
from history import load_alerts
from heartbeat import read_heartbeat
from classify import ask_alfred

if not config.API_TOKEN:
    sys.exit(
        "ALFRED_API_TOKEN is not set. Alfred's API refuses to start without one — "
        "set it to any random string, the same value the dashboard uses, and re-run."
    )

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local file:// pages send Origin: null, so this can't be
    allow_methods=["GET", "POST"],  # narrowed further — the token below is the real gate.
    allow_headers=["*"],
)


def require_token(x_alfred_token: str = Header(default=None)):
    if x_alfred_token != config.API_TOKEN:
        raise HTTPException(status_code=401, detail="Missing or invalid token")


# Simple in-memory rate limit for /api/ask — this endpoint costs real money per
# call, so an open door here means an open door to your Anthropic bill.
_ask_calls = []
ASK_LIMIT = 10
ASK_WINDOW_SECONDS = 60


def check_rate_limit():
    now = time.time()
    while _ask_calls and now - _ask_calls[0] > ASK_WINDOW_SECONDS:
        _ask_calls.pop(0)
    if len(_ask_calls) >= ASK_LIMIT:
        raise HTTPException(status_code=429, detail="Too many questions — wait a moment and try again.")
    _ask_calls.append(now)


def _status_payload() -> dict:
    scan = load_baseline(config.BASELINE_FILE)
    if not scan:
        return {"scanned": False}
    host_data = scan.get("hosts", {}).get(scan.get("target"), {})
    ports = [{"port": port, **info} for port, info in host_data.get("ports", {}).items()]
    return {
        "scanned": True,
        "target": scan.get("target"),
        "timestamp": scan.get("timestamp"),
        "ports": ports,
    }


@app.get("/api/status")
def status(x_alfred_token: str = Header(default=None)):
    require_token(x_alfred_token)
    return _status_payload()


@app.get("/api/alerts")
def alerts(x_alfred_token: str = Header(default=None)):
    require_token(x_alfred_token)
    history = load_alerts(config.ALERTS_FILE)
    return {"alerts": list(reversed(history))}


@app.get("/api/heartbeat")
def heartbeat(x_alfred_token: str = Header(default=None)):
    require_token(x_alfred_token)
    hb = read_heartbeat(config.HEARTBEAT_FILE)
    online = False
    if hb.get("last_seen"):
        last = datetime.datetime.fromisoformat(hb["last_seen"])
        online = (datetime.datetime.now(datetime.timezone.utc) - last).total_seconds() < 90
    return {"last_seen": hb.get("last_seen"), "online": online}


@app.get("/api/capabilities")
def capabilities(x_alfred_token: str = Header(default=None)):
    require_token(x_alfred_token)
    return {
        "read_only": config.READ_ONLY,
        "target": config.TARGET_HOST,
        "scan_ports": config.SCAN_PORTS,
        "scan_interval_hours": config.SCAN_INTERVAL_HOURS,
        "allowed_actions": config.ALLOWED_ACTIONS,
        "forbidden_actions": config.FORBIDDEN_ACTIONS,
    }


class AskRequest(BaseModel):
    question: str


@app.post("/api/ask")
def ask(req: AskRequest, x_alfred_token: str = Header(default=None)):
    require_token(x_alfred_token)
    check_rate_limit()
    status_data = _status_payload()
    alerts_data = list(reversed(load_alerts(config.ALERTS_FILE)))
    answer = ask_alfred(config.ANTHROPIC_API_KEY, req.question, status_data, alerts_data)
    return {"answer": answer}
