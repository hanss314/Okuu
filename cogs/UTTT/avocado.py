class MultiplayerAvocado:

    def __init__(self):
        self.spoon = -1
        self.turn = 0
        self.previous = []

    def switch_turn(self):
        if self.previous[-1] in self.previous[:-1] or self.previous[-1] < 0:
            raise ValueError
        else:
            self.turn = (self.turn + 1) % 2

    def set_avocados(self, count):
        if count < 0: raise ValueError
        self.previous.append(count % 256)
        self.switch_turn()

    def set_spoon(self, count):
        if count < 1: raise ValueError
        self.spoon = count % 256
        self.switch_turn()

    def slice(self):
        for x in reversed(range(2, self.previous[-1])):
            if self.previous[-1] % x  == 0:
                if x in [0, 1, self.previous[-1]]:
                    raise ValueError
                self.previous.append(x)
                break

        else:
            raise ValueError

        self.switch_turn()

    def mash(self):
        avocados = self.previous[-1] ** 2
        avocados %= 2 ** 8
        self.previous.append(avocados)
        self.switch_turn()

    def eat(self):
        self.previous.append(self.previous[-1] - self.spoon)
        self.switch_turn()

    def buy(self):
        avocados = self.previous[-1] + self.spoon
        avocados %= 2 ** 8
        self.previous.append(avocados)
        self.switch_turn()
