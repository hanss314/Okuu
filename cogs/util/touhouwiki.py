import re
import json
import aiohttp
import requests
import mwclient


BASE = 'https://en.touhouwiki.net'
touhouwiki = mwclient.Site('en.touhouwiki.net/', path='')

tablere = re.compile(
    r'<h2><span class="mw-headline" id=".+?"><a href="/wiki/.+?" title="(.+?)">\1</a></span></h2>\n'
    r'<table class="wikitable sortable" style="text-align: center;">\n?(.+?)</table>',
    re.DOTALL | re.MULTILINE
)

rowre = re.compile(r'<tr>\n?(<td>.+?)</tr>', re.DOTALL | re.MULTILINE)
colre = re.compile(r'<td>(.*?)\n?</td>', re.DOTALL | re.MULTILINE)
appearancere = re.compile(r'<a.*? href="(.+?)".*?>(.+?)</a>')
spellcardre = re.compile(
    r'<h3><span class="mw-headline" id="(.+?)">.+?</span></h3>\n'
    r'<table .+?>\n(.+?)</table>',
    re.DOTALL | re.MULTILINE
)
spellfieldsre = re.compile(r'<tr.*?>\n?(.+?)</tr>', re.DOTALL | re.MULTILINE)
spellimagere = re.compile(r'<img .*?src="(.+?)".*?>', re.DOTALL | re.MULTILINE)
spellnamere = re.compile(r'<span lang="ja">.+?</span><br />(.+?)<.+?>')
spelldiffre = re.compile(r'<th.*?>Owner:</th>\n\W*<td.*?>.+?<br />(.*?)&#8212;(.*?)<.+?>', re.DOTALL | re.MULTILINE)
diffre = re.compile(r'(Easy|Normal|Hard|Lunatic|Extra|Last Word|Phantasm|Overdrive|Level (\d{1,2}|E[Xx]|Spoiler)|(\d\W{2}|Last) Day)')
spellcommre = re.compile(
    r'<th.*?>(?:Comment|Translation):</th>\n\s*<td.*?>(.*?)</td>',
    re.DOTALL | re.MULTILINE
)
gomcardre = re.compile(r'<table.*?style="border-collapse: collapse;".*?>\n(.+?)</table>', re.DOTALL | re.MULTILINE)
gomcommre = re.compile(r'<(t[hd]).*?>(.+?)</\1>', re.DOTALL | re.MULTILINE)

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

