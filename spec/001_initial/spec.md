We need the simplest electronic circuit with two main components:

1. Sender
2. Receiver

## Sender

1. There is a physical push button connected to 230V AC
2. When the button is pushed, it gives power to the sender component (5V DC), which is normally off
3. When the component is turned on, it immediately triggers a radio signal at some common frequency for low-range communication

## Receiver

1. It's always on, connected to 5V DC
2. It listens at the radio frequency of the sender
3. It's a mini-computer such as minimal-spec Raspberry PI or similar that has access to local network through Wi-Fi or Ethernet
4. It hosts a web server that can send push notifications to connected clients when it reviews the radio signal

Let's plan for the simplest possible design that uses only common components easily available to buy, and integrate. It should be cost-efficient too.

Output Mermaid diagram syntax with the design explained on several levels:

* high level (sender-receiver relation)
* sender details - including specific electronic components to use and detailed wiring
* receiver details - including the mini-computer - radio integration both software and hardware
* sever-client communication protocols and design

I'm based in Poland, so take into account what electronic components are available to buy here.