from bingobot import BingoBot
from botcommands import allCommands

server = "irc2.speedrunslive.com"
channel = "#test"
botnick = "BingoBot"

bingoBot = BingoBot(botnick, server, channel, commands = allCommands)
bingoBot.connect()
bingoBot.listen()
    

