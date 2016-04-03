from collections import deque
import socket

from logger import logger
from messages import is_message, Message

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
                    logger.debug("Got empty string message, socket must be closed")
                    raise DeadSocketException("Socket Closed")

                return message.split("\n")
            except socket.timeout:
                logger.debug("Got timeout: " + str(attempt))
                # try again...
                pass

        logger.debug("Timed out completely")
        # if we run out of attempts, raise exception
        raise DeadSocketException("Timed out " + str(TIMEOUT_ATTEMPTS) + " times")


PRIVMSG_TEMPLATE = ":console!console@localhost PRIVMSG {nick} :{message}"

class ConsoleIrcConnection:

    def __init__(self, nick, server, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT):
        self.nick = nick
        self.server = server
        self.port = port
        self.timeout = timeout

    def connect(self):
        print("Connected")

    def send(self, line):
        if is_message(line):
            message = Message(line)
            print("-->", message.text, end="")
        else:
            print("###", line, end="")

    def read_line(self):
        try:
            line = input("==> ")
            return self._format_line(line)
        except EOFError:
            from bingobot import KillException
            print()
            raise KillException("Got EOF")

    def _format_line(self, line):
        return PRIVMSG_TEMPLATE.format(nick=self.nick, message=line)


