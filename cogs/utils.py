import asyncio

from string import ascii_letters
from .util import sudoku, comp_parser
from discord.ext import commands

acceptable = ascii_letters + '0123456789'


class Utils:

    def __init__(self, bot):
        self.bot = bot

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
