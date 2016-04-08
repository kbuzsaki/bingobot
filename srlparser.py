from datetime import date, timedelta
import json
import re
import urllib.error, urllib.parse, urllib.request

API_URL = "http://api.speedrunslive.com/"

def load_json_from_url(url):
    json_file = urllib.request.urlopen(url)
    json_dict = json.loads(json_file.read().decode())
    return json_dict

BINGO_URL_BASE = "speedrunslive.com/tools/oot-bingo"

BLACKLISTED_GOAL_WORDS = ["short", "blackout", "double"]

def is_bingo_goal(goal):
    goal = goal.lower()
    return BINGO_URL_BASE in goal and not any(word in goal for word in BLACKLISTED_GOAL_WORDS)

def get_stats_url(player):
    return API_URL + "stat?player=" + player

def get_number_races(player):
    g = load_json_from_url(get_stats_url(player))
    return g["stats"]["totalRaces"]

def get_results_url(player, race_count=-1):
    if race_count == -1:
        race_count = get_number_races(player)
    return API_URL + "pastraces?player=" + player + "&pageSize=" + str(race_count)

def get_race_history(player, race_count=-1):
    results_json = load_json_from_url(get_results_url(player, race_count))
    return results_json["pastraces"]

BINGO_V8_RELEASE = date(2013, 9, 11)

def get_oot_bingos_from(race_history):
    oot_races = [race for race in race_history if race["game"]["abbrev"] == "oot"]
    bingo_races = []
    for race in oot_races:
        race_date = date.fromtimestamp(float(race["date"]))
        if is_bingo_goal(race["goal"]) and race_date > BINGO_V8_RELEASE:
            bingo_races.append(race)
    return bingo_races

def get_results_from(bingo_races, player):
    bingo_results = []
    for race in bingo_races:
        for result_json in race["results"]:
            if result_json["player"].lower() == player.lower():
                result_json["date"] = race["date"]
                bingo_results.append(Result(result_json))
    return bingo_results

def get_average_time(times):
    if len(times) > 0:
        return sum(times, timedelta(0)) / len(times)
    else:
        return 0

def get_race_url(race_id):
    return "http://www.speedrunslive.com/races/result/#!/" + str(race_id)

class Result:
    def __init__(self, result_json):
        self.race_id = result_json["race"]
        self.date = date.fromtimestamp(float(result_json["date"]))
        self.time = timedelta(seconds=result_json["time"])
        self.message = result_json["message"]

    def __str__(self):
        return str(self.time)

    def __lt__(self, result):
        return self.time < result.time

    def is_forfeit(self):
        return self.time <= timedelta(0)

    def api_url(self):
        return API_URL + "pastraces?id=" + str(self.race_id)

    def race_url(self):
        return get_race_url(self.race_id)

class Racer:
    def __init__(self, username):
        self.username = username.strip()
        race_history = get_race_history(self.username)
        self.num_loaded_races = len(race_history)
        self.bingo_results = get_results_from(get_oot_bingos_from(race_history), self.username)

    def update(self):
        num_outdated = get_number_races(self.username) - self.num_loaded_races
        if num_outdated > 0:
            new_races = get_race_history(self.username, num_outdated)
            new_bingo_results = get_results_from(get_oot_bingos_from(new_races), self.username)
            self.bingo_results = new_bingo_results + self.bingo_results
            self.num_loaded_races += num_outdated

    @property
    def results(self):
        return self.bingo_results

    def valid_results(self):
        return [result for result in self.results if not result.is_forfeit()]

    def valid_times(self):
        return [result.time for result in self.valid_results()]

    def forfeit_results(self):
        return [result for result in self.results if result.is_forfeit()]

    def completion_rate(self):
        return len(self.valid_results()) / float(len(self.results))

    def average_time(self, min_times, max_times):
        times = self.valid_times()[min_times:max_times]

        return sum(times, timedelta()) / len(times)

    def median_time(self, min_times, max_times):
        times = self.valid_times()[min_times:max_times]

        return sorted(times)[len(times) // 2]


