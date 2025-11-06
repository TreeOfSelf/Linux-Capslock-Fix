#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then 
    echo "Run as root: sudo ./install.sh"
    exit 1
fi

echo "Installing python3-evdev..."
if command -v apt &> /dev/null; then
    apt install -y python3-evdev
elif command -v dnf &> /dev/null; then
    dnf install -y python3-evdev
elif command -v pacman &> /dev/null; then
    pacman -S --noconfirm python-evdev
else
    echo "Unknown package manager. Install python3-evdev manually."
    exit 1
fi

echo "Creating script..."
cat > /usr/local/bin/capslock-fix.py << 'EOF'
#!/usr/bin/env python3
import evdev
from evdev import UInput, ecodes as e
import select

devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
keyboards = [d for d in devices if e.EV_KEY in d.capabilities() and e.KEY_CAPSLOCK in d.capabilities()[e.EV_KEY] and e.KEY_A in d.capabilities()[e.EV_KEY]]

for kbd in keyboards:
    kbd.grab()

ui = UInput({
    e.EV_KEY: keyboards[0].capabilities()[e.EV_KEY],
    e.EV_MSC: [e.MSC_SCAN],
    e.EV_LED: [e.LED_NUML, e.LED_CAPSL, e.LED_SCROLLL]
}, name='capslock-fixed')

fd_to_device = {dev.fd: dev for dev in keyboards}

try:
    while True:
        r, w, x = select.select(fd_to_device, [], [])
        for fd in r:
            for event in fd_to_device[fd].read():
                if event.type == e.EV_KEY and event.code == e.KEY_CAPSLOCK:
                    if event.value == 1:
                        ui.write(e.EV_KEY, e.KEY_CAPSLOCK, 1)
                        ui.syn()
                        ui.write(e.EV_KEY, e.KEY_CAPSLOCK, 0)
                        ui.syn()
                else:
                    ui.write(event.type, event.code, event.value)
                    if event.type == e.EV_SYN:
                        ui.syn()
except KeyboardInterrupt:
    pass
finally:
    for kbd in keyboards:
        kbd.ungrab()
    ui.close()
EOF

chmod +x /usr/local/bin/capslock-fix.py

echo "Creating service..."
cat > /etc/systemd/system/capslock-fix.service << 'EOF'
[Unit]
Description=Caps Lock Instant Toggle Fix
After=systemd-user-sessions.service

[Service]
Type=simple
ExecStart=/usr/local/bin/capslock-fix.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling service..."
systemctl daemon-reload
systemctl enable capslock-fix.service
systemctl start capslock-fix.service

echo ""
echo "Done! Check status:"
echo "  sudo systemctl status capslock-fix.service"
