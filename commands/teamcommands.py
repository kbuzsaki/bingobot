from datetime import timedelta

from command import command
from commands.basiccommands import format_time

NUMBERS = "one two three four five six seven eight nine ten eleven twelve".split()

def get_patterns(patterns_filename):
    with open(patterns_filename) as patterns_file:
        return [get_pattern(line.strip()) for line in patterns_file]

def get_pattern(line):
    return [int(digit, 16) for digit in line]

PATTERNS_DICT = {
    2: {
        2: get_patterns("patterns/teams22")
    },
    3: {
        2: get_patterns("patterns/teams2"),
        3: get_patterns("patterns/teams3"),
        4: get_patterns("patterns/teams4")
    }
}


def mult_delta(delta, factor):
    seconds = delta.total_seconds() * factor
    return timedelta(seconds=seconds)

def chunk_list(elements, step=3):
    chunks = len(elements) // step
    for index in range(chunks):
        begin = index * step
        end = (index + 1) * step
        yield elements[begin:end]

def variance(elements):
    mean = sum(elements) / len(elements)
    squares = [(mean - element) ** 2 for element in elements]
    return sum(squares) / len(squares)

# constants and helpers for team_time()
AVG_BLACKOUT = timedelta(hours=3, minutes=15)
AVG_REGULAR = timedelta(hours=1, minutes=20)
AVG_BASE = timedelta(minutes=30)
AVG_OVERLAP = timedelta(minutes=5)

class Participant:

    def __init__(self, time, success_rate, name):
        self.time = time
        self.success_rate = success_rate
        self.name = name

    @classmethod
    def from_racher(constructor, racer):
        return constructor(racer.median_time(0, 15), max(racer.completion_rate(), 0.5), racer.username)

    @classmethod
    def from_time(constructor, time):
        return constructor(time, 1.0, str(time))

    @property
    def net_time(self):
        return self.time - AVG_BASE

    @property
    def effective_rate(self):
        return mult_delta(self.net_time, 1 / self.success_rate)

    @property
    def work_rate(self):
        return 1 / self.effective_rate.total_seconds()

    def __eq__(self, other):
        return self.work_rate == other.work_rate

    def __lt__(self, other):
        return self.work_rate < other.work_rate

def get_participants(bot, msg):
    racers = [bot.get_racer(msg.channel, username, msg.refresh) for username in msg.usernames]
    participants = [Participant.from_racher(racer) for racer in racers]
    participants += [Participant.from_time(time) for time in msg.times]
    return participants


def total_work_rate(participants):
    return sum([participant.work_rate for participant in participants])

def get_team_time(team):
    combined_work_rate = total_work_rate(team)
    # work rate is then used to calculate net average time for a normal bingo
    combined_rate = timedelta(seconds=(1 / combined_work_rate))

    # the team's net average time is then scaled up to blackout scale
    ratio = (AVG_BLACKOUT - AVG_BASE).total_seconds() / (AVG_REGULAR - AVG_BASE).total_seconds()
    # the base 30 minutes are added back to convert the net time to total time
    blackout_time = mult_delta(combined_rate, ratio) + AVG_BASE + AVG_OVERLAP

    return blackout_time

@command("teamtime")
def team_time(bot, msg):
    participants = get_participants(bot, msg)

    blackout_time = get_team_time(participants)

    message = "Team \"" + ", ".join(msg.usernames + [str(time) for time in msg.times])
    message += "\" would take about " + format_time(blackout_time) + " to complete a blackout."
    bot.sendmsg(msg.channel, message)

@command("balance")
def balance(bot, msg):
    participants = get_participants(bot, msg)

    # ensure that a valid number of participants have been passed
    if len(participants) not in [4, 6, 9, 12]:
        message = "Please provide a total of 4, 6, 9, or 12 usernames/times to balance."
        bot.sendmsg(msg.channel, message)
        return

    if len(participants) == 4:
        team_size = 2
    else:
        team_size = 3

    num_teams = len(participants) // team_size
    optimal_teams = list(chunk_list(participants, team_size))
    optimal_variance = variance([get_team_time(team).total_seconds() for team in optimal_teams])
    for pattern in PATTERNS_DICT[team_size][num_teams]:
        order = [participants[x] for x in pattern]
        new_teams = list(chunk_list(order, team_size))
        new_variance = variance([get_team_time(team).total_seconds() for team in new_teams])
        if new_variance < optimal_variance:
            optimal_teams = new_teams
            optimal_variance = new_variance

    message = ""
    for index, team in enumerate(optimal_teams):
        message += "Team " + NUMBERS[index] + ": \"" + ", ".join([participant.name for participant in team])
        message += "\" (" + format_time(get_team_time(team)) + ")\n"
    bot.sendmsg(msg.channel, message)

@command("fastbalance")
def fast_balance(bot, msg):
    participants = get_participants(bot, msg)

    if len(participants) % 3 != 0:
        message = "Must be divisible by three to form teams"
        bot.sendmsg(msg.channel, message)
        return

    # sort so highest work rates are at the top
    participants = sorted(participants, reverse=True)

    # sort into three tiers of players
    num_teams = len(participants) // 3

    tier_one = participants[:num_teams]
    tier_two = participants[num_teams:num_teams * 2]
    tier_three = participants[num_teams * 2:]

    teams = []

    # pair the best of tier 1 with worst of tier 2
    for player_index in range(num_teams):
        teams.append([tier_one[player_index], tier_two[-player_index - 1]])

    # sorts the resulting teams with highest work rates at the top
    team_rate = lambda team: team[0].work_rate + team[1].work_rate
    teams = sorted(teams, key=team_rate, reverse=True)

    # pair the best current teams with the worst tier 3 players
    for player_index in range(num_teams):
        teams[player_index].append(tier_three[-player_index - 1])

    message = ""
    for index, team in enumerate(teams):
        message += "Team " + NUMBERS[index] + ": \"" + ", ".join([participant.name for participant in team])
        message += "\" (" + format_time(get_team_time(team)) + ")\n"
    bot.sendmsg(msg.channel, message)

