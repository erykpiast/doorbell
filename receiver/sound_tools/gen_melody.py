#!/usr/bin/env python3
import wave
import struct
import math

SAMPLE_RATE = 44100
NOTE_DURATION = 0.4  # seconds
GAP = 0.05  # seconds of silence between notes

NOTE_FREQS = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25,
}

# Twinkle Twinkle Little Star
MELODY = [
    "C4", "C4", "G4", "G4", "A4", "A4", "G4",
    "F4", "F4", "E4", "E4", "D4", "D4", "C4",
]


def note_samples(freq, duration):
    n = int(SAMPLE_RATE * duration)
    samples = []
    fade = max(1, int(SAMPLE_RATE * 0.01))  # 10ms fade in/out to avoid clicks
    for i in range(n):
        t = i / SAMPLE_RATE
        amp = 0.5
        if i < fade:
            amp *= i / fade
        elif i > n - fade:
            amp *= (n - i) / fade
        val = amp * math.sin(2 * math.pi * freq * t)
        samples.append(int(val * 32767))
    return samples


def silence_samples(duration):
    return [0] * int(SAMPLE_RATE * duration)


def main():
    all_samples = []
    for note in MELODY:
        all_samples.extend(note_samples(NOTE_FREQS[note], NOTE_DURATION))
        all_samples.extend(silence_samples(GAP))

    with wave.open("melody.wav", "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        packed = struct.pack("<" + "h" * len(all_samples), *all_samples)
        wav_file.writeframes(packed)

    print(f"Wrote melody.wav ({len(all_samples) / SAMPLE_RATE:.2f}s)")


if __name__ == "__main__":
    main()
