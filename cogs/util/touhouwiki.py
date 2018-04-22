import re
import mwclient
import json
import aiohttp
import asyncio


BASE = 'https://en.touhouwiki.net/wiki/'
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

PAGE_CACHE = {}


def stage_name(predicate):
    def wrapper(f):
        STAGE_NAMES.append((predicate, f))

    return wrapper


@stage_name(lambda link, name: link['s'] in STAGE_ABBREVS)
def abbrev_stage(link, _):
    link['s'] = f'Spell Cards/{STAGE_ABBREVS[link["s"]]}'


@stage_name(lambda link, name: link['s'] == name or link['g'] in ('IaMP', 'UNL', 'ULiL', 'SWR'))
def character_stage(link, name):
    link['s'] = f'Spell Cards/{link["s"]}'


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


def get_spellcards(cached=True):
    if cached:
        return json.load(open('bot_data/spellcards.json', 'r'))

    pages = [
        touhouwiki.pages[f'List of Spell Cards/Touhou Project {num}'] for num in range(1, 4)
    ]
    sections = []
    entries = []
    for page in pages:
        sections += find_sections(page)

    for section in sections:
        entries += gather_section(section)

    json.dump(entries, open('bot_data/spellcards.json', 'w'))
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
    appearances = []
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
        if sc_page in PAGE_CACHE:
            page_entries = PAGE_CACHE[sc_page]
        else:
            page = touhouwiki.pages[sc_page].text().replace('||', '|')
            page_entries = re.findall(r'{{Spell Card Info(.*?)\n}}', page, re.DOTALL)
            page_entries = [
                [
                    value.split('=', 1) for value in page_entry.split('\n|')
                ] for page_entry in page_entries
            ]
            page_entries = [
                {
                    value[0].strip(): value[1].strip() for value in page_entry if len(value) > 1
                } for page_entry in page_entries
            ]
            for page_entry in page_entries:
                page_entry['transname'] = re.sub(r'<ref>.*?</ref>', '', page_entry['transname'])
                page_entry['image'] = page_entry['image'].split('<br />')[0]
                if 'comment' in page_entry:
                    spell_links = re.findall(
                        r'(?:{{SC\|g=(.+?)\|s=(.+?)\|n=(.+?)(?:\|m=.+?)?}})|(?:\[\[(.+?)\|IN\]\])',
                        page_entry['comment']
                    )
                    while spell_links:
                        spell = spell_links.pop(0)
                        if spell[-1]: spell_link = f'[IN]({BASE+spell[-1]})'
                        else:
                            data = {'g': spell[0], 's': spell[1]}
                            for rule in STAGE_NAMES:
                                if rule[0](data, ''):
                                    rule[1](data, '')
                                    break

                            spell_link = f'[{spell[0]}]({BASE}{GAME_ABBREVS[spell[0]]}/' \
                                         f'{data["s"]}#Spell Card {spell[2]})'

                        page_entry['comment'] = re.sub(
                            r'({{.+?}})|(\[\[.+?\]\])', spell_link.replace(' ', '_'),
                            page_entry['comment'], count=1
                        )

                    page_entry['comment'] = page_entry['comment'].replace('<br />', '\n')

                if page_entry['image'].startswith('[[') and page_entry['image'].endswith(']]'):
                    page_entry['image'] = page_entry['image'][2:-2].split('|')

            PAGE_CACHE[sc_page] = page_entries

        for page_entry in page_entries:
            try: entry_number = int(page_entry['number'])
            except ValueError: entry_number = page_entry['number']

            try: link_number = int(link['n'])
            except ValueError: link_number = link['n']

            if entry_number == link_number or \
                any(page_entry['name'] == e['name'] for e in appearances):
                appearances.append({
                    'name': page_entry['name'],
                    'game': link['g'],
                    'image': page_entry['image'][0],
                    'difficulty': page_entry['difficulty'] if 'difficulty' in page_entry else 'Story',
                    'comment': page_entry['comment'] if 'comment' in page_entry else ''
                })


    def clean(text):
        text = re.sub(r'<ref>.*?</ref>', r'', text)
        text = re.sub(r'\[\[.*?\|(.*?)\]\]', r'\1', text)
        text = re.sub(r'{{.*?\|(.*?)\|.*?}}', r'\1', text)
        text = text.replace('<br>', ' / ')
        return text

    sorted_entry = {
        'japanese': clean(entry[0]),
        'english': clean(entry[1]),
        'comments': entry[2].replace("''", '*'),
        'owner': name,
        'appearances': appearances
    }
    return sorted_entry


async def get_thumbnail(character):
    thumbnail = touhouwiki.pages[character].text(section=0)
    thumbnail = re.search(r'{{Infobox Character\n(.*)\n}}', thumbnail, re.DOTALL).group(1).split('\n|')
    for section in thumbnail:
        if section.strip().startswith('image'):
            thumbnail = section.split('=')[1].strip()[2:-2].split('|')[0]
            break

    return await get_image_url(thumbnail)

async def get_image_url(image):
    async with aiohttp.ClientSession() as session:
        page = await session.get(f'https://en.touhouwiki.net/wiki/{image}')

    page = await page.text()
    page = re.search(r'<img (.*?) />', page).group(1).split(' ')
    for value in page:
        if value.startswith('src'):
            page = value.split('=')[1][1:-1]
            return f'https://en.touhouwiki.net{page}'


if __name__ == '__main__':
    spellcards = get_spellcards(cached=True)