EXCEPTIONS = {
    'Superman "Soaring En no Ozuno"': 'Superman "Soaring En no Ozunu"',
    'Barrier "Curse of Dreams and Reality"': 'Bounded Field "Curse of Dreams and Reality"',
    'Barrier "Balance of Motion and Stillness"': 'Bounded Field "Balance of Motion and Stillness"',
    'Barrier "Mesh of Light and Darkness"': 'Bounded Field "Mesh of Light and Darkness"',
    'Yukari\'s Arcanum "Danmaku Barrier"': 'Yukari\'s Arcanum "Danmaku Bounded Field"',
    'Fantasy "Perpetual Motion Machine of the First Kind"': 'Phantasm "Perpetual Motion Machine of the First Kind"',
    'Border Sign "Boundary of Wave and Particle"': 'Boundary Sign "Boundary between Wave and Particle"',
    'Oni Sign "Complete Massacre on Mt. Ooe"': 'Oni Sign "Complete Massacre on Mt.Ooe"',
    '/wiki/Antinomy_of_Common_Flowers/Spell_Cards/Reisen_Udongein_Inaba#Spell_Card_Story_Mode_1': '/wiki/Antinomy_of_Common_Flowers/Spell_Cards/Reisen_Udongein_Inaba#Spell_Card_1',
    '/wiki/Antinomy_of_Common_Flowers/Spell_Cards/Reisen_Udongein_Inaba#Spell_Card_1': '/wiki/Antinomy_of_Common_Flowers/Spell_Cards/Reisen_Udongein_Inaba#Spell_Card_1_2',
    'Firefly Sign "Meteor on Earth"': 'Firefly Sign "Meteor On Earth"',
    'Wriggle Sign "Little Bug Storm"': 'Firefly Sign "Little Bug Storm"',
    'Bumper Crop "Promise of the Wheat God"': 'Shikigami "Promise of the Wheat God"',
    'Miracle "Daytime Guest Stars"': 'Wonder "Daytime Guest Stars"',
    '"Suwa War ~ Native Myth vs Central Myth"': '"Suwa War - Native Myth vs Central Myth"',
    'Cloud Realm "The Thunder Court in the Sea of Abstruse Clouds"': 'Cloud Realm "Thunder Court in the Sea of Abstruse Clouds"',
    'Spirit Sign "State of Freedom from Worldly Thoughts"': 'Temperament "State of Freedom from Worldly Thoughts"',
    'Image "All Ancestors Standing Beside Your Bed"': 'Symbol "All Ancestors Standing Beside Your Bed"',
    'Image "Danmaku Paranoia"': 'Symbol "Danmaku Paranoia"',
    'Unconscious "Rorschach in Danmaku"': 'Subconscious "Rorschach in Danmaku"',
    '/wiki/Urban_Legend_in_Limbo/Spell_Cards/Kasen_Ibaraki#Spell_Card_Story_Mode_3': '/wiki/Urban_Legend_in_Limbo/Spell_Cards/Kasen_Ibaraki#Spell_Card_Story_Mode_2',
    '/wiki/Urban_Legend_in_Limbo/Spell_Cards/Kasen_Ibaraki#Spell_Card_Story_Mode_4': '/wiki/Urban_Legend_in_Limbo/Spell_Cards/Kasen_Ibaraki#Spell_Card_Story_Mode_3',
    '/wiki/Hidden_Star_in_Four_Seasons/Spell_Cards/Stage_3#Spell_Card_1': '/wiki/Hidden_Star_in_Four_Seasons/Spell_Cards/Stage_3#Spell_Card_21',
    '/wiki/Impossible_Spell_Card/Spell_Cards/3rd_Day#Spell_Card_4_-_4': '/wiki/Impossible_Spell_Card/Spell_Cards/4th_Day#Spell_Card_4_-_4'
}
for i in range(1, 10):
    EXCEPTIONS[f'/wiki/Double_Spoiler/Spell_Cards/Stage_EX#Spell_Card_11_-_{i}'] = f'/wiki/Double_Spoiler/Spell_Cards/Stage_EX#Spell_Card_EX_-_{i}'
for i in range(4, 7):
    EXCEPTIONS[f'/wiki/Hopeless_Masquerade/Spell_Cards/Mamizou_Futatsuiwa#Spell_Card_Story_Mode_.28disguised.29_{i}'] = f'/wiki/Hopeless_Masquerade/Spell_Cards/Mamizou_Futatsuiwa#Spell_Card_Story_Mode_{i}'


PAGE_CACHE = {}


def get_spellcards(cached=True):
    if cached:
        return json.load(open('bot_data/spellcards.json', 'r'))

    pages = [requests.get(f'{BASE}/wiki/List_of_Spell_Cards/Touhou_Project_{num}').text for num in range(1, 4)]
    sections = []
    entries = []
    for page in pages:
        sections += find_sections(page)

    for section in sections:
        entries += gather_section(section)

    json.dump(entries, open('bot_data/spellcards.json', 'w'))
    return entries


def find_sections(page):
    sections = []
    tables = tablere.findall(page)
    for n, table in enumerate(tables):
        sections.append(table)

    return sections


def gather_section(section):
    name = section[0]
    entries = [*map(colre.findall, rowre.findall(section[1]))]
    entries = [sort_entry(name, entry) for entry in entries]
    return entries


