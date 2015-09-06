import time
import traceback
from datetime import datetime, timedelta
from termcolor import colored
from bingobot import BingoBot
import basiccommands
import teamcommands
import racecommands

TWO_MINUTES = timedelta(minutes=2)

RETRY_INTERVAL = timedelta(minutes=1)

server = "irc2.speedrunslive.com"
channels = ["#bingoleague", "#speedrunslive"]
botnick = "BingoBot"
password = ""
allCommands = basiccommands.allCommands + teamcommands.allCommands + racecommands.allCommands

with open("data/password", "r") as passwordFile:
    password = passwordFile.readline()

bingoBot = BingoBot(botnick, password, server, channels, commands = allCommands)

lastConnection = datetime(year=1999, month=1, day=1)

# infinite loop tries to reconnect if disconnected by timeout
while True:
    timeSinceLastConnection = datetime.now() - lastConnection
    if timeSinceLastConnection < RETRY_INTERVAL:
        time.sleep(60)

    lastConnection = datetime.now()

    try:
        print("Connecting to server...")
        bingoBot.connect()
        bingoBot.listen()
    except Exception as e:
        print(colored("Encountered exception while running:", "red"))
        print(colored(traceback.format_exc(), "red"))
        print(colored("Will retry within 60 seconds...", "red"))


