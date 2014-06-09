import socket
import traceback
import pickle
import os
from collections import deque
from datetime import timedelta
from termcolor import colored, cprint
from messages import Message, isMessage
from srlparser import Racer, Result
from botcommands import builtinCommands
from blacklist import Blacklist, FilteredRacer

def isPing(ircmsg):
    return "PING :" in ircmsg

# users with !say and !command privelages, very dangerous
ADMINS = ["saltor", "saltor_"]

# ops file name
# has names of users who can !kill and !blacklist
OPS_FILE = "ops"

# blacklist file name
# has ids of blacklisted races
BLACKLIST_FILE = "blacklist"

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
        self.blacklist = Blacklist(BLACKLIST_FILE)

        # load from config files
        if os.path.exists(OPS_FILE):
            with open(OPS_FILE, "rb") as opsFile:
                self.ops = pickle.load(opsFile)
        else:
            self.ops = set()

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
        elif msg.command == "!kill":
            print(colored("Kill request detected from " + msg.sender.lower(), "yellow"))
            if self.hasOp(msg.sender):
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
                self.racers[username] = FilteredRacer(username, self.blacklist)
            except:
                raise NameException(username)
        return self.racers[username]

    def hasAdmin(self, name):
        return name.lower() in ADMINS

    def hasOp(self, name):
        return name.lower() in self.ops or self.hasAdmin(name)

    def addOp(self, name):
        self.ops.add(name.lower())
        self.saveOps()

    def removeOp(self, name):
        self.ops.remove(name.lower())
        self.saveOps()

    def saveOps(self):
        with open(OPS_FILE, "wb") as opsFile:
            pickle.dump(self.ops, opsFile)


