#!/usr/bin/env python3
"""Probe the 433 MHz receiver on GPIO17: count edges for a few seconds and
print a histogram of HIGH pulse lengths. A sender with PT2262 timing shows
up as peaks near 350 us and 1050 us. Usage: rx_probe.py [seconds]"""
import sys
import time
import lgpio
from collections import Counter

GPIO_PIN = 17
SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 5
BUCKET = 100  # us

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, GPIO_PIN)

highs = Counter()
edges = 0
last = lgpio.gpio_read(h, GPIO_PIN)
last_t = time.monotonic_ns()
end = last_t + int(SECONDS * 1e9)
while True:
    now = time.monotonic_ns()
    if now > end:
        break
    v = lgpio.gpio_read(h, GPIO_PIN)
    if v != last:
        if last == 1:
            highs[(now - last_t) // 1000 // BUCKET * BUCKET] += 1
        edges += 1
        last, last_t = v, now
lgpio.gpiochip_close(h)

print(f"edges in {SECONDS:g} s: {edges}, level now: {last}")
print("HIGH pulse lengths (us bucket: count), top 10:")
for bucket, count in sorted(highs.most_common(10)):
    mark = "  <- SHORT" if 200 <= bucket < 500 else "  <- LONG" if 900 <= bucket < 1200 else ""
    print(f"  {bucket:>6}-{bucket + BUCKET - 1:<6} {count}{mark}")
