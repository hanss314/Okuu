import hashlib
import math
import random
import time
import asyncio
import re

from string import ascii_lowercase
from ruamel import yaml

from discord.ext import commands

ascii_digit = '0123456789'
wrongs = [
    'Oof',
    'Nope',
    'Not quite',
    'Almost',
    'Not a chance',
    'Are you even trying?',
    'Way off',
    'So close',
]

def number(arg: str) -> complex:
    arg = arg.replace('i', 'j')
    return complex(arg)

def factor(x):
    fs = set()
    for i in range(1, min(100000, int(math.ceil(math.sqrt(x))))):
        if x%i == 0:
            fs.add(x//i)
            fs.add(i)
    return fs

def p_factor(x):
    factors = set()
    i = 2
    while x > i:
        if x % i == 0:
            factors.add(i)
            x //= i
        else:
            i += 1
            
        if i > 100000:
            break

    return factors

class Fun:

    def __init__(self, bot):
        import os
        self.bot = bot
        self.wangernumb = False
        if os.path.exists('./wangs.yml'):
            wangs = yaml.safe_load(open('./wangs.yml'))
        else:
            wangs = {'lastwang': self.hash(1), 'leaderboard': {}}
            yaml.dump(wangs, open('./wangs.yml', 'w'))


        self.lastwang = wangs['lastwang']
        self.leaderboard = wangs['leaderboard']
        if 'typing' in wangs:
            self.typing = wangs['typing']
        else:
            self.typing = {}

    async def on_typing(self, channel, user, when):
        if user.bot: return
        start = time.time()

        def check(m):
            return m.author == user and m.channel == channel

        try:
            m = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return

        delta = time.time() - start
        words = len(re.sub('<[^>]+>', '', m.content))
        if words/delta > 10: return

        try:
            self.typing[user.id][0] += words
            self.typing[user.id][1] += delta
        except KeyError:
            self.typing[user.id] = [words, delta]

        self.write_wangfile()


    @staticmethod
    def hash(object):
        return hashlib.sha512(bytes(repr(object), 'utf8')).hexdigest()

    @staticmethod
    def to_int(string: str) -> int:
        try: return int(string)
        except ValueError: return 1

    def write_wangfile(self):
        yaml.dump(
            {
                'lastwang': self.lastwang,
                'leaderboard': self.leaderboard,
                'typing': self.typing
            },
            open('./wangs.yml', 'w')
        )

    def check_numberwang(self, num):
        r = num
        i = num.__dir__
        rstr = ''.join(c for c in self.hash(r) if c in ascii_lowercase)
        istr = self.to_int(''.join(c for c in self.hash(i) if c in ascii_digit))
        rstr = self.to_int(''.join(c for c in self.hash(rstr) if c in ascii_digit))
        lw = self.to_int(''.join(c for c in self.lastwang if c in ascii_digit))

        lw, istr = int(str(lw)[-int(str(istr)[0])//2-5:]), int(str(istr)[-int(str(lw)[0])//2-5:])
        lw = self.to_int(''.join(c for c in self.hash(factor(lw) ^ factor(istr)) if c in ascii_digit))
        lw, rstr = int(str(lw)[-int(str(rstr)[0]) // 2 - 5:]), int(str(rstr)[-int(str(lw)[0]) // 2 - 5:])
        final =  p_factor(lw) & p_factor(rstr)
        return len(final) > 0, len(final) > 1

    @commands.command(aliases=['mywpm'])
    async def myspeed(self, ctx):
        wpm = 12 * self.typing[ctx.author.id][0] / self.typing[ctx.author.id][1]
        await ctx.send(f'You are averaging {wpm:.2f} wpm.')

    @commands.command(aliases=['speedlb', 'typing'])
    async def typingspeed(self, ctx, page: int=0):
        speeds = sorted([
            (12*pair[0]/pair[1], user)
            for user, pair in self.typing.items()
        ], reverse=True)
        total = math.ceil(len(speeds) / 10)
        speeds = speeds[page*10:page*10 + 10]
        lst = '\n'.join(
            f'{n+page*10+1}. **{self.bot.get_user(pair[1]) or pair[1]}**: {pair[0]:.2f} wpm'
            for n, pair in enumerate(speeds)
        )
        await ctx.send(f'Fastest typers, page {page+1}/{total}\n{lst}')


    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.guild_only()
    async def numberwang(self, ctx, *, num):
        '''
        See if a number is numberwang.
        '''
        async with ctx.typing():
            is_numberwang, wangernumb = self.check_numberwang(num)


        if is_numberwang:
            self.lastwang = self.hash(self.lastwang + str(num))
            open('./lastwang', 'w').write(self.lastwang)
            if not self.wangernumb:
                await ctx.send(f'{ctx.author.mention} That\'s numberwang!')
                self.lastwang = self.hash(str(num)+self.lastwang[0])
                try: self.leaderboard[ctx.guild.id][ctx.author.id] += 1
                except KeyError: self.leaderboard[ctx.guild.id][ctx.author.id] = 1
                if wangernumb:
                    self.wangernumb = True
                    await ctx.send('Let\'s rotate the board!')

            else:
                await ctx.send('That\'s WangerNumb!')
                self.wangernumb = False
                try: self.leaderboard[ctx.guild.id][ctx.author.id] += 2
                except KeyError: self.leaderboard[ctx.guild.id][ctx.author.id] = 2

            self.write_wangfile()

        else:
            if not self.wangernumb:
                await ctx.send(f'I\'m sorry {ctx.author.mention}, but that is not numberwang.')
                self.lastwang = self.hash(self.lastwang + str(num))
                self.write_wangfile()
            else:
                await ctx.send(random.choice(wrongs))

    @numberwang.command(name='leaderboard', aliases=['lead', 'lb'])
    @commands.cooldown(1, 15, commands.BucketType.channel)
    @commands.guild_only()
    async def numberwang_leaderboard(self, ctx):
        leaders = sorted([(score, uid) for uid, score in self.leaderboard[ctx.guild.id].items()], reverse=True)
        leaders = leaders[:10]
        d = '**__Leaderboard:__**\n'
        for n, k in enumerate(leaders):
            score, uid = k
            user = ctx.guild.get_member(uid)
            if user: line = f'**{user.name}**: '
            else: line = f'{uid}: '
            if ord(self.lastwang[-n-1]) % 2: line += 'Leading '
            else: line += 'Trailing '
            left = score*ord(self.lastwang[-n-2])//ord(self.lastwang[-n-3])
            right = ord(self.lastwang[-n-2])*ord(self.lastwang[-n-3])
            right %= (left*3//2) + 1
            if ord(self.lastwang[-n-2]) % 2: line += f'`{left} - {right}`'
            else: line += f'`{right} - {left}`'
            d += f'{line}\n'

        await ctx.send(d)

    @numberwang.before_invoke
    @numberwang_leaderboard.before_invoke
    async def check_guild_lb(self, ctx):
        if ctx.guild.id not in self.leaderboard:
            self.leaderboard[ctx.guild.id] = {}

    @commands.command()
    async def birb(self, ctx):
        await ctx.send('Tis a birb. A dangerous birb. An incredibly dangerous birb. Birb.')



def setup(bot):
    bot.add_cog(Fun(bot))
