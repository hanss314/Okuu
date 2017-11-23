import discord
from discord.ext import commands

from cogs.codenames import checks
from cogs.codenames.board import Board
from cogs.codenames.enums import Teams


def to_lower(argument):
    return argument.lower()


class Codenames:
    @commands.command()
    @checks.spymaster()
    async def hint(self, ctx, word, num):
        """Give a hint"""
        try: await ctx.message.delete()
        except discord.Forbidden: pass
        if ctx.bot.board.max_moves != 0:
            return await ctx.send('You\'ve already made a hint!', delete_after=10)
        try: 
            n = int(num)
        except ValueError:
            n = 'unlimited'
            ctx.bot.board.set_hint_number(100000)
        else: 
            if n == 0:
                ctx.bot.board.set_hint_number(100000)
            elif n < 0:
                return await ctx.send('Just... No.')
            else:
                ctx.bot.board.set_hint_number(n)

        ctx.bot.board.hint_word = f'"{word}: {n}"'
        mention = ctx.bot.roles['red'] if ctx.bot.board.turn == Teams.RED else ctx.bot.roles['blue']
        await ctx.bot.get_channel(ctx.bot.config['channel']).send(
            '<@&{}> The hint is "{}: {}"'.format(mention, word, n)
        )
        
    @commands.command(aliases=['submit'])
    @checks.player_or_host()
    async def guess(self, ctx, word):
        """Guess a square"""
        if ctx.bot.board.max_moves == 0:
            return await ctx.send('There is no hint!', delete_after=10)
        move = ctx.bot.board.move_count
        result = ctx.bot.board.do_move(word)
        chan = ctx.bot.get_channel(ctx.bot.config['channel'])
        if result == -1: return
        chan.send('{}. {}'.format(move, word))
        ctx.bot.board.draw().save('board.png')
        img = discord.File(open('board.png', 'rb'))
        await chan.send(file=img)
        if result is not None:
            mention = ctx.bot.roles['red'] if ctx.bot.board.turn == Teams.RED else ctx.bot.roles['blue']
            await chan.send('<@&{}> You win! Good job!'.format(mention))
            await self.rem_roles(ctx)
            ctx.bot.board.draw(unhidden=True).save('board.png')
            img = discord.File(open('board.png', 'rb'))
            await chan.send(file=img)
            return
        
        if ctx.bot.board.max_moves == 0: 
            mention = ctx.bot.roles['red_sm'] if ctx.bot.board.turn == Teams.RED else ctx.bot.roles['blue_sm']
            await chan.send('<@&{}> It\'s your turn to make a hint!'.format(mention))
        
    @commands.command(aliases=['pass'])
    @checks.player()
    async def skip(self, ctx):
        """Skip your team's turn"""
        ctx.bot.board.switch_turn()
        chan = ctx.bot.get_channel(ctx.bot.config['channel'])
        ctx.send('Turn skipped.')
        mention = ctx.bot.roles['red_sm'] if ctx.bot.board.turn == Teams.RED else ctx.bot.roles['blue_sm']
        await chan.send('<@&{}> It\'s your turn to make a hint!'.format(mention))

    @commands.command
    @checks.player()
    async def get_hint(self, ctx):
        try: await ctx.send(ctx.bot.board.hint_word)
        except AttributeError:
            await ctx.send('There is no hint!')
        
    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def board(self, ctx):
        """Show the board"""
        ctx.bot.board.draw().save('board.png')
        img = discord.File(open('board.png', 'rb'))
        await ctx.send(file=img)

    @commands.command()
    @checks.host()
    async def setup(self, ctx, *words: to_lower):
        """Setup a new board"""
        ctx.bot.board = Board(words=list(set(words)))
        await ctx.send('Setup a new board!')
        chan = ctx.bot.get_channel(ctx.bot.config['revealed'])
        ctx.bot.board.draw(unhidden=True).save('board.png')
        await chan.send(file=discord.File(open('board.png', 'rb')))
        for member in ctx.guild.members:
            for role in member.roles:
                if role.id in (ctx.bot.roles['red_sm'], ctx.bot.roles['red_sm']):
                    try:
                        await member.send(file=discord.File(open('board.png', 'rb')))
                    except discord.Forbidden:
                        pass

        ctx.bot.board.draw().save('board.png')
        img = discord.File(open('board.png', 'rb'))
        chan = ctx.bot.get_channel(ctx.bot.config['channel'])
        await chan.send(file=img)
        await chan.send('<@&{}> It\'s your turn to make a hint!'.format(ctx.bot.roles['red_sm']))

    @staticmethod
    async def rem_roles(ctx):
        roles = [discord.utils.find(lambda r: r.id == i, ctx.guild.roles) for i in ctx.bot.roles.values()]
        for member in ctx.guild.members:
            await member.remove_roles(*roles, reason='Game over.')


def setup(bot):
    bot.add_cog(Codenames())
