from datetime import timedelta
from termcolor import colored

# helper method for bot

def formatTime(delta):
    return str(delta).split(".")[0]

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
        racer = bot.getRacer(msg.channel, msg.username, msg.refresh)

        message = msg.username + " has completed " + str(len(racer.validResults())) + " bingos "
        message += "and forfeited " + str(len(racer.forfeitResults()))
        bot.sendmsg(msg.channel, message)

def lookupRace(bot, msg):
    if msg.command == "!lookup":
        racer = bot.getRacer(msg.channel, msg.username, msg.refresh)
        lookupTime = msg.times[0]

        results = racer.validResults()[:]
        matches = [result for result in results if str(result.time) == str(lookupTime)]

        message = msg.username + "'s races with a time of " + str(lookupTime) + ":\n"
        message += resultsMessage(matches, detailed=True)

        bot.sendmsg(msg.channel, message)

def pastTimes(bot, msg):
    if msg.command == "!results":
        racer = bot.getRacer(msg.channel, msg.username, msg.refresh)

        results = racer.validResults()[msg.minimum:msg.maximum]
        resultsUsed = min(msg.maximum - msg.minimum, len(racer.validResults()))

        message = "Past " + str(resultsUsed) + " races for " + msg.username + ": "
        if msg.detailed:
            message += "\n"
        message += resultsMessage(results, msg.detailed)

        bot.sendmsg(msg.channel, message)

def averageTime(bot, msg):
    if msg.command == "!average":
        racer = bot.getRacer(msg.channel, msg.username, msg.refresh)

        averageTime = racer.averageTime(msg.minimum, msg.maximum)
        resultsUsed = min(msg.maximum - msg.minimum, len(racer.validResults()))

        message = "Average time from " + msg.username + "'s last " + str(resultsUsed)
        message += " bingos: " + formatTime(averageTime)
        bot.sendmsg(msg.channel, message)

def medianTime(bot, msg):
    if msg.command == "!median":
        racer = bot.getRacer(msg.channel, msg.username, msg.refresh)

        medianTime = racer.medianTime(msg.minimum, msg.maximum)
        resultsUsed = min(msg.maximum - msg.minimum, len(racer.validResults()))

        message = "Median time from " + msg.username + "'s last " 
        message += str(resultsUsed) + " bingos: " + formatTime(medianTime)
        bot.sendmsg(msg.channel, message)

def rankPlayers(bot, msg):
    if msg.command == "!rank":
        racers = [bot.getRacer(msg.channel, username, msg.refresh) for username in msg.usernames]
        stats = [(racer.medianTime(0, 15), racer.username) for racer in racers]
        stats = sorted(stats)

        message = "Player rankings: \n"
        for i in range(len(stats)):
            message += str(i + 1) + ". " + stats[i][1] + " (" + str(stats[i][0]) + ")\n"

        bot.sendmsg(msg.channel, message)

def bestTime(bot, msg):
    if msg.command == "!best":
        racer = bot.getRacer(msg.channel, msg.username, msg.refresh)

        results = sorted(racer.validResults())[:msg.getMaximum(default=5)]

        message = "Top " + str(len(results)) + " races for " + msg.username + ": "
        if msg.detailed:
            message += "\n"
        message += resultsMessage(results, msg.detailed)

        bot.sendmsg(msg.channel, message)

def worstTime(bot, msg):
    if msg.command == "!worst":
        racer = bot.getRacer(msg.channel, msg.username, msg.refresh)

        results = sorted(racer.validResults(), reverse=True)[:msg.getMaximum(default=5)]

        message = "Bottom " + str(len(results)) + " races for " + msg.username + ": "
        if msg.detailed:
            message += "\n"
        message += resultsMessage(results, msg.detailed)

        bot.sendmsg(msg.channel, message)


NAME = "RacerName"
RANGE_MESSAGE = "Optionally, you can specify a maximum number of races or range of races to use. "
REFRESH_MESSAGE = "Add \"refresh\" to force reload race data. "
DETAILED_MESSAGE = "Add \"detailed\" to get race dates and urls. "
EXACT_TIMES_MESSAGE = "Alternatively, you can supply exact times to use in the calculation. " 

def bingoBotPls(text):
    text = text.lower()
    return "bingobot pls" in text or "bingobot plz" in text or "bingobot please" in text

