import socket
import traceback
import pickle
import os
from collections import deque
from datetime import datetime, timedelta
from termcolor import colored, cprint
from messages import Message, is_message
from srlparser import Racer, Result
from blacklist import Blacklist
from racercache import RacerCache, NameException

TIMEOUT_SECONDS = 120

def is_ping(ircmsg):
    return "PING :" in ircmsg

# users with !say and !command privelages, very dangerous
ADMINS = ["saltor", "saltor_"]

# ops file name
# has names of users who can !kill and !blacklist
OPS_FILE = "data/ops"

# blacklist file name
# has ids of blacklisted races
BLACKLIST_FILE = "data/blacklist"

RACER_CACHE_FILE = "data/racercache"

class KillException(Exception):
    pass


class BingoBot:

    def __init__(self, nick, password, server, channels=[], commands=[]):
        self.nick = nick
        self.password = password
        self.server = server
        self.channels = channels
        self.commands = commands
        self.message_queue = deque()
        self.blacklist = Blacklist(BLACKLIST_FILE)
        self.racer_cache = RacerCache(RACER_CACHE_FILE)

        # load from config files
        if os.path.exists(OPS_FILE):
            with open(OPS_FILE, "rb") as ops_file:
                self.ops = pickle.load(ops_file)
        else:
            self.ops = set()

    def send(self, s):
        now = str(datetime.now())
        print(colored(now + " - OUTGOING: " + s.strip(), "magenta"))
        self.ircsock.send(s.encode("latin-1"))

    def connect(self):
        self.ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ircsock.settimeout(TIMEOUT_SECONDS)
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
        num_timeouts = 0
        while True:
            # if messages are available, process them
            if(len(self.message_queue) > 0):
                ircmsg = self.message_queue.popleft()
                self.process_line(ircmsg)
            # otherwise, wait for a new batch of messages
            else:
                try:
                    ircmsg = self.ircsock.recv(2048)

                    # empty string means closed socket, so exit
                    if not ircmsg:
                        print(colored("*************************************", "red"))
                        print(colored("SOCKET CLOSED", "red"))
                        print(colored("*************************************", "red"))
                        return

                    ircmsg = ircmsg.decode("latin-1").strip()
                    self.message_queue.extend(ircmsg.split("\n"))
                    num_timeouts = 0
                except socket.timeout:
                    num_timeouts += 1
                    print(colored("*************************************", "red"))
                    print(colored("TIMED OUT AFTER " + str(TIMEOUT_SECONDS) + " seconds (" + str(num_timeouts) + " times)", "red"))
                    print(colored("*************************************", "red"))
                    if num_timeouts >= 5:
                        print(colored("Giving up and attempting to reconnect...", "red"))
                        return

    def process_line(self, ircmsg):
        # pings are blue
        if is_ping(ircmsg):
            print(colored(ircmsg, "blue"))
            pingmsg = ircmsg.split("PING :")[1]
            self.send("PONG :" + pingmsg + "\n")
        # chat messages are grey
        elif is_message(ircmsg):
            print(ircmsg)
            self.process_message(ircmsg)
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
        if "NickServ!services@speedrunslive.com" in ircmsg:
            if "You are already identified." not in ircmsg:
                self.sendmsg("NickServ", "IDENTIFY " + self.password)

    def process_message(self, ircmsg):
        msg = Message(ircmsg)
        # ignore anything from #speedrunslive to avoid flooding it accidentally
        if msg.channel == "#speedrunslive":
            pass
        # kill command to force disconnect the bot from the server
        # WARNING: the bot will not reconnect until manually reset
        elif msg.command in {"!kill", ".kill"}:
            print(colored("Kill request detected from " + msg.sender.lower(), "yellow"))
            if self.has_op(msg.sender):
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

    def get_racer(self, channel, username, refresh=False):
        if refresh:
            self.racer_cache.refresh(username, self, channel)
        return self.racer_cache.get_or_load(username, self, channel)

    def has_admin(self, name):
        return name.lower() in ADMINS

    def has_op(self, name):
        return name.lower() in self.ops or self.has_admin(name)

    def add_op(self, name):
        self.ops.add(name.lower())
        self.save_ops()

    def remove_op(self, name):
        self.ops.remove(name.lower())
        self.save_ops()

    def save_ops(self):
        with open(OPS_FILE, "wb") as ops_file:
            pickle.dump(self.ops, ops_file)



