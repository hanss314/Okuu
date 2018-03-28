import traceback
import logging
import sys
import re

from discord.ext import commands
import ruamel.yaml as yaml
import discord


class CodeNamesBot(commands.Bot):
    class ErrorAlreadyShown(Exception): pass

    def __init__(self, log_file=None, *args, **kwargs):
        self.config = {}
        self.board = None
        self.yaml = yaml.YAML(typ='safe')
        
        with open('config.yml') as data_file:
            self.config = self.yaml.load(data_file)
            
        self.roles = self.config['role_ids']

        logging.basicConfig(level=logging.INFO, format='[%(name)s %(levelname)s] %(message)s')
        self.logger = logging.getLogger('bot')

        super().__init__(
            command_prefix=self.config['prefix'],
            *args,
            **kwargs
        )

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)

    async def on_command_error(self, ctx: commands.Context, exception: Exception):
        if isinstance(exception, commands.CommandInvokeError):
            # all exceptions are wrapped in CommandInvokeError if they are not a subclass of CommandError
            # you can access the original exception with .original
            if isinstance(exception.original, discord.Forbidden):
                # permissions error
                try:
                    await ctx.send('Permissions error: `{}`'.format(exception))
                except discord.Forbidden:
                    # we can't send messages in that channel
                    return

            # Print to log then notify developers
            try:
                lines = traceback.format_exception(type(exception),
                                                   exception,
                                                   exception.__traceback__)
            except RecursionError:
                raise exception

            self.logger.error(''.join(lines))

            return
        
        if isinstance(exception, commands.CheckFailure):
            await ctx.send(
                'Foreign substance detected! ...what do I do again? Whatever, I\'ll just ~~exterminate~~ ignore it.',
                delete_after = 10
            )
        elif isinstance(exception, commands.CommandOnCooldown):
            await ctx.send(f'Overheating! Try again in {exception.retry_after:.2f} seconds.')

        elif isinstance(exception, commands.CommandNotFound) or isinstance(exception, self.ErrorAlreadyShown):
            pass
        elif isinstance(exception, commands.UserInputError):
            error = ' '.join(exception.args)
            error_data = re.findall('Converting to \"(.*)\" failed for parameter \"(.*)\"\.', error)
            if not error_data:
                await ctx.send('Unyu? {}'.format(' '.join(exception.args)))
            else:
                await ctx.send('Unyu? I thought `{1}` was supposed to be a `{0}`...'.format(*error_data[0]))
        else:
            info = traceback.format_exception(type(exception), exception, exception.__traceback__, chain=False)
            self.logger.error('Unhandled command exception - {}'.format(''.join(info)))

    async def on_error(self, event_method, *args, **kwargs):
        info = sys.exc_info()
        if isinstance(info[1], self.ErrorAlreadyShown):
            return
        self.logger.error('Unhandled command exception - {}'.format(''.join(info)))

    async def on_ready(self):
        self.logger.info('Connected to Discord')
        self.logger.info('Guilds  : {}'.format(len(self.guilds)))
        self.logger.info('Users   : {}'.format(len(set(self.get_all_members()))))
        self.logger.info('Channels: {}'.format(len(list(self.get_all_channels()))))
        game = discord.Game(name='with a nuclear reactor | {}help'.format(self.command_prefix))
        await self.change_presence(game=game)

    async def close(self):
        await super().close()

    def run(self):
        debug = any('debug' in arg.lower() for arg in sys.argv) or self.config.get('debug_mode', False)

        if debug:
            # if debugging is enabled, use the debug subconfiguration (if it exists)
            if 'debug' in self.config:
                self.config = {**self.config, **self.config['debug']}
            self.logger.info('Debug mode active...')
            self.debug = True

        self.remove_command("help")
        token = self.config['token']
        cogs = self.config.get('cogs', [])
        for cog in cogs:
            try:
                self.load_extension(cog)
            except Exception as e:
                self.logger.exception('Failed to load cog {}.'.format(cog))
            else:
                self.logger.info('Loaded cog {}.'.format(cog))

        self.logger.info('Loaded {} cogs'.format(len(self.cogs)))
        super().run(token)

if __name__ == '__main__':
    bot = CodeNamesBot()
    bot.run()
