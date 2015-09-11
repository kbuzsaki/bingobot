import traceback
import pickle
import os
from ircconn import DeadSocketException
from collections import deque
from datetime import datetime, timedelta
from termcolor import colored, cprint
from messages import Message, is_message
from srlparser import Racer, Result
from blacklist import Blacklist
from racercache import RacerCache, NameException

def is_ping(ircmsg):
    return "PING :" in ircmsg

# users with !say and !command privelages, very dangerous
ADMINS = ["saltor", "saltor_", "kbuzsaki"]

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

    def __init__(self, nick, password, connection, channels=[], commands=[]):
        self.nick = nick
        self.password = password
        self.connection = connection
        self.channels = channels
        self.commands = commands
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
        self.connection.send(s)

    def connect(self):
        self.connection.connect()

    def sendmsg(self, chan, msg):
        for line in msg.strip().split("\n"):
            self.send("PRIVMSG " + chan + " :" + line + "\n")

    def joinchan(self, chan):
        self.send("JOIN " + chan + "\n")

    def leavechan(self, chan):
        self.send("PART " + chan + "\n")

    def listen(self):
        while True:
            try:
                next_line = self.connection.read_line()
                self.process_line(next_line)
            except DeadSocketException as e:
                print(colored("*************************************", "red"))
                print(colored(str(e), "red"))
                print(colored("*************************************", "red"))

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
        else:
            print(colored(ircmsg, "green"))

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



