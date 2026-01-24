#!/usr/bin/env python3
import evdev
from evdev import UInput, ecodes as e
import select
import sys

devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
keyboards = [
    d for d in devices
    if e.EV_KEY in d.capabilities()
    and e.KEY_CAPSLOCK in d.capabilities()[e.EV_KEY]
    and e.KEY_A in d.capabilities()[e.EV_KEY]
]

def last_used_keyboard(keyboards_list):
    """
    Find the last used keyboard from a list of keyboard devices.

    Args:
        keyboards_list: List of evdev.InputDevice

    Return: 
        last_used_keybaord: evdev.InputDevice. None if no keyboards are found.
    """

    if not keyboards_list:
        return None

    last_used_keyboard = None
    last_event_time = 0.0

    for keyboard in keyboards_list:
        try:
            # Get the last event time
            fd = keyboard.fd
            readable, _, _ = select.select([fd], [], [], 0.001) #Non-blocking select
            if readable:
                try:
                    event = keyboard.read_one()
                    current_time = event.sec + event.usec / 1000000.0
                    if current_time > last_event_time:
                        last_event_time = current_time
                        last_used_keyboard = keyboard
                except OSError:
                    pass
        except OSError:
            pass

        
    return last_used_keyboard



kbd = last_used_keyboard(keyboards)
while kbd is None:
    kbd = last_used_keyboard(keyboards)
kbd.grab()


ui = UInput(
    {
        e.EV_KEY: kbd.capabilities()[e.EV_KEY],
        e.EV_MSC: [e.MSC_SCAN],
        e.EV_LED: [e.LED_NUML, e.LED_CAPSL, e.LED_SCROLLL],
    },
    name="capslock-fixed",
)

try:
    while True:
            try:        
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
                            
            except OSError as err:
                if err.errno == 19: #keyboard unplugged, scan for new device until found
                    kbd = last_used_keyboard(keyboards)
                    while kbd is None:
                        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
                        keyboards = [
                            d for d in devices
                            if e.EV_KEY in d.capabilities()
                            and e.KEY_CAPSLOCK in d.capabilities()[e.EV_KEY]
                            and e.KEY_A in d.capabilities()[e.EV_KEY]
                        ]
                        kbd = last_used_keyboard(keyboards)
                    kbd.grab()
                else:
                    raise

except KeyboardInterrupt:
    pass

finally:
    kbd.ungrab()
    ui.close()