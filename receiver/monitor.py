"""Monitor client: shows the doorbell state in the terminal.

Run it by hand on the Pi, next to the service: python3 monitor.py
"""
import time

from events import subscribe

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
}

LOG = []

def log(msg, t):
    LOG.append(f"  {time.strftime('%H:%M:%S', time.localtime(t))}  {msg}")
    if len(LOG) > 10:
        LOG.pop(0)

def draw(state, code=None):
    frame = FRAMES[state].format(code=code)
    log_block = '\n'.join(LOG) if LOG else '  (no events yet)'
    print(frame + '\n' + log_block + '\n', flush=True)

for event in subscribe():
    kind = event.get('type')
    if kind == 'hello':
        log("connected to receiver", event['time'])
        draw('pressed' if event['pressed'] else 'idle', code='?')
    elif kind == 'press':
        log(f"press code={event['code']}", event['time'])
        draw('pressed', event['code'])
    elif kind == 'release':
        log(f"release after {event['duration']}s", event['time'])
        draw('idle')
