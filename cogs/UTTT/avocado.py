class MultiplayerAvocado:

    def __init__(self, avocados=0, spoon=0):
        self.avocados = avocados
        self.spoon = spoon
        self.move_made = False
        self.turn = 0
        self.previous = [avocados]

    def check_win(self):
        if self.avocados in self.previous[:-1]:
            return self.turn
        else:
            return -1

    def switch_turn(self):
        if self.move_made:
            self.turn = (self.turn + 1) % 2
            self.move_made = False
        else:
            raise ValueError

    def slice(self, num):
        if num in [0, 1, self.avocados]:
            raise ValueError
        if self.avocados % num == 0:
            self.avocados = num
        else:
            raise ValueError
        self.previous.append(self.avocados)
        self.move_made = True
        self.switch_turn()

    def mash(self):
        self.avocados = self.avocados ** 2
        self.avocados %= 2 ** 64
        self.previous.append(self.avocados)
        self.move_made = True
        self.switch_turn()

    def eat(self):
        if self.avocados < self.spoon:
            raise ValueError
        self.move_made = True
        self.avocados -= self.spoon
        self.previous.append(self.avocados)

    def buy(self):
        self.avocados += self.spoon
        self.avocados %= 2 ** 64
        self.previous.append(self.avocados)
        self.move_made = True
        self.switch_turn()
