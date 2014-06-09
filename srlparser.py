import json
import urllib.request, urllib.parse, urllib.error
import re
from datetime import date, timedelta
import pprint

API_URL = "http://api.speedrunslive.com/"

def loadJsonFromUrl(url):
    jsonFile = urllib.request.urlopen(url)
    jsonDict = json.loads(jsonFile.read().decode())
    return jsonDict

bingoRegex = re.compile(".*speedrunslive.com/tools/oot-bingo/\?.*seed=[0-9]+")

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

BINGO_V8_RELEASE = date(2013, 9, 11)

def getPastBingoRaces(player):
    pastRaces = getPastRaces(player)
    bingoRaces = []
    for race in pastRaces:
        raceDate = date.fromtimestamp(float(race["date"]))
        if isBingoGoal(race["goal"]) and raceDate > BINGO_V8_RELEASE:
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

    def __lt__(self, result):
        return self.time < result.time

    def isForfeit(self):
        return self.time <= timedelta(0)

    def apiUrl(self):
        return API_URL + "pastraces?id=" + str(self.raceid)

    def raceUrl(self):
        return "http://www.speedrunslive.com/races/result/#!/" + str(self.raceid)

class Racer:
    def __init__(self, username):
        self.username = username.strip()
        self.bingoResults = getPastBingoResults(username)

    @property
    def results(self):
        return self.bingoResults

    def validResults(self):
        return [result for result in self.results if not result.isForfeit()]

    def validTimes(self):
        return [result.time for result in self.validResults()]

    def forfeitResults(self):
        return [result for result in self.results if result.isForfeit()]

    def completionRate(self):
        return len(self.validResults()) / float(len(self.results))

    def averageTime(self, minTimes, maxTimes):
        times = self.validTimes()[minTimes:maxTimes]

        return sum(times, timedelta()) / len(times)

    def medianTime(self, minTimes, maxTimes):
        times = self.validTimes()[minTimes:maxTimes]

        return sorted(times)[len(times) // 2]


