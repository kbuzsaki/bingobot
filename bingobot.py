import socket
import traceback
import re
from datetime import timedelta
from termcolor import colored, cprint
from messages import Message, isMessage
from srlparser import Racer, Result

def isPing(ircmsg):
    return "PING :" in ircmsg

# users who can kill the bingobot using !kill
# this is devs, ops, and voices on #bingoleague
PRIVELAGED_USERS = ["saltor", "saltor_", "gombill", "keymakr", "exodus", "balatee"]

def hello(bot, msg):
    if msg.contains("Hello " + bot.nick) or msg.contains("Hi " + bot.nick):
        bot.sendmsg(msg.channel, "Hello, " + msg.sender + "!")

class NameException(Exception):
    pass

class KillException(Exception):
    pass


class BingoBot:
    def __init__(self, nick, server, channel, commands=[]):
        self.nick = nick
        self.server = server
        self.channel = channel
        self.commands = [hello] + commands
        self.racers = dict()

    def send(self, s):
        self.ircsock.send(s.encode())

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

    def listen(self):
        while True:
            ircmsg = self.ircsock.recv(2048)
            ircmsg = ircmsg.decode().strip()
            # pings are blue
            if isPing(ircmsg):
                print(colored(ircmsg, "blue"))
                pingmsg = ircmsg.split("PING :")[1]
                self.send("PONG :" + pingmsg + "\n")
                print(colored("RESPONDING TO PING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "blue"))
            # chat messages are grey
            elif isMessage(ircmsg):
                print(ircmsg)
                msg = Message(ircmsg)
                # kill command to force disconnect the bot from the server
                # WARNING: the bot will not reconnect until manually reset
                if msg.command == "!kill" :
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
            # if there's SOMETHING there
            elif len(ircmsg) > 0:
                print(colored(ircmsg, "green"))
            # else, must be disconnected
            else:
                print(colored("Disconnected from server?", "yellow"))
                return
            # weird hack thing for joining channels?
            if "End of /MOTD" in ircmsg:
                self.joinchan(self.channel)

    def getRacer(self, channel, username, refresh=False):
        username = username.lower()
        if (refresh or username not in self.racers):
            try:
                self.sendmsg(channel, "Loading data for " + username + "...")
                self.racers[username] = Racer(username)
            except:
                raise NameException(username)
        return self.racers[username]


