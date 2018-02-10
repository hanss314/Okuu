import discord
import random

from .UTTT import mafia
from .UTTT.board import UTTT_Board
from discord.ext import commands
from ruamel import yaml


def avocados(arg):
    try: return int(arg)
    except ValueError:
        return len([c for c in arg if ord(c) == 129361])


class Games:

    def __init__(self, bot):
        self.bot = bot
        self.mafia_games = yaml.safe_load(open('bot_data/mafia.yml', 'r'))

    @staticmethod
    def get_game(player, db, emptytype, auto_join=True, constr_args=()):
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
                await ctx.send(
                    f'{ctx.author.mention}, your move will be made on board {board.next_play} ```\n{board.to_UI()}```'
                )
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

    @commands.group(invoke_without_command=True)
    async def mafia(self, ctx):
        '''Play a game of mafia'''
        await ctx.send(f'Use `{ctx.prefix}mafia join` to join a game of mafia on this server!')

    @mafia.command(name='join')
    async def mafia_join(self, ctx):
        '''
        Join a game of mafia in this channel
        Use `mafia start` to vote to start the game
        '''
        if ctx.channel.id in self.mafia_games:
            game = self.mafia_games[ctx.channel.id]
        else:
            game = self.mafia_games[ctx.channel.id] = mafia.new_game(ctx.channel.id)

        if ctx.author.id in game['players']:
            return await ctx.send(
                f'You have already joined! Use `{ctx.prefix}mafia start` to vote to start the game.'
            )

        for existing_game in self.mafia_games.values():
            if ctx.author.id in existing_game['players']:
                return await ctx.send('You are in another game!')

        game['players'][ctx.author.id] = mafia.new_player()
        await ctx.send(f'Joined game! Use `{ctx.prefix}mafia start` to vote to start.')

    @mafia.command(name='start')
    async def mafia_start(self, ctx):
        '''Vote to start the game'''
        if ctx.channel.id not in self.mafia_games or ctx.author.id not in self.mafia_games[ctx.channel.id]['players']:
            return await ctx.send('You have not joined the game.')

        game = self.mafia_games[ctx.channel.id]
        if game['started']:
            return await ctx.send('Game has already started')

        game['players'][ctx.author.id]['can_start'] = True
        yes = 0
        no = 0
        for player in game['players'].values():
            if player['can_start']: yes += 1
            else: no += 1

        if len(game['players']) < 6:
            return await ctx.send(f'Decision noted, wait for {6-len(game["players"])} more to join.')
        elif yes / no < 2:
            return await ctx.send('Decision noted, wait for more people to start.')

        mafia.start(game)
        mafia_members = ', '.join(self.bot.get_user(member) for member in game['mafia'])
        for member in game['mafia']:
            self.bot.get_user(member).send(
                'You are a member of the mafia. Each night, vote amongst your fellow mafia to kill an innocent. '
                f'These are the members of the mafia: {mafia_members}.'
            )

        self.bot.get_user(game['doctor']).send(
            'You are the doctor. Each night you can choose one person to save.'
        )
        self.bot.get_user(game['detective']).send(
            'You are the detective. Each night you can see the role of one user.'
        )
        for innocent in game['innocents']:
            self.bot.get_user(innocent).send('You are an innocent. Every day, you vote to lynch someone.')

        await mafia.prompt_voting(self.bot, game)

    @mafia.command(name='vote')
    async def mafia_vote(self, ctx, number: int):
        number -= 1
        if not isinstance(ctx.channel, discord.abc.PrivateChannel):
            try: await ctx.message.delete()
            except discord.Forbidden: pass
            await ctx.send('Please only vote in DMs.')

        for game in self.mafia_games.values():
            if ctx.author.id in game['players']:
                game = game
                break
        else:
            return await ctx.send('You are not in a game.')

        if not game['started']:
            return await ctx.send('The game has not started.')

        if ctx.author.id not in game['can_vote']:
            return await ctx.send('You may not vote during this phase.')

        game['votes'][ctx.author.id] = number
        await ctx.send('Vote recorded')
        if len(game['votes']) < len(game['can_vote']): return

        count = len(game['candidates'])
        mafia.process_votes(game)


        if len(game['candidates']) == 1:
            win = await mafia.next_phase(self.bot, game)
        elif count != len(game['candidates']):
            await mafia.prompt_voting(self.bot, game)
            return
        else:
            game['candidates'] = random.sample(game['candidates'], 1)
            for user in game['can_vote']:
                self.bot.get_user(user).send('Stalemate reached. Choosing random user.')

            win = await mafia.next_phase(self.bot, game)

        if win:
            del self.mafia_games[game['channel']]

    @mafia_join.after_invoke
    @mafia_start.after_invoke
    async def save_mafia(self, _):
        yaml.dump(self.mafia_games, open('bot_data/mafia.yml', 'w'))


def setup(bot):
    bot.add_cog(Games(bot))
