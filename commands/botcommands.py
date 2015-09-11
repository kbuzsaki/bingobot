import re
from srlparser import get_race_url
from command import command

CHANNEL_PATTERN = re.compile("^#.+$")

def hello(bot, msg):
    if msg.contains("Hello " + bot.nick) or msg.contains("Hi " + bot.nick):
        bot.sendmsg(msg.channel, "Hello, " + msg.sender + "!")


# built in commands

@command("say")
def say(bot, msg):
    if bot.has_admin(msg.sender):
        if CHANNEL_PATTERN.match(msg.arguments[0]):
            bot.sendmsg(msg.arguments[0], " ".join(msg.arguments[1:]))
        else:
            bot.sendmsg(msg.channel, " ".join(msg.arguments))

@command("command")
def bot_command(bot, msg):
    if bot.has_admin(msg.sender):
        bot.send(" ".join(msg.arguments) + "\n")

@command("clear")
def clear(bot, msg):
    if bot.has_admin(msg.sender):
        bot.racer_cache.clear()
        bot.sendmsg(msg.channel, "Cache cleared.")

# don't allow .join because that conflicts with racebot
@command(exacts=["!join"])
def join(bot, msg):
    for argument in msg.arguments:
        if CHANNEL_PATTERN.match(argument):
            bot.sendmsg(msg.channel, "Joining " + argument + "...")
            bot.joinchan(argument)
        else:
            bot.sendmsg(msg.channel, "Is \"" + argument + "\" a channel?")

@command("leave")
def leave(bot, msg):
    if msg.channel != "#bingoleague":
        bot.sendmsg(msg.channel, "Leaving " + msg.channel + "...")
        bot.leavechan(msg.channel)
    else:
        message = "Error, cannot !leave #bingoleague. Ask an op or voice to /kick or !kill."
        bot.sendmsg(msg.channel, message)

# op commands
@command("op")
def op(bot, msg):
    if bot.has_op(msg.sender):
        username = msg.usernames[0]
        if bot.has_op(username):
            message = username + " is already an op."
        else:
            bot.add_op(username)
            message = username + " has been opped."
        bot.sendmsg(msg.channel, message)

@command("deop")
def deop(bot, msg):
    if bot.has_op(msg.sender):
        username = msg.usernames[0]
        if bot.has_admin(username):
            message = username + " cannot be deopped."
        elif not bot.has_op(username):
            message = username + " is not an op."
        else:
            bot.remove_op(username)
            message = username + " has been deopped."
        bot.sendmsg(msg.channel, message)

@command("ops")
def ops(bot, msg):
    message = "Bot Ops: " + ", ".join(bot.ops)
    bot.sendmsg(msg.channel, message)

# blacklist commands
@command("blacklist")
def blacklist(bot, msg):
    if bot.has_op(msg.sender):
        race_id = msg.numbers[0]
        if race_id in bot.blacklist:
            message = "Race " + str(race_id) + " is already blacklisted."
        else:
            bot.blacklist.add(race_id)
            message = "Race " + str(race_id) + " has been blacklisted."
        bot.sendmsg(msg.channel, message)

@command("unblacklist")
def unblacklist(bot, msg):
    if bot.has_op(msg.sender):
        race_id = msg.numbers[0]
        if race_id not in bot.blacklist:
            message = "Race " + str(race_id) + " is not blacklisted."
        else:
            bot.blacklist.remove(race_id)
            message = "Race " + str(race_id) + " has been unblacklisted."
        bot.sendmsg(msg.channel, message)

@command("blacklisted")
def blacklisted(bot, msg):
    if msg.detailed:
        message = "Blacklisted Races:\n"
        message += "\n".join([get_race_url(race_id) for race_id in bot.blacklist])
    else:
        message = "Blacklisted Races: "
        message += ", ".join([str(race_id) for race_id in bot.blacklist])
    bot.sendmsg(msg.channel, message)

# op help commands
NAME = "RacerName"

@command("ophelp")
def ophelp(bot, msg):
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

