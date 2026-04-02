#!/usr/bin/env python3
import os
import subprocess
import sys


SERVICE_NAME = "capslock-fix.service"
SERVICE_PATH = "/etc/systemd/system/capslock-fix.service"
SCRIPT_PATH = "/usr/local/bin/capslock-fix.py"
UNINSTALL_PATH = "/usr/local/bin/capslock-fix-uninstall.py"
CONFIG_PATH = "/etc/capslock-fix.json"


if os.geteuid() != 0:
    print("Run as root: sudo python3 ./uninstall.py")
    sys.exit(1)


subprocess.run(["systemctl", "stop", SERVICE_NAME], check=False)
subprocess.run(["systemctl", "disable", SERVICE_NAME], check=False)

for path in [SERVICE_PATH, SCRIPT_PATH, UNINSTALL_PATH, CONFIG_PATH]:
    if os.path.exists(path):
        os.remove(path)
        print(f"Removed {path}")

subprocess.run(["systemctl", "daemon-reload"], check=False)

print("Done. Capslock fix has been uninstalled.")
