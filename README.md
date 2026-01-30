# Caps Lock Instant Toggle Fix

Fixes Linux caps lock on Linux where `ON=key on down` but `OFF=only on release`.   
   
## **Why not [Linux-CapsLock-Delay-Fixer](https://github.com/hexvalid/Linux-CapsLock-Delay-Fixer)?**  
Because- that repo has an annoying bug where if you press Capslock and a button with a modifier (like ".") it will act like a shift (and type something like ">").
(The problem also isn't really a "delay" even though it feels like that)

As far as I know, this repo is the most "proper fix" to this behavior at the moment, but if that changes I will link to a better one.

## Quick Install
```bash
curl -O https://raw.githubusercontent.com/TreeOfSelf/Linux-Capslock-Fix/main/install.py
chmod +x install.py
sudo python ./install.py
```

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

### 2. Create script
```bash
sudo nano /usr/local/bin/capslock-fix.py
```
Paste the code from `capslock-fix.py`

### 3. Create service
```bash
sudo nano /etc/systemd/system/capslock-fix.service
```

Paste:
```ini
[Unit]
Description=Caps Lock Instant Toggle Fix
After=systemd-user-sessions.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/capslock-fix.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

Save and exit.

### 4. Enable service
```bash
sudo systemctl daemon-reload
sudo systemctl enable capslock-fix.service
sudo systemctl start capslock-fix.service
```

## Check status
```bash
sudo systemctl status capslock-fix.service
```

Done. Runs on boot forever.

## Special thanks
[tzrtvevo](https://github.com/tzrtvevo) - for helping fix a bug and greatly improving the installation process 
