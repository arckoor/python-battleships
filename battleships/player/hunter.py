
from random import randint

from battleships.core.base import BaseGame
from battleships.util.util import GameUtil


class Hunter(GameUtil):
    def __init__(self, ships: list, inst: BaseGame):
        super().__init__()
        self.game = inst
        self.shots = list(range(self.game.size))
        self.lines = self.game.get_lines()
        self.parity = self.get_parity()
        self.parity_c = self.parity.copy()
        self.ships = ships
        self.name = "Hunter"
        self.get_shot = self.strategy
        self.directions = [-1, 1, -self.game.length, self.game.length]

        self.to_shoot = []
        self.pos = None

    def reset_target(self):
        return

    def placement(self):
        self.game.random_placement(self.ships)

    def get_parity(self):
        parity = []
        offset = 0

        for line in self.lines:
            parity.extend(line[offset::2])
            offset = (offset + 1) % 2
        return parity

    def shoot(self, inst):  # method for giving user output to shots
        print("\nThis is Hunters board:")
        inst.render()
        pos = self.get_shot(inst)
        print(f"{self.name} chooses {self.convert_back(pos)}.")
        inst.game.shoot(pos)
        if inst.game.last_shot:  # if flag last_shot is true something was hit
            print("It's a hit!")
        else:
            print("It's a miss!")  # else its a miss

    def shoot_nc(self, inst):  # shoot without any output, for speed tests
        pos = self.get_shot(inst)
        inst.game.shoot(pos)

    def strategy(self, inst):
        if inst.game.last_shot:
            line = self.lines
            for x in line:
                if self.pos in x:
                    line = x
                    break
            dirs = [self.pos + x for x in self.directions[:2] if self.pos + x in line and self.pos + x in self.shots
                    and self.pos + x not in self.to_shoot]  # up, down
            dirs.extend([self.pos + x for x in self.directions[2:] if self.pos + x in self.shots
                         and self.pos + x not in self.to_shoot])  # left, right
            self.to_shoot.extend(dirs)

        if not self.to_shoot:
            self.pos = self.parity.pop(randint(0, len(self.parity) - 1))  # random pick from parity list
        else:
            self.pos = self.to_shoot.pop(0)  # next in to_shoot list
        self.rem(self.pos)
        return self.pos

    def rem(self, pos):
        try:
            self.parity.remove(pos)
        except ValueError:
            pass
        try:
            self.shots.remove(pos)
        except ValueError:
            pass

    def reset(self):
        self.shots = list(range(self.game.size))
        self.parity = self.parity_c.copy()
        self.to_shoot = []
        self.pos = None
