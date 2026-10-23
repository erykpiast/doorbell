"""Doorbell receiver: decodes the 433 MHz frames and broadcasts press/release
events on the event bus (see events.py). Clients (chime.py, monitor.py) react
to the events."""
import lgpio
import time
import threading
import os
from collections import deque

from events import EventServer

GPIO_PIN = 17

SHORT    = 350    # µs
LONG     = 1050   # µs
SYNC_LOW = 10500  # µs
TOL      = 0.6

RELEASED_AFTER = 0.5  # s without a decoded frame

LOG_FILE = os.path.expanduser('~/doorbell.log')

def log(msg, echo=True):
    line = f"{time.strftime('%H:%M:%S')}  {msg}"
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')
    if echo:
        print(line, flush=True)

def in_range(val, target):
    return target * (1 - TOL) < val < target * (1 + TOL)

HIGH_THRESHOLD = (SHORT + LONG) / 2  # 700µs: HIGH above → '1', below → '0'
HIGH_MAX = LONG * 2                   # reject gap/noise pulses as bits

def decode(pulses):
    for i in range(len(pulses) - 1):
        level, dur = pulses[i]
        if level == 1 and in_range(dur, SHORT):
            nl, nd = pulses[i + 1]
            if nl == 0 and in_range(nd, SYNC_LOW):
                bits = []
                j = i + 2
                # classify each bit by its HIGH pulse alone; skip past the LOW
                # regardless of length (the 24th bit's LOW is the inter-burst gap)
                while j + 1 < len(pulses) and len(bits) < 24:
                    hl, hd = pulses[j]
                    ll, ld = pulses[j + 1]
                    if hl != 1 or ll != 0:
                        break
                    if hd > HIGH_MAX or hd < SHORT * (1 - TOL):
                        break
                    bits.append(1 if hd > HIGH_THRESHOLD else 0)
                    j += 2
                if len(bits) == 24:
                    code = 0
                    for b in bits:
                        code = (code << 1) | b
                    return code
    return None

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, GPIO_PIN)

pulses = deque(maxlen=120)
edge_count = [0]
running = [True]

def poll_thread():
    last_level = lgpio.gpio_read(h, GPIO_PIN)
    last_t = time.monotonic_ns()
    while running[0]:
        level = lgpio.gpio_read(h, GPIO_PIN)
        if level != last_level:
            now = time.monotonic_ns()
            dur_us = (now - last_t) / 1000
            pulses.append((last_level, dur_us))
            edge_count[0] += 1
            last_level = level
            last_t = now

t = threading.Thread(target=poll_thread, daemon=True)
t.start()

server = EventServer()
log(f"listening on GPIO{GPIO_PIN}, events on {server.path}")

pressed_code = None     # code of the current press, None when released
pressed_at = None
last_signal_time = None
last_diag = time.monotonic()

try:
    while True:
        time.sleep(0.05)
        now = time.monotonic()

        snapshot = list(pulses)
        if len(snapshot) >= 50:
            code = decode(snapshot)
            if code is not None:
                last_signal_time = now
                pulses.clear()
                log(f"decoded code=0x{code:06X} ({code})", echo=False)
                if pressed_code is None:
                    pressed_code = code
                    pressed_at = now
                    log(f"press code=0x{code:06X}")
                    server.publish({'type': 'press', 'code': f'0x{code:06X}',
                                    'time': time.time()})

        if pressed_code is not None and now - last_signal_time > RELEASED_AFTER:
            duration = round(last_signal_time - pressed_at, 3)
            log(f"release code=0x{pressed_code:06X} duration={duration}s")
            server.publish({'type': 'release', 'code': f'0x{pressed_code:06X}',
                            'time': time.time(), 'duration': duration})
            pressed_code = None

        # periodic diagnostic so we can see the poller is alive
        if now - last_diag > 1.0:
            last_diag = now
            if pressed_code is None:
                log(f"edges={edge_count[0]} buf={len(snapshot)}", echo=False)
                # dump the full raw frame so we can hand-decode it
                if len(snapshot) >= 50:
                    with open(os.path.expanduser('~/frame.log'), 'w') as f:
                        for lv, d in snapshot:
                            f.write(f"{'H' if lv else 'L'} {round(d)}\n")
except KeyboardInterrupt:
    pass
finally:
    running[0] = False
    server.close()
    lgpio.gpiochip_close(h)
