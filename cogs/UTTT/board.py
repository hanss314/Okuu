class TTT_Board(list):
    ui_map = [
        ' ',
        'X',
        'O'
    ]

    def __init__(self):
        list.__init__(self,
                      # create 3x3 board of 0s
                      [[0, 0, 0] for i in range(3)]
                      )
        self.legal_moves = self.get_legal_moves()

    def get_legal_moves(self):
        legal_moves = []
        # iterate through every square
        for i in range(3):
            for j in range(3):
                # if square isn't taken
                if self[i][j] == 0:
                    legal_moves.append((i, j))
        return legal_moves

    def play_move(self, move, player):
        i, j = move[0], move[1]
        # set square
        self[i][j] = player
        # check for win
        winner = self.check_win((i, j))
        return winner

    def check_win(self, location):
        x, y = location[0], location[1]
        # vertical
        if self[0][y] == self[1][y] == self[2][y]:
            return self[x][y]
        # horizontal
        if self[x][0] == self[x][1] == self[x][2]:
            return self[x][y]
        # diagonal
        if x == y and self[0][0] == self[1][1] == self[2][2]:
            return self[x][y]
        # other diagonal
        if x + y == 2 and self[0][2] == self[1][1] == self[2][0]:
            return self[x][y]

        # check if not tie
        for i in range(3):
            for j in range(3):
                if self[i][j] == 0:
                    return 0
        # is tie
        return -1

    def to_rows(self):
        rows = ['' for i in range(3)]
        for i in range(3):
            for j in range(3):
                rows[i] += TTT_Board.ui_map[self[i][j]]
        return rows


class UTTT_Board(list):
    ui_map = {
        -1: ['***', '***', '***'],
        1: ['\\ /', ' X ', '/ \\'],
        2: ['/-\\', '| |', '\\_/']
    }

    def __init__(self):
        list.__init__(self,
                      # 3x3 of normal ttt boards
                      [[TTT_Board() for i in range(3)] for i in range(3)]
                      )
        # 1st move is free
        self.next_play = 0
        self.legal_moves = self.get_legal_moves()
        self.turn = 1

    def get_legal_moves(self):
        legal_moves = []
        # iterate through every board
        if self.next_play == 0:
            for i in range(3):
                for j in range(3):
                    # if board isn't taken
                    if type(self[i][j]) != int:
                        for move in self[i][j].get_legal_moves():
                            # i,j == board coordinates; move == square coordinates
                            legal_moves.append((i, j, move))
        else:
            i, j = self.next_play[0], self.next_play[1]
            for move in self[i][j].get_legal_moves():
                # same format as above
                legal_moves.append((i, j, move))
        return legal_moves

    def play_move(self, move, player):
        # board coords
        i, j = move[0], move[1]
        # square coords
        x, y = move[2][0], move[2][1]
        sub_board = self[i][j]
        # make move
        sub_winner = sub_board.play_move(move[2], player)
        winner = 0
        # if board gets taken
        if sub_winner != 0:
            # remove board from play and check for win
            self[i][j] = sub_winner
            winner = self.check_win((i, j))

        # if next move is directed to taken square
        if type(self[x][y]) == int:
            # give free move
            self.next_play = 0
        else:
            # set next move to specified board
            self.next_play = move[2]
        return winner

    def check_win(self, location):
        x, y = location[0], location[1]
        # ensure board is taken
        if type(self[x][y]) != int:
            return 0
        elif self[x][y] == -1:
            # check if not tie
            for i in range(3):
                for j in range(3):
                    if type(self[i][j]) != int:
                        return 0
            # is tie
            return -1

        # vertical
        if self[0][y] == self[1][y] == self[2][y]:
            return self[x][y]
        # horizontal
        if self[x][0] == self[x][1] == self[x][2]:
            return self[x][y]
        # diagonal
        if x == y and self[0][0] == self[1][1] == self[2][2]:
            return self[x][y]
        # other diagonal
        if x + y == 2 and self[0][2] == self[1][1] == self[2][0]:
            return self[x][y]

        # check if not tie
        for i in range(3):
            for j in range(3):
                if type(self[i][j]) != int:
                    return 0
        # is tie
        return -1

    def to_UI(self):
        rows = ['' for i in range(11)]
        for i in range(3):
            for j in range(3):
                # 3x3 array of chars indicating what ttt board should look like
                symbol = []
                if type(self[i][j]) == int:
                    symbol = UTTT_Board.ui_map[self[i][j]]
                else:
                    symbol = self[i][j].to_rows()
                # appends board to output
                for k in range(3):
                    rows[4 * i + k] += symbol[k]
                # draws big board
                if j < 2:
                    for k in range(3):
                        rows[4 * i + k] += '|'
            # draw horizontal dividers
            if i < 2:
                rows[4 * i + 3] = '---+---+---'

        if self.next_play == 0:
            d = '  0   1   2\n'
        else:
            d = ' ' * (self.next_play[1]*4 + 1) + '012\n'

        for n, row in enumerate(rows):
            if self.next_play == 0 and d % 4 == 1:
                d += f'{d//4}{row}\n'
            elif n//4 == self.next_play[0] and d % 4 != 3:
                d += f'{d%4}{row}\n'
            else:
                d += f' {row}\n'


        return d
