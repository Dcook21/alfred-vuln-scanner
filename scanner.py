import datetime
import nmap


def run_scan(target: str, ports: str = "1-1000") -> dict:
    """Run an nmap service/version scan against target, return structured results."""
    scanner = nmap.PortScanner()
    scanner.scan(target, ports, arguments="-sV -T4")

    results = {
        "target": target,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "hosts": {},
    }

    for host in scanner.all_hosts():
        host_data = {"state": scanner[host].state(), "ports": {}}
        for proto in scanner[host].all_protocols():
            for port in scanner[host][proto]:
                port_info = scanner[host][proto][port]
                host_data["ports"][str(port)] = {
                    "protocol": proto,
                    "state": port_info.get("state"),
                    "service": port_info.get("name"),
                    "product": port_info.get("product"),
                    "version": port_info.get("version"),
                }
        results["hosts"][host] = host_data

    return results
