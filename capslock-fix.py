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
