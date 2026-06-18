# Network Health Checker — Cisco IOS/IOS-XE

A Python automation tool that checks the health of multiple Cisco IOS/IOS-XE network devices — combining ICMP reachability tests with SSH-based data collection using [Netmiko](https://github.com/ktbyers/netmiko).

Built as part of my network automation toolkit. Designed for network engineers who want to move beyond manual `show` commands and start automating operational health checks.

---

## What it does

For each device in your inventory, the script:

1. **Pings the device** — confirms basic ICMP reachability
2. **SSHs in via Netmiko** — establishes an authenticated session
3. **Runs health commands** — collects CPU, memory, uptime, interface summary, BGP peers, OSPF neighbors
4. **Prints a clean report** to the terminal
5. **Saves outputs** as both JSON (full detail) and CSV (summary for sharing)

---

## Sample output

```
╔══════════════════════════════════════════════════════╗
║       Network Health Checker — Cisco IOS/IOS-XE      ║
║                  by Dhrumil Patel                    ║
╚══════════════════════════════════════════════════════╝

► Core-Router-01
  [~] Pinging Core-Router-01 (192.168.1.1)... ✓ UP
  [~] SSHing into Core-Router-01... ✓ Connected

══════════════════════════════════════════════════════════════
  NETWORK HEALTH REPORT — 2024-11-15 14:32

  Device  : Core-Router-01 (192.168.1.1)
  Ping    : ✓    SSH: ✓
  [CPU]
    CPU utilization for five seconds: 4%/1%; one minute: 5%; five minutes: 4%
  [Memory]
    Processor Pool Total: 856541184 Used: 214956336 Free: 641584848
  ...

  SUMMARY
  Total devices   : 3
  Reachable (ping): 3/3
  SSH connected   : 3/3
```

---

## Requirements

- Python 3.8+
- SSH access to your Cisco devices (IOS or IOS-XE)
- Netmiko library

---

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/network-health-checker.git
cd network-health-checker

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

**Step 1** — Edit the `DEVICES` list in `network_health_check.py`:

```python
DEVICES = [
    {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "your_password",
        "device_type": "cisco_ios",
        "name": "Core-Router-01",
    },
    # add more devices here...
]
```

**Step 2** — Run the script:

```bash
python network_health_check.py
```

**Step 3** — Find your output files in the `outputs/` folder:
- `health_YYYYMMDD_HHMMSS.json` — full detail for every device
- `health_YYYYMMDD_HHMMSS.csv` — summary table, easy to share

---

## Supported device types

| Platform       | `device_type` value  |
|----------------|----------------------|
| Cisco IOS      | `cisco_ios`          |
| Cisco IOS-XE   | `cisco_ios`          |
| Cisco NX-OS    | `cisco_nxos`         |
| Cisco ASA      | `cisco_asa`          |

---

## Health commands collected

| Label       | Command                                         |
|-------------|------------------------------------------------|
| Version     | `show version`                                  |
| CPU         | `show processes cpu`                            |
| Memory      | `show processes memory`                         |
| Interfaces  | `show interfaces summary`                       |
| BGP         | `show ip bgp summary`                           |
| OSPF        | `show ip ospf neighbor`                         |

You can add or remove commands by editing the `HEALTH_COMMANDS` dictionary in the script.

---

## Security note

Do not hardcode passwords in the script for production use. Consider using environment variables:

```python
import os
"password": os.environ.get("NET_PASSWORD")
```

Then run with:
```bash
export NET_PASSWORD="your_password"
python network_health_check.py
```

---

## Tech stack

- **Python 3** — core scripting
- **Netmiko** — multi-vendor SSH library for network devices
- **subprocess** — native ping via OS
- **json / csv** — structured output for reporting and logging

---

## Author

**Dhrumil Patel** — Network Engineer  
[LinkedIn](https://linkedin.com/in/YOUR_PROFILE) | dhrumil.p@itjobinbox.com

---

## Roadmap

- [ ] Load device list from external CSV/YAML inventory file
- [ ] Add email alerting when a device is unreachable
- [ ] Add Ansible playbook version
- [ ] Add support for Palo Alto firewalls (PAN-OS)
- [ ] Schedule via cron for periodic health checks
