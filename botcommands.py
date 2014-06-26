import re
from srlparser import getRaceUrl

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

def clear(bot, msg):
    if msg.command == "!clear":
        if bot.hasAdmin(msg.sender):
            bot.racerCache.clear()
            bot.sendmsg(msg.channel, "Cache cleared.")
             
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

# op commands
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

# blacklist commands 
def blacklist(bot, msg):
    if msg.command == "!blacklist":
        if bot.hasOp(msg.sender):
            raceId = msg.numbers[0]
            if raceId in bot.blacklist:
                message = "Race " + str(raceId) + " is already blacklisted."
            else:
                bot.blacklist.add(raceId)
                message = "Race " + str(raceId) + " has been blacklisted."
            bot.sendmsg(msg.channel, message)

def unblacklist(bot, msg):
    if msg.command == "!unblacklist":
        if bot.hasOp(msg.sender):
            raceId = msg.numbers[0]
            if raceId not in bot.blacklist:
                message = "Race " + str(raceId) + " is not blacklisted."
            else:
                bot.blacklist.remove(raceId)
                message = "Race " + str(raceId) + " has been unblacklisted."
            bot.sendmsg(msg.channel, message)

def blacklisted(bot, msg):
    if msg.command == "!blacklisted":
        if msg.detailed:
            message = "Blacklisted Races:\n"
            message += "\n".join([getRaceUrl(raceId) for raceId in bot.blacklist])
        else:
            message = "Blacklisted Races: " 
            message += ", ".join([str(raceId) for raceId in bot.blacklist]) 
        bot.sendmsg(msg.channel, message)
    
# op help commands
NAME = "RacerName"

def ophelp(bot, msg):
    if msg.command != "!ophelp":
        return
    search = msg.arguments[0] if len(msg.arguments) > 0 else None

    if search == None:
        message = "Operator Commands: !op, !deop, !blacklist, !unblacklist, !kill\n"
        message += "Run !ophelp <command> to get detailed help for a command."
    elif "deop" in search:
        message = "Removes operator status from a user. Prevents them from using operator commands.\n"
        message += "Example: \"!deop " + NAME + "\""
    elif "op" in search:
        message = "Gives operator status from a user. Lets them use operator commands.\n"
        message += "Example: \"!op " + NAME + "\""
    elif "unblacklist" in search:
        message = "Reverses a blacklisting, causing BingoBot to again use a race when calculating results. "
        message += "Use the race's ID to identify it.\n"
        message += "Example: \"!unblacklist 100176\""
    elif "blacklist" in search:
        message = "Blacklists a given race, causing BingoBot to ignore it when calculating results. "
        message += "Use the race's ID to identify it.\n"
        message += "Example: \"!blacklist 100176\""
    elif "kill" in search:
        message = "Causes BingoBot to shutdown. Use only in emergency situations if Bingo is misbehaving. "
        message += "BingoBot will be unavailable until it is restarted by Saltor.\n"
        message += "Example: \"!kill\""
    else:
        message = "No help information for " + msg.arguments[0]

    bot.sendmsg(msg.channel, message)

adminCommands = [say, command, clear]
opCommands = [op, deop, blacklist, unblacklist]
otherCommands = [hello, join, leave, ops, blacklisted, ophelp]
builtinCommands = adminCommands + opCommands + otherCommands

# end built in commands
             
