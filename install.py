#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys


SCRIPT_PATH = "/usr/local/bin/capslock-fix.py"
UNINSTALL_PATH = "/usr/local/bin/capslock-fix-uninstall.py"
SERVICE_PATH = "/etc/systemd/system/capslock-fix.service"
SERVICE_NAME = "capslock-fix.service"

SCRIPT_CONTENT = '''#!/usr/bin/env python3
import argparse
import json
import os
import select
import subprocess
import sys
import time

try:
    import evdev
    from evdev import UInput, ecodes as e
except ImportError:
    evdev = None
    UInput = None
    e = None

try:
    import pyudev
except ImportError:
    pyudev = None


CONFIG_PATH = "/etc/capslock-fix.json"
SERVICE_NAME = "capslock-fix.service"
VIRTUAL_DEVICE_NAME = "capslock-fixed"


def require_root():
    if os.geteuid() != 0:
        print("Run as root: sudo python3 ./capslock-fix.py")
        sys.exit(1)


def require_evdev():
    if evdev is None or UInput is None or e is None:
        print("Missing dependency: python3-evdev")
        sys.exit(1)


def require_pyudev():
    if pyudev is None:
        print("Missing dependency: python3-pyudev")
        sys.exit(1)


def is_keyboard(device):
    try:
        capabilities = device.capabilities()
    except OSError:
        return False

    return (
        device.name != VIRTUAL_DEVICE_NAME
        and e.EV_KEY in capabilities
        and e.KEY_CAPSLOCK in capabilities[e.EV_KEY]
        and e.KEY_A in capabilities[e.EV_KEY]
    )


def list_keyboard_devices():
    devices = []
    for path in evdev.list_devices():
        device = evdev.InputDevice(path)
        if is_keyboard(device):
            devices.append(device)
        else:
            device.close()
    return devices


def device_identity(device):
    info = device.info
    return {
        "name": device.name or "",
        "phys": device.phys or "",
        "uniq": device.uniq or "",
        "bustype": int(info.bustype),
        "vendor": int(info.vendor),
        "product": int(info.product),
        "version": int(info.version),
    }


def identity_matches(identity, device):
    current = device_identity(device)
    return all(current[key] == identity.get(key, "") for key in current)


def identity_label(identity):
    vendor = f"{identity['vendor']:04x}"
    product = f"{identity['product']:04x}"
    phys = identity["phys"] or "-"
    uniq = identity["uniq"] or "-"
    return (
        f"{identity['name']} "
        f"[vendor:product={vendor}:{product}, phys={phys}, uniq={uniq}]"
    )


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"keyboards": []}

    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    keyboards = data.get("keyboards")
    if not isinstance(keyboards, list):
        return {"keyboards": []}
    return {"keyboards": keyboards}


def save_config(config):
    parent = os.path.dirname(CONFIG_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\\n")


def configured_keyboards():
    return load_config()["keyboards"]


def restart_service():
    subprocess.run(["systemctl", "restart", SERVICE_NAME], check=False)


def service_is_active():
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", SERVICE_NAME],
        check=False,
    )
    return result.returncode == 0


def stop_service():
    subprocess.run(["systemctl", "stop", SERVICE_NAME], check=False)


def cleanup_devices(devices):
    for device in devices:
        try:
            device.close()
        except OSError:
            pass


def select_keyboard(prompt, predicate):
    announced_wait = False

    while True:
        devices = list_keyboard_devices()
        candidates = [device for device in devices if predicate(device)]

        if not candidates:
            if not announced_wait:
                print("No matching keyboards found. Waiting for one to appear...")
                announced_wait = True
            time.sleep(0.5)
            cleanup_devices(devices)
            continue

        if announced_wait:
            print("Matching keyboard detected.")
            announced_wait = False

        print(prompt)

        fd_to_device = {device.fd: device for device in candidates}
        try:
            readable, _, _ = select.select(list(fd_to_device), [], [], 1)
        except OSError:
            cleanup_devices(devices)
            time.sleep(0.5)
            continue

        if not readable:
            cleanup_devices(devices)
            continue

        for fd in readable:
            device = fd_to_device[fd]
            try:
                for event in device.read():
                    if event.type == e.EV_KEY and event.value == 1:
                        identity = device_identity(device)
                        cleanup_devices(devices)
                        return identity
            except OSError:
                pass

        cleanup_devices(devices)


def add_keyboard(no_restart=False):
    require_root()
    require_evdev()
    config = load_config()

    identity = select_keyboard(
        "Press a key on the keyboard you want to add...",
        lambda device: not any(
            identity_matches(saved, device) for saved in config["keyboards"]
        ),
    )

    if any(identity == saved for saved in config["keyboards"]):
        print(f"Keyboard already configured: {identity_label(identity)}")
        return 0

    config["keyboards"].append(identity)
    save_config(config)
    print(f"Added keyboard: {identity_label(identity)}")

    if not no_restart:
        restart_service()
    return 0


def remove_keyboard(no_restart=False):
    require_root()
    require_evdev()
    config = load_config()
    if not config["keyboards"]:
        print("No configured keyboards to remove.")
        return 1

    was_active = service_is_active()
    if was_active:
        stop_service()

    try:
        identity = select_keyboard(
            "Press a key on the keyboard you want to remove...",
            lambda device: any(
                identity_matches(saved, device) for saved in config["keyboards"]
            ),
        )
    except KeyboardInterrupt:
        if was_active:
            restart_service()
        print("Remove cancelled.")
        return 130
    finally:
        if was_active and no_restart:
            restart_service()

    new_keyboards = [saved for saved in config["keyboards"] if saved != identity]
    if len(new_keyboards) == len(config["keyboards"]):
        print(f"Keyboard was not configured: {identity_label(identity)}")
        return 1

    config["keyboards"] = new_keyboards
    save_config(config)
    print(f"Removed keyboard: {identity_label(identity)}")

    if was_active and not no_restart:
        restart_service()
    return 0


def list_configured_keyboards():
    require_evdev()
    config = load_config()
    if not config["keyboards"]:
        print("No keyboards configured.")
        return 0

    connected = list_keyboard_devices()
    try:
        for index, identity in enumerate(config["keyboards"], start=1):
            is_connected = any(identity_matches(identity, dev) for dev in connected)
            status = "connected" if is_connected else "missing"
            print(f"{index}. {identity_label(identity)} [{status}]")
    finally:
        cleanup_devices(connected)

    return 0


def release_keyboard(path, active):
    keyboard = active.pop(path, None)
    if keyboard is None:
        return

    try:
        keyboard.ungrab()
    except OSError:
        pass

    try:
        keyboard.close()
    except OSError:
        pass


def grab_configured_keyboards(active, configured):
    changed = False
    seen_paths = set()

    for device in list_keyboard_devices():
        seen_paths.add(device.path)

        if not any(identity_matches(identity, device) for identity in configured):
            device.close()
            continue

        if device.path in active:
            device.close()
            continue

        try:
            device.grab()
            active[device.path] = device
            changed = True
        except OSError:
            device.close()

    for path in list(active):
        if path not in seen_paths:
            release_keyboard(path, active)
            changed = True

    return changed


def create_virtual_keyboard(source_keyboard):
    capabilities = source_keyboard.capabilities()
    return UInput(
        {
            e.EV_KEY: capabilities[e.EV_KEY],
            e.EV_MSC: [e.MSC_SCAN],
            e.EV_LED: [e.LED_NUML, e.LED_CAPSL, e.LED_SCROLLL],
        },
        name=VIRTUAL_DEVICE_NAME,
    )


def create_udev_monitor():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="input")
    monitor.start()
    return monitor


def run_service():
    require_evdev()
    require_pyudev()
    configured = configured_keyboards()
    if not configured:
        print("No configured keyboards. Run `capslock-fix.py add` first.")
        return 1

    active = {}
    ui = None
    monitor = create_udev_monitor()
    monitor_fd = monitor.fileno()

    try:
        grab_configured_keyboards(active, configured)

        while True:
            if ui is None and active:
                ui = create_virtual_keyboard(next(iter(active.values())))
            fd_to_path = {device.fd: path for path, device in active.items()}

            try:
                readable, _, _ = select.select([monitor_fd, *fd_to_path], [], [])
            except (OSError, ValueError):
                grab_configured_keyboards(active, configured)
                continue

            if monitor_fd in readable:
                while True:
                    event = monitor.poll(timeout=0)
                    if event is None:
                        break
                grab_configured_keyboards(active, configured)
                readable = [fd for fd in readable if fd != monitor_fd]

            for fd in readable:
                path = fd_to_path.get(fd)
                keyboard = active.get(path) if path else None
                if keyboard is None:
                    continue

                try:
                    for event in keyboard.read():
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
                except OSError as err:
                    if err.errno == 19:
                        release_keyboard(path, active)
                    else:
                        raise
    except KeyboardInterrupt:
        return 0
    finally:
        for path in list(active):
            release_keyboard(path, active)
        if ui is not None:
            ui.close()

    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Caps Lock instant-toggle fix with managed keyboard selection."
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the background keyboard service.")
    run_parser.set_defaults(handler=lambda args: run_service())

    add_parser = subparsers.add_parser("add", help="Add a keyboard by pressing a key on it.")
    add_parser.add_argument("--no-restart", action="store_true", help=argparse.SUPPRESS)
    add_parser.set_defaults(handler=lambda args: add_keyboard(no_restart=args.no_restart))

    remove_parser = subparsers.add_parser(
        "remove",
        help="Remove a keyboard by pressing a key on it.",
    )
    remove_parser.add_argument("--no-restart", action="store_true", help=argparse.SUPPRESS)
    remove_parser.set_defaults(
        handler=lambda args: remove_keyboard(no_restart=args.no_restart)
    )

    list_parser = subparsers.add_parser("list", help="List configured keyboards.")
    list_parser.set_defaults(handler=lambda args: list_configured_keyboards())

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        return run_service()

    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
'''

