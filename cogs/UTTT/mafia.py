import random


def new_game(channel):
    return {
        'channel': channel,
        'players': {},
        'dead': [],
        'mafia': [],
        'detective': None,
        'doctor': None,
        'innocents': [],
        'started': False,
        'will_die': [],
        'night': True,
        'can_vote': [],
        'votes': {}
    }


def new_player():
    return {
        'can_start': False
    }


def start(game):
    mafias = round(len(game['players']) ** 0.5)
    specials = random.sample(game['players'].keys(), mafias + 2)
    game['detective'] = specials.pop()
    game['doctor'] = specials.pop()
    game['mafia'] = specials
    game['started'] = True
