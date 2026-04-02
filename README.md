# Linux Caps Lock Fix

## The Problem
By default, Linux distributions mimic old physical typewriters in the way Caps Lock works:
* **ON:** Activates immediately when you press the key down.
* **OFF:** Activates only once you **release** the key.

This delay often leads to `HEllo` style typos because you have not lifted your finger off Caps Lock fast enough.
This script makes the toggle instant for both states.

## Quick Install
```bash
curl -O https://raw.githubusercontent.com/TreeOfSelf/Linux-Capslock-Fix/main/install.py
chmod +x install.py
sudo python3 ./install.py
```

During install, it will ask you to press a key on the first keyboard you want to add.

## Commands
```bash
sudo /usr/local/bin/capslock-fix.py add
sudo /usr/local/bin/capslock-fix.py remove
sudo /usr/local/bin/capslock-fix.py list
sudo /usr/local/bin/capslock-fix-uninstall.py
```

Use `add` to add a keyboard, `remove` to remove one, and `list` to see what is currently added.  
For `add` and `remove`, it will ask you to press a key on the keyboard you want.

## Manual Install

### 1. Install dependency

**Debian/Ubuntu:**
```bash
sudo apt install python3-evdev
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-evdev
```

**Arch:**
```bash
sudo pacman -S python-evdev
```

### 2. Install the scripts
```bash
sudo cp capslock-fix.py /usr/local/bin/capslock-fix.py
sudo cp uninstall.py /usr/local/bin/capslock-fix-uninstall.py
sudo chmod +x /usr/local/bin/capslock-fix.py /usr/local/bin/capslock-fix-uninstall.py
```

### 3. Create service
```bash
sudo nano /etc/systemd/system/capslock-fix.service
```

Paste:
```ini
[Unit]
Description=Caps Lock Instant Toggle Fix
Before=display-manager.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/capslock-fix.py run
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

### 4. Reload and add a keyboard
```bash
sudo systemctl daemon-reload
sudo /usr/local/bin/capslock-fix.py add
sudo systemctl enable capslock-fix.service
sudo systemctl start capslock-fix.service
```

## Uninstall
```bash
sudo python3 ./uninstall.py
```
