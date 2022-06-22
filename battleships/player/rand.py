
from random import randint

from battleships.core.base import BaseGame
from battleships.util.util import GameUtil


class Rand(GameUtil):
    def __init__(self, ships: list, inst: BaseGame, fodder=False):
        super().__init__()
        self.game = inst
        self.ships = ships
        self.shots = list(range(self.game.size))
        self.name = "Random"
        self.fodder = fodder  # disables the render function for testing

    def placement(self):
        self.game.random_placement(self.ships)

    def shoot(self, inst):  # method for giving user output to shots
        if self.fodder:
            inst.render = lambda *_: None  # replace render with empty lambda
        print("\nThis is randoms board:")
        inst.render()
        pos = self.shots.pop(randint(0, len(self.shots) - 1))
        print(f"{self.name} chooses {self.convert_back(pos)}.")
        inst.game.shoot(pos)
        if inst.game.last_shot:  # if flag last_shot is true something was hit
            print("It's a hit!")
        else:
            print("It's a miss!")  # else its a miss

    def shoot_nc(self, inst):  # shoot without any output, for speed tests
        pos = self.shots.pop(randint(0, len(self.shots) - 1))
        inst.game.shoot(pos)

    def reset(self):
        self.shots = list(range(self.game.size))