UNINSTALL_CONTENT = '''#!/usr/bin/env python3
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
'''

SERVICE_CONTENT = """[Unit]
Description=Caps Lock Instant Toggle Fix
Before=display-manager.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/capslock-fix.py run
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""


def require_root():
    if os.geteuid() != 0:
        print("Run as root: sudo python3 ./install.py")
        sys.exit(1)


def ensure_python_module(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def ensure_dependencies():
    missing = []
    if not ensure_python_module("evdev"):
        missing.append("evdev")
    if not ensure_python_module("pyudev"):
        missing.append("pyudev")

    if not missing:
        return

    if shutil.which("apt"):
        packages = []
        if "evdev" in missing:
            packages.append("python3-evdev")
        if "pyudev" in missing:
            packages.append("python3-pyudev")
        subprocess.run(["apt", "install", "-y", *packages], check=True)
    elif shutil.which("dnf"):
        packages = []
        if "evdev" in missing:
            packages.append("python3-evdev")
        if "pyudev" in missing:
            packages.append("python3-pyudev")
        subprocess.run(["dnf", "install", "-y", *packages], check=True)
    elif shutil.which("pacman"):
        packages = []
        if "evdev" in missing:
            packages.append("python-evdev")
        if "pyudev" in missing:
            packages.append("python-pyudev")
        subprocess.run(["pacman", "-S", "--noconfirm", *packages], check=True)
    else:
        print("Unknown package manager. Install python3-evdev and python3-pyudev manually.")
        sys.exit(1)


def write_file(path, content, mode):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    os.chmod(path, mode)


def main():
    require_root()
    ensure_dependencies()

    subprocess.run(["systemctl", "stop", SERVICE_NAME], check=False)
    subprocess.run(["systemctl", "disable", SERVICE_NAME], check=False)

    print("Creating script...")
    write_file(SCRIPT_PATH, SCRIPT_CONTENT, 0o755)

    print("Creating uninstall script...")
    write_file(UNINSTALL_PATH, UNINSTALL_CONTENT, 0o755)

    print("Creating service...")
    write_file(SERVICE_PATH, SERVICE_CONTENT, 0o644)

    subprocess.run(["systemctl", "daemon-reload"], check=False)

    print("Add your first keyboard now.")
    add_result = subprocess.run(
        [sys.executable, SCRIPT_PATH, "add", "--no-restart"],
        check=False,
    )
    if add_result.returncode != 0:
        print("Keyboard was not added during install. You can add one later with:")
        print(f"sudo {SCRIPT_PATH} add")
        print(f"sudo systemctl start {SERVICE_NAME}")
    else:
        subprocess.run(["systemctl", "enable", SERVICE_NAME], check=False)
        subprocess.run(["systemctl", "start", SERVICE_NAME], check=False)

    print("Done.")
    print(f"Add keyboard: sudo {SCRIPT_PATH} add")
    print(f"Remove keyboard: sudo {SCRIPT_PATH} remove")
    print(f"List keyboards: sudo {SCRIPT_PATH} list")
    print(f"Uninstall: sudo {UNINSTALL_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
