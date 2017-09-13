import discord
from discord.ext import commands

from cogs.codenames.enums import Teams

def host():
    async def predicate(ctx: commands.Context) -> bool:
        r = discord.utils.find(lambda m:m.id == ctx.bot.roles['host'], ctx.guild.roles)
        return r in ctx.author.roles   
    return commands.check(predicate)

def spymaster():
    async def predicate(ctx: commands.Context) -> bool:
        if (ctx.bot.board is not None and ctx.bot.board.get_winner() is None):
            smrole = ctx.bot.roles['red_sm'] if ctx.bot.board.turn == Teams.RED else ctx.bot.roles['blue_sm']
            for role in ctx.author.roles:
                if role.id == smrole: return True
        
        return False
    return commands.check(predicate)

def player():
    async def predicate(ctx: commands.Context) -> bool:
        if (ctx.bot.board is not None and ctx.bot.board.get_winner() is None):
            smrole = ctx.bot.roles['red'] if ctx.bot.board.turn == Teams.RED else ctx.bot.roles['blue']
            for role in ctx.author.roles:
                if role.id == smrole: return True
        
        return False
    return commands.check(predicate)

def player_or_host():
    async def predicate(ctx: commands.Context) -> bool:
        if (ctx.bot.board is not None and ctx.bot.board.get_winner() is None):
            smrole = ctx.bot.roles['red'] if ctx.bot.board.turn == Teams.RED else ctx.bot.roles['blue']
            for role in ctx.author.roles:
                if role.id == smrole: return True
            
        r = discord.utils.find(lambda m:m.id == ctx.bot.roles['host'], ctx.guild.roles)
        return r in ctx.author.roles   
    return commands.check(predicate)
