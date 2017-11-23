from .UTTT.board import TTT_Board, UTTT_Board
from discord.ext import commands


class TTT:

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def uttt(self, ctx):
        '''Play a game of ultimate tic tac toe'''
        m = 'Subcommands:\n'
        for command in ctx.command.commands:
            m += f'`{command.name}`-{command.brief}\n'
        await ctx.send(m)

    @uttt.command(name='play')
    async def uttt_play(self, ctx, x: int, y: int):
        '''
        Use this command to start a game and to play a game.
        To start a game, the x and y coordinates are the sub-board of your first move
        Use this command to specify the sub-board when needed and make a move when sub-board is specified
        '''
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
        else:
            board = boards[game]

        player = game.index(ctx.author.id) + 1
        if board.turn != player:
            return await ctx.send(f'{ctx.author.mention} It\'s not your turn!')

        if board.next_play == 0:
            legal_moves = [x[:2] for x in board.get_legal_moves()]
            if (x, y) in legal_moves:
                board.next_play = (x, y)
                await ctx.send(f'{ctx.author.mention}, your move will be made on board {board.next_play}')
                return
            else:
                await ctx.send(f'{ctx.author.mention} that is not a playable board.')
                return

        else:
            move = (*board.next_play, (x, y))
            if move not in board.get_legal_moves():
                return await ctx.send(f'{ctx.author.mention} that is not a legal move.')
            winner = board.play_move(move, board.turn)
            board.turn = board.turn % 2 + 1
            if winner != 0:
                await ctx.send(f'<@{game[winner-1]}> has won! ```\n{board.to_UI()}```')
                return
            else:
                if board.next_play == 0:
                    await ctx.send(
                        f'<@{game[winner-1]}> your turn, select a sub-board to play on using `{ctx.prefix}utt play` ```\n{board.to_UI()}```'
                    )
                else:
                    await ctx.send(
                        f'<@{game[board.turn-1]}> your turn, you are playing on sub-board {board.next_play}. ```\n{board.to_UI()}```'
                    )

    @uttt_play.before_invoke
    async def check_board(self, ctx):
        if not hasattr(self.bot, 'uttt_boards'):
            self.bot.uttt_boards = {}


def setup(bot):
    bot.add_cog(TTT(bot))
