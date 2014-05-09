
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

queryCommands = [racerStats, lookupRace]
listCommands = [pastTimes, bestTime, worstTime]
calculationCommands = [averageTime, medianTime, completionRate, teamTime]
metaCommands = [help, about]
allCommands = queryCommands + listCommands + calculationCommands + metaCommands    

