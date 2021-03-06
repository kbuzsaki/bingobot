from datetime import datetime, timedelta
import os
import pickle

from blacklist import FilteredRacer

TIME_THRESHOLD = timedelta(hours=1)

def load(username, blacklist):
    racer = FilteredRacer(username, blacklist)
    return RacerCacheEntry(racer)

class RacerCacheEntry:

    def __init__(self, racer):
        self.racer = racer
        self.loadtime = datetime.now()

    def update(self):
        self.racer.update()
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
            with open(filename, "rb") as cache_file:
                self.entries = pickle.load(cache_file)
        else:
            self.entries = dict()

    def __contains__(self, racer):
        return racer in self.entries

    def __iter__(self):
        for racer in self.entries:
            yield racer

    def clear(self):
        self.entries.clear()
        self.save()

    def refresh(self, username, bot, channel):
        try:
            bot.sendmsg(channel, "Loading data for " + username + "...")
            self.entries[username] = load(username, bot.blacklist)
            self.save()
        except:
            raise NameException(username)

    def update(self, username, bot, channel):
        bot.sendmsg(channel, "Updating data for " + username + "...")
        self.entries[username].update()
        self.save()

    def get_or_load(self, username, bot, channel):
        username = username.lower()
        if username not in self.entries:
            self.refresh(username, bot, channel)
        if self.entries[username].outdated:
            self.update(username, bot, channel)
        # hack for fixing blacklist bug
        self.entries[username].racer.blacklist = bot.blacklist
        return self.entries[username].racer

    def save(self):
        with open(self.filename, "wb") as cache_file:
            pickle.dump(self.entries, cache_file)



