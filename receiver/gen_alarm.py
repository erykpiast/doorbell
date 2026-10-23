#!/usr/bin/env python3
"""Generate a scream-like 'roughness' alarm tone: a carrier in the ear's most
sensitive range (2-5 kHz) amplitude-modulated at 30-150 Hz, the acoustic
feature that makes screams uniquely alarming (Arnal et al., 2015)."""
import wave
import struct
import math

SAMPLE_RATE = 44100
DURATION = 2.0
CARRIER_FREQ = 3500.0   # Hz, peak of ear-canal resonance sensitivity
MOD_FREQ = 70.0         # Hz, "roughness" modulation rate (30-150 Hz range)
MOD_DEPTH = 0.8         # how deep the amplitude modulation goes


def main():
    n = int(SAMPLE_RATE * DURATION)
    samples = []
    fade = int(SAMPLE_RATE * 0.02)  # 20ms fade in/out
    for i in range(n):
        t = i / SAMPLE_RATE
        carrier = math.sin(2 * math.pi * CARRIER_FREQ * t)
        mod = 1.0 - MOD_DEPTH * (0.5 * (1 + math.sin(2 * math.pi * MOD_FREQ * t)))
        amp = 0.6
        if i < fade:
            amp *= i / fade
        elif i > n - fade:
            amp *= (n - i) / fade
        val = amp * mod * carrier
        samples.append(int(max(-1.0, min(1.0, val)) * 32767))

    with wave.open("alarm.wav", "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        packed = struct.pack("<" + "h" * len(samples), *samples)
        wav_file.writeframes(packed)

    print(f"Wrote alarm.wav ({DURATION:.2f}s)")


if __name__ == "__main__":
    main()
