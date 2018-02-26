import re
import mwclient

touhouwiki = mwclient.Site('en.touhouwiki.net/', path='')

GAME_ABBREVS = {
    'EoSD': 'Embodiment of Scarlet Devil',
    'PCB': 'Perfect Cherry Blossom',
    'IaMP': 'Immaterial and Missing Power',
    'IN': 'Imperishable Night',
    'PoFV': 'Phantasmagoria of Flower View',
    'StB': 'Shoot the Bullet',
    'MoF': 'Mountain of Faith',
    'SWR': 'Scarlet Weather Rhapsody',
    'SA': 'Subterranean Animism',
    'UFO': 'Undefined Fantastic Object',
    'Soku': 'Touhou Hisoutensoku',
    'HSTS': 'Touhou Hisoutensoku',
    'DS': 'Double Spoiler',
    'FW': 'Fairy Wars',
    'TD': 'Ten Desires',
    'HM': 'Hopeless Masquerade',
    'DDC': 'Double Dealing Character',
    'ISC': 'Impossible Spell Card',
    'ULiL': 'Urban Legend in Limbo',
    'LoLK': 'Legacy of Lunatic Kingdom',
    'AoCF': 'Antimony of Common Flowers',
    'HSiFS': 'Hidden Star in Four Seasons',
    'GoM': 'The Grimoire of Marisa'
}

STAGE_ABBREVS = {
    'EX': 'Extra',
    'PH': 'Phantasm',
    'LW': 'Last Word',
    'SP': 'Spoiler Stage'
}

STAGE_NAMES = []


def stage_name(predicate):
    def wrapper(f):
        STAGE_NAMES.append((predicate, f))

    return wrapper


@stage_name(lambda link, name: link['s'] in STAGE_ABBREVS)
def abbrev_stage(link, _):
    link['s'] = f'Spell Cards/{STAGE_ABBREVS[link["s"]]}'


@stage_name(lambda link, name: link['s'] == name)
def character_stage(link, name):
    link['s'] = f'Spell Cards/{name}'


@stage_name(lambda link, name: link['g'] in ('DS', 'StB'))
def level_stage(link, _):
    link['s'] = f'Spell Cards/Level {link["s"]}'


@stage_name(lambda link, name: link['g'] == 'ISC')
def day_stage(link, _):
    link['s'] = f'Spell Cards/{link["s"]}'


'''
@stage_name(lambda link, name: link['g'] == 'GoM')
def grimoire(link, name):
    link['s'] = f"{name}'s Spell Cards"
    if touhouwiki.pages[link['s']].text() == '':
        link['s'] = f"{name}'s Spell Card"

'''


@stage_name(lambda _, __: True)
def otherwise(link, _):
    link['s'] = f'Spell Cards/Stage {link["s"]}'


def get_spellcards():
    pages = [
        touhouwiki.pages[f'List of Spell Cards/Touhou Project {num}'] for num in range(1, 2)
    ]
    sections = []
    entries = []
    for page in pages:
        sections += find_sections(page)

    for section in sections:
        entries += gather_section(section)

    return entries


def find_sections(page):
    section = 1
    sections = []
    while True:
        try:
            sections.append(page.text(section=section))
        except mwclient.errors.APIError:
            sections.pop()
            break
        section += 1

    return sections


def gather_section(section):
    name = re.search(r'==\[\[(.*)\]\]==', section.split('|-')[0]).group(1)
    raw_entries = [
        [
            section.strip('\n') for section in entry.strip('|').split('\n|')
        ] for entry in section.split('|-') if entry.strip().startswith('|')
    ]
    entries = [entry[1:] for entry in raw_entries if len(entry) > 2]
    entries = [sort_entry(name, entry) for entry in entries]
    return entries


def sort_entry(name, entry):
    if entry[-1] == '}': entry.pop()
    if len(entry) != 5: print(entry)
    links = []
    for link in entry[3].split('<br>'):
        link = link.strip('|').strip()
        if not (link.startswith('{{') and link.endswith('}}')):
            continue

        link = link[2:-2].split('|')[1:]
        link = {k: v for k, v in (f.split('=') for f in link)}
        if link['g'] == 'GoM': continue
        for rule in STAGE_NAMES:
            if rule[0](link, name):
                rule[1](link, name)
                break

        sc_page = f"{GAME_ABBREVS[link['g']]}/{link['s']}"
        print(link, sc_page)

    sorted_entry = {
        'japanese': entry[0],
        'english': entry[1],
        'comments': entry[2].replace("''", '*'),
        'owner': name,
        'links': links
    }
    return sorted_entry


if __name__ == '__main__':
    print(get_spellcards())
