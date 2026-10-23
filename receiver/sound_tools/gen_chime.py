#!/usr/bin/env python3
"""Generate a classic two-note 'ding-dong' doorbell chime with a bell timbre.

Notes are one octave above the usual E5/C5 chime, because the small YD27
speaker reproduces little below ~800 Hz. The result is normalized close to
full scale so it plays as loud as the DAC allows."""
import wave
import struct
import math

SAMPLE_RATE = 44100
DING_FREQ = 1318.51   # E6
DONG_FREQ = 1046.50   # C6
DONG_START = 0.55     # seconds after the ding
DURATION = 2.4
PEAK = 0.95           # leave a little headroom below full scale

# (frequency ratio, relative amplitude, decay time constant in seconds)
PARTIALS = [
    (1.0, 1.00, 0.70),
    (2.0, 0.45, 0.35),
    (3.0, 0.20, 0.20),
    (4.2, 0.08, 0.12),  # slightly inharmonic, gives the metallic shimmer
]


def strike(freq, t):
    if t < 0:
        return 0.0
    attack = min(1.0, t / 0.003)  # 3 ms attack avoids a click
    return attack * sum(
        amp * math.exp(-t / tau) * math.sin(2 * math.pi * freq * ratio * t)
        for ratio, amp, tau in PARTIALS
    )


def main():
    n = int(SAMPLE_RATE * DURATION)
    raw = []
    for i in range(n):
        t = i / SAMPLE_RATE
        raw.append(strike(DING_FREQ, t) + strike(DONG_FREQ, t - DONG_START))

    scale = PEAK / max(abs(v) for v in raw)
    fade = int(SAMPLE_RATE * 0.05)  # 50 ms fade-out at the very end
    samples = []
    for i, v in enumerate(raw):
        if i > n - fade:
            v *= (n - i) / fade
        samples.append(int(v * scale * 32767))

    with wave.open("chime.wav", "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(struct.pack("<" + "h" * len(samples), *samples))

    print(f"Wrote chime.wav ({DURATION:.2f}s)")


if __name__ == "__main__":
    main()
