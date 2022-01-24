
from battleships.loop.loop import Loop
from battleships.util.selector import Selector


class Game(Selector):  # todo ability to change opponent after round without restarting the game?
    def __init__(self, size: tuple[int, int], use_spacer: bool, random_board: bool, ships: list[int]):
        super().__init__()
        self.size = size
        self.use_spacer = use_spacer
        self.ships = ships
        self.random_board = random_board

        self.p1 = self.get_p()
        self.p2 = self.get_p()
        Loop(self.p1, self.p2, self.random_board, 0.5)

    def get_p(self):
        options = {
            0: (self.human_io, "Human Player"),
            1: (self.random,   "Random Player         (AI)"),
            2: (self.hunter,   "Hunting Player        (AI)"),
            3: (self.dense,    "Density Player        (AI)"),
            4: (self.tf,       "Neural Network Player (AI)")
        }
        print("Please choose one of the available options:")
        for k, v in options.items():
            print(k, ":", v[1])  # show all options
        print()
        while True:
            usr = input("Which player do you choose?: ")
            try:
                usr = int(usr)
                if not 0 <= usr <= len(options.keys()):
                    raise ValueError
                name = input("What would you like to be called?: ") if not usr else None  # name only affects HumanIO
                print()
                return options[usr][0](name)  # options -> key -> 0 -> call with name
            except ValueError:
                print("Invalid input, please try again.")


Game((10, 10), False, True, [5, 4, 3, 3, 2])
