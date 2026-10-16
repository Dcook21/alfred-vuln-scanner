import logging
from apscheduler.schedulers.blocking import BlockingScheduler

import config
from scanner import run_scan
from baseline import load_baseline, save_baseline, diff_scans
from classify import classify_findings
from notify import send_alert
from history import append_alert
from heartbeat import write_heartbeat

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ALFRED] %(message)s")
log = logging.getLogger("alfred")


def run_cycle():
    log.info(f"Starting scan of {config.TARGET_HOST}")
    new_scan = run_scan(config.TARGET_HOST, config.SCAN_PORTS)
    old_scan = load_baseline(config.BASELINE_FILE)

    changes = diff_scans(old_scan, new_scan)
    has_changes = any(changes.values())

    if has_changes:
        log.info(f"Changes detected: {changes}")
        notes = classify_findings(config.ANTHROPIC_API_KEY, changes)
        # recommended_action stays advisory text, not a command Alfred runs itself —
        # the operator copies and runs it manually.
        alert_text = "\n".join(
            f"[{n['severity'].upper()}] Port {n['port']}: {n['note']} -> Suggested: {n['recommended_action']}"
            for n in notes
        ) or str(changes)
        send_alert(config.NOTIFY_WEBHOOK_URL, alert_text)
        append_alert(config.ALERTS_FILE, changes, notes)
    else:
        log.info("No changes since last scan.")

    save_baseline(config.BASELINE_FILE, new_scan)


def beat():
    write_heartbeat(config.HEARTBEAT_FILE)


def checkin():
    """Periodic status ping, independent of whether anything changed —
    so you hear from Alfred even on a quiet day, not just when something's wrong."""
    scan = load_baseline(config.BASELINE_FILE)
    if not scan:
        return
    host_data = scan.get("hosts", {}).get(scan.get("target"), {})
    port_count = len(host_data.get("ports", {}))
    message = (
        f"Alfred check-in: online, target {config.TARGET_HOST}, "
        f"{port_count} open port(s) as of last scan ({scan.get('timestamp')})."
    )
    log.info(message)
    send_alert(config.NOTIFY_WEBHOOK_URL, message)


if __name__ == "__main__":
    beat()
    run_cycle()  # run once immediately on startup

    scheduler = BlockingScheduler()
    scheduler.add_job(run_cycle, "interval", hours=config.SCAN_INTERVAL_HOURS)
    scheduler.add_job(beat, "interval", seconds=config.HEARTBEAT_INTERVAL_SECONDS)
    scheduler.add_job(checkin, "interval", hours=config.CHECKIN_INTERVAL_HOURS)
    log.info(
        f"Alfred scheduled every {config.SCAN_INTERVAL_HOURS}h, "
        f"heartbeat every {config.HEARTBEAT_INTERVAL_SECONDS}s, "
        f"check-in every {config.CHECKIN_INTERVAL_HOURS}h"
    )
    scheduler.start()
