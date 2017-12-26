import random
import discord

from os import listdir
from os.path import isfile, join

from ruamel import yaml
from discord.ext import commands


RESP_DIR = 'cogs/responses'
SUPERSCRIPT = ['ˢᵗ', 'ᶮᵈ', 'ʳᵈ'] + ['ᵗʰ'] * 7
PERCENTAGE = 0.8


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

    def get_count(self, filename):
        acc = 0
        for vote in self.votes['votes'].values():
            for pair in vote:
                if filename in pair:
                    acc += 1

        for pair in self.votes['slides'].values():
            if filename in pair:
                acc += 0.5

        return acc

    @commands.command()
    async def vote(self, ctx, response: one_of_them=None):
        """
        Use `vote` to get a voting slide
        Pick a slide with `vote a` or `vote b`
        """
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
                votes.append(v)
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
                return await ctx.send('You\'ve voted on everything, please stop voting.')

            self.votes['slides'][ctx.author.id] = slide

        def count_lines(lines):
            try:
                lines = lines.split('\n')
            except TypeError:
                return 1
            count = len(lines)
            for x in reversed(lines):
                if x == '':
                    count -= 1
                else:
                    return count

        slide = self.votes['slides'][ctx.author.id]
        try:
            content = open(slide[0], 'r').read()
        except UnicodeDecodeError:
            content = open(slide[0], 'rb').read()
        lang = slide[0].split(".")[-1]
        d = 'Pick the better one:\n'
        d += ':regional_indicator_a: '
        if slide in self.votes['broke']:
            d += '**Not working** '
        d += f'{count_lines(content)} line(s)'
        if len(content) < 1900:
            d += f'```{lang}\n{content}```\n'
            await ctx.send(d)
        else:
            d += f'```{lang}\n{content[:1900]}```\n'
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
        if slide in self.votes['broke']:
            d += '**Not working** '
        d += f'{count_lines(content)} line(s)'
        if len(content) < 1900:
            d += f'```{lang}\n{content}```\n'
            await ctx.send(d)
        else:
            d += f'```{lang}\n{content[:1900]}```\n'
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

            dead = n < len(responses) * PERCENTAGE
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


def setup(bot):
    bot.add_cog(Voting(bot))