def sort_entry(name, entry):
    def clean(text):
        text = re.sub('<br( /)?>', ' / ', text)
        text = re.sub(r'<(.+?)>', '', text)
        return text
    # if 'Suika' not in name: return
    appearances = []
    for link, stage in zip(appearancere.findall(entry[3]), entry[4].split('<br />')):
        sc_page, game = link
        sc_page = EXCEPTIONS.get(sc_page, sc_page).split('#')[0]
        if game not in GAME_ABBREVS: continue
        if sc_page not in PAGE_CACHE:
            page = requests.get(BASE+sc_page).text
            if game == 'GoM':
                page_entries = gomcardre.findall(page)
                page_spells = {}
                for page_entry in page_entries:
                    rows = spellfieldsre.findall(page_entry)
                    rows = [re.sub(r'<.+?>', '', gomcommre.findall(row)[-1][1].strip()).strip('\n') for row in rows]
                    spellname = rows[0].strip('\n')
                    notes = re.split('[:\u3000]', rows[2], 1)
                    level = re.split('[:\u3000]', rows[3], 1)
                    others = {
                        notes[0].replace('• ', ''): notes[-1],
                        level[0].replace('• ', ''): level[-1]
                    }
                    comment = '\n'.join(re.sub(r'&\S+;', '', r) for r in rows[4:])
                    page_spells[spellname] = {
                        'comment': comment,
                        'game': game,
                        'name': spellname,
                        'difficulty': 'GoM',
                        'others': others
                    }

            else:
                page_entries = spellcardre.findall(page)
                page_spells = {}
                for sc, page_entry in page_entries:
                    page_entry = spellfieldsre.findall(page_entry)
                    image = spellimagere.search(page_entry[0])
                    spellname = spellnamere.search(page_entry[0])
                    diff = spelldiffre.search(page_entry[1])
                    comment = spellcommre.search(page_entry[-1])
                    if spellname: spellname = spellname.group(1)
                    else: spellname = ''
                    if diff is None: diff = 'Use'
                    else:
                        diff_result = diff.group(2).strip()
                        if diff_result.isdigit(): diff_result = diff.group(1)
                        diff = diff_result.strip()
                        if not diff: diff = 'Story'
                        elif '{{{difficulty}}}' in diff: diff = 'Use'
                        else: diff = diffre.search(diff).group(1)
                    if image: image = image.group(1)
                    else: image = None
                    if comment: comment = comment.group(1)
                    else: comment = ''

                    comment = re.sub(r'<a.*?href="(.+?)".*?>(.+?)</a>', f'[\\2]({BASE}\\1)', comment)
                    comment = re.sub(r'<.+?>', '', comment)
                    page_spells[sc] = {
                        'comment': comment,
                        'game': game,
                        'name': spellname,
                        'difficulty': diff,
                        'image': BASE+image if image else ''
                    }

            PAGE_CACHE[sc_page.strip('\n')] = page_spells

        if game == 'GoM':
            entry[1] = re.sub(r'&\S+;', '', entry[1]).replace('  ', ' ').strip()
            entry[1] = re.sub(r'<.+?>', '', entry[1])
            entry[1] = EXCEPTIONS.get(entry[1], entry[1])
            for k, v in PAGE_CACHE[sc_page].items():
                k = re.sub(r'&\S+;', '', k).replace('  ', ' ').strip()
                if entry[1] in k or k in entry[1] or k == entry[1]:
                    spells = [v]
                    break

            else:
                entry[1] = re.sub(r' -.+?-', '', entry[1])
                for k, v in PAGE_CACHE[sc_page].items():
                    k = re.sub(r'&\S+;', '', k).replace('  ', ' ').strip()
                    if entry[1] in k or k in entry[1] or k == entry[1]:
                        spells = [v]
                        break
                else:
                    raise Exception('Linked spell not found')

                # __import__('sys').exit(1)

        elif '#' in link[0] and stage != 'Use':
            page_id = EXCEPTIONS.get(link[0], link[0])
            page_id = page_id.split('#')[-1]
            linked_spell = PAGE_CACHE[sc_page].get(page_id)
            if linked_spell is None:
                try:
                    page_id = page_id.split('_')
                    page_id[-1] = f'{int(page_id[-1]):03d}'
                    page_id = '_'.join(page_id)
                    linked_spell = PAGE_CACHE[sc_page].get(page_id)
                except ValueError:
                    raise Exception('Could not find linked spell')

            spells = [spell for spell in PAGE_CACHE[sc_page].values() if spell['name'] == linked_spell['name']]

        else:
            spells = [{
                'comment': re.sub("</?i>", '*', entry[2]),
                'name': clean(entry[1]),
                'game': game,
                'difficulty': 'Use'
            }]

        appearances.extend(spells)

    sorted_entry = {
        'japanese': clean(entry[0]),
        'english': clean(entry[1]),
        'comments': re.sub("</?i>", '*', entry[2]),
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
        if value.startswith('src='):
            page = value.split('=')[1][1:-1]

    return f'https://en.touhouwiki.net{page}'


if __name__ == '__main__':
    spellcards = get_spellcards(cached=False)
