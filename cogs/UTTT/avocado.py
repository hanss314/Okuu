class MultiplayerAvocado:

    def __init__(self, avocados=0, spoon=0):
        self.avocados = avocados
        self.spoon = spoon
        self.move_made = False
        self.turn = 0
        self.previous = [avocados]

    def check_win(self):
        if self.avocados in self.previous[:-1]:
            return self.turn, self.previous.index(self.turn)
        else:
            for n, pair in enumerate(self.previous[:-1]):
                if (isinstance(pair, tuple) and pair[0] % self.spoon == self.avocados % self.spoon and
                  pair[0] <= self.avocados <= pair[0] + self.spoon * pair[1]):
                    return self.turn, n

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

    def eat(self, amount):
        amount = min(amount, self.avocados // self.spoon)
        if amount > 0:
            self.avocados = self.avocados - amount * self.spoon
            self.move_made = True
            for n, hit in enumerate(self.previous[:-1]):
                if isinstance(hit, int):
                    if (self.avocados <= hit <= self.avocados + amount * self.spoon and
                    (hit-self.avocados) % self.spoon == 0):
                        raise ValueError(hit, n)
                elif isinstance(hit, tuple):
                    if self.avocados % self.spoon == hit[0] % self.spoon:
                        if hit[0] <= self.avocados <= hit[0] + self.spoon * hit[1]:
                            raise ValueError(self.avocados, n)
                        elif self.avocados <= hit[0] <= self.avocados + self.spoon * amount:
                            raise ValueError(hit[0], n)

            self.previous.append((self.avocados, amount))
        return amount

    def buy(self):
        self.avocados += self.spoon
        self.avocados %= 2 ** 64
        self.previous.append(self.avocados)
        self.move_made = True
        self.switch_turn()
