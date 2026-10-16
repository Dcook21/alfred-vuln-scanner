# Alfred — Autonomous Vulnerability Scanning Agent

Scans a system you own on a schedule, remembers what it saw last time, and
only alerts you on what's *new* — a new open port, a changed service
version, a port that closed.

## Before you run this

Check your VPS provider's acceptable-use policy on port scanning, even
against your own instance. Some providers (AWS, certain DigitalOcean plans)
flag or require pre-authorization for scanning traffic, even self-targeted.
Confirm this first — it's the one thing that can silently kill a live
deployment.

## Setup

1. Set environment variables (or put them in a `.env` and load with
   `python-dotenv` if you prefer):

   ```
   ALFRED_TARGET_HOST=<your VPS public IP>
   ALFRED_SCAN_PORTS=1-1000
   ALFRED_SCAN_INTERVAL_HOURS=6
   ANTHROPIC_API_KEY=<your key>
   ALFRED_WEBHOOK_URL=<optional Slack incoming webhook>
   ```

2. Local test run (no Docker):

   ```
   pip install -r requirements.txt
   # nmap binary must be installed locally: brew install nmap (Mac)
   python agent.py
   ```

   First run has nothing to diff against, so it'll just save a baseline —
   run it a second time after manually opening/closing a test port to
   confirm the diff logic actually flags it.

3. Build and run in Docker:

   ```
   docker build -t alfred .
   docker run -d \
     -e ALFRED_TARGET_HOST=<your VPS IP> \
     -e ANTHROPIC_API_KEY=<your key> \
     -e ALFRED_WEBHOOK_URL=<optional> \
     -v alfred-data:/data \
     alfred
   ```

4. Deploy to Render / Fly.io / Railway: push this as a container service,
   set the same env vars in their dashboard, attach a persistent volume for
   `/data` so the baseline survives restarts.

## New in this version

- **On/off status**: `agent.py` writes a heartbeat every 30s independent of
  the scan cycle. The dashboard shows Alfred as offline if it hasn't heard a
  heartbeat in 90 seconds — so it reflects the process being alive, not just
  the last scan time.
- **Declared parameters**: `config.py` has an explicit `READ_ONLY`,
  `ALLOWED_ACTIONS`, and `FORBIDDEN_ACTIONS` — shown on the dashboard as-is.
  Alfred does not scan anything outside `TARGET_HOST`, does not exploit
  findings, and does not auto-remediate. This is a stated boundary, not
  enforced sandboxing — don't rely on it as a security control by itself.
- **Structured notes**: findings are classified per-port (severity, status,
  note, recommended action) instead of one paragraph, so each shows up as
  its own entry on the dashboard.
- **Ask Alfred**: a chat box on the dashboard that answers questions about
  current findings, using the Claude API with your scan/alert data as
  context. This is a nice-to-have — if you're short on time before Sunday,
  everything else works without it.

## Running the dashboard

Three things run at once now, each in its own terminal tab (all need the
venv active and env vars set):

**Tab 1 — the agent** (scans + heartbeat):
```
python agent.py
```

**Tab 2 — the API**:
```
uvicorn server:app --port 8000
```

**Then** open `index.html` in a browser. It polls every 15 seconds.

## Security hardening

- **API requires a token.** Generate any random string (e.g. `openssl rand -hex 16`)
  and set it as `ALFRED_API_TOKEN` in every terminal running `agent.py` or
  `server.py`. `server.py` refuses to start without it. The dashboard will
  prompt you for the same value once and remember it in your browser.
- **Bind the API to localhost only** when you deploy — don't expose port
  8000 to the open internet unless you've put real auth and TLS in front of
  it. On the VPS, that means firewalling 8000 from external access, or only
  letting the dashboard reach it via SSH tunnel/localhost.
- **Ask endpoint is rate-limited** (10 requests/minute) since it calls the
  paid Claude API — this stops a bug or a stray script from running up your
  bill.
- **Alfred does not modify the target.** `recommended_action` on each
  finding is advisory text — a suggested command or fix — not something
  Alfred executes. You review and run it yourself. This is deliberate, not
  a missing feature.

## Check-ins

Separate from alerts, Alfred now sends a periodic status message even when
nothing changed — `ALFRED_CHECKIN_INTERVAL_HOURS` (default 24). This goes
through the same webhook as alerts.

## What counts as "working" before Sunday

- Run 1: saves baseline, no alert (nothing to compare yet)
- Manually change something on the VPS (open a test port with `nc -l`,
  or stop/start a service)
- Run 2: should detect and alert on exactly that change

If it doesn't flag a deliberate change, the diff logic is broken — fix that
before worrying about anything else (Docker, scheduling, deployment).

## Known gaps (v2, not this weekend)

- No auth/dashboard — this is a scanning agent, not a UI. The minimalistic
  website is separate work, layered on top once this loop is proven.
- No CVE database lookup — severity ranking currently comes from the LLM's
  judgment on service/version strings, not a CVE feed match. Good enough to
  demo; not a substitute for a real scanner like Nessus/OpenVAS long-term.