def help(bot, msg):
    if msg.command != "!help" and not bingoBotPls(msg.text):
        return
    search = msg.arguments[0] if len(msg.arguments) > 0 else None

    if search == None or bingoBotPls(msg.text):
        message = "Commands: !racer, !results, !best, !worst, !lookup, !average, "
        message += "!median, !teamtime, !balance, !join, !leave, !about.\n"
        message += "Run !help <command> to get detailed help for a command."
    elif "racer" in search:
        message = "Looks up a racer's bingo history including total completed and forfeited. "
        message += REFRESH_MESSAGE + "\n"
        message += "Example: \"!racer " + NAME + "\""
    elif "results" in search:
        message = "Looks up a portion of a racer's bingo history. "
        message += RANGE_MESSAGE + REFRESH_MESSAGE + DETAILED_MESSAGE + "\n"
        message += "Examples: \"!results " + NAME + "\", \"!results " + NAME + " 15\""
    elif "best" in search:
        message = "Looks up a racer's fastest bingo results. "
        message += RANGE_MESSAGE + REFRESH_MESSAGE + DETAILED_MESSAGE + "\n"
        message += "Examples: \"!best " + NAME + "\", \"!best " + NAME + " 15\""
    elif "worst" in search:
        message = "Looks up a racer's slowest bingo results. "
        message += RANGE_MESSAGE + REFRESH_MESSAGE + DETAILED_MESSAGE + "\n"
        message += "Examples: \"!worst " + NAME + "\", \"!worst " + NAME + " 15\""
    elif "lookup" in search:
        message = "Finds all of a racer's results with a given time. "
        message += REFRESH_MESSAGE + "\n"
        message += "Examples: \"!lookup " + NAME + " 1:48:39\", \"!lookup " + NAME + " 5:49:51\""
    elif "average" in search:
        message = "Calculates the average time for a racer from their past N races. "
        message += RANGE_MESSAGE + REFRESH_MESSAGE + "\n"
        message += "Examples: \"!average " + NAME + "\", \"!average " + NAME + " 5\""
    elif "median" in search:
        message = "Calculates the median time for a racer from their past N races. "
        message += RANGE_MESSAGE + REFRESH_MESSAGE + "\n"
        message += "Examples: \"!median " + NAME + "\", \"!median " + NAME + " 5\""
    elif "rank" in search:
        message = "Finds each player's median result from their past 15 races and then ranks them "
        message += "according to those times. " + REFRESH_MESSAGE + "\n"
        message += "Examples: \"!rank " + NAME + "1 " + NAME + "2 " + NAME + "3 \""
    elif "teamtime" in search:
        message = "Calculates the expected time blackout bingo time for a team of players. "
        message += "Uses each player's average from their past 15 bingo results. "
        message += EXACT_TIMES_MESSAGE + REFRESH_MESSAGE + "\n"
        message += "Examples: \"!teamtime bradwickliffe1997 gombill saltor\", "
        message += "\"!teamtime " + NAME + " 1:20:15 1:34:17\""
    elif "fastbalance" in search:
        message = "Finds relatively balanced teams for any set of 6, 9, 12, etc. players. "
        message += "Ranks players by their average bingo times, splits them up into high, medium, "
        message += "and low \"tiers\", and then forms teams by taking one racer from each group."
        message += "Uses each player's average from their past 15 bingo results. "
        message += EXACT_TIMES_MESSAGE + REFRESH_MESSAGE + "\n"
        message += "Example: \"!fastbalance bradwickliffe1997 gombill saltor thecowness balatee exodus\"."
    elif "balance" in search:
        message = "Finds the optimally balanced teams for a set of 6 players. "
        message += "Uses each player's average from their past 15 bingo results. "
        message += EXACT_TIMES_MESSAGE + REFRESH_MESSAGE + "\n"
        message += "Example: \"!balance bradwickliffe1997 gombill saltor thecowness balatee exodus\"."
    elif "help" in search:
        message = "Displays a help message explaining how to use a command.\n"
        message += "Examples: \"!help\", \"!help !results\""
    elif "join" in search:
        message = "Makes BingoBot join a particular channel. Use this if you want to use BingoBot "
        message += "to set up a race so you don't spam #bingoleage.\n"
        message += "Example: \"!join #srl-abcde\"."
    elif "leave" in search:
        message = "Makes BingoBot leave the channel. Use it in the channel that you want BingoBot "
        message += "to leave.\n"
        message += "Example: \"!leave\"."
    elif "about" in search:
        message = "Displays version information and the people who have contributed to this bot."
    elif search == "me":
        message = "Very funny, " + msg.sender + "."
    else:
        message = "No help information for " + msg.arguments[0]

    bot.sendmsg(msg.channel, message)

def about(bot, msg):
    if msg.command == "!about":
        message = "Version 0.6\n"
        message += "Created by Saltor. !teamtime algorithm by Gombill."
        bot.sendmsg(msg.channel, message)

queryCommands = [racerStats, lookupRace]
listCommands = [pastTimes, rankPlayers, bestTime, worstTime]
calculationCommands = [averageTime, medianTime]
metaCommands = [help, about]
allCommands = queryCommands + listCommands + calculationCommands + metaCommands    

