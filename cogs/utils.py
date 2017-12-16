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

        while len(rows[-1]) < 9:
            rows[-1].append(0)

        while len(rows) < 9:
            rows.append([0] * 9)
        solved = sudoku.solve(sudoku.Sudoku(rows))
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
