
from random import randint, choice

from battleships.core.base import BaseGame
from battleships.util.util import GameUtil


class Hunter(GameUtil):
    def __init__(self, ships: list, inst: BaseGame):
        super().__init__()
        self.game = inst
        self.shots = list(range(self.game.get_size()))
        self.lines = self.game.get_lines()
        self.parity = self.get_parity()
        self.parity_c = self.parity.copy()
        self.ships = ships
        self.name = "Hunter"
        self.get_shot = self.strategy
        self.directions = [-1, 1, -self.game.get_length(), self.game.get_length()]

        self.to_shoot = []
        self.lp = None

        self.target_found = False
        self.last_pos = None
        self.start_pos = None

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
        if inst.game.get_last_shot():  # if flag last_shot is true something was hit
            print("It's a hit!")
        else:
            print("It's a miss!")  # else its a miss

    def shoot_nc(self, inst):  # shoot without any output, for speed tests
        pos = self.get_shot(inst)
        inst.game.shoot(pos)

    def strategy(self, inst):
        if inst.game.get_last_shot():
            line = self.lines
            for x in line:
                if self.lp in x:
                    line = x
                    break
            dirs = [self.lp+x for x in self.directions[:2] if self.lp+x in line and self.lp+x in self.shots
                    and self.lp+x not in self.to_shoot]
            dirs.extend([self.lp+x for x in self.directions[2:] if self.lp+x in self.shots
                         and self.lp+x not in self.to_shoot])
            self.to_shoot.extend(dirs)

        if not self.to_shoot:
            self.lp = self.parity.pop(randint(0, len(self.parity)-1))
        else:
            self.lp = self.to_shoot.pop(0)
        self.rem(self.lp)
        return self.lp

    def rem(self, pos):
        try:
            self.parity.remove(pos)
        except ValueError:
            pass
        try:
            self.shots.remove(pos)
        except ValueError:
            pass

    def find_target(self):
        return choice(self.parity)

    def reset(self):
        self.shots = list(range(self.game.get_size()))
        self.parity = self.parity_c.copy()
        self.to_shoot = []
        self.lp = None
