# Linux Caps Lock Fix

## The Problem
By default, Linux distributions mimic old physical typewriters in the way Caps lock works:   
* **ON:** Activates immediately when you press the key down.  
* **OFF:** Activates only once you **release** the key.  

This "delay" often leads to `HEllo` style typos where the first two letters of a word are capitalized because you haven't lifted your finger off the Caps Lock key fast enough.   
This script makes the toggle instant for both states.

## **Why not [Linux-CapsLock-Delay-Fixer](https://github.com/hexvalid/Linux-CapsLock-Delay-Fixer)?**  
Because, that repo has an annoying bug where if you press Capslock and a button with a modifier (like ".") it will act like a shift (and type something like ">").

## Quick Install
```bash
curl -O https://raw.githubusercontent.com/TreeOfSelf/Linux-Capslock-Fix/main/install.py
chmod +x install.py
sudo python3 ./install.py
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

### 2. Create the script
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

Done. Runs on boot automatically.

## Uninstall
```bash
sudo systemctl stop capslock-fix.service
sudo systemctl disable capslock-fix.service
sudo rm /etc/systemd/system/capslock-fix.service
sudo rm /usr/local/bin/capslock-fix.py
sudo systemctl daemon-reload
```

## But this is how it is supposed to work!
Yes, I have heard the argument before. Old typewriters used to have physical latches, the default behavior of Caps lock in Linux mimics this.   
But it is not pleasant to type with, no other OS does this, and it interrupts the flow of typing (especially for people who rely on Caps lock for capitalizing)   
Sometimes ergonomics and user-friendliness are preferred over being "historically correct".      
We aren't here to debate, we just want our computers to work the way we want them to. 

## Special thanks
[tzrtvevo](https://github.com/tzrtvevo) - for helping fix a bug and greatly improving the installation process 
