"""Doorbell event bus. The receiver broadcasts events, clients subscribe.

Transport: a Unix stream socket at DOORBELL_SOCKET (default /tmp/doorbell.sock).
The server sends one JSON object per line. Clients send nothing.

Events (`time` is Unix time in seconds):
  {"type": "hello", "pressed": false, "time": 1729700000.0}
      The first line after each connect. `pressed` is the current button state.
  {"type": "press", "code": "0xA55A5A", "time": 1729700000.0}
  {"type": "release", "code": "0xA55A5A", "time": 1729700001.2, "duration": 0.7}
      `duration` is the time between the first and the last decoded frame.
"""
import json
import os
import socket
import threading
import time

SOCKET_PATH = os.environ.get('DOORBELL_SOCKET', '/tmp/doorbell.sock')
SEND_TIMEOUT = 0.5  # s; a client that does not read for this long is dropped


def _server_alive(path):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        try:
            s.connect(path)
            return True
        except OSError:
            return False


class EventServer:
    def __init__(self, path=SOCKET_PATH):
        self.path = path
        self.clients = []
        self.pressed = False
        self.lock = threading.Lock()
        if _server_alive(path):
            raise RuntimeError(f"another event server is running on {path}")
        try:
            os.unlink(path)  # stale socket from a crash
        except FileNotFoundError:
            pass
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(path)
        self.sock.listen()
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return  # socket closed
            conn.settimeout(SEND_TIMEOUT)
            # hold the lock so that no event goes out between hello and the
            # moment the client joins the list
            with self.lock:
                hello = {'type': 'hello', 'pressed': self.pressed, 'time': time.time()}
                if self._send(conn, hello):
                    self.clients.append(conn)

    @staticmethod
    def _send(conn, event):
        try:
            conn.sendall((json.dumps(event) + '\n').encode())
            return True
        except OSError:
            conn.close()
            return False

    def publish(self, event):
        with self.lock:
            if event['type'] in ('press', 'release'):
                self.pressed = event['type'] == 'press'
            self.clients = [c for c in self.clients if self._send(c, event)]

    def close(self):
        self.sock.close()
        with self.lock:
            for c in self.clients:
                c.close()
            self.clients = []
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass


def subscribe(path=SOCKET_PATH, retry=1.0):
    """Yield events forever. Reconnect when the receiver restarts.

    After each (re)connect the first event is `hello`. Use it to reset state:
    a `release` can get lost while the client is disconnected.
    """
    waiting = False
    while True:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(path)
                waiting = False
                for line in s.makefile('r', encoding='utf-8'):
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            if not waiting:
                print(f"events: no receiver at {path} ({e}), retrying", flush=True)
                waiting = True
        time.sleep(retry)
