import time
import traceback
from datetime import datetime, timedelta
from termcolor import colored
from bingobot import BingoBot
import glob
import importlib

import command

TWO_MINUTES = timedelta(minutes=2)

RETRY_INTERVAL = timedelta(minutes=1)

server = "irc2.speedrunslive.com"
channels = ["#bingoleague", "#speedrunslive"]
botnick = "BingoBot"
password = ""

loaded_modules = []

def load_commands(path="./commands"):
    for module_path in glob.glob("commands/*.py"):
        # hackily get the actual name of the module (the * here)
        module_name = "commands." + module_path[9:-3]
        module = importlib.import_module(module_name)
        loaded_modules.append(module)

    return command.command.loaded_commands

all_commands = load_commands()

with open("data/password", "r") as password_file:
    password = password_file.readline()

bingo_bot = BingoBot(botnick, password, server, channels, commands = all_commands)

last_connection = datetime(year=1999, month=1, day=1)

# infinite loop tries to reconnect if disconnected by timeout
while True:
    time_since_last_connection = datetime.now() - last_connection
    if time_since_last_connection < RETRY_INTERVAL:
        time.sleep(60)

    last_connection = datetime.now()

    try:
        print("Connecting to server...")
        bingo_bot.connect()
        bingo_bot.listen()
    except Exception as e:
        print(colored("Encountered exception while running:", "red"))
        print(colored(traceback.format_exc(), "red"))
        print(colored("Will retry within 60 seconds...", "red"))


