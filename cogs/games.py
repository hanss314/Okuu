from .UTTT.board import UTTT_Board
from .UTTT.avocado import MultiplayerAvocado
from discord.ext import commands

def avocados(arg):
    try: return int(arg)
    except ValueError:
        return len([c for c in arg if ord(c) == 129361])


class Games:

    def __init__(self, bot):
        self.bot = bot

    def get_game(self, player, db, emptytype, auto_join=True, constr_args=()):
        game = None
        for k in db.keys():
            if player in k:
                game = k
                break
            if len(k) == 1:
                game = k

        if not game:
            if not auto_join: raise ValueError
            board = emptytype(*constr_args)
            game = (player,)
            db[game] = board
        elif len(game) == 1 and player not in game:
            if not auto_join: raise ValueError
            board = db[game]
            del db[game]
            game = (game[0], player)
            db[game] = board
        else:
            board = db[game]

        return game, board


    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def uttt(self, ctx, row: int, column: int):
        '''
        Use this command to start and play a uttt game.
        To start a game, the x and y coordinates are the sub-board of your first move
        Use this command to specify the sub-board when needed and make a move when sub-board is specified
        '''
        x, y = row, column
        boards = self.bot.uttt_boards[ctx.guild.id]
        board, game = self.get_game(ctx.author.id, boards, UTTT_Board)

        player = game.index(ctx.author.id) + 1
        if board.turn != player:
            return await ctx.send(f'{ctx.author.mention} It\'s not your turn!')

        if board.next_play == 0:
            legal_moves = [x[:2] for x in board.get_legal_moves()]
            if (x, y) in legal_moves:
                board.next_play = (x, y)
                await ctx.send(f'{ctx.author.mention}, your move will be made on board {board.next_play} ```\n{board.to_UI()}```')
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
                del boards[game]
                del board
                return
            else:
                if len(game) == 1:
                    d = 'Anyone\'s turn'
                else:
                    d = f'<@{game[board.turn-1]}> your turn'

                if board.next_play == 0:
                    d += f', select a sub-board to play on using `{ctx.prefix}utt play` ```\n{board.to_UI()}```'
                else:
                    d += f', you are playing on sub-board {board.next_play}. ```\n{board.to_UI()}```'

                await ctx.send(d)


    @uttt.before_invoke
    async def check_board(self, ctx):
        if not hasattr(self.bot, 'uttt_boards'):
            self.bot.uttt_boards = {}
        if ctx.guild.id not in self.bot.uttt_boards:
            self.bot.uttt_boards[ctx.guild.id] = {}

    @uttt.command(name='cancel')
    @commands.guild_only()
    async def uttt_cancel(self, ctx):
        '''Cancel a game of UTTT'''
        boards = self.bot.uttt_boards[ctx.guild.id]
        for k in boards.keys():
            if ctx.author.id in k:
                game = k
                break
        else:
            return await ctx.send('You have no game running.')

        del boards[game]
        if len(game) > 1:
            other = ctx.guild.get_member(game[game.index(ctx.author.id)-1])
            await ctx.send(f'{ctx.author.mention} Cancelled your game against {other.mention}.')
        else:
            await ctx.send(f'{ctx.author.mention} Game cancelled.')


    @uttt.command(name='help')
    async def uttt_help(self, ctx):
        '''Gives you help on UTTT'''
        d = '**Rules:**\n'
        d += '''
Win three games of Tic Tac Toe in a row. 
You may only play in the big field that corresponds to the last small field your opponent played. 
When your are sent to a field that is already decided, you can choose freely. 
<https://mathwithbaddrawings.com/2013/06/16/ultimate-tic-tac-toe/>
        '''
        await ctx.send(d)

    @commands.group(invoke_without_command=True, aliases=['avo', '🎮🥑🎮'])
    async def avocado(self, ctx):
        """Play a game of Multiplayer Avocado!"""
        d = '''Rules for Multiplayer Avocado:
The first player decides the number of Avocados, using the Avacado emoji
The second player decides the spoon size which is an integer greater or equal to 0
Each player takes turn performing actions. The possible actions are:
1.) "Slice" reduce the number of Avocados to a factor of the current number that is not 1 or the current number
2.) "Mash" square the number of Avocados
3.) "Eat" subtract the spoon size from the number of Avocados and take another turn
4.) "Buy" add the spoon size to the number of Avocados.
If after any action, the number of Avocados reaches a number that was already reached, the player that performed the action loses.
The number of Avocados must be an integer greater or equal to 0 at all times.'''

        await ctx.send(d)

    @avocado.command(name='join')
    @commands.guild_only()
    async def avocado_join(self, ctx, *, number: avocados):
        """Start a game of Multiplayer Avocado"""
        if number < 0: return await ctx.send('No negative avocados please.')
        boards = self.bot.avocados[ctx.guild.id]
        for players in boards.keys():
            if ctx.author.id in players:
                return await ctx.send(f'{ctx.author.mention} You\'re already in a game!')

        game, board = self.get_game(ctx.author.id, boards, MultiplayerAvocado)
        if len(game) == 1:
            board.avocados = number
            board.previous = [number]
            await ctx.send(f'{ctx.author.mention} Started a game with {number} avocado{"s" if number != 1 else ""}!')
        else:
            if number < 1:
                await ctx.send('Spoon size must be greater than 0!')
                boards[(game[0],)] = board
                del board[game]
                return

            board.spoon = number
            await ctx.send(
                f'<@{game[0]}> your turn. Spoon size is {number}.' +
                f'There are {board.avocados} avocado{"s" if board.avocados != 1 else ""}')

    async def get_avocado_game(self, ctx, error=True):
        await self.check_avocado(ctx)
        if (ctx.author.id,) in self.bot.avocados[ctx.guild.id]:
            await ctx.send('It\'s not your turn!')
            raise ValueError
        try:
            players, game = self.get_game(
                    ctx.author.id,
                    self.bot.avocados[ctx.guild.id],
                    None, False)
            if players[game.turn] == ctx.author.id:
                return players, game

        except ValueError as e:
            await ctx.send('You aren\'t in a game!')
            raise e

        if error:
            await ctx.send('It\'s not your turn!')
            raise ValueError
        else: return players, game

    @avocado.command(name='slice')
    @commands.guild_only()
    async def avocado_slice(self, ctx, number: int):
        """Slice the Avocados"""
        try:  players, game = await self.get_avocado_game(ctx)
        except ValueError: return
        try:
            game.slice(number)
            await ctx.send(f'<@{players[game.turn]}> your turn, ' +
                           f'there are {game.avocados} avocado{"s" if game.avocados != 1 else ""}')
        except ValueError:
            return await ctx.send('You can\'t slice like that!')

        winner = game.check_win()
        if winner >= 0:
            await ctx.send(f'{game.avocados} has been reached before! <@{players[winner]}> wins!')
            del self.bot.avocados[ctx.guild.id][players]
            return

    @avocado.command(name='mash')
    @commands.guild_only()
    async def avocado_mash(self, ctx):
        """Mash the Avocados"""
        try: players, game = await self.get_avocado_game(ctx)
        except ValueError: return
        game.mash()
        winner = game.check_win()
        if winner >= 0:
            await ctx.send(f'{game.avocados} has been reached before! <@{players[winner]}> wins!')
            del self.bot.avocados[ctx.guild.id][players]
            return

        await ctx.send(f'<@{players[game.turn]}> your turn, ' +
                       f'there are {game.avocados} avocado{"s" if game.avocados != 1 else ""}')

    @avocado.command(name='eat')
    @commands.guild_only()
    async def avocado_eat(self, ctx, times: int = 1):
        """Eat some Avocados"""
        try: players, game = await self.get_avocado_game(ctx)
        except ValueError: return
        for i in range(times):
            try: game.eat()
            except ValueError:
                await ctx.send(
                    f'Ate {i} time{"s" if i != 1 else ""} before not having enough avocados. ' +
                    f'There are {game.avocados} avocados {"s" if game.avocados != 1 else ""}')
                return

            winner = game.check_win()
            if winner >= 0:
                await ctx.send(f'{game.avocados} has been reached before! <@{players[winner]}> wins!')
                del self.bot.avocados[ctx.guild.id][players]
                return

        await ctx.send(f'There are {game.avocados} avocado{"s" if game.avocados != 1 else ""}')

    @avocado.command(name='buy')
    @commands.guild_only()
    async def avocado_buy(self, ctx):
        """Buy some Avocados"""
        try: players, game = await self.get_avocado_game(ctx)
        except ValueError: return
        game.buy()
        winner = game.check_win()
        if winner >= 0:
            await ctx.send(f'{game.avocados} has been reached before! <@{players[winner]}> wins!')
            del self.bot.avocados[ctx.guild.id][players]
            return

        await ctx.send(f'<@{players[game.turn]}> your turn, ' +
                       f'there are {game.avocados} avocado{"s" if game.avocados != 1 else ""}')

    @avocado.command(name='skip')
    @commands.guild_only()
    async def avocado_skip(self, ctx):
        """End your turn"""
        try: players, game = await self.get_avocado_game(ctx)
        except ValueError: return
        try: game.switch_turn()
        except ValueError:
            await ctx.send('You have to make a move!')

        await ctx.send(f'<@{players[game.turn]}> your turn, ' +
                       f'there are {game.avocados} avocado{"s" if game.avocados != 1 else ""}')

    @avocado.command(name='cancel')
    @commands.guild_only()
    async def avocado_cancel(self, ctx):
        """Cancel a game of Multiplayer Avocado"""
        try:
            players, game = await self.get_avocado_game(ctx, False)
        except ValueError:
            return
        del self.bot.avocados[ctx.guild.id][players]
        if len(players) > 1:
            await ctx.send(f'Cancelled your game with <@{players[players.index(ctx.author.id) - 1]}>')
        else:
            await ctx.send('Game cancelled.')

    @avocado.command(name='previous')
    @commands.guild_only()
    async def avocado_previous(self, ctx):
        """Check previous Avocado counts"""
        try: players, game = await self.get_avocado_game(ctx, False)
        except ValueError: return
        await ctx.send(str(game.previous))

    @avocado_join.before_invoke
    async def check_avocado(self, ctx):
        if not hasattr(self.bot, 'avocados'):
            self.bot.avocados = {}
        if ctx.guild.id not in self.bot.avocados:
            self.bot.avocados[ctx.guild.id] = {}


def setup(bot):
    bot.add_cog(Games(bot))
