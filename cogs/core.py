import sys
import discord
import subprocess
import asyncio
import inspect

from discord.ext import commands


class Core:

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def say(self, ctx, channel: discord.TextChannel, *, text: str):
        await channel.send(text)

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def reload(self, ctx, *, cog=''):
        """Reloads an extension"""
        try:
            ctx.bot.unload_extension(cog)
            ctx.bot.load_extension(cog)
        except Exception as e:
            await ctx.send('<:okuuSad:383088578684649500> Failed to load: `{}`\n```py\n{}\n```'.format(cog, e))
        else:
            await ctx.send('<:okuuHappy:383086039100686336> Reloaded cog {} successfully'.format(cog))

    @reload.group(name='all', invoke_without_command=True)
    @commands.is_owner()
    async def reload_all(self, ctx):
        """Reloads all extensions"""
        if 'cogs.util' in sys.modules:
            import importlib
            importlib.reload(sys.modules['cogs.util'])

        for extension in ctx.bot.extensions.copy():
            ctx.bot.unload_extension(extension)
            try:
                ctx.bot.load_extension(extension)
            except Exception as e:
                await ctx.send('<:okuuSad:383088578684649500> Failed to load `{}`:\n```py\n{}\n```'.format(extension, e))

        await ctx.send('<:okuuHappy:383086039100686336> Reloaded {} cogs successfully'.format(len(ctx.bot.extensions)))

    @commands.command(aliases=['exception'])
    @commands.is_owner()
    async def error(self, ctx, *, text: str = None):
        """Raises an error. Testing purposes only, please don't use."""
        await ctx.send('Foreign substance detected! Uhh... what do I do again? Oh well, I\'ll just kill it!')
        raise Exception(text or 'Pichuun~')

    @commands.command()
    @commands.is_owner()
    async def setname(self, ctx, *, name):
        """Change the bot's username"""
        try:
            await self.bot.user.edit(username=name)
        except (discord.HTTPException, discord.Forbidden):
            await ctx.send('Unyu? What\'s my name again?')

    @commands.command()
    @commands.is_owner()
    async def setnick(self, ctx, *, name):
        """Change the bot's nickname"""
        try:
            await ctx.guild.get_member(self.bot.user.id).edit(nick=name)
        except (discord.HTTPException, discord.Forbidden):
            await ctx.send('Unyu? What\'s my name again?')

    @commands.command()
    @commands.is_owner()
    async def setavatar(self, ctx):
        """Change the bot's profile picture"""
        attachment = ctx.message.attachments[0]
        await attachment.save(attachment.filename)
        try:
            with open(attachment.filename, 'rb') as avatar:
                await self.bot.user.edit(avatar=avatar.read())
        except discord.HTTPException:
            await ctx.send('Changing the avatar failed.')
        except discord.InvalidArgument:
            await ctx.send('You did not upload an image.')

    @commands.command(aliases=['shutdown'])
    @commands.is_owner()
    async def die(self, ctx):
        """Shuts down the bot"""
        ctx.bot.dying = True
        await ctx.send('<:power:383084655764832256>Pichuun~<:power:383084655764832256>')
        await ctx.bot.logout()

    @commands.command(aliases=['git_pull'])
    async def update(self, ctx):
        """Updates the bot from git"""

        await ctx.send(':radioactive: Warning! :radioactive: Warning! :radioactive: Pulling from git!')

        if sys.platform == 'win32':
            process = subprocess.run('git pull', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.stdout, process.stderr
        else:
            process = await asyncio.create_subprocess_exec('git', 'pull', stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE)
            stdout, stderr = await process.communicate()
        stdout = stdout.decode().splitlines()
        stdout = '\n'.join('+ ' + i for i in stdout)
        stderr = stderr.decode().splitlines()
        stderr = '\n'.join('- ' + i for i in stderr)

        await ctx.send('`Git` response: ```diff\n{}\n{}```'.format(stdout, stderr))

    @commands.command()
    async def revert(self, ctx, commit):
        """Revert local copy to specified commit"""

        await ctx.send(':radioactive: Warning! :radioactive: Warning! :radioactive: Reverting!')

        if sys.platform == 'win32':
            process = subprocess.run('git reset --hard {}'.format(commit), shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            stdout, stderr = process.stdout, process.stderr
        else:
            process = await asyncio.create_subprocess_exec('git', 'reset', '--hard', commit, stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE)
            stdout, stderr = await process.communicate()
        stdout = stdout.decode().splitlines()
        stdout = '\n'.join('+ ' + i for i in stdout)
        stderr = stderr.decode().splitlines()
        stderr = '\n'.join('- ' + i for i in stderr)

        await ctx.send('`Git` response: ```diff\n{}\n{}```'.format(stdout, stderr))

    @commands.command(aliases=['gitlog'])
    async def git_log(self, ctx, commits: int = 20):
        """Shows the latest commits. Defaults to 20 commits."""

        if sys.platform == 'win32':
            process = subprocess.run('git log --pretty=oneline --abbrev-commit', shell=True,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.stdout, process.stderr
        else:
            process = await asyncio.create_subprocess_exec('git', 'log', '--pretty=oneline', '--abbrev-commit',
                                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await process.communicate()
        stdout = stdout.decode().splitlines()
        stdout = '\n'.join('+ ' + i[:90] for i in stdout[:commits])
        stderr = stderr.decode().splitlines()
        stderr = '\n'.join('- ' + i for i in stderr)

        if commits > 10:
            try:
                await ctx.author.send('`Git` response: ```diff\n{}\n{}```'.format(stdout, stderr))
            except discord.errors.HTTPException:
                import os
                with open('gitlog.txt', 'w') as log_file:
                    log_file.write('{}\n{}'.format(stdout, stderr))
                with open('gitlog.txt', 'r') as log_file:
                    await ctx.author.send(file=discord.File(log_file))
                os.remove('gitlog.txt')
        else:
            await ctx.send('`Git` response: ```diff\n{}\n{}```'.format(stdout, stderr))

    @commands.command(aliases=['eval'])
    @commands.is_owner()
    async def debug(self, ctx, *, code: str):
        '''Evaluates code'''

        env = {
            'ctx': ctx,
            'bot': ctx.bot,
            'guild': ctx.guild,
            'author': ctx.author,
            'message': ctx.message,
            'channel': ctx.channel
        }
        env.update(globals())

        try:
            result = eval(code, env)

            if inspect.isawaitable(result):
                result = await result

            colour = 0x00FF00
        except Exception as e:
            result = type(e).__name__ + ': ' + str(e)
            colour = 0xFF0000

        embed = discord.Embed(colour=colour, title=code, description='```py\n{}```'.format(result))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Core(bot))
