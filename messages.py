import re
from datetime import timedelta

def isMessage(ircmsg):
    return "PRIVMSG" in ircmsg

wordPattern = re.compile("^[a-zA-Z_][a-zA-Z_0-9]+$")
numberPattern = re.compile("^\d+$")
timePattern = re.compile("^\d?\d:\d\d(:\d\d)?$")

def parseTime(timestr):
    data = timestr.split(":")
    hours = int(data[0])
    minutes = int(data[1])
    seconds = float(data[2]) if len(data) > 2 else 0.0
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)

class Message:
    def __init__(self, ircmsg):
        if not isMessage(ircmsg):
            raise Exception("improperly detected message: " + ircmsg)
        messageInfo = ircmsg[1:].split(":")[0].strip()
        self.sender = messageInfo.split("!")[0]
        # after the first hash but before any following spaces
        self.channel = messageInfo.split(" ")[-1] if "#" in messageInfo else self.sender
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
        return [argument for argument in self.arguments if wordPattern.match(argument)]

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
        return [int(argument) for argument in self.arguments if numberPattern.match(argument)]

    @property
    def minimum(self):
        return self.numbers[0] if len(self.numbers) > 1 else 0

    @property
    def maximum(self):
        return self.getMaximum()

    def getMaximum(self, default=10):
        if len(self.numbers) > 1:
            return self.numbers[1]
        elif len(self.numbers) > 0:
            return self.numbers[0]
        else:
            return default

    @property
    def times(self):
        return [parseTime(arg) for arg in self.arguments if timePattern.match(arg)]

    @property
    def refresh(self):
        return "refresh" in self.arguments

    @property
    def detailed(self):
        return "detailed" in self.arguments
                   
