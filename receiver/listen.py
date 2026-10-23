import lgpio
import time
import threading
import subprocess
import re
import os
from collections import deque

GPIO_PIN = 17
ALARM_WAV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         os.environ.get('DOORBELL_SOUND', 'chime.wav'))

SHORT    = 350    # µs
LONG     = 1050   # µs
SYNC_LOW = 10500  # µs
TOL      = 0.6

RELEASED_AFTER = 0.5
IDLE_AFTER     = 1.5

FRAMES = {
    'idle': """\033[2J\033[H
  ╔══════════════════════╗
  ║       DOORBELL       ║
  ╚══════════════════════╝

           .-----.
          |       |
          |   ○   |    Waiting...
          |       |
           '-----'
""",
    'pressed': """\033[2J\033[H
  ╔══════════════════════╗
  ║       DOORBELL       ║
  ╚══════════════════════╝

           .-----.
          |#######|
          |   ●   |  *** DING DONG! ***
          |#######|
           '-----'

  code: {code}
""",
    'released': """\033[2J\033[H
  ╔══════════════════════╗
  ║       DOORBELL       ║
  ╚══════════════════════╝

           .-----.
          |       |
          |   ○   |    Released
          |       |
           '-----'
""",
}

LOG = []

def log(msg):
    ts = time.strftime('%H:%M:%S')
    line = f"  {ts}  {msg}"
    LOG.append(line)
    if len(LOG) > 10:
        LOG.pop(0)
    with open('/home/erykpiast/doorbell.log', 'a') as f:
        f.write(line + '\n')

def draw(s, code=None):
    frame = FRAMES[s]
    if code is not None:
        frame = frame.format(code=f'0x{code:06X}')
    log_block = '\n'.join(LOG) if LOG else '  (no events yet)'
    print(frame + '\n' + log_block + '\n', flush=True)

def find_dac_card():
    """Find the ALSA card index for the MAX98357A DAC, as in test_dac.sh."""
    try:
        out = subprocess.run(['aplay', '-l'], capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    for line in out.splitlines():
        m = re.match(r'card (\d+):.*MAX98357A', line)
        if m:
            return m.group(1)
    return None

DAC_CARD = find_dac_card()

def play_alarm():
    if DAC_CARD is None:
        log("alarm: no MAX98357A DAC found, skipping playback")
        return
    device = f'plughw:{DAC_CARD},0'
    subprocess.Popen(
        ['aplay', '-D', device, ALARM_WAV],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

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

draw('idle')

state = 'idle'
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
                log(f"decoded code=0x{code:06X} ({code})")
                if state != 'pressed':
                    log("alarm: playing")
                    play_alarm()
                state = 'pressed'
                draw('pressed', code)

        # periodic diagnostic so we can see the poller is alive
        if now - last_diag > 1.0:
            last_diag = now
            if state == 'idle':
                log(f"edges={edge_count[0]} buf={len(snapshot)}")
                # dump the full raw frame so we can hand-decode it
                if len(snapshot) >= 50:
                    with open('/home/erykpiast/frame.log', 'w') as f:
                        for lv, d in snapshot:
                            f.write(f"{'H' if lv else 'L'} {round(d)}\n")
                draw('idle')

        if last_signal_time is not None:
            silence = now - last_signal_time
            if silence > IDLE_AFTER and state != 'idle':
                state = 'idle'
                log("idle")
                draw('idle')
            elif silence > RELEASED_AFTER and state == 'pressed':
                state = 'released'
                log("released")
                draw('released')
except KeyboardInterrupt:
    pass
finally:
    running[0] = False
    lgpio.gpiochip_close(h)
