from datetime import datetime

from termcolor import colored

ERROR_COLOR = "red"
DEBUG_COLOR = "yellow"
INCOMING_INFO_COLOR = "green"
INCOMING_PING_COLOR = "blue"
OUTGOING_COLOR = "magenta"


class Logger:
    """Basic colorizing logger. Prints to terminal by default."""

    def _log(self, message, color=None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(colored(now + " - " + message, color))

    def log(self, message):
        self._log(message)

    def error(self, message, e=None):
        self._log(message, ERROR_COLOR)

    def debug(self, message):
        self._log(message, DEBUG_COLOR)

    def incoming_info(self, message):
        self._log(message, INCOMING_INFO_COLOR)

    def incoming_ping(self, message):
        self._log(message, INCOMING_PING_COLOR)

    def outgoing(self, message):
        self._log(message, OUTGOING_COLOR)

logger = Logger()
