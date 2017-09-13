from discord.ext import commands
import discord

from cogs.codenames.enums import Teams
from cogs.codenames.board import Board
from cogs import checks

class Players():
    @commands.command()
    @checks.spymaster()
    async def hint(self, ctx, word, num):
        '''Give a hint'''
        try: await ctx.message.delete()
        except: pass
        if ctx.bot.board.max_moves != 0: return await ctx.send('You\'ve already made a hint!', delete_after=10)
        try: 
            n=int(num)
        except: 
            n = 'unlimited'
            ctx.bot.board.set_hint_number(100000)
        else: 
            if n==0: ctx.bot.board.set_hint_number(100000)
            elif n<0: return await ctx.send('Just... No.')
            else: ctx.bot.board.set_hint_number(n)
            
        mention = ctx.bot.roles['red'] if ctx.bot.board.turn==Teams.RED else ctx.bot.roles['blue']
        await ctx.bot.get_channel(ctx.bot.config['channel']).send('<@&{}> The hint is "{}: {}"'.format(mention, word, n))
        
    @commands.command(aliases=['submit'])
    @checks.player_or_host()
    async def guess(self, ctx, word):
        '''Guess a square'''
        if ctx.bot.board.max_moves == 0: return await ctx.send('There is no hint!', delete_after=10)
        move = ctx.bot.board.move_count
        result = ctx.bot.board.do_move(word)
        chan = ctx.bot.get_channel(ctx.bot.config['channel'])
        if result == -1: return
        chan.send('{}. {}'.format(move, word))
        ctx.bot.board.draw().save('board.png')
        img = discord.File(open('board.png', 'rb'))
        await chan.send(file=img)
        if result is not None:
            mention = ctx.bot.roles['red'] if ctx.bot.board.turn==Teams.RED else ctx.bot.roles['blue']
            await chan.send('<@&{}> You win! Good job!'.format(mention))
            await self.rem_roles(ctx)
            ctx.bot.board.draw(unhidden=True).save('board.png')
            img = discord.File(open('board.png', 'rb'))
            await chan.send(file=img)
            return
        
        if ctx.bot.board.max_moves == 0: 
            mention = ctx.bot.roles['red_sm'] if ctx.bot.board.turn==Teams.RED else ctx.bot.roles['blue_sm']
            await chan.send('<@&{}> It\'s your turn to make a hint!'.format(mention))
        
    @commands.command(aliases=['pass'])
    @checks.player()
    async def skip(self, ctx):
        '''Skip your team's turn'''
        ctx.bot.board.switch_turn()
        chan = ctx.bot.get_channel(ctx.bot.config['channel'])
        ctx.send('Turn skipped.')
        mention = ctx.bot.roles['red_sm'] if ctx.bot.board.turn==Teams.RED else ctx.bot.roles['blue_sm']
        await chan.send('<@&{}> It\'s your turn to make a hint!'.format(mention))
        
    @commands.command()
    async def board(self, ctx):
        '''Show the board'''
        ctx.bot.board.draw().save('board.png')
        img = discord.File(open('board.png', 'rb'))
        await ctx.send(file=img)

    
    @commands.command()
    async def help(self, ctx, *args):
        '''This help message :D'''
        commands = {i for i in ctx.bot.all_commands.values()}

        if len(args) == 0:
            d = '**Bot help:**'

            for cmd in commands:
                d += '\n`{}{}`'.format(ctx.prefix, cmd.name)

                brief = cmd.brief
                if brief is None and cmd.help is not None:
                    brief = cmd.help.split('\n')[0]

                if brief is not None:
                    d += ' - {}'.format(brief)
        elif len(args) == 1:
            if args[0] not in ctx.bot.all_commands:
                d = 'Command not found.'
            else:
                cmd = ctx.bot.all_commands[args[0]]
                d = 'Help for command `{}`:\n'.format(cmd.name)
                d += '\n**Usage:**\n'

                params = list(cmd.clean_params.items())
                p_str = ''
                for p in params:
                    if p[1].default == p[1].empty:
                        p_str += ' [{}]'.format(p[0])
                    else:
                        p_str += ' <{}>'.format(p[0])

                d += '`{}{}{}`\n'.format(ctx.prefix, cmd.name, p_str)
                d += '\n**Description:**\n'
                d += '{}\n'.format('None' if cmd.help is None else cmd.help.strip())

                if cmd.checks:
                    d += '\n**Checks:**'
                    for check in cmd.checks:
                        d += '\n{}'.format(check.__qualname__.split('.')[0])
                    d += '\n'

                if cmd.aliases:
                    d += '\n**Aliases:**'
                    for alias in cmd.aliases:
                        d += '\n`{}{}`'.format(ctx.prefix, alias)

                    d += '\n'
        else:
            d = '**TWOWBot help:**'

            for i in args:
                if i in ctx.bot.all_commands:
                    cmd = ctx.bot.all_commands[i]
                    d += '\n`{}{}`'.format(ctx.prefix, i)

                    brief = cmd.brief
                    if brief is None and cmd.help is not None:
                        brief = cmd.help.split('\n')[0]

                    if brief is None:
                        brief = 'No description'

                    d += ' - {}'.format(brief)
                else:
                    d += '\n`{}{}` - Command not found'.format(ctx.prefix, i.replace('@', '@\u200b').replace('`', '`\u200b'))

        d += '\n*Made by hanss314#0128*'
        await ctx.bot.send_message(ctx.channel, d)

        
    async def rem_roles(self, ctx):
        if ctx.guild.large: await ctx.bot.request_offline_members(ctx.guild)
        roles = [discord.utils.find(lambda r: r.id==i, ctx.guild.roles) for i in ctx.bot.roles.values()]
        for member in ctx.guild.members:
            await member.remove_roles(*roles, reason='Game over.')

def setup(bot):
    bot.add_cog(Players())
