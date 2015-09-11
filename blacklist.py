import os
import pickle
from srlparser import Racer

# defines a blacklist of racers for use by the FilteredRacer
class Blacklist:

    def __init__(self, filename="blacklist"):
        self.filename = filename
        if os.path.exists(filename):
            with open(filename, "rb") as blacklist_file:
                self.races = pickle.load(blacklist_file)
        else:
            self.races = set()

    def __contains__(self, race):
        return race in self.races

    def __iter__(self):
        for race in self.races:
            yield race

    def add(self, race):
        self.races.add(race)
        self.save()

    def remove(self, race):
        self.races.remove(race)
        self.save()

    def save(self):
        with open(self.filename, "wb") as blacklist_file:
            pickle.dump(self.races, blacklist_file)

# defines a racer that filters from a blacklist
class FilteredRacer(Racer):

    def __init__(self, username, blacklist):
        Racer.__init__(self, username)
        self.blacklist = blacklist

    @property
    def results(self):
        return [result for result in self.bingo_results if result.race_id not in self.blacklist]

