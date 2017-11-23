import discord

from .UTTT.board import TTT_Board, UTTT_Board
from discord.ext import commands


class TTT:

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def uttt(self, ctx):
        m = 'Subcommands:\n'
        for command in ctx.command.commands:
            m += f'`{command.name}-{command.brief}\n`'
        await ctx.send(m)

    @uttt.command(name='play')
    async def uttt_play(self, ctx):
        game = None
        boards = self.bot.uttt_boards
        for k in boards.keys():
            if ctx.author.id in k:
                game = k
                break
            if len(k) == 1:
                game = k

        if not game:
            board = UTTT_Board()
            boards[(ctx.author.id,)] = board
        elif len(game) == 1:
            board = boards[game]
            del boards[game]
            game = (game[0], ctx.author.id)
            boards[game] = board

        player = game.index(ctx.author.id)


    @uttt_play.before_invoke
    async def check_board(self, ctx):
        if not hasattr(self.bot, 'uttt_boards'):
            self.bot.uttt_boards = {}


def setup(bot):
    bot.add_cog(TTT(bot))
