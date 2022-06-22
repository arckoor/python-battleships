
from _ctypes import PyObj_FromPtr
from colorama import Style, Fore
from numpy import format_float_positional
from collections import Counter
import json
import re


class GameUtil:
    """
    Class for utility functions shared between middle layer classes.
    """
    def __init__(self):
        if type(self) == GameUtil:
            raise NotImplementedError("This class must be subclassed and may not be instanced directly.")

        self.placeholder = None
        self.name = None
        self.game = None
        self.alive = []

        self.placeholder = '▣'
        self.hit = Fore.RED + '¤' + Style.RESET_ALL
        self.miss = Fore.GREEN + '○' + Style.RESET_ALL
        # the characters

    def render(self, win: int = 0):
        """
        Parameters:
            win: int, default 0
        Alters self.game.board and uses game.render to draw it.
        If win is True, all ships will be revealed.
        """
        # modify the board and call the BaseGame render method
        if not win:
            board = self.game.shots
            for i, element in enumerate(board):
                if not element:
                    board[i] = self.placeholder
                elif element == 1:
                    board[i] = self.hit
                else:
                    board[i] = self.miss
        else:
            colors = [Fore.RED, Fore.GREEN, Fore.MAGENTA, Fore.CYAN, Fore.BLUE, Fore.YELLOW, Fore.BLACK]
            board = [self.placeholder] * len(self.game.board)
            # everything else is going to be placeholder anyway, so just start with only placeholders
            ships = self.game.ships
            for i, ship in enumerate(ships):
                for spot in ship:
                    board[spot] = colors[i % len(colors)] + str(i + 1) + Style.RESET_ALL
                    # color the ships according to number
        self.game.render(1, board)

    def shoot(self, inst):
        raise NotImplementedError

    def placement(self):
        raise NotImplementedError

    def convert(self, pos: str) -> int:
        """
        Parameters:
            pos: str
        Converts a string, i.e. "A2" to a number that can be used for indexing.
        The supplied string should be passed through check_pos first to ensure a valid number is produced.
        """
        return self.game.letters.index(pos[0]) + (int(pos[1:]) - 1) * self.game.length
        # math at its finest
        # first get the letter and its indexed position i.e. A -> 0, B -> 1, ...
        # then get the line -> first extract the actual line, decrease by one and multiply by the line offset,
        # which is the length of 1 line
        # then add the two together and that's it

    def convert_back(self, pos: int) -> str:
        """
        Parameters:
            pos: int
        Converts a position in numerical format back to the "letter:number" format to be user readable.
        The number should be in range self.game.size.
        """
        col = pos % self.game.length
        return self.game.letters[col] + str(((pos - col + 1) // self.game.length + 1))
        # convert in reverse
        # calculate column by % with length
        # then get letters and use col to index
        # number is just position - col + 1
        # then integer divided by length, finally +1

    def check_pos(self, pos: str) -> bool:
        """
        Parameters:
            pos: str
        Checks the validity of the string under game parameters.
        Supplied strings must be uppercase and come in the format "letter:number(s)"
        """
        if 1 < len(pos) <= 1 + len(str(self.game.height)):  # checks the length, must be over 1 and below or equal
            # the max length, which is 1+height of playing field, i.e 3 for "A10"
            if pos[0] in self.game.letters:  # letter has to be part of letter range in self.game
                nums = pos[1:]  # all the things after the first char
                for char in nums:
                    if char not in [str(x) for x in range(0, 10)]:  # all have to be numbers
                        return False  # if not a number exit early
                num = int(nums)  # its all numbers, convert to real number
                if 0 < num <= self.game.height:  # is it smaller then the max game height?
                    # A10 and A99 have the sma length, but one a 10x10 board only A10 is valid
                    return True
                # works with <letter>0<number(s)> as well
                # not intended but welcome anyways
        return False

    def alive_update(self):
        """
        Function to buffer the ship list.
        Must be called before the game starts and should only be called once.
        """
        self.alive.extend(self.game.alive)  # buffer the ship list

    def check_sunken(self):
        """
        Checks if a new ship has been sunken and prints a message.
        """
        old = self.alive.copy()  # get the old ships
        new = self.game.alive  # and the updated ones
        for i, (n, o) in enumerate(zip(new, old)):  # i for indexing, (n, o) for comparing the lists
            if n != o:  # if they don't match something changed
                self.alive[i] = n
                print(f"Ship {i + 1} of length {self.game.length_ship_sunk} has been sunken!")
                # give the user a message about it

    def win(self):  # todo check if game was forfeit, then display that
        """
        Shows the board at the end of the game.
        """
        print(f"{self.name}, this was your board:")
        self.render(1)  # render with win=1, ships will be revealed

    def reset(self):
        """
        Resets parameters of class.
        """
        pass

    def initialize(self, inst):
        """
        Initializes variables of a class.
        """
        pass


class CalcUtil:
    def __init__(self):
        if type(self) == CalcUtil:
            raise NotImplementedError("This class must be subclassed and may not be instanced directly.")

    @staticmethod
    def counter(shots):
        cnt = Counter(shots)  # counts occurrences of elements

        def get(x):
            temp = cnt.get(x)
            return temp if temp is not None else 0  # failsafe

        return get(0), get(1), get(2)  # not shot, hits, misses

    @staticmethod
    def mean(lst):  # basic mean function
        return sum(lst) / len(lst)

    @staticmethod
    def format_float(num):  # numpy float formatting, removes trailing zero's
        return format_float_positional(float(num), trim='-')


class NoIndent(object):  # https://stackoverflow.com/a/42721412/12203337
    """ Value wrapper. """
    def __init__(self, value):
        if not isinstance(value, (list, tuple)):
            raise TypeError('Only lists and tuples can be wrapped')
        self.value = value


class JSONFlatEncoder(json.JSONEncoder):  # https://stackoverflow.com/a/42721412/12203337
    FORMAT_SPEC = '@@{}@@'  # Unique string pattern of NoIndent object ids.
    regex = re.compile(FORMAT_SPEC.format(r'(\d+)'))  # compile(r'@@(\d+)@@')

    def __init__(self, **kwargs):
        # Keyword arguments to ignore when encoding NoIndent wrapped values.
        ignore = {'cls', 'indent'}

        # Save copy of any keyword argument values needed for use here.
        self._kwargs = {k: v for k, v in kwargs.items() if k not in ignore}
        super(JSONFlatEncoder, self).__init__(**kwargs)

    def default(self, obj):
        return (self.FORMAT_SPEC.format(id(obj)) if isinstance(obj, NoIndent)
                else super(JSONFlatEncoder, self).default(obj))

    def iterencode(self, obj, **kwargs):
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.

        # Replace any marked-up NoIndent wrapped values in the JSON repr
        # with the json.dumps() of the corresponding wrapped Python object.
        for encoded in super(JSONFlatEncoder, self).iterencode(obj, **kwargs):
            match = self.regex.search(encoded)
            if match:
                id_ = int(match.group(1))
                no_indent = PyObj_FromPtr(id_)
                json_repr = json.dumps(no_indent.value, **self._kwargs)
                # Replace the matched id string with json formatted representation
                # of the corresponding Python object.
                encoded = encoded.replace(f"{format_spec.format(id_)}", json_repr)

            yield encoded
