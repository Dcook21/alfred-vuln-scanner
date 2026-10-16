import json
import os


def load_baseline(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_baseline(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def diff_scans(old: dict, new: dict) -> dict:
    """Compare old vs new scan results. Return only what changed."""
    changes = {"new_ports": [], "changed_services": [], "closed_ports": []}

    old_hosts = old.get("hosts", {})
    new_hosts = new.get("hosts", {})

    for host, new_host_data in new_hosts.items():
        old_host_data = old_hosts.get(host, {"ports": {}})
        old_ports = old_host_data.get("ports", {})
        new_ports = new_host_data.get("ports", {})

        for port, port_data in new_ports.items():
            if port not in old_ports:
                changes["new_ports"].append({"host": host, "port": port, **port_data})
            else:
                old_service = old_ports[port]
                if (old_service.get("product") != port_data.get("product")
                        or old_service.get("version") != port_data.get("version")):
                    changes["changed_services"].append({
                        "host": host,
                        "port": port,
                        "old": old_service,
                        "new": port_data,
                    })

        for port in old_ports:
            if port not in new_ports:
                changes["closed_ports"].append({"host": host, "port": port, **old_ports[port]})

    return changes
