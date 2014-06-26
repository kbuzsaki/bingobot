import os
import pickle
from datetime import datetime, timedelta
from srlparser import Racer
from blacklist import FilteredRacer

TIME_THRESHOLD = timedelta(hours=24)

def load(username, blacklist):
    racer = FilteredRacer(username, blacklist)
    return RacerCacheEntry(racer)

class RacerCacheEntry:

    def __init__(self, racer):
        self.racer = racer
        self.loadtime = datetime.now()

    @property
    def outdated(self):
        return datetime.now() - self.loadtime > TIME_THRESHOLD

class NameException(Exception):
    pass

# defines a cache of racers loaded from SRL
class RacerCache:

    def __init__(self, filename="racercache"):
        self.filename = filename
        if os.path.exists(filename):
            with open(filename, "rb") as cacheFile:
                self.entries = pickle.load(cacheFile)
        else:
            self.entries = dict()

    def __contains__(self, racer):
        return racer in self.entries

    def __iter__(self):
        for racer in self.entries:
            yield racer

    def refresh(self, username, bot, channel):
        try:
            bot.sendmsg(channel, "Loading data for " + username + "...")
            self.entries[username] = load(username, bot.blacklist)
            self.save()
        except:
            raise NameException(username)

    def getOrLoad(self, username, bot, channel):
        username = username.lower()
        if (username not in self.entries or self.entries[username].outdated):
            self.refresh(username, bot, channel)
        return self.entries[username].racer

    def save(self):
        with open(self.filename, "wb") as cacheFile:
            pickle.dump(self.entries, cacheFile)



