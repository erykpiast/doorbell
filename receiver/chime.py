"""Chime client: plays a sound for doorbell events from the receiver.

The rules live in `Series` and `choose_sound()`. Change them to get other
patterns. The defaults:
- A press starts a new series when the last release was more than
  DOORBELL_SERIES_GAP seconds ago.
- The Nth press of a series plays the Nth sound of DOORBELL_SOUNDS. Later
  presses play the last sound. A new press stops the current sound.
- While the button stays pressed, the sound repeats, for at most
  DOORBELL_MAX_HOLD seconds.
"""
import os
import re
import subprocess
import threading
import time

from events import subscribe

HERE = os.path.dirname(os.path.abspath(__file__))
SOUNDS = os.environ.get('DOORBELL_SOUNDS', 'chime.wav,melody.wav').split(',')
SERIES_GAP = float(os.environ.get('DOORBELL_SERIES_GAP', '10'))  # s
MAX_HOLD = float(os.environ.get('DOORBELL_MAX_HOLD', '30'))       # s


class Series:
    """Press history of one visitor: presses close together in time."""

    def __init__(self, gap):
        self.gap = gap
        self.count = 0              # presses in the current series
        self.held = False
        self.pressed_at = None      # monotonic time of the current press
        self.last_release = None    # event time of the last release

    def press(self, t):
        if self.last_release is None or t - self.last_release > self.gap:
            self.count = 0
        self.count += 1
        self.held = True
        self.pressed_at = time.monotonic()

    def release(self, t):
        self.held = False
        self.last_release = t

    def reset(self, pressed):
        """Sync with the receiver after a (re)connect."""
        self.held = pressed


def choose_sound(series):
    return SOUNDS[min(series.count, len(SOUNDS)) - 1]


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


class Player:
    """Plays one sound at a time. A new play() stops the current sound."""

    def __init__(self, device):
        self.device = device
        self.proc = None
        self.generation = 0
        self.lock = threading.Lock()

    def play(self, path, repeat_while=lambda: False):
        if self.device is None:
            print("chime: no MAX98357A DAC found, skipping playback", flush=True)
            return
        with self.lock:
            self.generation += 1
            self._stop()
            gen = self.generation
        threading.Thread(target=self._loop, args=(gen, path, repeat_while), daemon=True).start()

    def _stop(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()

    def _loop(self, gen, path, repeat_while):
        while True:
            with self.lock:
                if gen != self.generation:
                    return
                self.proc = subprocess.Popen(
                    ['aplay', '-D', self.device, path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                proc = self.proc
            proc.wait()
            if not repeat_while():
                return


def main():
    card = find_dac_card()
    player = Player(None if card is None else f'plughw:{card},0')
    series = Series(SERIES_GAP)

    def still_held():
        return series.held and time.monotonic() - series.pressed_at < MAX_HOLD

    print(f"chime: sounds={SOUNDS} series_gap={SERIES_GAP}s max_hold={MAX_HOLD}s", flush=True)
    for event in subscribe():
        kind = event.get('type')
        if kind == 'hello':
            series.reset(event['pressed'])
        elif kind == 'press':
            series.press(event['time'])
            sound = choose_sound(series)
            print(f"chime: press #{series.count}, playing {sound}", flush=True)
            player.play(os.path.join(HERE, sound), repeat_while=still_held)
        elif kind == 'release':
            series.release(event['time'])


if __name__ == '__main__':
    main()
