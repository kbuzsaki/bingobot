from datetime import datetime, timedelta
import glob
import importlib
import sys
import time
import traceback

from bingobot import BingoBot, KillException
import command
from ircconn import ConsoleIrcConnection, IrcConnection
from logger import logger, Priority

TWO_MINUTES = timedelta(minutes=2)

RETRY_INTERVAL = timedelta(minutes=1)

server = "irc2.speedrunslive.com"
channels = ["#bingoleague", "#speedrunslive"]
nick = "BingoBot"
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

if "--cli" in sys.argv:
    connection = ConsoleIrcConnection(nick, server)
    logger.threshold = Priority.error
else:
    connection = IrcConnection(nick, server)

bingo_bot = BingoBot(nick, password, connection, channels, commands=all_commands)

last_connection = datetime(year=1999, month=1, day=1)

# infinite loop tries to reconnect if disconnected by timeout
while True:
    time_since_last_connection = datetime.now() - last_connection
    if time_since_last_connection < RETRY_INTERVAL:
        time.sleep(60)

    last_connection = datetime.now()

    try:
        logger.log("Connecting to server...")
        bingo_bot.connect()
        bingo_bot.listen()
    except KillException as e:
        logger.error("Got KillException: " + str(e))
        sys.exit()
    except Exception as e:
        logger.error("Encountered exception while running:")
        logger.error(traceback.format_exc())
        logger.error("Will retry within 60 seconds...")


