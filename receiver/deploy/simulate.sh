#!/usr/bin/env bash
# Run simulate.py on the Raspberry Pi to test the clients without the radio.
# Stops the receiver for the session and starts it again on exit, if it ran.
# Usage: simulate.sh [command...]    (no commands: interactive prompt)
#   simulate.sh                      # prompt: t, t 3, h 5, d, u, q
#   simulate.sh "t 2" "h 5"          # run the commands, then exit
# Override the host with DOORBELL_HOST (default: erykpiast@doorbell.local)
# and the remote directory with DOORBELL_DIR (default: ~/doorbell).
set -euo pipefail

HOST="${DOORBELL_HOST:-erykpiast@doorbell.local}"
REMOTE_DIR="${DOORBELL_DIR:-doorbell}"

ARGS=""
if [ $# -gt 0 ]; then
  ARGS="$(printf ' %q' "$@")"
fi

ssh -t "$HOST" "
  cd '$REMOTE_DIR' || exit 1
  if systemctl is-active --quiet doorbell; then
    sudo systemctl stop doorbell
    trap 'echo \"=== Start receiver ===\"; sudo systemctl start doorbell' EXIT
  fi
  python3 simulate.py$ARGS
"
