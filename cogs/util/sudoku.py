class Sudoku:

    def __init__(self, board):
        self.board = []
        for row in board[:9]:
            selfrow = []
            for tile in row[:9]:
                if isinstance(tile, int) and 0 < tile < 10:
                    selfrow.append(tile)
                else:
                    selfrow.append(None)
            self.board.append(selfrow)

    @staticmethod
    def in_range_of(x, y):
        in_range = set()
        for i in range(9):
            in_range.add((x, i))
            in_range.add((i, y))

        sx = (x // 3) * 3
        sy = (y // 3) * 3

        for i in range(3):
            for j in range(3):
                in_range.add((sx+i, sy+j))

        in_range.discard((x, y))
        return in_range

    def get(self, x, y):
        return self.board[x][y]

    def set(self, x, y, value):
        if not (0 < value < 10):
            raise ValueError
        self.board[x][y] = value

    def possible(self, x, y):
        possible = set(range(1, 10))
        for i, j in self.in_range_of(x, y):
            possible.discard(self.get(i, j))

        return possible

    def solved(self):
        return all([
            all(map(lambda x: x is not None and 0 < x < 10, row))
            for row in self.board])

    def empty(self):
        return {
            (x, y)
            for x in range(9) for y in range(9)
            if self.get(x, y) is None
        }

    def __str__(self):
        d = ''
        for x in range(9):
            r = ''
            for y in range(9):
                v = self.get(x, y)
                if v is not None:
                    r += f'{v} '
                else:
                    r += f'x '

            d += f'{r}\n'

        return d

    def __repr__(self):
        return self.__str__()

    def __copy__(self):
        return Sudoku(self.board)


def solve(board):
    stuff_left = True
    if len(board.empty()) > 81-17: return None
    while stuff_left:
        stuff_left = False
        for x in range(9):
            for y in range(9):
                if board.get(x, y) is None:
                    possible = board.possible(x, y)
                    if len(possible) == 0:
                        return None
                    elif len(possible) == 1:
                        board.set(x, y, possible.pop())
                        stuff_left = True

    if board.solved():
        return board

    grid = sorted(list(board.empty()), key=lambda x: len(board.possible(*x)))
    grid = grid[0]
    values = board.possible(*grid)
    for value in values:
        new_board = board.__copy__()
        new_board.set(*grid, value)
        solved = solve(new_board)
        if solved is not None:
            return solved

    return None


