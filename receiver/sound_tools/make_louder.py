#!/usr/bin/env python3
"""Make a quiet WAV louder: apply gain, then a soft limiter (tanh) so peaks
round off instead of clipping hard. Usage: make_louder.py in.wav out.wav [gain_db]"""
import sys
import wave
import struct
import math

src, dst = sys.argv[1], sys.argv[2]
gain = 10 ** (float(sys.argv[3] if len(sys.argv) > 3 else 12) / 20)

with wave.open(src) as w:
    params = w.getparams()
    data = w.readframes(w.getnframes())
samples = struct.unpack("<%dh" % (len(data) // 2), data)

# tanh(x) is ~x for small values and approaches 1.0 for large ones.
out = [int(32767 * 0.98 * math.tanh(gain * s / 32767)) for s in samples]

with wave.open(dst, "w") as w:
    w.setparams(params)
    w.writeframes(struct.pack("<%dh" % len(out), *out))
print(f"Wrote {dst}")
