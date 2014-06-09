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

# constants and helpers for teamTime()
AVG_BLACKOUT = timedelta(hours=3, minutes=15)
AVG_REGULAR = timedelta(hours=1, minutes=20)
AVG_BASE = timedelta(minutes=30)
AVG_OVERLAP = timedelta(minutes=5)

def multDelta(delta, factor):
    seconds = delta.total_seconds() * factor
    return timedelta(seconds=seconds)

def getTeamWorkRates(times, successRates):
    netAverages = [time - AVG_BASE for time in times]
    tuples = list(zip(netAverages, successRates))
    effectiveRates = [multDelta(delta, 1 / successrate) for (delta, successrate) in tuples]

    # calculates the combined "work rate" or contribution rate of the team
    workRates = [1 / rate.total_seconds() for rate in effectiveRates]
    return workRates

def getTeamTime(workRates):
    combinedWorkRate = sum(workRates)
    # work rate is then used to calculate net average time for a normal bingo
    combinedRate = timedelta(seconds=(1 / combinedWorkRate))

    # the team's net average time is then scaled up to blackout scale
    ratio = (AVG_BLACKOUT - AVG_BASE).total_seconds() / (AVG_REGULAR - AVG_BASE).total_seconds() 
    # the base 30 minutes are added back to convert the net time to total time
    blackoutTime = multDelta(combinedRate, ratio) + AVG_BASE + AVG_OVERLAP
    
    return blackoutTime

def teamTime(bot, msg):
    if msg.command == "!teamtime":
        racers = [bot.getRacer(msg.channel, username, msg.refresh) for username in msg.usernames]

        # calcualtes the effective goal completion rate of each racer
        times = [racer.medianTime(0, 15) for racer in racers] + msg.times
        successRates = [max(racer.completionRate(), 0.5) for racer in racers] + [1.0] * len(msg.times)
        blackoutTime = getTeamTime(getTeamWorkRates(times, successRates))
        
        message = "Team \"" + ", ".join(msg.usernames + [str(time) for time in msg.times]) 
        message += "\" would take about " + formatTime(blackoutTime) + " to complete a blackout."
        bot.sendmsg(msg.channel, message)

def balance(bot, msg):
    if msg.command == "!balance":
        racers = [bot.getRacer(msg.channel, username, msg.refresh) for username in msg.usernames]

        # calcualtes the effective goal completion rate of each racer
        stats = [(racer.medianTime(0, 15), racer.completionRate(), racer.username) for racer in racers]
        adjustedStats = [(time - AVG_BASE, successRate, name) for (time, successRate, name) in stats]
        participants = [(multDelta(time, 1 / rate), name) for (time, rate, name) in adjustedStats] 
        participants += [(time - AVG_BASE, str(time)) for time in msg.times]
        
        # ensure that 6 participants have been passed
        if len(participants) != 6:
            message = "Please provide a total of 6 usernames or times to balance"
            bot.sendmsg(msg.channel, message)
            return

        # calculates the work rate for each racer
        participants = [(1 / rate.total_seconds(), name) for (rate, name) in participants]

        def sumRates(participants):
            return sum([rate for (rate, name) in participants])

        # this feels really gross and unpythonic
        # I don't know a better way to check for identity though
        # you have to check for identity so duplicate times aren't omitted
        def complementTeam(teamOne, participants):
            teamTwo = []
            for racer in participants:
                used = False
                for member in teamOne:
                    if racer is member:
                        used = True
                if not used:
                    teamTwo.append(racer)
            return teamTwo

        optimalTeamOne = [participants[0], participants[1], participants[2]]
        optimalTeamTwo = complementTeam(optimalTeamOne, participants)
        optimalRateDiff = abs(sumRates(optimalTeamOne) - sumRates(optimalTeamTwo))
        for x in range(1,6):
            for y in range(x+1,6):
                teamOne = [participants[0], participants[x], participants[y]]
                teamTwo = complementTeam(teamOne, participants)
                rateDiff = abs(sumRates(teamOne) - sumRates(teamTwo))
                if rateDiff < optimalRateDiff:
                    print(colored("Best found: ", "yellow"))
                    optimalTeamOne = teamOne
                    optimalTeamTwo = teamTwo
                    optimalRateDiff = rateDiff
                print(colored("Team One: " + ", ".join([name for (rate, name) in teamOne]), "yellow"))
                print(colored("Team Two: " + ", ".join([name for (rate, name) in teamTwo]), "yellow"))

        teamOneNames = [name for (rate, name) in optimalTeamOne]
        teamOneTime = getTeamTime([rate for (rate, name) in optimalTeamOne])
        teamTwoNames = [name for (rate, name) in optimalTeamTwo]
        teamTwoTime = getTeamTime([rate for (rate, name) in optimalTeamTwo])

        message = "Team one: \"" + ", ".join(teamOneNames) + "\" (" + formatTime(teamOneTime) + ")\n"
        message += "Team two: \"" + ", ".join(teamTwoNames) + "\" (" + formatTime(teamTwoTime) + ")"
        bot.sendmsg(msg.channel, message)

NAME = "RacerName"
RANGE_MESSAGE = "Optionally, you can specify a maximum number of races or range of races to use. "
REFRESH_MESSAGE = "Add \"refresh\" to force reload race data. "
DETAILED_MESSAGE = "Add \"detailed\" to get race dates and urls. "

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
    elif "teamtime" in search:
        message = "Calculates the expected time blackout bingo time for a team of players. "
        message += "Uses each player's average from their past 15 bingo results. "
        message += "Alternatively, you can supply exact times to use in the calculation. "
        message += REFRESH_MESSAGE + "\n"
        message += "Examples: \"!teamtime bradwickliffe1997 gombill saltor\", "
        message += "\"!teamtime " + NAME + " 1:20:15 1:34:17\""
    elif "balance" in search:
        message = "Finds the optimally balanced teams for a set of 6 players. "
        message += "Uses each player's average from their past 15 bingo results. "
        message += "Alternatively, you can supply exact times to use in the calculation. "
        message += REFRESH_MESSAGE + "\n"
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
        message = "Version 0.5\n"
        message += "Created by Saltor. !teamtime algorithm by Gombill."
        bot.sendmsg(msg.channel, message)

queryCommands = [racerStats, lookupRace]
listCommands = [pastTimes, rankPlayers, bestTime, worstTime]
calculationCommands = [averageTime, medianTime, teamTime, balance]
metaCommands = [help, about]
allCommands = queryCommands + listCommands + calculationCommands + metaCommands    
