
from string import ascii_uppercase, ascii_lowercase, punctuation
from random import randint

from battleships.core.error import FieldSizeError, ShotError, LengthError, InvalidPositionError, ShipLengthError


class BaseGame:
    def __init__(self, size: tuple[int, int], use_spacer: bool = False):
        if type(self) != BaseGame:
            raise AttributeError("BaseGame should not be inherited and only passed as an instance.")
        """
        Parameters:
            size: tuple (x, y) or int. Constructs a field with size x, y or x, x if int is given
            use_spacer: bool. Set True if ships may not touch during placing
        """
        if isinstance(size, tuple):
            if len(size) == 1:
                size = (size[0], size[0])
            elif len(size) > 2:
                raise LengthError(len(size), "size", "BaseGame.__init__", 2)
        else:
            raise ValueError(f"Argument size expects a tuple, {type(size)} was given.")
        self.__length = size[0]
        self.__height = size[1]
        self.__use_spacer = bool(use_spacer)
        self.__test_size()
        self.__size = self.__height * self.__length  # calculate length
        self.__board = [0] * self.__size
        self.__shots = [0] * self.__size
        self.__letters = (ascii_uppercase + ascii_lowercase + punctuation)[:self.__length]

        # flags
        self.__game_over = False
        self.__game_forfeit = False
        self.__last_shot = False
        self.__ship_sunk = False
        self.__length_ship_sunk = 0

        # internal variables
        self.__lines = self.get_lines()
        self.__columns = self.get_columns()
        self.__ships = []
        self.__alive = []
        self.__calculated = {}

    def get_lines(self) -> list[list[int]]:
        lines = []
        for line in range(self.__height):
            lines.append([x for x in range(line * self.__length, line * self.__length + self.__length)])
            # all lines the board contains, used in horizontal calculation
        return lines

    def get_columns(self) -> list[list[int]]:
        columns = []
        for column in range(self.__length):
            columns.append([x for x in range(column, self.__size, self.__length)])
        return columns

    @property
    def alive(self):  # getter functions - users may not modify internal values
        return [*self.__alive]  # self.__alive.copy()  # copy, else reference would be returned, allowing modification

    @property
    def board(self) -> list[int]:
        return [*self.__board]  # self.__board.copy()

    @property
    def shots(self) -> list[int]:
        return [*self.__shots]  # self.__shots.copy()

    @property
    def ships(self) -> list[list[int]]:
        return [*self.__ships]  # self.__ships.copy()

    @property
    def length_ship_sunk(self) -> int:
        return self.__length_ship_sunk

    @property
    def height(self) -> int:
        return self.__height

    @property
    def length(self) -> int:
        return self.__length

    @property
    def size(self) -> int:
        return self.__size

    @property
    def game_over(self) -> bool:
        return self.__game_over

    @property
    def game_forfeit(self) -> bool:
        return self.__game_forfeit

    @property
    def last_shot(self) -> bool:
        return self.__last_shot

    @property
    def ship_sunk(self) -> bool:
        return self.__ship_sunk

    @property
    def letters(self) -> str:
        return self.__letters

    def __test_size(self):  # __ to disable direct access from outside -> you should not use these
        if self.__length > 84:  # self.__letters is max 84 chars long
            raise FieldSizeError(self.__length)

    def __check_surroundings(self, position) -> bool:
        # used to check the surroundings of a spot, used for use_spacer
        line = None
        for element in self.__lines:
            if position in element:
                line = element  # line in which position sits
                break
        positions = []
        for element in (-1, 1):
            if position + element in line:
                positions.append(position + element)
            # check if in line, wrap around is avoided
        for element in (-self.__length, self.__length):
            if position + element in list(range(self.__size)):
                positions.append(position + element)
                # prevent overflow from top or bottom
        cnt = 0
        for element in positions:
            if not self.__board[element]:
                cnt += 1  # count if all spaces are suitable
        if cnt == len(positions):  # return result
            return True
        return False

    def __ships_sunken(self):
        """
        Checks if all ships in self.ships are sunken.
        Sets self.__game_over True if all ships have been sunken.
        Protected, flags should not be set from the outside.
        """
        self.__ship_sunk = False
        self.__length_ship_sunk = 0
        if self.__last_shot:  # don't bother calculating if something was sunk if nothing was hit with the last shot
            cnt = 0
            for i, ship in enumerate(self.__ships):
                if not self.__alive[i]:  # don't set the flag twice
                    if all(map(self.__extract, ship)):  # if every position has a non-zero value its been sunken
                        self.__alive[i] = 1
                        self.__ship_sunk = True
                        self.__length_ship_sunk = len(ship)
                        cnt += 1
                else:
                    cnt += 1
            if cnt == len(self.__ships):
                self.__game_over = True

    def __extract(self, x: int) -> int:
        return self.__shots[x]

    def calculate_spot_combinations(self, size: int, spot: int) -> list[list[int]]:
        """
        Parameters:
            size: int
            spot: int
        Calculates all combinations for ship of length (size) through a single field (spot) on the board.
        Returns and empty list if board is too small to account for a ship of the given size.
        """
        combinations = []
        line = None  # get the line the spot is on
        for li in self.__lines:
            if spot in li:
                line = set(li)

        for i in range(1 - size, 1):
            shift = [spot + x + i for x in range(size)]  # progressively increment all values
            if min(shift) >= 0 and max(shift) < self.__size and set(shift).issubset(line):  # in-bounds and in line
                shift.sort()
                combinations.append(shift)

        for i in range(1 - size, 1):
            shift = [spot + self.__length * x + self.__length * i for x in range(size)]
            if min(shift) >= 0 and max(shift) < self.__size:
                shift.sort()
                combinations.append(shift)

        combinations.sort()
        return combinations

    def calculate_combinations(self, size: int) -> list[list[int]]:
        """
        Parameters:
            size: int
        Calculates all possible combinations for ship of length (size).
        Returns an empty list if board is too small to account for a ship of the given size.
        """

        if size in self.__calculated:
            return self.__calculated[size].copy()
        # ships may have the same size or the function may be called again
        # saving already computed combinations for a given size saves a huge amount of computation that would otherwise
        # be performed multiple times

        if size > self.__length and size > self.__height:
            raise ShipLengthError(size, max(self.__height, self.__length), (self.__length, self.__height))
        horizontal = list(range(size))  # initial starting point horizontal, i.e. [0, 1, 2]
        vertical = [x * self.__length for x in range(size)]  # initial starting point vertical, i.e. [0, 4, 8]
        combinations_hor = [horizontal]  # init for all horizontal combinations
        combinations_vert = [vertical]  # same for vertical

        while max(horizontal) < self.__size - 1:
            horizontal = [x + 1 for x in horizontal]  # increment all by one
            combinations_hor.append(horizontal)
            # check if new list is subset of one line, if not wrap around occurs:
            # 0 0 1 1
            # 1 0 0 0
            # 0 0 0 0
            # check with lines to eliminate those cases
        while max(vertical) < self.__size - 1:
            vertical = [x + 1 for x in vertical]
            combinations_vert.append(vertical)
            # no need to check for wrap around, if one wraps all wrap
            # 0 0 1    0 0 0
            # 0 0 1 -> 1 0 0
            # 0 0 0    1 0 0
        combinations = combinations_hor + combinations_vert  # combine the two
        c = []  # new combinations list
        lines_columns = self.__lines + self.__columns  # all lines and columns
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
        Sets ship on self.__board if no obstructions are found.
        Raises InvalidPositionError if ship cannot be placed.
        """
        ship.sort()
        if ship not in self.calculate_combinations(len(ship)):  # test if ship is a valid combination
            raise InvalidPositionError(len(ship), ship)

        possibles = [0] * len(ship)  # keep track of non-obstructed fields
        for i, element in enumerate(ship):
            if not self.__board[element]:  # check if board position is free
                possibles[i] = 1
        if self.__use_spacer:
            for i, element in enumerate(ship):
                if not self.__check_surroundings(element):
                    possibles[i] = 0  # check for surroundings if ships may not touch

        if all(possibles):
            self.__ships.append(ship)
            self.__alive.append(0)
            for element in ship:
                self.__board[element] = 1  # make changes to board
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
        Calls set_ship() for each ship in ships.
        """
        for ship in ships:
            self.set_ship(ship)

    def random_placement(self, ships: list):
        """
        Parameters:
             ships: list of ints, each element is the length of one ship
             [3, 2, 1] -> 1 of len 3, 1 of len 2, ...
        Randomly places len(ships) on the board.
        """
        for ship in ships:
            combinations = self.calculate_combinations(ship)  # get possible combinations
            while 1:
                try:
                    combination = combinations.pop(randint(0, len(combinations) - 1))  # pick one
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
        Default shoot function.
        Modifies self.__shots at given position.
        1 if ship is present at position, 2 if not.
        Raises ShotError if position was already shot at.
        """
        if not self.__shots[position]:
            if self.__board[position]:
                self.__shots[position] = 1  # hit
                self.__last_shot = True  # set flag
            else:
                self.__shots[position] = 2  # miss
                self.__last_shot = False  # set flag
        else:
            raise ShotError(position)  # already shot there
        self.__ships_sunken()

    def render(self, *args: bool or list):
        """
        Parameters:
            args: bool or list
        Debug render function.
        Draws self.__board if no argument is specified,
        Self.__shots if len(args) is 1,
        Args[1] if 2 args are given.
        Args[1] has to be of length self.__size
        """
        btp = self.__board if len(args) == 1 else self.__shots if len(args) == 0 else args[1]
        if len(args) > 1:
            if len(args[1]) != self.__size:
                raise LengthError(len(args[1]), "args", "BaseGame.render", self.__size)
        print()
        line_str = " " * 12
        for char in self.__letters:
            line_str += char + "  "
        print(line_str + "\n")
        for line in range(self.__height):
            length = 4 - (len(str(line + 1)) - 1)
            line_str = " " * 5 + str(line + 1) + " " * length
            for char in range(self.__length):
                line_str += "  " + str(btp[line * self.__length + char])
            print(line_str)
        print()

    def forfeit(self):
        """
        Immediately forfeits the game.
        Next self.ships_sunken call will return True.
        """
        self.__game_forfeit = True
        self.__last_shot = True
        for i in range(len(self.__alive)):
            self.__alive[i] = 1
        self.__ships_sunken()

    def reset(self):
        """
        Resets all by gameplay affected values to default.
        """
        self.__board = [0] * self.__size
        self.__shots = [0] * self.__size
        self.__last_shot = False
        self.__ship_sunk = False
        self.__game_over = False
        self.__length_ship_sunk = 0
        self.__ships = []
        self.__alive = []
