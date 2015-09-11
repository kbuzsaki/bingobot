import functools

# command decorator
# only invokes the function if msg.command is one of the
# provided commands, or if one of the predicates is met.
def command(*commands, exacts=set(), predicates=set()):
    mod_commands = {"!" + cmd for cmd in commands}
    mod_commands |= {"." + cmd for cmd in commands}
    mod_commands |= set(exacts)

    def decorator(func):
        @functools.wraps(func)
        def replacement(bot, msg):
            command_match = msg.command in mod_commands
            predicate_match = any(predicate(msg) for predicate in predicates)

            if command_match or predicate_match:
                func(bot, msg)

        command.loaded_commands.append(replacement)

        return replacement
    return decorator

command.loaded_commands = []


