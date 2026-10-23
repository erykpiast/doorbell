#!/usr/bin/env bash
# Runs on the Raspberry Pi. Installs the dependencies and the systemd service,
# then (re)starts it. deploy.sh calls this script over SSH.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT=/etc/systemd/system/doorbell.service

if ! python3 -c 'import lgpio' 2>/dev/null; then
  echo "=== Install rpi-lgpio ==="
  pip3 install rpi-lgpio --break-system-packages
fi

echo "=== Write $UNIT ==="
sed -e "s#@USER@#$USER#" -e "s#@DIR@#$DIR#g" "$DIR/deploy/doorbell.service" \
  | sudo tee "$UNIT" >/dev/null

sudo systemctl daemon-reload
sudo systemctl enable doorbell.service
sudo systemctl restart doorbell.service

sleep 1
systemctl --no-pager --lines=5 status doorbell.service || true
echo "Logs: journalctl -u doorbell -f"
