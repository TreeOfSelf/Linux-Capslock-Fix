#!/usr/bin/env python3
import subprocess
import select
import sys
import os


if os.geteuid() != 0:
    print("Run as root: sudo python ./install.py")
    sys.exit(1)


try:
    import evdev
    from evdev import UInput, ecodes as e
except ImportError:

    if subprocess.run("apt").returncode == 0:
        subprocess.run(["apt","install","-y","python3-evdev"])
        import evdev
        from evdev import UInput, ecodes as e

    elif subprocess.run("dnf").returncode == 0:
        subprocess.run(["dnf","install","-y","python3-evdev"])
        import evdev
        from evdev import UInput, ecodes as e

    elif subprocess.run("pacman").returncode == 0:
        subprocess.run(["pacman","-S","--noconfirm","python3-evdev"])
        import evdev
        from evdev import UInput, ecodes as e

    else:
        print("Unknown package manager. Install python3-evdev manually")
        sys.exit(1)






# Stop already running fix to prevent grabbing fixed virtual keyboard
subprocess.run(["systemctl","stop","capslock-fix.service"])
subprocess.run(["systemctl","disable","capslock-fix.service"])

devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
keyboards = [
    d for d in devices
    if e.EV_KEY in d.capabilities()
    and e.KEY_CAPSLOCK in d.capabilities()[e.EV_KEY]
    and e.KEY_A in d.capabilities()[e.EV_KEY]]

if not keyboards:
    print("No keyboards found")
    sys.exit(1)


print("Press any key to detect the keyboard...")

kbd = None
try:
    inputs, _, _ = select.select(keyboards, [], [])

    if inputs:
        kbd = inputs[0]
        print(f"Detected keyboard: {kbd.name} ({kbd.path})")
    else:
        print("No key pressed.")
        sys.exit(1)

except KeyboardInterrupt:
    print("\nExiting...")
    sys.exit(0)


print("Creating script...")

script_content = f"""
#!/usr/bin/env python3
import evdev
from evdev import UInput, ecodes as e
import select
import sys

device_path = "{kbd.path}"

kbd = evdev.InputDevice(device_path)

ui = UInput(
    {{
        e.EV_KEY: kbd.capabilities()[e.EV_KEY],
        e.EV_MSC: [e.MSC_SCAN],
        e.EV_LED: [e.LED_NUML, e.LED_CAPSL, e.LED_SCROLLL],
    }},
    name="capslock-fixed",
)


kbd.grab()

try:
    while True:
        select.select([kbd.fd], [], [])
        for event in kbd.read():
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
    kbd.ungrab()
    ui.close()

"""


script_path = "/usr/local/bin/capslock-fix.py"
try:
    with open(script_path, "w") as f:
        f.write(script_content)

    os.chmod(script_path, 0o755)

except Exception as e:
    print(f"An error occurred: {e}")


print("Creating service...")

service_content = """
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
"""

service_path = "/etc/systemd/system/capslock-fix.service"
try:
    with open(service_path, "w") as f:
        f.write(service_content)


except Exception as e:
    print(f"An error occurred: {e}")


subprocess.run(["systemctl","daemon-reload"])
subprocess.run(["systemctl","enable","capslock-fix.service"])
subprocess.run(["systemctl","start","capslock-fix.service"])

print("Done! Check status: ")
print("sudo systemctl status capslock-fix.service")