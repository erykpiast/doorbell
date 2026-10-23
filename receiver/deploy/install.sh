#!/usr/bin/env bash
# Runs on the Raspberry Pi. Installs the dependencies and the systemd services
# (one unit for each deploy/*.service file), then (re)starts them.
# deploy.sh calls this script over SSH.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! python3 -c 'import lgpio' 2>/dev/null; then
  echo "=== Install rpi-lgpio ==="
  pip3 install rpi-lgpio --break-system-packages
fi

UNITS=()
for TEMPLATE in "$DIR"/deploy/*.service; do
  UNIT="$(basename "$TEMPLATE")"
  UNITS+=("$UNIT")
  echo "=== Write /etc/systemd/system/$UNIT ==="
  sed -e "s#@USER@#$USER#" -e "s#@DIR@#$DIR#g" "$TEMPLATE" \
    | sudo tee "/etc/systemd/system/$UNIT" >/dev/null
done

sudo systemctl daemon-reload
sudo systemctl enable "${UNITS[@]}"
sudo systemctl restart "${UNITS[@]}"

sleep 1
systemctl --no-pager --lines=5 status "${UNITS[@]}" || true
echo "Logs: journalctl -u 'doorbell*' -f"
