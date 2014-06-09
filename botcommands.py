import re

channelPattern = re.compile("^#.+$")

def hello(bot, msg):
    if msg.contains("Hello " + bot.nick) or msg.contains("Hi " + bot.nick):
        bot.sendmsg(msg.channel, "Hello, " + msg.sender + "!")

# built in commands

def say(bot, msg):
    if msg.command == "!say":
        if bot.hasAdmin(msg.sender):
            if channelPattern.match(msg.arguments[0]):
                bot.sendmsg(msg.arguments[0], " ".join(msg.arguments[1:]))
            else:
                bot.sendmsg(msg.channel, " ".join(msg.arguments))

def command(bot, msg):
    if msg.command == "!command":
        if bot.hasAdmin(msg.sender):
            bot.send(" ".join(msg.arguments) + "\n")
             
def join(bot, msg):
    if msg.command == "!join":
        for argument in msg.arguments:
            if channelPattern.match(argument):
                bot.sendmsg(msg.channel, "Joining " + argument + "...")
                bot.joinchan(argument)
            else:
                bot.sendmsg(msg.channel, "Is \"" + argument + "\" a channel?") 
        
def leave(bot, msg):
    if msg.command == "!leave":
        if msg.channel != "#bingoleague":
            bot.sendmsg(msg.channel, "Leaving " + msg.channel + "...")
            bot.leavechan(msg.channel)
        else:
            message = "Error, cannot !leave #bingoleague. Ask an op or voice to /kick or !kill."
            bot.sendmsg(msg.channel, message)

def op(bot, msg):
    if msg.command == "!op":
        if bot.hasOp(msg.sender):
            username = msg.usernames[0]
            if bot.hasOp(username):
                message = username + " is already an op."
            else:
                bot.addOp(username)
                message = username + " has been opped."
            bot.sendmsg(msg.channel, message)

def deop(bot, msg):
    if msg.command == "!deop":
        if bot.hasOp(msg.sender):
            username = msg.usernames[0]
            if bot.hasAdmin(username):
                message = username + " cannot be deopped."
            elif not bot.hasOp(username):
                message = username + " is not an op."
            else:
                bot.removeOp(username)
                message = username + " has been deopped."
            bot.sendmsg(msg.channel, message)

def ops(bot, msg):
    if msg.command == "!ops":
        message = "Bot Ops: " + ", ".join(bot.ops) 
        bot.sendmsg(msg.channel, message)

    
builtinCommands = [hello, say, command, join, leave, op, deop, ops]

# end built in commands
             
