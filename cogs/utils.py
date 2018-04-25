import asyncio
import discord
import matplotlib as mpl
mpl.rcParams['text.usetex'] = True
mpl.use('agg')
from matplotlib import pyplot as plt

from PIL import Image
from os import path
from ruamel import yaml
from .util import sudoku, comp_parser, touhouwiki
from .util.rpn import rpncalc, convert, to_str
from discord.ext import commands




class Utils:

    def __init__(self, bot):
        import importlib
        from .util import rpn
        importlib.reload(rpn)
        importlib.reload(touhouwiki)
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
        stack, var = self.stacks[ctx.author.id]
        stack, var = list(stack), dict(var)
        loop = asyncio.get_event_loop()
        for n, op in enumerate(ops):
            if op in rpncalc:
                try:
                    task = asyncio.wait_for(
                        loop.run_in_executor(None, rpncalc[op][1], stack, var), 1
                    )
                    await task
                except asyncio.TimeoutError:
                    return await ctx.send(f'Operation {n+1}: `{op}` timed out. Aborting.')
                except IndexError:
                    return await ctx.send(f'Stack size too small on operation {n+1}: `{op}`. Aborting')
                except Exception as e:
                    if len(e.args[0]) > 500:
                        m = ctx.send(f'`{e.args[0][:500]}...` [Error truncated due to length], aborting.')
                    else:
                        m = ctx.send(f'`{e}`, aborting.')
                    loop.create_task(m)
                    return

            else:
                try:
                    stack.append(convert(op))
                except ValueError:
                    return await ctx.send(f'Invalid value or operation: `{op}`. Aborting')

        while len(var) > 64:
            var.popitem()

        self.stacks[ctx.author.id] = (stack[-256:], var)
        await ctx.invoke(self.show_stack)

    @rpn.command(name='help')
    async def rpn_help(self, ctx, op=None):
        """Get a list of all operations"""
        if op is None:
            await ctx.send(
                f'Available operations: ```{", ".join(x for x in rpncalc.keys())}```\n'
                'All other operations will attempt to evaluate the operator in the order '
                '`int, float, complex, string` and push the value to the stack. '
                f'See `{ctx.prefix}rpn help \'` for help on strings, '
                f'and `{ctx.prefix}rpn help <op>` for help on an operator.'
            )

        else:
            help_text = rpncalc.get(op)
            if help_text is None:
                return await ctx.send('Unyu? That\'s not an operator')

            help_text = help_text[0]
            await ctx.send(f'Help for `{op}`: \n\n{help_text}')

    @rpn.command(name='stack')
    async def show_stack(self, ctx):
        """View your stack"""
        if len(self.stacks[ctx.author.id][0]) == 0:
            return await ctx.send('Your stack is empty.')

        await ctx.send(', '.join(to_str(x) for x in self.stacks[ctx.author.id][0]))

    @rpn.command(name='variables', aliases=['vars'])
    async def show_variables(self, ctx):
        """View your stack"""
        if len(self.stacks[ctx.author.id][1]) == 0:
            return await ctx.send('You have no defined variables.')

        await ctx.send('; '.join(
            f'{to_str(k)} = {to_str(v)}' for k, v in self.stacks[ctx.author.id][1].items()
        ))

    @rpn.before_invoke
    @show_stack.before_invoke
    @show_variables.before_invoke
    async def check_exists(self, ctx):
        if ctx.author.id not in self.stacks:
            self.stacks[ctx.author.id] = ([], {})

        elif type(self.stacks[ctx.author.id]) == list:
            self.stacks[ctx.author.id] = (self.stacks[ctx.author.id], {})

    @rpn.after_invoke
    async def save_stack(self, _):
        with open('bot_data/stacks.yml', 'w') as stacks:
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

    @commands.command(aliases=['tex'])
    async def latex(self, ctx, *, text):
        """Render a LaTeX equation"""
        plt.clf()
        fig, ax = plt.subplots()
        ax.set_axis_off()
        fig.patch.set_visible(False)
        fig.text(0, 0.5, r'\[ ' + text.strip('`') + r' \]', fontsize=14)
        try:
            fig.savefig('latex.png')
        except RuntimeError as e:
            return await ctx.send(f'Unyu? That doesn\'t look right.')
        image = Image.open('latex.png')
        thresholded = [(0, ) * 4 if item[3] == 0 else item for item in image.getdata()]
        image.putdata(thresholded)
        image = image.crop(image.getbbox())
        image.save('latex.png')
        await ctx.send(file=discord.File('latex.png'))

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
        Search for a touhou spellcard

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
                    if value in spellcard['english'].lower().replace('"', '')
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

        if 'name' in search_terms:
            for spellcard in search:
                if search_terms['name'] == spellcard['english'].lower().replace('"', ''):
                    search = [spellcard]
                    break

        if len(search) == 0:
            return await ctx.send('Unyu? I didn\'t find any spellcards')
        elif len(search) > 1:
            m = '**Found the following:**\n'
            for entry in search:
                if len(m) + len(entry["owner"]) + len(entry["english"]) > 1900:
                    m += '\n\nThat\'s a lot of results. I forget the rest'
                    break

                m += f'\n{entry["owner"]} - {entry["english"]}'

            m += '\n\n Please narrow your search terms'
            await ctx.send(m)

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

            embed = discord.Embed(title=entry['japanese'], description=entry['english'])
            embed.set_author(
                name=entry['owner'],
                url=f'https://en.touhouwiki.net/wiki/{entry["owner"].replace(" ", "_")}'
            )
            thumb = await touhouwiki.get_thumbnail(entry['owner'])
            embed.set_thumbnail(url=thumb)
            if len(search) == 1:
                appearance = search[0]
                if 'others' in appearance:
                    for field, value in appearance['others'].items():
                        embed.add_field(name=field or 'Notes', value=value, inline=True)

                if 'comment' in appearance and appearance['comment']:
                    embed.add_field(name='Comment', value=appearance['comment'])

                try:
                    embed.set_image(url=appearance['image'])
                except KeyError:
                    pass

                embed.set_footer(
                    text=f'{touhouwiki.GAME_ABBREVS[appearance["game"]]} | {appearance["difficulty"]}'
                )

            else:
                if 'comment' in entry and entry['comment']:
                    embed.add_field(name='Comment', value=entry['comments'])

                if search:
                    embed.add_field(
                        name='Appears in:',
                        value='\n'.join(f'{touhouwiki.GAME_ABBREVS[a["game"]]} - {a["difficulty"]}' for a in search),
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
