
from string import ascii_uppercase, ascii_lowercase, punctuation
from random import randint

from battleships.core.error import *


class BaseGame:
    def __init__(self, size: tuple[int, int], use_spacer: bool = False):
        if type(self) != BaseGame:
            raise AttributeError("BaseGame should not be inherited and only passed as an instance.")
        """
        Parameters:
            size: tuple (x, y) or int. constructs a field with size x, y or x, x if int is given
            use_spacer: bool. set True if ships may not touch during placing
        """
        if isinstance(size, tuple):
            if len(size) == 1:
                size = (size[0], size[0])
            elif len(size) > 2:
                raise LengthError(len(size), "size", "BaseGame.__init__", 2)
        else:
            raise ValueError(f"Argument size expects a tuple, {type(size)} was given.")
        self.length = size[0]
        self.height = size[1]
        self.use_spacer = bool(use_spacer)
        self.__test_size()
        self.size = self.height * self.length  # calculate length
        self.board = [0] * self.size  # todo protect them all
        self.shots = [0] * self.size
        self.letters = (ascii_uppercase + ascii_lowercase + punctuation)[:self.length]

        # flags
        self.game_over = False
        self.game_forfeit = False
        self.last_shot = False
        self.ship_sunk = False
        self.length_ship_sunk = 0

        # internal variables
        self.lines = self.get_lines()
        self.columns = self.get_columns()
        self.__ships = []
        self.__alive = []
        self.__calculated = {}

    def get_lines(self) -> list[list[int]]:
        lines = []
        for line in range(self.height):
            lines.append([x for x in range(line * self.length, line * self.length + self.length)])
            # all lines the board contains, used in horizontal calculation
        return lines

    def get_columns(self) -> list[list[int]]:
        columns = []
        for column in range(self.length):
            columns.append([x for x in range(column, self.size, self.length)])
        return columns

    def get_alive(self) -> list[int]:  # getter functions - users may not modify internal values
        return [*self.__alive]  # self.__alive.copy()  # copy, else reference would be returned, allowing modification

    def get_board(self) -> list[int]:
        return [*self.board]  # self.board.copy()

    def get_shots(self) -> list[int]:
        return [*self.shots]  # self.shots.copy()

    def get_ships(self) -> list[list[int]]:
        return [*self.__ships]  # self.__ships.copy()

    def get_length_ship_sunk(self) -> int:
        return self.length_ship_sunk

    def get_height(self) -> int:
        return self.height

    def get_length(self) -> int:
        return self.length

    def get_size(self) -> int:
        return self.size

    def get_game_over(self) -> bool:
        return self.game_over

    def get_game_forfeit(self) -> bool:
        return self.game_forfeit

    def get_last_shot(self) -> bool:
        return self.last_shot

    def get_ship_sunk(self) -> bool:
        return self.ship_sunk

    def get_letters(self) -> str:
        return self.letters

    def __test_size(self):  # __ to disable direct access from outside -> you should not use these
        if self.length > 84:  # self.letters is max 84 chars long
            raise FieldSizeError(self.length)

    def __check_surroundings(self, position) -> bool:
        # used to check the surroundings of a spot, used for use_spacer
        line = None
        for element in self.lines:
            if position in element:
                line = element  # line in which position sits
                break
        positions = []
        for element in (-1, 1):
            if position + element in line:
                positions.append(position + element)
            # check if in line, wrap around is avoided
        for element in (-self.length, self.length):
            if position + element in list(range(self.size)):
                positions.append(position + element)
                # prevent overflow from top or bottom
        cnt = 0
        for element in positions:
            if not self.board[element]:
                cnt += 1  # count if all spaces are suitable
        if cnt == len(positions):  # return result
            return True
        return False

    def __ships_sunken(self):
        """
        checks if all ships in self.ships are sunken
        sets self.game_over True if all ships have been sunken
        protected, flags should not be set from the outside
        """
        self.ship_sunk = False
        self.length_ship_sunk = 0
        if self.last_shot:  # don't bother calculating if something was sunk if nothing was hit with the last shot
            cnt = 0
            for i, ship in enumerate(self.__ships):
                if not self.__alive[i]:  # don't set the flag twice
                    if all(map(self.__extract, ship)):  # if every position has a non-zero value its been sunken
                        self.__alive[i] = 1
                        self.ship_sunk = True
                        self.length_ship_sunk = len(ship)
                        cnt += 1
                else:
                    cnt += 1
            if cnt == len(self.__ships):
                self.game_over = True

    def __extract(self, x: int) -> int:
        return self.shots[x]

    def calculate_spot_combinations(self, size: int, spot: int) -> list[list[int]]:
        """
        parameters:
            size: int
            spot: int
        calculates all combinations for ship of length (size) through a single field (spot) on the board and
        returns them
        returns and empty list if board is too small
        """
        combinations = []
        line = None  # get the line the spot is on
        for li in self.lines:
            if spot in li:
                line = set(li)

        for i in range(1-size, 1):
            shift = [spot + x + i for x in range(size)]  # progressively increment all values
            if min(shift) >= 0 and max(shift) < self.size and set(shift).issubset(line):  # in-bounds and in line
                shift.sort()
                combinations.append(shift)

        for i in range(1-size, 1):
            shift = [spot + self.length * x + self.length * i for x in range(size)]
            if min(shift) >= 0 and max(shift) < self.size:
                shift.sort()
                combinations.append(shift)

        combinations.sort()
        return combinations

    def calculate_combinations(self, size: int) -> list[list[int]]:
        """
        Parameters:
            size: int
        calculates all possible combinations for ship of length (size) and returns them
        returns an empty list if board is too small
        """

        if size in self.__calculated:
            return self.__calculated[size].copy()
        # ships may have the same size or the function may be called again
        # saving already computed combinations for a given size saves a huge amount of computation that would otherwise
        # be performed multiple times

        if size > self.length and size > self.height:
            raise ShipLengthError(size, max(self.height, self.length), (self.length, self.height))
        horizontal = list(range(size))  # initial starting point horizontal, i.e. [0, 1, 2]
        vertical = [x * self.length for x in range(size)]  # initial starting point vertical, i.e. [0, 4, 8]
        combinations_hor = [horizontal]  # init for all horizontal combinations
        combinations_vert = [vertical]  # same for vertical

        while max(horizontal) < self.size - 1:
            horizontal = [x + 1 for x in horizontal]  # increment all by one
            combinations_hor.append(horizontal)
            # check if new list is subset of one line, if not wrap around occurs:
            # 0 0 1 1
            # 1 0 0 0
            # 0 0 0 0
            # check with lines to eliminate those cases
        while max(vertical) < self.size - 1:
            vertical = [x + 1 for x in vertical]
            combinations_vert.append(vertical)
            # no need to check for wrap around, if one wraps all wrap
            # 0 0 1    0 0 0
            # 0 0 1 -> 1 0 0
            # 0 0 0    1 0 0
        combinations = combinations_hor + combinations_vert  # combine the two
        c = []  # new combinations list
        lines_columns = self.lines + self.columns  # all lines and columns
        for element in combinations:
            s = set(element)
            for comb in lines_columns:
                if s.issubset(comb):  # and element not in c:  # if combination is in all lines and columns append
                    # todo check if necessary (and element not in c) -> probably not but not sure
                    c.append(element)  # if not then there is wrap around, don't want that
        self.__calculated.update({size: c})
        return [*c]  # don't return a reference, but a copy

    def set_ship(self, ship: list):
        """
        Parameters:
            ship: list
        sets ship on self.board if no obstructions are found
        raises InvalidPositionError if ship cannot be placed
        """
        ship.sort()
        if ship not in self.calculate_combinations(len(ship)):  # test if ship is a valid combination
            raise InvalidPositionError(len(ship), ship)

        possibles = [0] * len(ship)  # keep track of non-obstructed fields
        for i, element in enumerate(ship):
            if not self.board[element]:  # check if board position is free
                possibles[i] = 1
        if self.use_spacer:
            for i, element in enumerate(ship):
                if not self.__check_surroundings(element):
                    possibles[i] = 0  # check for surroundings if ships may not touch

        if all(possibles):
            self.__ships.append(ship)
            self.__alive.append(0)
            for element in ship:
                self.board[element] = 1  # make changes to board
        else:
            obstructed = []
            for i, element in enumerate(possibles):
                if not element:
                    obstructed.append(ship[i])
            raise InvalidPositionError(len(ship), ship)
            # error handling, show obstructed spaces to user

    def set_ships(self, ships: list[list]):
        """
        Parameters:
            ships: list[list]
        calls set_ship() for each ship in ships
        i.e. [[1, 2], [27, 28, 29], [98, 99]]
        """
        for ship in ships:
            self.set_ship(ship)

    def random_placement(self, ships: list):
        """
        Parameters:
             ships: list of ints, each element is the length of one ship
             [3, 2, 1] -> 1 of len 3, 1 of len 2, ...
        randomly places len(ships) on the board
        """
        for ship in ships:
            combinations = self.calculate_combinations(ship)  # get possible combinations
            while 1:
                try:
                    combination = combinations.pop(randint(0, len(combinations)-1))  # pick one
                    self.set_ship(combination)  # try it
                    break  # worked
                except InvalidPositionError:
                    pass  # something in the way, try another one
                except ValueError:
                    raise RecursionError(f"Placing ship of length {ship} failed. Increase the field size or decrease "
                                         "the number or length of ships.")

    def shoot(self, position: int):
        """
        Parameters:
            position: int
        default shoot function
        modifies self.shots at given position
        1 if ship is present at position,
        2 if not
        raises ShotError if position was already shot at
        """
        if not self.shots[position]:
            if self.board[position]:
                self.shots[position] = 1  # hit
                self.last_shot = True  # set flag
            else:
                self.shots[position] = 2  # miss
                self.last_shot = False  # set flag
        else:
            raise ShotError(position)  # already shot there
        self.__ships_sunken()

    def render(self, *args: bool or list):
        """
        Parameters:
            args: bool or list
        debug render function
        draws self.board if no argument is specified,
        self.shots if len(args) is 1,
        args[1] if 2 args are given
        args[1] has to be of length self.size
        """
        btp = self.board if len(args) == 1 else self.shots if len(args) == 0 else args[1]
        if len(args) > 1:
            if len(args[1]) != self.size:
                raise LengthError(len(args[1]), "args", "BaseGame.render", self.size)
        print()
        line_str = " " * 12
        for char in self.letters:
            line_str += char + "  "
        print(line_str + "\n")
        for line in range(self.height):
            length = 4 - (len(str(line + 1)) - 1)
            line_str = " " * 5 + str(line + 1) + " " * length
            for char in range(self.length):
                line_str += "  " + str(btp[line * self.length + char])
            print(line_str)
        print()

    def forfeit(self):
        """
        immediately forfeit the game
        next self.ships_sunken call will return True
        """
        self.game_forfeit = True
        self.last_shot = True
        for i in range(len(self.__alive)):
            self.__alive[i] = 1
        self.__ships_sunken()

    def reset(self):
        """
        resets all by gameplay affected values to default
        """
        self.board = [0] * self.size
        self.shots = [0] * self.size
        self.last_shot = False
        self.ship_sunk = False
        self.game_over = False
        self.length_ship_sunk = 0
        self.__ships = []
        self.__alive = []
