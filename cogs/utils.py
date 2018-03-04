import asyncio
import math
import statistics
import discord

from os import path
from ruamel import yaml
from string import ascii_letters
from .util import sudoku, comp_parser, touhouwiki
from discord.ext import commands

acceptable = ascii_letters + '0123456789'

rpncalc = {
    # constants
    'pi': lambda l: [math.pi] + l,
    'e': lambda l: [math.e] + l,

    # arithmetic
    '+': lambda l: [l[1]+l[0]] + l[2:],
    '-': lambda l: [l[1]-l[0]] + l[2:],
    '*': lambda l: [l[1]*l[0]] + l[2:],
    '/': lambda l: [l[1]/l[0]] + l[2:],
    '^': lambda l: [l[1]**l[0]] + l[2:],
    '**': lambda l: [l[1]**l[0]] + l[2:],
    'sqrt': lambda l: [l[0]**0.5] + l[2:],

    # trig
    'sin': lambda l: [math.sin(l[0])] + l[1:],
    'cos': lambda l: [math.cos(l[0])] + l[1:],
    'tan': lambda l: [math.tan(l[0])] + l[1:],
    'asin': lambda l: [math.asin(l[0])] + l[1:],
    'acos': lambda l: [math.acos(l[0])] + l[1:],
    'atan': lambda l: [math.atan(l[0])] + l[1:],

    # hyperbolic
    'sinh': lambda l: [math.sinh(l[0])] + l[1:],
    'cosh': lambda l: [math.cosh(l[0])] + l[1:],
    'tanh': lambda l: [math.tanh(l[0])] + l[1:],
    'asinh': lambda l: [math.asinh(l[0])] + l[1:],
    'acosh': lambda l: [math.acosh(l[0])] + l[1:],
    'atanh': lambda l: [math.atanh(l[0])] + l[1:],

    # logs
    'ln': lambda l: [math.log(l[0])] + l[1:],
    'log': lambda l: [math.log10(l[0])] + l[1:],
    'logb': lambda l: [math.log(l[0], l[1])] + l[2:],

    # misc
    'ceil': lambda l: [math.ceil(l[0])] + l[1:],
    'flr': lambda l: [math.floor(l[0])] + l[1:],

    # statistics
    'meana': lambda l: [statistics.mean(l)],
    'stdva': lambda l: [statistics.stdev(l)],
    'mean': lambda l: [statistics.mean(l[1: l[0]+1])] + l[l[0]+1:],
    'stdv': lambda l: [statistics.stdev(l[1: l[0]+1])] + l[l[0]+1:],
    'meanstdva': lambda l: [statistics.mean(l), statistics.stdev(l)],
    'meanstdv': lambda l: [
                              statistics.mean(l[1: l[0]+1]),
                              statistics.stdev(l[1: l[0]+1])
                          ] + l[l[0]+1:],

    # stack operations
    'swp': lambda l: [l[1], l[0]] + l[2:],
    'drp': lambda l: l[1:],
    'dup': lambda l: [l[0]] + l,
    'clr': lambda l: [],
}


def std_complex(string) -> complex:
    try:
        return complex(string)
    except ValueError:
        return complex(string.replace('i', 'j'))


conv_list = [
    int,
    float,
    std_complex,
]


def convert(string):
    for func in conv_list:
        try:
            return func(string)
        except ValueError:
            pass

    raise ValueError


