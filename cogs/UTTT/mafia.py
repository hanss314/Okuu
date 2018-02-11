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

        messages = random.choice(stories)
        if game['will_die']:
            await bot.get_channel(game['channel']).send(
                messages[0].format(dead=bot.get_user(game['will_die'][0]))
            )
            if len(game['will_die']) > 1 and game['will_die'][1] == game['will_die'][0]:
                await bot.get_channel(game['channel']).send(
                    messages[1].format(dead=bot.get_user(game['will_die'][0]))
                )
            else:
                kill(game, game['will_die'][0])

        game['candidates'] = [
            p for p in game['players'].keys()
            if p not in game['dead']
        ]
        game['can_vote'] = list(game['candidates'])
        game['phase'] = 63

    elif game['phase'] == 63:
        kill(game, game['candidates'][0])

    increment_phase(game)
    win_state = check_win(game)
    if win_state == -1:
        await bot.get_channel(game['channel']).send('All the innocents are dead. The mafia win!')
        return -1
    elif win_state == 1:
        await bot.get_channel(game['channel']).send('The mafia are dead. The villagers win!')
        return 1
    await prompt_voting(bot, game)
    return 0


def increment_phase(game):
    if game['phase'] == 1 and (game['doctor'] is None or game['doctor'] in game['dead']):
        game['can_vote'] = [game['detective']]
        game['phase'] = 2
        increment_phase(game)

    elif game['phase'] == 2 and (game['detective'] is None or game['detective'] in game['dead']):
        game['candidates'] = [
            p for p in game['players'].keys()
            if p not in game['dead']
        ]
        game['can_vote'] = list(game['candidates'])
        game['phase'] = 63
        increment_phase(game)


def kill(game, user):
    if user in game['mafia']:
        game['mafia'].remove(user)

    if user == game['doctor']:
        game['doctor'] = None

    if user == game['detective']:
        game['detective'] = None

    game['dead'].append(user)

    if user in game['candidates']:
        game['candidates'].remove(user)

    game['will_die'] = []


def check_win(game):
    for player in game['players'].keys():
        # if a living player is not a mafia
        if player not in game['dead'] and player not in game['mafia']:
            break

    else:
        # if no living players are not mafia, mafia win
        return -1

    for player in game['mafia']:
        # if mafia is alive
        if player not in game['dead']:
            break

    else:
        # if no mafia are alive villagers win
        return 1

    # no winstate
    return 0


stories = [
    (
        '{dead} fell into a nuclear reactor and burned so hard there were no ashes left.',
        'but that was nothing that couldn\'t be fixed with some shady drugs'
    )
]
