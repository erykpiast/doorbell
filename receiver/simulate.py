"""Simulator: sends fake doorbell events, to test clients without the radio.

It takes the place of listen.py on the event socket. Stop the receiver first:
    sudo systemctl stop doorbell
    python3 simulate.py                  # interactive prompt
    python3 simulate.py "t 2" "h 5"      # run commands, then exit
    sudo systemctl start doorbell

Commands:
    t [n] [gap]   tap n times (default 1), gap s between taps (default 1)
    h [s]         hold for s seconds (default 3)
    d             press down and keep the button pressed
    u             release
    q             quit (Ctrl-D also works)
"""
import readline  # noqa: F401 -- line editing and history for input()
import sys
import time

from events import EventServer

CODE = '0xA55A5A'
TAP = 0.2  # s, a short press

try:
    server = EventServer()
except RuntimeError as e:
    sys.exit(f"{e}\nStop the receiver first: sudo systemctl stop doorbell")

pressed_at = None

def press():
    global pressed_at
    if pressed_at is not None:
        print("already pressed")
        return
    pressed_at = time.monotonic()
    server.publish({'type': 'press', 'code': CODE, 'time': time.time()})
    print(f"press   ({len(server.clients)} clients)")

def release():
    global pressed_at
    if pressed_at is None:
        print("not pressed")
        return
    duration = round(time.monotonic() - pressed_at, 3)
    pressed_at = None
    server.publish({'type': 'release', 'code': CODE, 'time': time.time(),
                    'duration': duration})
    print(f"release after {duration}s")

def hold(seconds):
    press()
    time.sleep(seconds)
    release()

def tap(n=1, gap=1.0):
    for i in range(int(n)):
        if i:
            time.sleep(gap)
        hold(TAP)

def run(line):
    """Run one command. Return False to quit."""
    cmd, *args = line.split() or ['']
    try:
        args = [float(a) for a in args]
        if cmd == 't':
            tap(*args)
        elif cmd == 'h':
            hold(*args or [3])
        elif cmd == 'd':
            press()
        elif cmd == 'u':
            release()
        elif cmd == 'q':
            return False
        elif cmd:
            print(__doc__[__doc__.index('Commands:'):])
    except (ValueError, TypeError):
        print(f"bad arguments: {line}")
    return True

time.sleep(1.5)  # clients retry once per second; let them connect
print(f"events on {server.path}, {len(server.clients)} clients connected")

try:
    if len(sys.argv) > 1:
        for line in sys.argv[1:]:
            print(f"> {line}")
            run(line)
        time.sleep(0.5)
    else:
        print("Commands: t [n] [gap], h [s], d, u, q")
        while True:
            try:
                line = input('> ')
            except EOFError:
                break
            if not run(line):
                break
except KeyboardInterrupt:
    pass
finally:
    if pressed_at is not None:
        release()
    server.close()
