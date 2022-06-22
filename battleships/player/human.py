
from battleships.core.error import InvalidPositionError
from battleships.core.base import BaseGame
from battleships.util.util import GameUtil


class HumanIO(GameUtil):  # todo add forfeit method, user should be able to ff at any time
    def __init__(self, use_spacer: bool, ships: list, name: str, inst: BaseGame):
        super().__init__()
        self.game = inst  # The BaseGame Instance
        self.name = name
        self.ships = ships
        self.use_spacer = use_spacer

    def placement(self):
        """
        Ship placement function for players.
        Prompts the user to place all ships specified in self.ships
        """
        print(f"{self.name}, it's time to place you ships. You may choose between orientations right or down.")
        for ship in self.ships:  # for each ship length specified in self.ships
            print(f"Place ship of length {ship}.\nThis is the board:")
            self.render(1)  # render for each new ship
            while True:
                pos = input("Which field is you starting field?: ").upper()
                if not self.check_pos(pos):  # check the entered pos is valid
                    print("This is not a valid position. Please try again.")
                else:
                    pos = self.convert(pos)  # convert it to a number that can be used for indexing
                    orient = input("Which orientation would you like the ship to be facing? [down/d/right/r]: ").lower()
                    if orient not in ("down", "d", "right", "r"):  # check the orientation
                        print("This is not a valid orientation. Please try again.")
                    else:
                        if orient in ("down", "d"):  # calculate the ship with orientation and pos given
                            n_ship = [pos + x * self.game.length for x in range(ship)]
                        else:
                            n_ship = [pos + x for x in range(ship)]
                        try:
                            self.game.set_ship(n_ship)  # try to set it, if successful break, else let user try again
                            break
                        except InvalidPositionError:
                            msg = '\nSpacer usage is enabled, so ships may not touch directly and must have at least ' \
                                  'one space between them.\nDoes not apply diagonally.\n' if self.use_spacer else ''
                            print(f"\nSome locations seem to be obstructed.{msg}Your board for reference:\n")

    def shoot(self, inst):
        """
        Parameters:
            inst: Class, middle-layer instance of BaseGame, requires the game attribute
        User is prompted to shoot on the field of inst.
        """
        print(f"{self.name}, it is your turn. This is your board:")
        inst.render()  # render instances board -> this does NOT call inst.game.render, but the render function
        # of the instance itself, including the modifiers like in this class
        print()
        while True:
            pos = input("Which field would you like to shoot at?: ").upper()
            if not self.check_pos(pos):  # check if pos is valid
                print("This is not a valid position. Please try again.")
            else:
                pos = self.convert(pos)  # convert to number for indexing
                if not inst.game.shots[pos]:  # check if pos was already shot at
                    inst.game.shoot(pos)  # make the shot
                    if inst.game.last_shot:  # if flag last_shot is true something was hit
                        print("It's a hit!")
                    else:
                        print("It's a miss!")  # else its a miss
                    break
                else:
                    print("This position was already shot at. Please try again.")
