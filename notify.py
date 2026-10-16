import requests


def send_alert(webhook_url: str, message: str) -> None:
    if not webhook_url:
        print("[ALFRED ALERT - no webhook configured]\n" + message)
        return
    try:
        requests.post(webhook_url, json={"text": message}, timeout=10)
    except requests.RequestException as e:
        print(f"[ALFRED] Failed to send alert: {e}\n{message}")
