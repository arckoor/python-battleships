
from battleships.core.base import BaseGame
from battleships.player.rand import Rand
from battleships.player.human import HumanIO
from battleships.player.hunter import Hunter
from battleships.player.dense import Dense


class Selector:
    def __init__(self):
        if type(self) == Selector:  # useless if not inherited, placeholders will be None, must be overwritten
            raise NotImplementedError("This class must be subclassed and may not be instanced directly.")

        self.ships = None
        self.use_spacer = None
        self.size = None  # placeholders

    def __pre_process(self):
        self.ships.sort()
        self.use_spacer = bool(self.use_spacer)
        self.size = tuple(int(x) for x in self.size)

    def random(self, _=None):  # each returns an instance of the class described
        self.__pre_process()
        return Rand(self.ships, self.base())

    def human_io(self, name):
        self.__pre_process()
        return HumanIO(self.use_spacer, self.ships, name, self.base())

    def hunter(self, _=None):
        self.__pre_process()
        return Hunter(self.ships, self.base())

    def dense(self, id_=0, monitor=False):
        self.__pre_process()
        return Dense(self.ships, self.base(), id_, monitor)

    def base(self):  # provides the BaseGame instance for other functions
        self.__pre_process()
        return BaseGame(self.size, self.use_spacer)
