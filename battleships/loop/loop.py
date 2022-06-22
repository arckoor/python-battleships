
from colorama import Fore, Style, init
from time import sleep

init()


class Loop:  # todo incorporate ability to forfeit
    """
    Defines game loop, takes two classes. Called from game.py.
    """
    def __init__(self, p1, p2, random_board: bool, delay: float):
        self.p1 = p1  # Player 1 and 2
        self.p2 = p2
        self.random_board = random_board
        self.delay = delay
        self.red_line = Fore.RED + "-" * 50 + Style.RESET_ALL
        self.game_loop()

    def game_loop(self):
        if self.random_board:  # place ships randomly
            self.p1.game.random_placement(self.p1.ships)
            self.p2.game.random_placement(self.p2.ships)
        else:
            self.p1.placement()
            self.spacer()  # spacer so players don't reveal their board to each other
            self.p2.placement()
            self.spacer()
        self.p1.alive_update()
        self.p2.alive_update()
        while 1:
            self.line()
            self.p1.shoot(self.p2)  # shoot
            self.p2.check_sunken()  # check if something sank
            if self.p2.game.get_game_over():  # check if game is over
                print(f"{self.p1.name} won!")
                self.p1.win()  # show the boards
                self.p2.win()
                break
            self.line()
            self.p2.shoot(self.p1)  # same as above
            self.p1.check_sunken()
            if self.p1.game.get_game_over():
                print(f"{self.p2.name} won!")
                self.p2.render()
                self.p1.win()
                self.p2.win()
                break

    def spacer(self):
        print(self.red_line)
        print("\n" * 80)

    def line(self):
        sleep(self.delay)
        print(f"\n{self.red_line}\n\n")
