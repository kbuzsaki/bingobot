from datetime import timedelta
from termcolor import colored
from botcommands import formatTime
                        
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

commands = [teamTime, balance]
                                               
