from discord.ext import commands
import ruamel.yaml as yaml
import discord

from cogs.codenames.board import Board
from cogs import checks

def to_lower(argument):
    return argument.lower()

class Hosting():
    @commands.command()
    @checks.host()
    async def setup(self, ctx, *words: to_lower):
        '''Setup a new board'''
        ctx.bot.board = Board(words=list(set(words)))
        await ctx.send('Setup a new board!')
        chan = ctx.bot.get_channel(ctx.bot.config['revealed'])
        ctx.bot.board.draw(unhidden=True).save('board.png')
        await chan.send(file=discord.File(open('board.png', 'rb')))
        for member in ctx.guild.members:
            for role in member.roles:
                if role.id in (ctx.bot.roles['red_sm'], ctx.bot.roles['red_sm']):
                    try: await member.send(file=discord.File(open('board.png', 'rb')))
                    except: pass
                    
        ctx.bot.board.draw().save('board.png')
        img = discord.File(open('board.png', 'rb'))
        chan = ctx.bot.get_channel(ctx.bot.config['channel'])
        await chan.send(file=img)
        await chan.send('<@&{}> It\'s your turn to make a hint!'.format(ctx.bot.roles['red_sm']))
    """
    @commands.command()
    @checks.host()
    async def addrole(self, ctx, role, *members: discord.Member):
        '''Assign roles'''
        if role not in ctx.bot.roles:
            return await ctx.send('Valid roles: {}'.format(
                ', '.join(
                    list(ctx.bot.roles.keys())
                    )
                ))
        role = discord.utils.find(lambda r: r.id==ctx.bot.roles[role], ctx.guild.roles)
        for member in members:
            await member.add_roles(role, reason='Give role for codenames.')
        await ctx.send('Roles added!')
            
    @commands.command()
    async def remrole(self, ctx, role, *members: discord.Member):
        '''Assign roles'''
        if role not in ctx.bot.roles:
            return await ctx.send('Valid roles: {}'.format(
                ', '.join(
                    list(ctx.bot.roles.keys())
                    )
                ))
        role = discord.utils.find(lambda r: r.id==ctx.bot.roles[role], ctx.guild.roles)
        if role==None: return await ctx.send('Could not find role with id {}'.format(ctx.bot.roles[role]))
        for member in members:
            await member.remove_roles(role, reason='Remove role for codenames.')
        await ctx.send('Roles removed!')
        """
          
def setup(bot):
    bot.add_cog(Hosting())
