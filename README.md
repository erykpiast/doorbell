# Doorbell

A wireless add-on for an existing 230 V doorbell. When someone presses the
button, a small radio sender inside the apartment transmits a signal. A
Raspberry Pi in the local network receives it and broadcasts a press event.
Clients subscribe to the events. The chime client plays a sound. The planned
next client pushes the event to web clients on the LAN.

The goal is the simplest and cheapest design that uses common parts available
in Poland. The sender needs no batteries and no rewiring of the button.

## How it works

```mermaid
flowchart LR
  btn[Doorbell button 230V] -->|powers only while pressed| sender[Sender: ATtiny85 + FS1000A]
  sender -->|433 MHz OOK radio| rx[Receiver: SYN480R]
  rx -->|GPIO17| pi[Raspberry Pi Zero: listen.py]
  pi -->|events socket| chime[Chime client: chime.py]
  chime --> amp[MAX98357A + speaker]
  pi -->|events socket| monitor[Monitor client: monitor.py]
  pi -.->|planned| push[Web push client]
```

The dashed arrow is not built yet. See
[`spec/003_event_bus.md`](spec/003_event_bus.md) for the event protocol.

## Repository layout

| Path | Content |
| --- | --- |
| `sender/doorbell_sender.ino` | Arduino firmware for the ATtiny85 |
| `receiver/listen.py` | Decoder. Broadcasts press and release events |
| `receiver/events.py` | Event bus: the server for `listen.py`, `subscribe()` for clients |
| `receiver/chime.py` | Client that plays a sound. Holds the press pattern rules |
| `receiver/monitor.py` | Client that shows the doorbell state in the terminal |
| `receiver/simulate.py` | Sends fake press events, to test clients without the radio |
| `receiver/*.wav` | Sounds that `chime.py` plays |
| `receiver/deploy/` | Scripts that copy the receiver to the Pi and install the service |
| `receiver/sound_tools/` | Scripts that generate and amplify the sounds |
| `receiver/rx_probe.py`, `test_dac.sh` | Hardware debug tools for the radio and the DAC |
| `spec/` | Design documents |

## Specs

1. [`spec/001_initial/spec.md`](spec/001_initial/spec.md): the original
   requirements.
2. [`spec/001_initial/plan.md`](spec/001_initial/plan.md): the first design
   plan, with wiring, parts list, and programming steps. Some assumptions
   changed during the build.
3. [`spec/002_build.md`](spec/002_build.md): what was built, the final
   design, and the lessons learned. This file takes priority over the plan.
4. [`spec/003_event_bus.md`](spec/003_event_bus.md): the split of the
   receiver into an event broadcaster and clients.

Start with `spec/002_build.md` for the current design.
