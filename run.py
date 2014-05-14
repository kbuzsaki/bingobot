from bingobot import BingoBot
from botcommands import allCommands

server = "irc2.speedrunslive.com"
channel = "#bingoleague"
botnick = "BingoBot"

bingoBot = BingoBot(botnick, server, channel, commands = allCommands)

# infinite loop tries to reconnect if disconnected by timeout
while True:
    bingoBot.connect()
    bingoBot.listen()
    

