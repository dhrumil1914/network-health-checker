#!/usr/bin/env python3
"""
Network Health Checker — Cisco IOS/IOS-XE
------------------------------------------
Checks reachability (ping) and collects key health data
from multiple Cisco devices via SSH using Netmiko.

Author  : Dhrumil Patel
GitHub  : github.com/dhrumilpatel  (update this)
Version : 1.0.0
"""

import subprocess
import platform
import json
import csv
import os
from datetime import datetime
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


# ─────────────────────────────────────────────
#  DEVICE LIST — edit these before running
# ─────────────────────────────────────────────
DEVICES = [
    {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "cisco123",
        "device_type": "cisco_ios",
        "name": "Core-Router-01",
    },
    {
        "host": "192.168.1.2",
        "username": "admin",
        "password": "cisco123",
        "device_type": "cisco_ios",
        "name": "Distribution-SW-01",
    },
    {
        "host": "192.168.1.3",
        "username": "admin",
        "password": "cisco123",
        "device_type": "cisco_ios",
        "name": "Access-SW-01",
    },
]

# Commands to run on each device after SSH login
HEALTH_COMMANDS = {
    "Version":     "show version | include uptime|Software|IOS",
    "CPU":         "show processes cpu | include CPU utilization",
    "Memory":      "show processes memory | include Processor Pool",
    "Interfaces":  "show interfaces summary",
    "BGP":         "show ip bgp summary | include ^[0-9]",
    "OSPF":        "show ip ospf neighbor | include FULL",
}


# ─────────────────────────────────────────────
#  STEP 1 — Ping check (ICMP reachability)
# ─────────────────────────────────────────────
def ping_device(host: str) -> bool:
    """Returns True if device responds to ping."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    result = subprocess.run(
        ["ping", param, "3", "-W", "2", host],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


# ─────────────────────────────────────────────
#  STEP 2 — SSH into device and run commands
# ─────────────────────────────────────────────
def collect_device_health(device: dict) -> dict:
    """SSH into a Cisco device and pull health data."""
    result = {
        "name":      device["name"],
        "host":      device["host"],
        "ping":      False,
        "ssh":       False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data":      {},
        "error":     None,
    }

    # --- Ping first ---
    print(f"  [~] Pinging {device['name']} ({device['host']})...", end=" ")
    result["ping"] = ping_device(device["host"])
    print("✓ UP" if result["ping"] else "✗ UNREACHABLE")

    if not result["ping"]:
        result["error"] = "Host unreachable (ping failed)"
        return result

    # --- SSH and run commands ---
    print(f"  [~] SSHing into {device['name']}...", end=" ")
    try:
        connection = ConnectHandler(
            host=device["host"],
            username=device["username"],
            password=device["password"],
            device_type=device["device_type"],
            timeout=10,
        )
        result["ssh"] = True
        print("✓ Connected")

        for label, command in HEALTH_COMMANDS.items():
            try:
                output = connection.send_command(command, read_timeout=10)
                result["data"][label] = output.strip() if output.strip() else "No output"
            except Exception as e:
                result["data"][label] = f"Command failed: {e}"

        connection.disconnect()

    except NetmikoAuthenticationException:
        result["error"] = "SSH authentication failed — check username/password"
        print("✗ Auth failed")
    except NetmikoTimeoutException:
        result["error"] = "SSH connection timed out"
        print("✗ Timeout")
    except Exception as e:
        result["error"] = str(e)
        print(f"✗ Error: {e}")

    return result


# ─────────────────────────────────────────────
#  STEP 3 — Print results to terminal
# ─────────────────────────────────────────────
def print_report(results: list):
    """Print a clean health summary to the terminal."""
    divider = "─" * 60
    print(f"\n{'═' * 60}")
    print(f"  NETWORK HEALTH REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═' * 60}\n")

    for r in results:
        ping_icon = "✓" if r["ping"] else "✗"
        ssh_icon  = "✓" if r["ssh"]  else "✗"

        print(f"{divider}")
        print(f"  Device  : {r['name']} ({r['host']})")
        print(f"  Ping    : {ping_icon}    SSH: {ssh_icon}")
        print(f"  Time    : {r['timestamp']}")

        if r["error"]:
            print(f"  Error   : {r['error']}")
        elif r["data"]:
            print()
            for label, output in r["data"].items():
                print(f"  [{label}]")
                for line in output.splitlines()[:5]:   # show max 5 lines per command
                    print(f"    {line}")
                if len(output.splitlines()) > 5:
                    print(f"    ... ({len(output.splitlines()) - 5} more lines in JSON output)")
                print()

    # Summary table
    print(f"{'═' * 60}")
    print(f"  SUMMARY")
    print(f"{'─' * 60}")
    total     = len(results)
    reachable = sum(1 for r in results if r["ping"])
    connected = sum(1 for r in results if r["ssh"])
    print(f"  Total devices   : {total}")
    print(f"  Reachable (ping): {reachable}/{total}")
    print(f"  SSH connected   : {connected}/{total}")
    print(f"{'═' * 60}\n")


# ─────────────────────────────────────────────
#  STEP 4 — Save outputs (JSON + CSV)
# ─────────────────────────────────────────────
def save_json(results: list, filename: str):
    """Save full output as JSON for later analysis."""
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  [✓] JSON saved  → {filename}")


def save_csv(results: list, filename: str):
    """Save a summary CSV (great for sharing with teams)."""
    headers = ["Name", "Host", "Timestamp", "Ping", "SSH", "Error"]
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "Name":      r["name"],
                "Host":      r["host"],
                "Timestamp": r["timestamp"],
                "Ping":      "UP" if r["ping"] else "DOWN",
                "SSH":       "OK" if r["ssh"]  else "FAILED",
                "Error":     r["error"] or "",
            })
    print(f"  [✓] CSV saved   → {filename}")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║       Network Health Checker — Cisco IOS/IOS-XE      ║")
    print("║                  by Dhrumil Patel                    ║")
    print("╚══════════════════════════════════════════════════════╝\n")
    print(f"  Checking {len(DEVICES)} device(s)...\n")

    all_results = []

    for device in DEVICES:
        print(f"► {device['name']}")
        result = collect_device_health(device)
        all_results.append(result)
        print()

    # Print to terminal
    print_report(all_results)

    # Save output files
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    save_json(all_results, f"{output_dir}/health_{timestamp}.json")
    save_csv(all_results,  f"{output_dir}/health_{timestamp}.csv")

    print(f"\n  Done.\n")


if __name__ == "__main__":
    main()
