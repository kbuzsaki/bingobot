import socket
from datetime import timedelta
from termcolor import colored, cprint
from srlparser import Racer, Result

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


# helper method for bot

def detailedMessage(result):
        return str(result.date) + ": " + str(result) + " - " + result.raceUrl()

def resultsMessage(results, detailed=False):
    if not detailed:
        return ", ".join([str(result) for result in results])
    else:
        reps = [detailedMessage(result) for result in results]
        return "\n".join(reps)

# bot commands

def racerStats(bot, msg):
    if msg.command == "!racer":
        username = msg.elements[1].lower()
        racer = bot.getRacer(msg.channel, username, "refresh" in msg.elements)

        message = username + " has completed " + str(len(racer.validResults())) + " bingos "
        bot.sendmsg(msg.channel, message)

def pastTimes(bot, msg):
    if msg.command == "!results":
        username = msg.elements[1].lower()
        racer = bot.getRacer(msg.channel, username, "refresh" in msg.elements)
        if len(msg.elements) > 2 and msg.elements[2].isdigit():
            maxResults = int(msg.elements[2])
        else:
            maxResults = 10
        detailed = "detailed" in msg.elements

        results = racer.validResults()[:maxResults]

        message = "Past " + str(maxResults) + " races for " + username + ": "
        if detailed:
            message += "\n"
        message += resultsMessage(results, detailed)

        bot.sendmsg(msg.channel, message)

def averageTime(bot, msg):
    if msg.command == "!average":
        username = msg.elements[1].lower()
        racer = bot.getRacer(msg.channel, username, "refresh" in msg.elements)
        if len(msg.elements) > 2 and msg.elements[2].isdigit():
            maxResults = int(msg.elements[2])
        else:
            maxResults = 10

        averageTime = racer.averageTime(maxResults)

        # gets rid of trailing decimals
        formattedTime = str(averageTime).split(".")[0]
        message = "Average time for " + username + ": " + formattedTime
        bot.sendmsg(msg.channel, message)

def medianTime(bot, msg):
    if msg.command == "!median":
        username = msg.elements[1].lower()
        racer = bot.getRacer(msg.channel, username, "refresh" in msg.elements)
        if len(msg.elements) > 2 and msg.elements[2].isdigit():
            maxResults = int(msg.elements[2])
        else:
            maxResults = 10

        relevantTimes = racer.validTimes()[:maxResults]
        medianTime = relevantTimes[len(relevantTimes) // 2]

        # gets rid of trailing decimals
        formattedTime = str(medianTime).split(".")[0]
        message = "Median time for " + username + ": " + formattedTime
        bot.sendmsg(msg.channel, message)

def bestTime(bot, msg):
    if msg.command == "!best":
        username = msg.elements[1].lower()
        racer = bot.getRacer(msg.channel, username, "refresh" in msg.elements)
        if len(msg.elements) > 2 and msg.elements[2].isdigit():
            maxResults = int(msg.elements[2])
        else:
            maxResults = 5
        detailed = "detailed" in msg.elements

        results = sorted(racer.validResults())[:maxResults]

        message = "Top " + str(maxResults) + " races for " + username + ": "
        if detailed:
            message += "\n"
        message += resultsMessage(results, detailed)

        bot.sendmsg(msg.channel, message)

def worstTime(bot, msg):
    if msg.command == "!worst":
        username = msg.elements[1].lower()
        racer = bot.getRacer(msg.channel, username, "refresh" in msg.elements)
        if len(msg.elements) > 2 and msg.elements[2].isdigit():
            maxResults = int(msg.elements[2])
        else:
            maxResults = 5
        detailed = "detailed" in msg.elements

        results = sorted(racer.validResults(), reverse=True)[:maxResults]

        message = "Bottom " + str(maxResults) + " races for " + username + ": "
        if detailed:
            message += "\n"
        message += resultsMessage(results, detailed)

        bot.sendmsg(msg.channel, message)

def completionRate(bot, msg):
    if msg.command == "!rate":
        username = msg.elements[1].lower()
        racer = bot.getRacer(msg.channel, username, "refresh" in msg.elements)
        if len(msg.elements) > 2 and msg.elements[2].isdigit():
            maxResults = int(msg.elements[2])
        else:
            maxResults = 10

        rate = racer.averageRate(maxResults)
        goalsPer2Hours = timedelta(hours=2).total_seconds() / rate.total_seconds()
        
        # get rid of trailing decimals
        formattedRate = str(rate).split(".")[0]
        message = "Average rate for " + username + ": " + formattedRate + " per goal, "
        message += " or " + "{0:.2f}".format(goalsPer2Hours) + " goals in 2 hours."
        bot.sendmsg(msg.channel, message)

AVG_BLACKOUT = 3.25
AVG_REGULAR = 1.3
AVG_BASE = 0.5
AVG_OVERLAP = 0.1

def teamTime(bot, msg):
    if msg.command == "!teamtime":
        usernames = msg.elements[1:]
        if "refresh" in usernames:
            usernames.remove("refresh")
        racers = [bot.getRacer(msg.channel, username, "refresh" in msg.elements) for username in usernames]

        rates = [racer.averageRate() for racer in racers]
        workRates = [1 / rate.total_seconds() for rate in rates]
        totalWorkRate = sum(workRates)
        totalRate = timedelta(seconds=(1 / totalWorkRate))
        
        goalsPerHour = timedelta(hours=1).total_seconds() / totalRate.total_seconds()
        blackoutTime = 25 / goalsPerHour
        
        # get rid of trailing decimals
        formattedRate = str(totalRate).split(".")[0]
        teamName = ", ".join(usernames)
        message = "Average rate for " + teamName + ": " + formattedRate + " per goal, "
        message += " or " + "{0:.2f}".format(goalsPerHour * 2) + " goals in 2 hours.\n"
        message += "They would take about " + str(blackoutTime) + " to complete a blackout."
        bot.sendmsg(msg.channel, message)

def help(bot, msg):
    if msg.command == "!help":
        message = "Commands: !racer, !results, !best, !worst, !average, !rate.\n"
        message += "Format is \"!command <racer> [maxResults]\". "
        message += "Add \"detailed\" to the end of a list command to get dates and urls. "
        message += "Add \"refresh\" to the end of any command to force reload race data.\n"
        message += "Note that players with a large race history may take a while to load "
        message += "when they are first accessed. Race history is cached for subsequent commands."
        bot.sendmsg(msg.channel, message)

def about(bot, msg):
    if msg.command == "!about":
        message = "Version 0.2\n"
        message += "Created by Saltor."
        bot.sendmsg(msg.channel, message)

readCommands = [racerStats, averageTime, medianTime, completionRate, teamTime]
listCommands = [pastTimes, bestTime, worstTime]
metaCommands = [help, about]
allCommands = readCommands + listCommands + metaCommands

# runs the bot

server = "irc2.speedrunslive.com"
channel = "#test"
botnick = "BingoBot"

bingoBot = BingoBot(botnick, server, channel, commands = allCommands)
bingoBot.connect()
bingoBot.listen()

