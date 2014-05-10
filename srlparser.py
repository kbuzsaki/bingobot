import json
import urllib
import re
from datetime import date, timedelta
import pprint

API_URL = "http://api.speedrunslive.com/"

def loadJsonFromUrl(url):
    jsonFile = urllib.urlopen(url)
    jsonDict = json.loads(jsonFile.read())
    return jsonDict

bingoRegex = re.compile(".*speedrunslive.com/tools/oot-bingo/\?seed=[0-9]+")

def isBingoGoal(goal):
    goal = goal.lower()
    return bingoRegex.match(goal) and "short" not in goal and "blackout" not in goal

def getStatsUrl(player):
    return API_URL + "stat?player=" + player

def getNumberRaces(player):
    statsJson = loadJsonFromUrl(getStatsUrl(player))
    return statsJson["stats"]["totalRaces"]

def getResultsUrl(player):
    numRaces = getNumberRaces(player)
    return API_URL + "pastraces?player=" + player + "&pageSize=" + str(numRaces)

def getPastRaces(player):
    resultsJson = loadJsonFromUrl(getResultsUrl(player))
    return resultsJson["pastraces"]

def getPastBingoRaces(player):
    pastRaces = getPastRaces(player)
    bingoRaces = []
    for race in pastRaces:
        if isBingoGoal(race["goal"]):
            bingoRaces.append(race)
    return bingoRaces

def getPastBingoResultsJson(player):
    bingoRaces = getPastBingoRaces(player)
    bingoResults = []
    for race in bingoRaces:
        for result in race["results"]:
            if result["player"].lower() == player.lower():
                result["date"] = race["date"]
                bingoResults.append(result)
    return bingoResults

def getPastBingoResults(player):
    resultJsons = getPastBingoResultsJson(player)
    return [Result(resultJson) for resultJson in resultJsons]

def getAverageTime(times):
    if(len(times) > 0):
        return sum(times, timedelta(0)) / len(times)
    else:
        return 0

class Result:
    def __init__(self, resultJson):
        self.raceid = resultJson["race"]
        self.date = date.fromtimestamp(float(resultJson["date"]))
        self.time = timedelta(seconds=resultJson["time"])
        self.message = resultJson["message"]

    def __str__(self):
        return str(self.time)

    def __cmp__(self, result):
        return cmp(self.time, result.time)

    def isForfeit(self):
        return self.time <= timedelta(0)

    def apiUrl(self):
        return API_URL + "pastraces?id=" + str(self.raceid)

    def raceUrl(self):
        return "http://www.speedrunslive.com/races/result/#!/" + str(self.raceid)

class Racer:
    def __init__(self, username):
        self.username = username.strip()
        self.results = getPastBingoResults(username)

    def validResults(self):
        return [result for result in self.results if not result.isForfeit()]

    def validTimes(self):
        return [result.time for result in self.validResults()]

    def forfeitResults(self):
        return [result for result in self.results if result.isForfeit()]

    def completionRate(self):
        return len(self.validResults()) / float(len(self.results))

    def averageTime(self, maxTimes=-1):
        if maxTimes > 0 and maxTimes < len(self.validTimes()):
            times = self.validTimes()[:maxTimes]
        else:
            times = self.validTimes()

        return sum(times, timedelta()) / len(times)

    def averageRate(self, maxTimes=-1):
        average = self.averageTime(maxTimes)
        return (average - timedelta(minutes = 20)) / 5





"""
usernames = open("usernames")
usernames = ["mrbubbleskp"]
for username in usernames:
    username = username.strip()
    print "running user " + username
    bingoTimes = getPastBingoTimes(username)
    validTimes = removeForfeits(bingoTimes)
    forfeits = numForfeits(bingoTimes)
    print "number valid bingos: " + str(len(validTimes))
    print "number forfeits: " + str(forfeits)
    print "average (recent 15): " + str(getAverageTime(validTimes[0:15]))
    print "average (recent 10): " + str(getAverageTime(validTimes[0:10]))
    print "average (recent 5): " + str(getAverageTime(validTimes[0:5]))
    print "last 5 times: "
    for time in validTimes[0:5]:
        print str(time)
    print ""
"""

