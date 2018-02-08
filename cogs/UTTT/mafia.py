import random


def new_game(channel):
    return {
        'channel': channel,
        'players': {},
        'dead': [],
        'mafia': [],
        'candidates': [],
        'detective': None,
        'doctor': None,
        'innocents': [],
        'started': False,
        'will_die': None,
        'phase': 0,  # 0 = mafia, 1 = doctor, 2 = detective, 63 = daytime
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
    game['innocents'] = [
        p for p in game['players'].keys()
        if p not in specials
    ]
    game['detective'] = specials.pop()
    game['doctor'] = specials.pop()
    game['mafia'] = specials
    game['candidates'] = [
        p for p in game['players'].keys()
        if p not in game['mafia'] and p not in game['dead']
    ]
    game['can_vote'] = [p for p in game['mafia']]
    game['started'] = True


async def prompt_voting(bot, game):
    if game['phase'] == 0:
        m = '**Pick someone to be killed.**\n\n'
    elif game['phase'] == 1:
        m = '**Pick someone to save.**\n\n'
    elif game['phase'] == 2:
        m = '**Pick someone to investigate.**\n\n'
    else:
        m = '**Pick someone to lynch.**\n\n'

    for n, candidate in enumerate(game['candidates']):
        m += f'{n}. *{bot.get_user(candidate)}'

    for voter in game['can_vote']:
        await bot.get_user(voter).send(m)


def process_votes(game):
    votes = {}
    for vote in game['votes'].values():
        try:
            votes[vote] += 1
        except KeyError:
            votes[vote] = 1

    most = max(votes.values())
    candidates = [game['candidates'][k] for k, v in votes.items() if v == most]
    game['candidates'] = candidates
    game['votes'] = {}


async def next_phase(bot, game):
    '''Called when voting is done'''
    m = f'Selected {bot.get_user(game["candidates"][0])}'
    for voter in game['can_vote']:
        await bot.get_user(voter).send(m)

    if game['phase'] == 0:
        game['will_die'] = game['candidates']
        game['candidates'] = [
            p for p in game['players'].keys()
            if p not in game['dead']
        ]
        game['can_vote'] = [game['doctor']]
        game['phase'] = 1

    elif game['phase'] == 1:
        game['will_die'].append(game['candidates'][0])
        game['candidates'] = [
            p for p in game['players'].keys()
            if p not in game['dead'] and p != game['detective']
        ]
        game['can_vote'] = [game['detective']]
        game['phase'] = 2

    elif game['phase'] == 2:
        selected = bot.get_user(game['candidates'][0])
        detective = bot.get_user(game['detective'])
        if selected in game['mafia']:
            await detective.send(f'{selected} is in the mafia.')
        elif selected == game['doctor']:
            await detective.send(f'{selected} is the doctor.')
        else:
            await detective.send(f'{selected} is an innocent.')

        game['phase'] = 63


stories = [
    (
        '{dead} fell into a nuclear reactor and burned so hard there were no ashes left.',
        'but that was nothing that couldn\'t be fixed with some shady drugs'
    )
]
