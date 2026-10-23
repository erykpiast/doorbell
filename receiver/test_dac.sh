#!/usr/bin/env bash
set -euo pipefail

echo "=== MAX98357A DAC test ==="
echo ""

echo "--- ALSA devices ---"
aplay -l
echo ""

# Find the card index for the MAX98357A
CARD=$(aplay -l | awk '/MAX98357A/{gsub(/[^0-9].*/,"",$2); print $2; exit}' | tr -d ':')

if [[ -z "$CARD" ]]; then
  echo "ERROR: MAX98357A not found in aplay -l"
  echo "Check: dtoverlay=max98357a is in /boot/config.txt and the Pi has been rebooted."
  exit 1
fi

echo "Found MAX98357A on card $CARD"
echo ""

echo "--- Playing 440 Hz sine tone for 3 seconds (you should hear it from the speaker) ---"
speaker-test -D "plughw:${CARD},0" -t sine -f 440 -c 1

echo ""
echo "DAC test complete."
