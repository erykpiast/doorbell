# Deploy

Scripts that copy the receiver code to the Raspberry Pi and run it as
systemd services.

| File | What it does |
| --- | --- |
| `deploy.sh` | Runs on your computer. Copies the receiver over SSH, then runs `install.sh` on the Pi. |
| `simulate.sh` | Runs on your computer. Runs `simulate.py` on the Pi over SSH, to test the clients without the radio. |
| `install.sh` | Runs on the Pi. Installs the dependency and one service for each `*.service` file, then restarts the services. |
| `doorbell.service` | Unit template for the receiver, `listen.py`. |
| `doorbell-chime.service` | Unit template for the chime client, `chime.py`. |

`install.sh` fills in the user and the directory in each template. To add a
client, add a `*.service` file here.

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
`~/doorbell`. The copy leaves out `sound_tools/`, `deploy.sh`, and
`simulate.sh`, because they run on your computer. Run the same command again
after each code change. It also restarts the services.

## What the services do

- `doorbell` runs `listen.py`. `doorbell-chime` runs `chime.py`.
- Both run as the SSH user, start on boot, and restart 3 seconds after a crash.
- A client reconnects by itself when the receiver restarts.

## Check and control the service

```
ssh erykpiast@doorbell.local
journalctl -u 'doorbell*' -f       # live logs of all services
systemctl status doorbell doorbell-chime   # state
sudo systemctl stop doorbell       # stop, for example before running listen.py by hand
sudo systemctl disable --now doorbell-chime   # no sound, and do not start on boot
python3 ~/doorbell/monitor.py      # terminal display, next to the services
```

Only one process can read the GPIO pin. Stop `doorbell` before you run
`listen.py` or `rx_probe.py` by hand.

## Test the chime without the radio

`simulate.py` takes the place of the receiver and sends fake presses. The
chime client connects to it by itself. Run it from your computer:

```
receiver/deploy/simulate.sh                # prompt: t = tap, t 3 = 3 taps, h 5 = hold 5 s, d/u = down/up, q = quit
receiver/deploy/simulate.sh "t 2" "h 5"    # run the commands, then exit
DOORBELL_HOST=pi@192.168.1.50 receiver/deploy/simulate.sh
```

The script stops the receiver for the session. On exit, also after Ctrl-C, it
starts the receiver again if it ran before. The same steps by hand:

```
ssh erykpiast@doorbell.local
sudo systemctl stop doorbell
python3 ~/doorbell/simulate.py     # prompt: t = tap, t 3 = 3 taps, h 5 = hold 5 s, d/u = down/up, q = quit
sudo systemctl start doorbell
```

The simulator refuses to start while the receiver runs.

## Change the chime settings

Use a drop-in file:

```
sudo systemctl edit doorbell-chime
# [Service]
# Environment=DOORBELL_SOUNDS=chime.wav,melody.wav,alarm_loud.wav
```
