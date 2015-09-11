from datetime import timedelta
from termcolor import colored
from commands.basiccommands import formatTime
from command import command

NUMBERS = "one two three four five six seven eight nine ten eleven twelve".split()

def getPatterns(patternsFilename):
    with open(patternsFilename) as patternsFile:
       return [getPattern(line.strip()) for line in patternsFile]

def getPattern(line):
    return [int(digit, 16) for digit in line]

PATTERNS_DICT = {
    2: {
        2: getPatterns("patterns/teams22")
    },
    3: {
        2: getPatterns("patterns/teams2"),
        3: getPatterns("patterns/teams3"),
        4: getPatterns("patterns/teams4")
    }
}


def multDelta(delta, factor):
    seconds = delta.total_seconds() * factor
    return timedelta(seconds=seconds)

def chunkList(elements, step=3):
    chunks = len(elements) // step
    for index in range(chunks):
        yield elements[index * step : (index + 1) * step]

def variance(elements):
    mean = sum(elements) / len(elements)
    squares = [(mean - element) ** 2 for element in elements]
    return sum(squares) / len(squares)

# constants and helpers for teamTime()
AVG_BLACKOUT = timedelta(hours=3, minutes=15)
AVG_REGULAR = timedelta(hours=1, minutes=20)
AVG_BASE = timedelta(minutes=30)
AVG_OVERLAP = timedelta(minutes=5)

class Participant:

    def __init__(self, time, successRate, name):
        self.time = time
        self.successRate = successRate
        self.name = name

    @classmethod
    def fromRacer(constructor, racer):
        return constructor(racer.medianTime(0, 15), max(racer.completionRate(), 0.5), racer.username)

    @classmethod
    def fromTime(constructor, time):
        return constructor(time, 1.0, str(time))

    @property
    def netTime(self):
        return self.time - AVG_BASE

    @property
    def effectiveRate(self):
        return multDelta(self.netTime, 1 / self.successRate)

    @property
    def workRate(self):
        return 1 / self.effectiveRate.total_seconds()

    def __eq__(self, other):
        return self.workRate == other.workRate

    def __lt__(self, other):
        return self.workRate < other.workRate

def getParticipants(bot, msg):
    racers = [bot.getRacer(msg.channel, username, msg.refresh) for username in msg.usernames]
    participants = [Participant.fromRacer(racer) for racer in racers]
    participants += [Participant.fromTime(time) for time in msg.times]
    return participants


def totalWorkRate(participants):
    return sum([participant.workRate for participant in participants])

def getTeamTime(team):
    combinedWorkRate = totalWorkRate(team)
    # work rate is then used to calculate net average time for a normal bingo
    combinedRate = timedelta(seconds=(1 / combinedWorkRate))

    # the team's net average time is then scaled up to blackout scale
    ratio = (AVG_BLACKOUT - AVG_BASE).total_seconds() / (AVG_REGULAR - AVG_BASE).total_seconds()
    # the base 30 minutes are added back to convert the net time to total time
    blackoutTime = multDelta(combinedRate, ratio) + AVG_BASE + AVG_OVERLAP

    return blackoutTime

@command("teamtime")
def teamTime(bot, msg):
    participants = getParticipants(bot, msg)

    blackoutTime = getTeamTime(participants)

    message = "Team \"" + ", ".join(msg.usernames + [str(time) for time in msg.times])
    message += "\" would take about " + formatTime(blackoutTime) + " to complete a blackout."
    bot.sendmsg(msg.channel, message)

@command("balance")
def balance(bot, msg):
    participants = getParticipants(bot, msg)

    # ensure that a valid number of participants have been passed
    if len(participants) not in [4, 6, 9, 12]:
        message = "Please provide a total of 4, 6, 9, or 12 usernames/times to balance."
        bot.sendmsg(msg.channel, message)
        return

    if len(participants) == 4:
        teamSize = 2
    else:
        teamSize = 3

    numTeams = len(participants) // teamSize
    optimalTeams = list(chunkList(participants, teamSize))
    optimalVariance = variance([getTeamTime(team).total_seconds() for team in optimalTeams])
    for pattern in PATTERNS_DICT[teamSize][numTeams]:
        order = [participants[x] for x in pattern]
        newTeams = list(chunkList(order, teamSize))
        newVariance = variance([getTeamTime(team).total_seconds() for team in newTeams])
        if newVariance < optimalVariance:
            optimalTeams = newTeams
            optimalVariance = newVariance

    message = ""
    for index, team in enumerate(optimalTeams):
        message += "Team " + NUMBERS[index] + ": \"" + ", ".join([participant.name for participant in team])
        message += "\" (" + formatTime(getTeamTime(team)) + ")\n"
    bot.sendmsg(msg.channel, message)

@command("fastbalance")
def fastBalance(bot, msg):
    participants = getParticipants(bot, msg)

    if len(participants) % 3 != 0:
        message = "Must be divisible by three to form teams"
        bot.sendmsg(msg.channel, message)
        return

    # sort so highest work rates are at the top
    participants = sorted(participants, reverse=True)

    # sort into three tiers of players
    numTeams = len(participants) // 3

    tierOne = participants[:numTeams]
    tierTwo = participants[numTeams:numTeams*2]
    tierThree = participants[numTeams*2:]

    teams = []

    # pair the best of tier 1 with worst of tier 2
    for playerIndex in range(numTeams):
        teams.append([tierOne[playerIndex], tierTwo[-playerIndex - 1]])

    #sorts the resulting teams with highest work rates at the top
    teamRate = lambda team: team[0].workRate + team[1].workRate
    teams = sorted(teams, key=teamRate, reverse=True)

    # pair the best current teams with the worst tier 3 players
    for playerIndex in range(numTeams):
        teams[playerIndex].append(tierThree[-playerIndex - 1])

    message = ""
    for index, team in enumerate(teams):
        message += "Team " + NUMBERS[index] + ": \"" + ", ".join([participant.name for participant in team])
        message += "\" (" + formatTime(getTeamTime(team)) + ")\n"
    bot.sendmsg(msg.channel, message)

