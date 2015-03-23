from urllib.request import urlopen
import execjs
import json
import random
from botcommands import command

SRL_BASE = "http://speedrunslive.com"
BINGO_URL = SRL_BASE + "/tools/oot-bingo"

def loadGenerator():
    # super hacky way to load the generator js from srl so it's not stored in the repo
    pageText = urlopen(BINGO_URL).read().decode("utf-8").split()
    jsUrlLine = [line for line in pageText if "bingo" in line and "script" in line][0]
    jsUrl = jsUrlLine.split('"')[1]

    # srl stores the generator in strings and evals them on the page
    # so we need to add evals for the string variables
    jsText = urlopen(SRL_BASE + jsUrl).read().decode("utf-8")
    varNames = [line.split(" ")[1] for line in jsText.split("\n") if " " in line]
    # only the first 3 lines are actually used for the generator
    # the rest are for the ui and use jquery which we don't want to load
    varNames = varNames[:3]

    varEval = "\n".join("eval(" + varName + ");" for varName in varNames)
    fullJs = jsText + varEval + "\n"
    return BingoGenerator(fullJs)


class BingoGenerator:
    CACHED_INSTANCE = None

    @staticmethod
    def loaded():
        return BingoGenerator.CACHED_INSTANCE is not None

    @staticmethod
    def instance():
        if not BingoGenerator.CACHED_INSTANCE:
            BingoGenerator.CACHED_INSTANCE = loadGenerator()
        return BingoGenerator.CACHED_INSTANCE

    @staticmethod
    def reload():
        BingoGenerator.CACHED_INSTANCE = loadGenerator()

    def __init__(self, generatorJs):
        self.context = execjs.compile(generatorJs)

    def getCard(self, seed=None):
        if seed is not None:
            opts = "{ seed: " + str(seed) + " }"
        else:
            opts = "{}"

        jscommand = "ootBingoGenerator(bingoList, " + opts + ")"
        card = self.context.eval(jscommand)
        # for some reason the first element of the list is a garbage None?
        card = card[1:]

        return card

    def getBlackoutCard(self, teamSize=3):
        # just try to generate a bunch of cards
        # if we fail too many times, abort
        for attempt in range(10):
            seed = random.randint(0, 1000000)
            print("trying seed: " + str(seed))
            card = self.getCard(seed)
            if isBlackoutCard(card, teamSize):
                return seed, card
        raise Exception("Failed to generate card for teamsize: " + str(teamSize))


def isBlackoutCard(card, teamSize=3):
    names = [goal["name"] for goal in card]

    # no duplicates allowed
    if len(names) != len(set(names)):
        return False

    return True

def getCardUrl(seed):
    return SRL_BASE + "/tools/oot-bingo/?seed=" + str(seed)

@command("blackoutcard")
def generateBlackoutCard(bot, msg):
    if not BingoGenerator.loaded():
        bot.sendmsg(msg.channel, "Loading Bingo Generator...")
    generator = BingoGenerator.instance()

    seed, card = generator.getBlackoutCard()
    bot.sendmsg(msg.channel, getCardUrl(seed))


allCommands = [generateBlackoutCard]

