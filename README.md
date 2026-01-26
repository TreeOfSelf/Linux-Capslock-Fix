# Caps Lock Instant Toggle Fix

Fixes Linux caps lock bug where ON=instant but OFF=only on release.   
   
## **Why not [Linux-CapsLock-Delay-Fixer](https://github.com/hexvalid/Linux-CapsLock-Delay-Fixer)?**  
Because- that repo has an annoying bug where if you press Capslock and a button with a modifier (like ".") it will act like a shift (and type something like ">").    

As far as I know, this repo is the most "proper fix" to this annoying behavior at the moment, but if that changes I will link to a better one.

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

---

<sub><sup>I don't care if it's how typewriters worked, we're not using typewriters. We have computers with millisecond input polling and people typing at 145+ WPM. The "press to lock, release to unlock" behavior is a HALF-CENTURY OLD mechanical limitation, not some sacred design principle. You know what else typewriters did? They jammed if you typed too fast. Should we add that feature too for "authenticity"? Every other modern OS figured this out decades ago- Windows, Mac, even BSD - they all toggle on PRESS because that's what makes sense for actual human typing patterns. When I hit Caps Lock, I want it to change STATE right then, not when I eventually get around to lifting my finger. This isn't about Mac vs Linux or "correct" behavior. It's about a kernel bug that breaks the expected behavior of a modifier key, and instead of fixing it, Linux maintainers are pointing at typewriters from before computers existed and saying "actually this is correct." It's ridiculous. The fact that we need arcane XKB hacks with undocumented Private() actions and mystery data values just to make a TOGGLE KEY work like every other toggle in computing is embarrassing. This is basic HID functionality that's been solved everywhere else.</sup></sub>
