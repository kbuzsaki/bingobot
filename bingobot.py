import socket
from datetime import timedelta
from termcolor import colored, cprint
from srlparser import Racer, Result
from botcommands import allCommands

def isPing(ircmsg):
    return "PING :" in ircmsg

def isMessage(ircmsg):
    return "PRIVMSG" in ircmsg

def hello(bot, msg):
    if msg.contains("Hello " + bot.nick):
        bot.sendmsg(msg.channel, "Hello, " + msg.sender + "!")

class NameException(Exception):
    pass

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


class BingoBot:
    def __init__(self, nick, server, channel, commands=[]):
        self.nick = nick
        self.server = server
        self.channel = channel
        self.commands = [hello] + commands
        self.ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.racers = dict()

    def connect(self):
        self.ircsock.connect((self.server, 6667))
        self.ircsock.send("USER " + self.nick + " " + self.nick + " " + self.nick + " :BingoBot yo\n")
        self.ircsock.send("NICK " + self.nick + "\n")

    def sendmsg(self, chan, msg):
        for line in msg.strip().split("\n"):
            self.ircsock.send("PRIVMSG " + chan + " :" + line + "\n")

    def joinchan(self, chan):
        self.ircsock.send("JOIN " + chan + "\n")

    def listen(self):
        while True:
            ircmsg = self.ircsock.recv(2048)
            ircmsg = str(ircmsg.strip('\n\r'))
            # pings are blue
            if isPing(ircmsg):
                print colored(ircmsg, "blue")
                pingmsg = ircmsg.split("PING :")[1]
                self.ircsock.send("PONG :" + pingmsg + "\n")
                print colored("RESPONDING TO PING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "blue")
            # chat messages are grey
            elif isMessage(ircmsg):
                print ircmsg
                msg = Message(ircmsg)
                for command in self.commands:
                    try:
                        command(self, msg)
                    except NameException as e:
                        print "Name Exception:" + str(e)
                        message = "There was a problem looking up data for " + str(e) + "."
                        self.sendmsg(msg.channel, message)
                    except Exception as e:
                        print e
                        self.sendmsg(msg.channel, "Something weird happened...")
            # all other messages are green
            else:
                print colored(ircmsg, "green")
            # weird hack thing for joining channels?
            if ircmsg.find("End of /MOTD"):
                self.joinchan(self.channel)

    def getRacer(self, channel, username, refresh=False):
        if (refresh or username not in self.racers):
            try:
                self.sendmsg(channel, "Loading data for " + username + "...")
                self.racers[username] = Racer(username)
            except:
                raise NameException(username)
        return self.racers[username]


# runs the bot

server = "irc2.speedrunslive.com"
channel = "#testest"
botnick = "TestBingoBot"

bingoBot = BingoBot(botnick, server, channel, commands = allCommands)
bingoBot.connect()
bingoBot.listen()

