import asyncio
import discord

from os import path
from ruamel import yaml
from discord.ext import commands


def lower(arg):
    return arg.lower()

class Flairs:
    def __init__(self, bot):
        self.bot = bot
        if not path.isfile('bot_data/flairs.yml'):
            with open('bot_data/flairs.yml', 'w+') as flairs:
                yaml.dump({}, flairs)

        with open('bot_data/flairs.yml', 'r') as flairs:
            self.flairs = yaml.load(flairs)

    async def safe_delete(self, ctx, after=5):
        async def _delete():
            await asyncio.sleep(after)
            if ctx.me.guild_permissions.manage_messages:
                await ctx.message.delete()

        asyncio.ensure_future(_delete(), loop=self.bot.loop)

    @commands.command(aliases=['flairs'])
    @commands.guild_only()
    async def listflairs(self, ctx):
        """List the available flairs for this server"""
        embed = discord.Embed(title='Available flairs:',
                              color=ctx.me.color.value)
        flairs = self.flairs.get(ctx.guild.id)
        if flairs is None or len(flairs) == 0:
            embed.add_field(name='Error', value='No flairs setup')
        else:
            embed.description = f'*Use `{ctx.prefix}fclear [category '\
                                 '(optional)]` to remove your flairs.*'

            for f in flairs:
                embed.add_field(
                    name=f'*{f}*',
                    value='\n'.join(f'`{ctx.prefix}f {i}`' for i in flairs[f]),
                    inline=False)
        embed.set_footer(text=f'Requested by {ctx.author}')

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def fclear(self, ctx, *, flair: str=''):
        """Remove all your flairs for this server"""
        await self.safe_delete(ctx)

        flairs = self.flairs.get(ctx.guild.id)
        if flairs is None or len(flairs) == 0:
            return await ctx.send('No flairs setup', delete_after=5)

        if not ctx.me.guild_permissions.manage_roles:
            return await ctx.send('I don\'t have `Manage Roles` permission.',
                                  delete_after=5)

        if flair:
            for category in flairs:
                if category.lower() == flair.lower():
                    break
            else:
                return await ctx.send('No category found with that name.',
                                      delete_after=5)

            to_remove = []
            for f in flairs[category]:
                role = discord.utils.get(ctx.guild.roles,
                                         id=flairs[category][f])
                if role is not None:
                    to_remove.append(role)

            await ctx.author.remove_roles(*to_remove)

            return await ctx.send(f'All "{category}" flairs have been removed.',
                                  delete_after=5)
        else:
            to_remove = []

            for category in flairs:
                for f in flairs[category]:
                    role = discord.utils.get(ctx.guild.roles,
                                             id=flairs[category][f])
                    if role is not None:
                        to_remove.append(role)

            await ctx.author.remove_roles(*to_remove)

            return await ctx.send('All your flairs have been removed.',
                                  delete_after=5)

    @commands.command(aliases=['flair'])
    @commands.guild_only()
    async def f(self, ctx, *, flair: str=''):
        """Get a flair"""
        await self.safe_delete(ctx)

        flairs = self.flairs.get(ctx.guild.id)
        if flairs is None or len(flairs) == 0:
            return await ctx.send('No flairs setup', delete_after=5)

        if not flair:
            return await ctx.send('I need to know what flair you want.. '
                                  f'Use `{ctx.prefix}flairs` to list them all.',
                                  delete_after=5)

        if not ctx.me.guild_permissions.manage_roles:
            return await ctx.send('I don\'t have `Manage Roles` permission.',
                                  delete_after=5)

        for category in flairs:
            if flair in flairs[category]:
                break
        else:
            return await ctx.send('No such flair avaliable with that name.',
                                  delete_after=5)

        to_remove = []
        to_add = None
        for f in flairs[category]:
            role = discord.utils.get(ctx.guild.roles, id=flairs[category][f])
            if f == flair:
                if role is None:
                    return await ctx.send('The flairs have be configured '
                                          'incorrectly; this flair is '
                                          'unavaliable.',
                                          delete_after=5)
                to_add = role
            elif role is not None:
                to_remove.append(role)

        await ctx.author.remove_roles(*to_remove)
        await ctx.author.add_roles(to_add)

        return await ctx.send('You have been given the requested flair!',
                              delete_after=5)

    @commands.command(aliases=['addflair'])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def add_flair(self, ctx, category: lower, name: lower, role: discord.Role):
        """Adds a flair to a category"""
        if ctx.guild.id not in self.flairs:
            self.flairs[ctx.guild.id] = {}

        if category not in self.flairs[ctx.guild.id]:
            self.flairs[ctx.guild.id][category] = {}

        for category, flairs in self.flairs[ctx.guild.id].items():
            if name in flairs and category != category:
                return await ctx.send(
                    f'That name is in the flair category `{category}`, remove it with `remflair` first'
                )

        self.flairs[ctx.guild.id][category][name] = role.id
        await ctx.send(f'Added {role} under {category} as {name}')

    @commands.command(aliases=['remflair'])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def rem_flair(self, ctx, name):
        if ctx.guild.id not in self.flairs:
            return await ctx.send('Flair not found')

        for category, flairs in self.flairs[ctx.guild.id].items():
            if name in flairs:
                del flairs[name]
                return await ctx.send(f'Removed {name} from {category}')

        await ctx.send('Flair not found')

    @add_flair.after_invoke
    @rem_flair.after_invoke
    async def save_flairs(self, _):
        with open('bot_data/flairs.yml', 'w') as flairs:
            yaml.dump(self.flairs, flairs)

def setup(bot):
    bot.add_cog(Flairs(bot))
