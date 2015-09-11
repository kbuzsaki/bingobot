from datetime import timedelta
import re

def is_message(ircmsg):
    return "PRIVMSG" in ircmsg

WORD_PATTERN = re.compile("^[a-zA-Z_][a-zA-Z_0-9]+$")
NUMBER_PATTERN = re.compile("^\d+$")
TIME_PATTERN = re.compile("^\d?\d:\d\d(:\d\d)?$")

def parse_time(timestr):
    data = timestr.split(":")
    hours = int(data[0])
    minutes = int(data[1])
    seconds = float(data[2]) if len(data) > 2 else 0.0
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)

class Message:
    def __init__(self, ircmsg):
        if not is_message(ircmsg):
            raise Exception("improperly detected message: " + ircmsg)
        message_info = ircmsg[1:].split(":")[0].strip()
        self.sender = message_info.split("!")[0]
        # after the first hash but before any following spaces
        self.channel = message_info.split(" ")[-1] if "#" in message_info else self.sender
        self.text = ircmsg[1:].split(":", 1)[1]

    def contains(self, string):
        return self.text.find(string) != -1

    @property
    def elements(self):
        return self.text.split(" ")

    @property
    def command(self):
        return self.elements[0]

    @property
    def arguments(self):
        return self.elements[1:]

    @property
    def words(self):
        return [argument for argument in self.arguments if WORD_PATTERN.match(argument)]

    @property
    def usernames(self):
        words = self.words
        if "refresh" in words:
            words.remove("refresh")
        if "detailed" in words:
            words.remove("detailed")
        return words

    @property
    def username(self):
        if len(self.usernames) > 0:
            return self.usernames[0]
        else:
            return self.sender

    @property
    def numbers(self):
        return [int(argument) for argument in self.arguments if NUMBER_PATTERN.match(argument)]

    @property
    def minimum(self):
        return self.numbers[0] if len(self.numbers) > 1 else 0

    @property
    def maximum(self):
        return self.get_maximum()

    def get_maximum(self, default=10):
        if len(self.numbers) > 1:
            return self.numbers[1]
        elif len(self.numbers) > 0:
            return self.numbers[0]
        else:
            return default

    @property
    def times(self):
        return [parse_time(arg) for arg in self.arguments if TIME_PATTERN.match(arg)]

    @property
    def refresh(self):
        return "refresh" in self.arguments

    @property
    def detailed(self):
        return "detailed" in self.arguments

