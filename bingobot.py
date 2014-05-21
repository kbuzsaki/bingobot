import socket
import traceback
import re
from collections import deque
from datetime import timedelta
from termcolor import colored, cprint
from messages import Message, isMessage
from srlparser import Racer, Result

def isPing(ircmsg):
    return "PING :" in ircmsg

# users who can kill the bingobot using !kill
# this is devs, ops, and voices on #bingoleague
ADMINS = ["saltor", "saltor_"]
PRIVELAGED_USERS = ADMINS + ["gombill", "keymakr", "exodus", "balatee"]

channelPattern = re.compile("^#.+$")

def hello(bot, msg):
    if msg.contains("Hello " + bot.nick) or msg.contains("Hi " + bot.nick):
        bot.sendmsg(msg.channel, "Hello, " + msg.sender + "!")

# built in commands

def say(bot, msg):
    if msg.command == "!say":
        if msg.sender.lower() in ADMINS:
            if channelPattern.match(msg.arguments[0]):
                bot.sendmsg(msg.arguments[0], " ".join(msg.arguments[1:]))
            else:
                bot.sendmsg(msg.channel, " ".join(msg.arguments))

def command(bot, msg):
    if msg.command == "!command":
        if msg.sender.lower() in ADMINS:
            bot.send(" ".join(msg.arguments) + "\n")
             
def join(bot, msg):
    if msg.command == "!join":
        for argument in msg.arguments:
            if channelPattern.match(argument):
                bot.sendmsg(msg.channel, "Joining " + argument + "...")
                bot.joinchan(argument)
            else:
                bot.sendmsg(msg.channel, "Is \"" + argument + "\" a channel?") 
        

def leave(bot, msg):
    if msg.command == "!leave":
        if msg.channel != "#bingoleague":
            bot.sendmsg(msg.channel, "Leaving " + msg.channel + "...")
            bot.leavechan(msg.channel)
        else:
            message = "Error, cannot !leave #bingoleague. Ask an op or voice to /kick or !kill."
            bot.sendmsg(msg.channel, message)
    
builtinCommands = [hello, say, command, join, leave]

# end built in commands

class NameException(Exception):
    pass

class KillException(Exception):
    pass


class BingoBot:
    def __init__(self, nick, password, server, channels=[], commands=[]):
        self.nick = nick
        self.password = password
        self.server = server
        self.channels = channels
        self.commands = builtinCommands + commands
        self.messageQueue = deque()
        self.racers = dict()

    def send(self, s):
        print(colored("OUTGOING: " + s.strip(), "magenta"))
        self.ircsock.send(s.encode("latin-1"))

    def connect(self):
        self.ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ircsock.connect((self.server, 6667))
        self.send("USER " + self.nick + " " + self.nick + " " + self.nick + " :BingoBot yo\n")
        self.send("NICK " + self.nick + "\n")

    def sendmsg(self, chan, msg):
        for line in msg.strip().split("\n"):
            self.send("PRIVMSG " + chan + " :" + line + "\n")

    def joinchan(self, chan):
        self.send("JOIN " + chan + "\n")

    def leavechan(self, chan):
        self.send("PART " + chan + "\n")

    def listen(self):
        while True:
            # if messages are available, process them
            if(len(self.messageQueue) > 0):
                ircmsg = self.messageQueue.popleft()
                self.processLine(ircmsg)
            # otherwise, wait for a new batch of messages
            else:
                ircmsg = self.ircsock.recv(2048)
                ircmsg = ircmsg.decode("latin-1").strip()
                self.messageQueue.extend(ircmsg.split("\n"))

    def processLine(self, ircmsg):
        # pings are blue
        if isPing(ircmsg):
            print(colored(ircmsg, "blue"))
            pingmsg = ircmsg.split("PING :")[1]
            self.send("PONG :" + pingmsg + "\n")
        # chat messages are grey
        elif isMessage(ircmsg):
            print(ircmsg)
            self.processMessage(ircmsg)
        # if there's SOMETHING there
        elif len(ircmsg) > 0:
            print(colored(ircmsg, "green"))
        # else, must be disconnected
        else:
            print(colored("Disconnected from server?", "yellow"))
            return

        # weird hack thing for joining channels?
        if "End of /MOTD" in ircmsg:
            for channel in self.channels:
                self.joinchan(channel)
        # weird hack thing for nickserv identify
        if "NickServ" in ircmsg and "/msg NickServ IDENTIFY" in ircmsg:
            self.sendmsg("NickServ", "IDENTIFY " + self.password)

    def processMessage(self, ircmsg):
        msg = Message(ircmsg)
        # ignore anything from #speedrunslive to avoid flooding it accidentally
        if msg.channel == "#speedrunslive":
            pass
        # kill command to force disconnect the bot from the server
        # WARNING: the bot will not reconnect until manually reset
        elif msg.command == "!kill" :
            print(colored("Kill request detected from " + msg.sender.lower(), "yellow"))
            if msg.sender.lower() in PRIVELAGED_USERS:
                # actually kills the bot if the sender is privelaged
                self.send("QUIT Kill requested by " + msg.sender + "\n")
                raise KillException
        else:
            for command in self.commands:
                try:
                    command(self, msg)
                except NameException as e:
                    print(colored(traceback.format_exc(), "red"))
                    message = "There was a problem looking up data for " + str(e) + ". "
                    message += "Do they have an SRL profile?"
                    self.sendmsg(msg.channel, message)
                except Exception as e:
                    print(colored(traceback.format_exc(), "red"))
                    self.sendmsg(msg.channel, "Something weird happened...")

    def getRacer(self, channel, username, refresh=False):
        username = username.lower()
        if (refresh or username not in self.racers):
            try:
                self.sendmsg(channel, "Loading data for " + username + "...")
                self.racers[username] = Racer(username)
            except:
                raise NameException(username)
        return self.racers[username]


