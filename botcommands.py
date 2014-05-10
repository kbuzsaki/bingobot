from datetime import timedelta

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
        username = msg.elements[1].lower()
        racer = bot.getRacer(msg.channel, username, "refresh" in msg.elements)

        message = username + " has completed " + str(len(racer.validResults())) + " bingos "
        bot.sendmsg(msg.channel, message)

def lookupRace(bot, msg):
    if msg.command == "!lookup":
        username = msg.elements[1].lower()
        racer = bot.getRacer(msg.channel, username, "refresh" in msg.elements)
        lookupTime = msg.elements[2].lower()
        if len(msg.elements) > 3 and msg.elements[3].isdigit():
            maxResults = int(msg.elements[3])
        else:
            maxResults = None

        results = racer.validResults()[:maxResults]
        matches = [result for result in results if str(result.time) == lookupTime]

        message = username + "'s races with a time of " + lookupTime + ":\n"
        message += resultsMessage(matches, detailed=True)

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
        resultsUsed = min(maxResults, len(racer.validResults()))

        message = "Past " + str(resultsUsed) + " races for " + username + ": "
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
        resultsUsed = min(maxResults, len(racer.validResults()))

        message = "Average time from " + username + "'s last " + str(resultsUsed)
        message += " bingos: " + formatTime(averageTime)
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

        message = "Median time from " + username + "'s last " 
        message += str(len(relevantTimes)) + " bingos: " + formatTime(medianTime)
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

        message = "Top " + str(len(results)) + " races for " + username + ": "
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

        message = "Bottom " + str(len(results)) + " races for " + username + ": "
        if detailed:
            message += "\n"
        message += resultsMessage(results, detailed)

        bot.sendmsg(msg.channel, message)

# broken, disabled
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
        
        message = "Average rate for " + username + ": " + formatTime(rate) + " per goal, "
        message += " or " + "{0:.2f}".format(goalsPer2Hours) + " goals in 2 hours."
        bot.sendmsg(msg.channel, message)

# constants and helpers for teamTime()
AVG_BLACKOUT = timedelta(hours=3, minutes=15)
AVG_REGULAR = timedelta(hours=1, minutes=20)
AVG_BASE = timedelta(minutes=30)
AVG_OVERLAP = timedelta(minutes=5)

def multDelta(delta, factor):
    seconds = delta.total_seconds() * factor
    return timedelta(seconds=seconds)

def teamTime(bot, msg):
    if msg.command == "!teamtime":
        usernames = msg.elements[1:]
        if "refresh" in usernames:
            usernames.remove("refresh")
        racers = [bot.getRacer(msg.channel, username, "refresh" in msg.elements) for username in usernames]

        # calcualtes the effective goal completion rate of each racer
        netAverages = [racer.averageTime(15) - AVG_BASE for racer in racers]
        successRates = [max(racer.completionRate(), 0.5) for racer in racers]
        tuples = zip(netAverages, successRates)
        effectiveRates = [multDelta(delta, 1 / successrate) for (delta, successrate) in tuples]

        # calculates the combined "work rate" or contribution rate of the team
        workRates = [1 / rate.total_seconds() for rate in effectiveRates]
        combinedWorkRate = sum(workRates)
        # work rate is then used to calculate net average time for a normal bingo
        combinedRate = timedelta(seconds=(1 / combinedWorkRate))

        # the team's net average time is then scaled up to blackout scale
        ratio = (AVG_BLACKOUT - AVG_BASE).total_seconds() / (AVG_REGULAR - AVG_BASE).total_seconds() 
        # the base 30 minutes are added back to convert the net time to total time
        blackoutTime = multDelta(combinedRate, ratio) + AVG_BASE + AVG_OVERLAP
        
        message = "Team \"" + ", ".join(usernames) + "\" would take about "
        message += formatTime(blackoutTime) + " to complete a blackout."
        bot.sendmsg(msg.channel, message)

def help(bot, msg):
    if msg.command == "!help":
        message = "Commands: !racer, !results, !lookup, !best, !worst, !average, !median, !teamtime.\n"
        message += "Format is \"!command <racer> [maxResults]\". "
        message += "!lookup requires a time after the racer name as well.\n"
        message += "Add \"detailed\" to the end of a list command to get dates and urls. "
        message += "Add \"refresh\" to the end of any command to force reload race data."
        message += "Note that players with a large race history may take a while to load "
        message += "when they are first accessed. Race history is cached for subsequent commands."
        bot.sendmsg(msg.channel, message)

def about(bot, msg):
    if msg.command == "!about":
        message = "Version 0.3\n"
        message += "Created by Saltor. !teamtime algorithm by Gombill."
        bot.sendmsg(msg.channel, message)

queryCommands = [racerStats, lookupRace]
listCommands = [pastTimes, bestTime, worstTime]
calculationCommands = [averageTime, medianTime, teamTime]
metaCommands = [help, about]
allCommands = queryCommands + listCommands + calculationCommands + metaCommands    

