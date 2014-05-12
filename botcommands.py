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

        times = racer.validTimes()[msg.minimum:msg.maximum]
        averageTime = sum(times, timedelta()) / len(times)
        resultsUsed = min(msg.maximum - msg.minimum, len(racer.validResults()))

        message = "Average time from " + msg.username + "'s last " + str(resultsUsed)
        message += " bingos: " + formatTime(averageTime)
        bot.sendmsg(msg.channel, message)

def medianTime(bot, msg):
    if msg.command == "!median":
        racer = bot.getRacer(msg.channel, msg.username, msg.refresh)

        relevantTimes = racer.validTimes()[msg.minimum:msg.maximum]
        medianTime = relevantTimes[len(relevantTimes) // 2]

        message = "Median time from " + msg.username + "'s last " 
        message += str(len(relevantTimes)) + " bingos: " + formatTime(medianTime)
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

# broken, disabled
def completionRate(bot, msg):
    if msg.command == "!rate":
        racer = bot.getRacer(msg.channel, msg.username, msg.refresh)
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

def toEffectiveRate(averageTime, successRate):
    netAverage = averageTime - AVG_BASE
    return multDelta(netAverage, 1 / successRate)

def mapToScore(workRate):
    x = workRate * 10000
    score = (-0.628391 * x**3) + (2.3329 * x**2) + (27.3814 * x) - 13.1937 
    return score
    
# hidden command
def effectiveRate(bot, msg):
    if msg.command == "!rawrate":
        if len(msg.times) > 0:
            effectiveRate = toEffectiveRate(msg.times[0], successRate=1.0)
            identifier = str(msg.times[0])
        else:
            racer = bot.getRacer(msg.channel, msg.username, msg.refresh)
            times = racer.validTimes()[msg.minimum:msg.maximum]
            averageTime = sum(times, timedelta()) / len(times)
            successRate = max(racer.completionRate(), 0.5)
            effectiveRate = toEffectiveRate(averageTime, successRate)
            identifier = racer.username

        workRate = 1 / effectiveRate.total_seconds()

        message = "Raw work rate for " + identifier + ": " + str(workRate) 

        bot.sendmsg(msg.channel, message)

def effectiveScore(bot, msg):
    if msg.command == "!score":
        if len(msg.times) > 0:
            effectiveRate = toEffectiveRate(msg.times[0], successRate=1.0)
            identifier = str(msg.times[0])
        else:
            racer = bot.getRacer(msg.channel, msg.username, msg.refresh)
            times = racer.validTimes()[msg.minimum:msg.maximum]
            averageTime = sum(times, timedelta()) / len(times)
            successRate = max(racer.completionRate(), 0.5)
            effectiveRate = toEffectiveRate(averageTime, successRate)
            identifier = racer.username

        workRate = 1 / effectiveRate.total_seconds()
        workScore = mapToScore(workRate)

        message = "Adjusted score for " + identifier + ": " + str(int(workScore)) 

        bot.sendmsg(msg.channel, message)

def teamTime(bot, msg):
    if msg.command == "!teamtime":
        racers = [bot.getRacer(msg.channel, username, msg.refresh) for username in msg.usernames]

        # calcualtes the effective goal completion rate of each racer
        times = [racer.averageTime(15) for racer in racers] + msg.times
        netAverages = [time - AVG_BASE for time in times]
        successRates = [max(racer.completionRate(), 0.5) for racer in racers] + [1.0] * len(msg.times)
        tuples = list(zip(netAverages, successRates))
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
        
        message = "Team \"" + ", ".join(msg.usernames + [str(time) for time in msg.times]) 
        message += "\" would take about " + formatTime(blackoutTime) + " to complete a blackout."
        bot.sendmsg(msg.channel, message)

NAME = "RacerName"
RANGE_MESSAGE = "Optionally, you can specify a maximum number of races or range of races to use. "
REFRESH_MESSAGE = "Add \"refresh\" to force reload race data. "
DETAILED_MESSAGE = "Add \"detailed\" to get race dates and urls. "

def help(bot, msg):
    if msg.command != "!help":
        return
    search = msg.elements[1] if len(msg.elements) > 1 else None

    if search == None:
        message = "Commands: !racer, !results, !best, !worst, !lookup, !average, "
        message += "!median, !teamtime, !score, !help, !about.\n"
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
    elif "score" in search:
        message = "Calculates a rough \"bingo effectiveness\" score based on a racer's previous"
        message += "times. 100 corresponds to an effective average of 1:07:00, while "
        message += "1 corresponds to around 6:00:00. "
        message += "Alternatively, you can supply an exact time to use in the calculation. "
        message += REFRESH_MESSAGE + "\n"
        message += "Examples: \"!score " + NAME + "\", \"!score 1:20\""
    elif "help" in search:
        message = "Displays a help message explaining how to use a command.\n"
        message += "Examples: \"!help\", \"!help !results\""
    elif "about" in search:
        message = "Displays version information and the people who have contributed to this bot."
    elif search == "me":
        message = "Very funny, " + msg.sender + "."
    else:
        message = "No help information for " + msg.elements[1]

    bot.sendmsg(msg.channel, message)

def about(bot, msg):
    if msg.command == "!about":
        message = "Version 0.4\n"
        message += "Created by Saltor. !teamtime algorithm by Gombill."
        bot.sendmsg(msg.channel, message)

queryCommands = [racerStats, lookupRace]
listCommands = [pastTimes, bestTime, worstTime]
calculationCommands = [averageTime, medianTime, effectiveRate, effectiveScore, teamTime]
metaCommands = [help, about]
allCommands = queryCommands + listCommands + calculationCommands + metaCommands    