class Utils:

    def __init__(self, bot):
        self.bot = bot
        if not path.isfile('bot_data/stacks.yml'):
            with open('bot_data/stacks.yml', 'w+') as flairs:
                yaml.dump({}, flairs)

        with open('bot_data/stacks.yml', 'r') as stacks:
            self.stacks = yaml.load(stacks)

        self.spellcards = touhouwiki.get_spellcards()

    @commands.group(invoke_without_command=True)
    async def rpn(self, ctx, *ops):
        """Use an RPN calculator"""
        stack = self.stacks[ctx.author.id]
        loop = asyncio.get_event_loop()
        for n, op in enumerate(ops):
            if op in rpncalc:
                try:
                    stack = await asyncio.wait_for(
                        loop.run_in_executor(None, rpncalc[op], stack), 1
                    )
                except asyncio.TimeoutError:
                    return await ctx.send(f'Operation {n+1}: `{op}` timed out. Aborting.')
                except IndexError:
                    return await ctx.send(f'Stack size too small on operation {n+1}: `{op}`. Aborting')
                except Exception as e:
                    return await ctx.send(f'{e}, aborting.')

            else:
                try:
                    stack = [convert(op)] + stack
                except ValueError:
                    return await ctx.send(f'Invalid value or operation: `{op}`. Aborting')

        self.stacks[ctx.author.id] = stack[:16]
        await ctx.invoke(self.show_stack)

    @rpn.command(name='help')
    async def rpn_help(self, ctx):
        """Get a list of all operations"""
        await ctx.send(f'Available operations: {", ".join(x for x in rpncalc.keys())}')

    @rpn.command(name='stack')
    async def show_stack(self, ctx):
        """View your stack"""
        if len(self.stacks[ctx.author.id]) == 0:
            return await ctx.send('Your stack is empty.')

        await ctx.send(', '.join(str(x) for x in self.stacks[ctx.author.id]).replace('j', 'i'))

    @rpn.before_invoke
    @show_stack.before_invoke
    async def check_exists(self, ctx):
        if ctx.author.id not in self.stacks:
            self.stacks[ctx.author.id] = []

    @rpn.after_invoke
    async def save_stack(self, _):
        with open('stacks.yml', 'w') as stacks:
            yaml.dump(self.stacks, stacks)

    @commands.command()
    async def sudoku(self, ctx, *, puzzle):
        """
        Solve a sudoku.
        Acceptable non-blanks are non whitespace characters.
        Acceptable blanks are alphanumerics not 1-9.
        Other characters are ignored
        """
        def to_int(num):
            try:
                return int(num)
            except ValueError:
                return 0

        args = [c for c in puzzle if c not in ' \n']
        rows = []
        while args:
            row, args = args[:9], args[9:]
            rows.append([to_int(c) for c in row])

        if len(rows[-1]) < 9 or len(rows) < 9:
            return await ctx.send('Please fill in everything')
        loop = asyncio.get_event_loop()
        puzzle = sudoku.Sudoku(rows)
        for x in range(9):
            for y in range(9):
                v = puzzle.get(x, y)
                if v is not None and v not in puzzle.possible(x, y):
                    return await ctx.send('Unsolvable sudoku.')

        try:
            solved = await asyncio.wait_for(loop.run_in_executor(None, sudoku.solve, puzzle), 1)
        except asyncio.TimeoutError:
            return await ctx.send('Are you sure you entered a proper sudoku?')

        if solved is not None:
            await ctx.send(f'```{str(solved)}```')
        else:
            await ctx.send('Unsolvable sudoku.')

    @commands.command(aliases=['mass', 'molarmass'])
    async def molar_mass(self, ctx, *, compound):
        """
        Get the molar mass of a compound.
        Charges are not supported
        """
        try:
            composition, charge = comp_parser.get_mass(
                comp_parser.parse_comp(compound)
            )
        except ValueError:
            return await ctx.send('Are your brackets balanced?')
        except KeyError:
            return await ctx.send('Invalid element')
        else:
            await ctx.send(
                f'The molar mass of `{compound}` is {composition:.3f}g/mol. '
                f'The charge is {charge:+d}.'
            )

    @commands.command()
    async def spellcard(self, ctx, *search_params: lambda s: s.lower()):
        """
        Search for a spellcard

        Search options:
            `--user <user>` - Find spellcards by character
            `--name <name>` - Find spellcards by name
            `--game <game>` - Find spellcards by game
            `--diff <difficulty>` - Find spellcards by difficuty
        """
        key = ''
        value = ''
        search_terms = {}
        for term in search_params:
            if term.startswith('--'):
                if value and key:
                    search_terms[key] = value.strip()
                    value = ''

                if term[2:] not in ['user', 'name', 'game', 'diff']:
                    return await ctx.send(f'Invalid flag: `{term}`')

                key = term[2:]
            else:
                value += term + ' '

        if value and key: search_terms[key] = value.strip()
        if not search_terms:
            return await ctx.send('Unyu? Search parameters are required')

        search = self.spellcards
        for key, value in search_terms.items():
            if key == 'user':
                search = [
                    spellcard for spellcard in search
                    if value in spellcard['owner'].lower()
                ]
            elif key == 'name':
                search = [
                    spellcard for spellcard in search
                    if value in spellcard['english'].lower()
                ]
            elif key == 'game':
                search = [
                    spellcard for spellcard in search
                    if any(
                        value == appearance['game'].lower() or
                        value in touhouwiki.GAME_ABBREVS[appearance['game']].lower()
                        for appearance in spellcard['appearances']
                    )
                ]
            elif key == 'diff':
                search = [
                    spellcard for spellcard in search
                    if any(
                        appearance['difficulty'].lower().startswith(value) or appearance['difficulty'] == value
                        for appearance in spellcard['appearances']
                    )
                ]

        if len(search) == 0:
            return await ctx.send('Unyu? I didn\'t find any spellcards')
        elif len(search) > 1:
            m = '**Found the following:**\n'
            for entry in search:
                m += f'\n{entry["owner"]} - {entry["english"]}'

            m += '\n\n Please narrow your search terms'
            try:
                await ctx.send(m)
            except discord.HTTPException:
                await ctx.send('That\'s a lot of results. I forget the first one')

        else:
            entry = search[0]
            search = entry['appearances']
            for key, value in search_terms.items():
                if key == 'game':
                    search = [
                        appearance for appearance in search
                        if value == appearance['game'].lower()
                        or value in touhouwiki.GAME_ABBREVS[appearance['game']].lower()
                    ]
                elif key == 'diff':
                    search = [
                        appearance for appearance in search
                        if appearance['difficulty'].lower().startswith(value) or
                        appearance['difficulty'] == value
                    ]

            if len(search) == 0:
                return await ctx.send('Unyu? I didn\'t find any spellcards')
            else:
                embed = discord.Embed(title=entry['japanese'], description=entry['english'])
                embed.set_author(
                    name=entry['owner'],
                    url=f'https://en.touhouwiki.net/wiki/{entry["owner"].replace(" ", "_")}'
                )

                embed.set_thumbnail(url=await touhouwiki.get_thumbnail(entry['owner']))

                if len(search) == 1:
                    appearance = search[0]
                    if 'comment' in appearance and appearance['comment']:
                        embed.add_field(name='Comment', value=appearance['comment'])

                    embed.set_image(url=await touhouwiki.get_image_url(appearance['image']))
                    embed.set_footer(
                        text=f'{touhouwiki.GAME_ABBREVS[appearance["game"]]} | {appearance["difficulty"]}'
                    )

                else:
                    if 'comment' in entry and entry['comment']:
                        embed.add_field(name='Comment', value=entry['comments'])

                    embed.add_field(
                        name='Appears in:',
                        value='\n'.join(f'{a["game"]} - {a["difficulty"]}' for a in search),
                        inline=False
                    )

                await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def reload_spellcards(self, ctx):
        """Reload the spellcard database"""
        await ctx.send('Reloading spellcards')
        self.spellcards = await self.bot.loop.run_in_executor(
            None, touhouwiki.get_spellcards, False
        )
        await ctx.send('Reloaded spellcards')


def setup(bot):
    bot.add_cog(Utils(bot))


if __name__ == '__main__':
    cog = Utils(None)
