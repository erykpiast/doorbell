# Deploy

Scripts that copy the receiver code to the Raspberry Pi and run it as a
systemd service.

| File | What it does |
| --- | --- |
| `deploy.sh` | Runs on your computer. Copies the receiver over SSH, then runs `install.sh` on the Pi. |
| `install.sh` | Runs on the Pi. Installs the dependency and the service, then restarts the service. |
| `doorbell.service` | Template of the systemd unit. `install.sh` fills in the user and the directory. |

## Requirements

- The Pi is reachable over SSH. The default address is `erykpiast@doorbell.local`.
- `rsync` is installed on your computer and on the Pi.
- The user on the Pi can run `sudo`.

## Deploy

```
receiver/deploy/deploy.sh
```

Use another host or another remote directory:

```
receiver/deploy/deploy.sh pi@192.168.1.50
DOORBELL_DIR=apps/doorbell receiver/deploy/deploy.sh
```

The remote directory is relative to the home directory. The default is
`~/doorbell`. The copy leaves out `sound_tools/`. Run the same command again
after each code change. It also restarts the service.

## What the service does

- It runs `listen.py` as the SSH user.
- It starts on boot.
- It restarts 3 seconds after a crash.

## Check and control the service

```
ssh erykpiast@doorbell.local
journalctl -u doorbell -f          # live logs
systemctl status doorbell          # state
sudo systemctl stop doorbell       # stop, for example before running listen.py by hand
sudo systemctl disable --now doorbell   # stop and do not start on boot
```

Only one process can read the GPIO pin. Stop the service before you run
`listen.py` or `rx_probe.py` by hand.
