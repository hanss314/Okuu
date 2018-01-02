import asyncio
import math

from ruamel import yaml
from string import ascii_letters
from .util import sudoku, comp_parser
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

    # stack operations
    'swp': lambda l: [l[1], l[0]] + l[2:],
    'drp': lambda l: l[1:],
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
        with open('stacks.yml', 'r') as stacks:
            self.stacks = yaml.load(stacks)

    @commands.group(invoke_without_command=True)
    async def rpn(self, ctx, *ops):
        """Use an RPN calculator"""
        stack = self.stacks[ctx.author.id]
        loop = asyncio.get_event_loop()
        for op in ops:
            if op in rpncalc:
                try:
                    stack = await asyncio.wait_for(
                        loop.run_in_executor(None, rpncalc[op], stack), 1
                    )
                except asyncio.TimeoutError:
                    return await ctx.send('Operation timed out. Aborting.')
                except IndexError:
                    return await ctx.send('Stack size too small. Aborting')
                except Exception as e:
                    return await ctx.send(f'{e} Aborting.')

            else:
                try:
                    stack = [convert(op)] + stack
                except ValueError:
                    return await ctx.send('Invalid value or operation. Aborting')

        self.stacks[ctx.author.id] = stack[:16]
        await ctx.invoke(self.show_stack)

    @rpn.command(name='help')
    async def rpn_help(self, ctx):
        await ctx.send(f'Available operations: {", ".join(x for x in rpncalc.keys())}')

    @rpn.command(name='stack')
    async def show_stack(self, ctx):
        """View your stack"""
        if len(self.stacks[ctx.author.id]) == 0:
            return await ctx.send('Your stack is empty.')

        await ctx.send(', '.join(str(x) for x in self.stacks[ctx.author.id]))

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
            composition = comp_parser.parse_comp(compound)
        except ValueError:
            return await ctx.send('Are your brackets balanced?')
        except KeyError:
            return await ctx.send('Invalid element')
        else:
            await ctx.send(f'The molar mass of `{compound}` is {comp_parser.get_mass(composition):.3f}g/mol')


def setup(bot):
    bot.add_cog(Utils(bot))
