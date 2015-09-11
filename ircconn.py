import socket
from collections import deque

DEFAULT_PORT = 6667
DEFAULT_TIMEOUT = 120

ENCODING = "latin-1"
BUFFER_SIZE = 2048

TIMEOUT_ATTEMPTS = 5

class DeadSocketException(Exception):
    pass

class IrcConnection:

    def __init__(self, nick, server, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT):
        self.nick = nick
        self.server = server
        self.port = port
        self.timeout = timeout

        self.message_queue = deque()

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        self.socket.connect((self.server, self.port))
        self.send("USER " + self.nick + " " + self.nick + " " + self.nick + " :BingoBot yo\n")
        self.send("NICK " + self.nick + "\n")

    def send(self, message):
        self.socket.send(message.encode(ENCODING))

    def read_line(self):
        if not self.message_queue:
            lines = self._read_lines()
            self.message_queue.extend(lines)

        return self.message_queue.popleft()

    def _read_lines(self):
        for attempt in range(TIMEOUT_ATTEMPTS):
            try:
                message = self.socket.recv(BUFFER_SIZE).decode(ENCODING).strip()

                # empty string means closed socket, so exit
                if not message:
                    raise DeadSocketException("Socket Closed")

                return message.split("\n")
            except socket.timeout:
                # try again...
                pass
        else:
            raise DeadSocketException("Timed out " + str(TIMEOUT_ATTEMPTS) + " times")


class ConsoleIrcConnection:
    pass

