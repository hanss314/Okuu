import random
import discord
import shlex
import asyncio
import time

from os import listdir
from os.path import isfile, join
from .UTTT.avocado import MultiplayerAvocado
from subprocess import Popen, PIPE

from ruamel import yaml
from discord.ext import commands


RESP_DIR = 'cogs/responses'
SUPERSCRIPT = ['ˢᵗ', 'ᶮᵈ', 'ʳᵈ'] + ['ᵗʰ'] * 7
PERCENTAGE = 0.85


def one_of_them(arg):
    if arg[0].lower() not in 'ab':
        raise ValueError()
    else:
        return arg[0].lower()


class Voting:

    def __init__(self, bot):
        self.bot = bot
        with open('votes.yml', 'r') as votes:
            self.votes = yaml.load(votes)

        self.can_vote = False

    def get_count(self, filename):
        acc = 0
        for vote in self.votes['votes'].values():
            for pair in vote:
                if filename in pair:
                    acc += 1

        for pair in self.votes['slides'].values():
            if pair != -1 and filename in pair:
                acc += 0.5

        return acc

    @commands.command()
    async def vote(self, ctx, response: one_of_them=None):
        """
        Use `vote` to get a voting slide
        Pick a slide with `vote a` or `vote b`
        """
        if not self.can_vote:
            return await ctx.send(
                'Voting is not enabled right now. '
                'Contact hanss314#0128 if you think this is a mistake'
            )

        if ctx.author.id in self.votes['slides'] and self.votes['slides'][ctx.author.id] == -1:
            return await ctx.send('You\'ve voted on everything, please stop voting.')

        if not isinstance(ctx.channel, discord.abc.PrivateChannel):
            try: await ctx.message.delete()
            except discord.Forbidden: pass
            return await ctx.send('Please only vote in DMs.')
        create_new = False
        if ctx.author.id in self.votes['slides'] and response:
            try:
                votes = self.votes['votes'][ctx.author.id]
            except KeyError:
                votes = self.votes['votes'][ctx.author.id] = []

            v = self.votes['slides'][ctx.author.id]
            if response == 'a':
                votes.append((v[0], v[1]))
            else:
                votes.append((v[1], v[0]))

            create_new = True

        elif ctx.author.id not in self.votes['slides']:
            create_new = True

        if create_new:
            responses = []
            for path in listdir(RESP_DIR):
                file = join(RESP_DIR, path)
                if isfile(file):
                    responses.append((self.get_count(file), file))

            responses.sort()
            fewest = [x for x in responses if x[0] == responses[0][0]]
            rest = [x for x in responses if x not in fewest]
            random.shuffle(fewest)

            def voted_before(a, b):
                try:
                    for vote in self.votes['votes'][ctx.author.id]:
                        if a[1] in vote and b[1] in vote:
                            return True
                    else:
                        return False
                except KeyError:
                    self.votes['votes'][ctx.author.id] = []
                    return False

            slide = None
            for x in fewest:
                for y in fewest:
                    if x != y and not voted_before(x, y):
                        slide = (x[1], y[1])
                        break
                else:
                    continue
                break

            if slide is None:
                for x in fewest+rest:
                    for y in fewest+rest:
                        if x != y and not voted_before(x, y):
                            slide = (x[1], y[1])
                            break
                    else:
                        continue
                    break

            if slide is None:
                self.votes['slides'][ctx.author.id] = -1
                return await ctx.send('You\'ve voted on everything, please stop voting.')

            self.votes['slides'][ctx.author.id] = slide

        def count_lines(lines):
            try:
                lines = lines.rstrip('\n').split('\n')
            except TypeError:
                lines = lines.rstrip(b'\n').split(b'\n')

            return len(lines)

        slide = self.votes['slides'][ctx.author.id]
        try:
            content = open(slide[0], 'r').read()
        except UnicodeDecodeError:
            content = open(slide[0], 'rb').read()
        lang = slide[0].split(".")[-1]
        d = 'Pick the better one:\n'
        d += ':regional_indicator_a: '
        if slide[0] in self.votes['broke']:
            d += '**Not working** '
        d += f'{count_lines(content)} line(s)'
        if len(content) < 1900:
            d += f'```{lang}\n{content}```\n'
            await ctx.send(d)
        else:
            d += f'```{lang}\n{content[:1850]}```\n'
            await ctx.send(
                content=f'{d} *Too much content, see attached file*',
                file=discord.File(open(slide[0], 'rb'), filename=f'a.{lang}')
            )

        try:
            content = open(slide[1], 'r').read()
        except UnicodeDecodeError:
            content = open(slide[1], 'rb').read()
        lang = slide[1].split(".")[-1]
        d = ':regional_indicator_b: '
        if slide[1] in self.votes['broke']:
            d += '**Not working** '
        d += f'{count_lines(content)} line(s)'
        if len(content) < 1900:
            d += f'```{lang}\n{content}```\n'
            await ctx.send(d)
        else:
            d += f'```{lang}\n{content[:1850]}```\n'
            await ctx.send(
                content=f'{d} *Too much content, see attached file*',
                file=discord.File(open(slide[1], 'rb'), filename=f'b.{lang}')
            )

    @vote.after_invoke
    async def save(self, _):
        with open('votes.yml', 'w') as votes:
            yaml.dump(self.votes, votes)

    @commands.command()
    @commands.is_owner()
    async def results(self, ctx):
        """Do results"""
        def get_percentage(response):
            return 100 * sum(response['votes']) / response['count']

        responses = {join(RESP_DIR, path): {
            'votes': [],
            'count': 0
        } for path in listdir(RESP_DIR) if isfile(join(RESP_DIR, path))}
        for votes in self.votes['votes'].values():
            if len(votes) == 0: continue
            power = 1/len(votes)
            for vote in votes:
                responses[vote[0]]['votes'].append(power)
                responses[vote[1]]['votes'].append(0)
                responses[vote[0]]['count'] += power
                responses[vote[1]]['count'] += power

        responses = [{'response': response, **votes} for response, votes in responses.items()]
        for entry in responses:
            entry['percentage'] = get_percentage(entry)

        responses.sort(key=lambda x: x['percentage'], reverse=True)
        for n, response in enumerate(responses):
            if (n // 10) % 10 == 1:
                symbol = SUPERSCRIPT[-1]
            else:
                symbol = SUPERSCRIPT[n % 10]

            dead = n > len(responses) * PERCENTAGE
            try:
                content = open(response['response'], 'r').read()
            except UnicodeDecodeError:
                content = open(response['response'], 'rb').read()

            lang = response['response'].split(".")[-1]
            file = None
            if len(content) > 1800:
                content = '*Too much content, see attached file*'
                content += f'```{lang}\n{content[:1800]}```\n'
                file = discord.File(open(response['response'], 'r'), filename=f'response.{lang}')
            else:
                content = f'```{lang}\n{content}```\n'

            msg = '{}\n{} **{}{} place**: {}\n**<@{}>** ({}%)'.format(
                '=' * 50,
                ':skull_crossbones:' if (dead and n != 0) else ':white_check_mark:',
                n + 1, symbol, content,
                response['response'].split('.')[0].split('/')[-1],
                round(response['percentage'], 2)
            )
            await ctx.send(msg, file=file)
            with open('results.txt', 'a+') as results_file:
                results_file.write(msg+'\n\n\n')

    @commands.command()
    @commands.is_owner()
    async def toggle_voting(self, ctx):
        """Toggle voting"""
        self.can_vote = not self.can_vote
        if self.can_vote: await ctx.send('Voting enabled.')
        else: await ctx.send('Voting disabled.')

    @commands.command()
    @commands.is_owner()
    async def fully_voted(self, ctx):
        """See the people who have voted the max number of times"""
        await ctx.send(', '.join(
            self.bot.get_user(user).name for user in self.votes['slides'] if self.votes['slides'][user] == -1
        ) or 'Nobody')

    @commands.command()
    @commands.is_owner()
    async def fight(self, ctx):
        moves = {
            0: 'slice',
            1: 'mash',
            2: 'eat',
            3: 'buy'
        }
        competitors = {
            'responses/100764870617624576': 'Zwei',
            'python3 responses/140564059417346049.py': 'Noahkiq',
            'python3 responses/240995021208289280.py': 'hanss314',
            'node responses/107118384813977600.js': 'Untypable',
            'python3 responses/161508165672763392.py': 'Bottersnike',
            'lua responses/248156896131940354.lua': '_zM',
            'python3 responses/137001076284063744.py': 'Bazinga_9000',
            'python3 responses/186553034439000064.py':' Milo Jacquet',
            'responses/bin/236257776421175296': '96 LB'
        }
        results = {competitor: 0 for competitor in competitors.values()}
        competitions = [(a, b) for a in competitors.keys() for b in competitors.keys() if a != b]

        async def fight(a, b):
            fighters = [a, b]
            a = shlex.split(a)
            b = shlex.split(b)
            game = MultiplayerAvocado()
            while True:
                if game.turn == 0:
                    turn = a
                else:
                    turn = b

                proc = Popen(turn + [str(game.spoon)] + list(map(str, game.previous)), stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                if err:
                    await ctx.send(f'{competitors[fighters[game.turn]]} errored!')
                    break

                o = f'{competitors[fighters[game.turn]]} outputs `{out.decode("utf-8").strip()}`.'

                try:
                    out = int(out)
                    if len(game.previous) == 0:
                        game.set_avocados(out)
                        await ctx.send(f'{o} The starting avocado count is `{game.previous[0]}`')
                    elif game.spoon == -1:
                        game.set_spoon(out)
                        await ctx.send(f'{o} The starting spoon size is `{game.spoon}`')
                    else:
                        move = moves[out]
                        try: game.__getattribute__(move)()
                        finally: await ctx.send(f'{o} They will `{move}`. The avocado count is `{game.previous[-1]}`')
                        if len(game.previous) % 10 == 0:
                            await ctx.send(f'Avocado history: {", ".join(list(map(str, game.previous)))}')

                except (ValueError, KeyError):
                    await ctx.send(f'Avocado history: {", ".join(list(map(str, game.previous)))}')
                    break

                await asyncio.sleep(7)

            return (game.turn + 1) % 2

        await ctx.send('The competition starts now!')
        start_times = [time.time() + x * 24 * 60 * 60 / len(competitions) for x in range(1, len(competitions) + 1)]
        start_times[-1] = 0
        for pairing, timing in zip(competitions, start_times):
            await ctx.send(f'**{competitors[pairing[0]]}** vs. **{competitors[pairing[1]]}**')
            winner = await fight(*pairing)
            await ctx.send(f'{competitors[pairing[winner]]} wins!')
            results[competitors[pairing[winner]]] += 1
            results[competitors[pairing[winner-1]]] -= 1
            yaml.dump(results, open('bot_data/comp_results.json', 'w'))
            if timing == 0:
                results = list(results.items())
                results.sort(key=lambda p: p[1])
                results.reverse()
                await ctx.send(
                    f"**Final results:** \n{chr(10).join('*{}*: {}'.format(*entry) for entry in results)}"
                )
                yaml.dump(results, open('bot_data/comp_results.json', 'w'))
                break
            elif time.time() < timing:
                wait_time = timing - time.time()
                await ctx.send(f'The next round starts in {int(wait_time//60):02d}:{int(wait_time%60):02d}')
                await asyncio.sleep(wait_time)
            else:
                await ctx.send('The next round starts now!')


def setup(bot):
    bot.add_cog(Voting(bot))
