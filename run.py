from datetime import datetime, timedelta
from bingobot import BingoBot
from botcommands import allCommands

TWO_MINUTES = timedelta(minutes=2)

server = "irc2.speedrunslive.com"
channel = "#bingoleague"
botnick = "BingoBot"

bingoBot = BingoBot(botnick, server, channel, commands = allCommands)

lastConnection = datetime(year=1999, month=1, day=1)

# infinite loop tries to reconnect if disconnected by timeout
while datetime.now() - lastConnection > TWO_MINUTES:
    lastConnection = datetime.now()
    bingoBot.connect()
    bingoBot.listen()
    

