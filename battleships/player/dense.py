
from battleships.core.base import BaseGame
from battleships.util.util import GameUtil

import warnings
import itertools
import pathlib
import os


class Dense(GameUtil):
    def __init__(self, ships: list, inst: BaseGame, id_=0, monitor=False):
        super().__init__()
        self.game = inst
        self.ships = ships
        self.remaining_ships = self.ships.copy()
        self.size = self.game.size
        self.path = os.path.abspath(pathlib.Path(__file__).parent.resolve())  # get directory of dense.py
        # monitoring function
        if monitor:
            self.length = self.game.length
            warnings.warn(
                "monitor potentially creates lots of small files in .\\data\\, especially when used with benchmark.py. "
                "Use at your own discretion", RuntimeWarning)

            self.shoot_nc = self.shoot_monitor  # assign monitoring function
            path = self.path + "./data/"
            if not os.path.exists(path):  # make sure dir exists
                os.mkdir(path)
        else:
            self.shoot_nc = self.shoot_none  # assign function without monitor call
        # internal game variables
        self.tracked_hits = []
        self.shot = []
        self.last_updated = []
        self.remove_queue = []
        self.last_pos = None
        self.distribution = None
        self.distribution_master = None

        # shot and round tracker
        self.cnt = 0
        self.round = 0
        self.id = id_
        self.name = "Dense"

    def initialize(self, inst):
        self.distribution = self.create_score_map(inst)
        self.distribution_master = self.distribution.copy()

    def placement(self):
        self.game.random_placement(self.ships)

    def shoot(self, inst):
        pos, _ = self.get_shot(inst)
        print(f"This is {self.name}'s board:")
        inst.render()
        print(f"{self.name} chooses {self.convert_back(pos)}")
        inst.game.shoot(pos)
        if inst.game.last_shot:  # if flag last_shot is true something was hit
            print("It's a hit!")
        else:
            print("It's a miss!")  # else it's a miss
        self.after_shot(inst, pos)

    def shoot_none(self, inst):
        try:
            pos, _ = self.get_shot(inst)
            inst.game.shoot(pos)
            self.after_shot(inst, pos)
        except Exception as e:
            with open(self.path + f"\\error\\error_{self.id}.txt", "a") as file:
                file.write(str(inst.game.ships) + f" {self.cnt} " + str(e) + "\n")
            self.game.forfeit()

    def shoot_monitor(self, inst):
        pos, m = self.get_shot(inst)  # get position and map
        self.prepare_monitor(inst, m)  # draw monitor picture
        inst.game.shoot(pos)  # shoot
        self.after_shot(inst, pos)  # past shot processing

    def get_shot(self, inst):
        if self.tracked_hits:  # if non-sunk ships are present, target them else find a new target
            return self.target_score(inst)
        return self.hunter_score(inst)

    def after_shot(self, inst, pos):
        self.cnt += 1  # increment shot counter
        self.last_pos = pos  # save last_pos
        self.shot.append(pos)  # mark pos as shot

        if inst.game.last_shot:  # if last shot was a hit append to tracked hits
            self.tracked_hits.append(pos)
        self.tracked_hits.sort()  # sort, just for good measure

        if inst.game.ship_sunk:  # if a ship was sunken, get length and try to remove it from the tracked shots
            length = inst.game.length_ship_sunk
            self.remove_from_target(inst, length)

        if self.remove_queue:  # if a remove queue is present try to clear it
            self.try_remove_queue(inst)

    def combinations(self, inst, length, last_pos):
        combinations = inst.game.calculate_combinations(length)  # all the combinations of a ship length n
        c = []
        possible_combinations = [list(x) for x in itertools.combinations(self.tracked_hits, length)]
        # all combinations of length n that fit in tracked hits
        for combination in combinations:
            if combination in possible_combinations and last_pos in combination:
                c.append(combination)
                # if the combination is possible, and it contains a spot where a ship is located, add it to the buffer
        return c

    def remove_from_target(self, inst, length):
        c = self.combinations(inst, length, self.last_pos)  # get the combinations
        if len(c) > 1:  # if there's more than one it is not certain which one's the right one
            self.remove_queue.append((self.last_pos, length))  # postpone the decision and store all information
        else:  # there's only one possible placement
            if len(c):
                for spot in c[0]:
                    self.tracked_hits.remove(spot)  # remove it from tracked hits
                self.remaining_ships.remove(length)  # mark ship as sunk
            self.update_distribution(inst)

    def try_remove_queue(self, inst):
        ship_combinations = []
        for ship in self.remove_queue:
            ship_combinations.append(self.combinations(inst, ship[1], ship[0]))  # get combination of each ship
        possible_pairings = list(itertools.product(*ship_combinations))  # pair them all up in length of remove_queue

        valid = []
        for pair in possible_pairings:  # format is something like [[x, y], [z, a, b]]
            flat = self.flatten(pair)  # flatten the pair into one list -> [x, y, z, a, b]
            if len(set(flat)) == len(flat):  # if length of set is equal to length of initial no element is a duplicate
                valid.append(pair)  # this means the pairing is valid
        if len(valid) == 1:  # if just one pairing is present
            for ship in valid[0]:  # loop through each ship in the pairing
                for spot in ship:
                    self.tracked_hits.remove(spot)  # remove all spots from tracked hits
                self.remaining_ships.remove(len(ship))  # mark ship as sunk
                for t_ship in self.remove_queue:  # loop through remove queue and find the ship
                    if t_ship[0] in ship and len(ship) == t_ship[1]:  # right ship must contain the shot position
                        self.remove_queue.remove(t_ship)
            self.update_distribution(inst)

    @staticmethod
    def flatten(t):  # https://stackoverflow.com/a/952952/12203337
        return [item for sublist in t for item in sublist]

    def update_distribution(self, inst):
        self.distribution = self.create_score_map(inst)
        self.find_difference(inst)

    def hunter_score(self, inst):  # see create_score_map
        shots = inst.game.shots
        for field in self.find_difference(inst):  # this time only for new fields
            for ship in self.remaining_ships:
                for combination in inst.game.calculate_spot_combinations(ship, field):
                    if not any(shots[x] for x in combination if x != field):
                        for spot in combination:
                            self.distribution[spot] -= 1
        return self.distribution.index(max(self.distribution)), self.distribution

    def create_score_map(self, inst):
        score_map = [0] * self.size  # make a list the size of the game board, fill it with zeros
        shots = inst.game.shots  # get all the shots
        for ship in self.remaining_ships:  # loop through all remaining ships
            all_combinations = inst.game.calculate_combinations(ship)  # get all the combinations
            for combination in all_combinations:  # loop through them
                if not any(shots[x] for x in combination):  # if the combination contains no field that has been shot at
                    for x in combination:
                        score_map[x] += 1  # add to each spot of the combination
        return score_map

    def find_difference(self, inst):
        shots = inst.game.shots
        updated = [i for i, x in enumerate(shots) if x]  # every shot field
        result = [x for x in updated if x not in self.last_updated]  # every shot field that hasn't been checked yet
        self.last_updated = updated
        return result

    def target_score(self, inst):
        score_map = [0] * self.size  # make a list the size of the game board, fill it with zeros
        shots = inst.game.shots  # get all the shots
        valid = [x for x in self.shot if shots[x] != 1]
        for ship in self.remaining_ships:  # loop through all remaining ships
            all_combinations = inst.game.calculate_combinations(ship)  # get all the combinations
            for combination in all_combinations:  # loop through them
                if not any(x in combination for x in valid):
                    # no field has been shot except if it's a hit, that's fine
                    if len([0 for x in combination if not shots[x] == 2]) == ship:
                        # the combination contains no missed spots and is the correct length
                        if not len([0 for x in combination if shots[x]]) == ship:
                            # not all spots have been shot
                            a = sum([x in self.tracked_hits for x in combination])
                            # test if any spot of the combination is already tracked, count True
                            if a:  # there are tracked fields
                                if not any(x in combination for x in self.shot if x not in self.tracked_hits):
                                    # no spots have been shot at and if they have been they are currently tracked
                                    # (they could be from some already sunken ship)
                                    for x in combination:
                                        if x not in self.tracked_hits and x not in self.shot:
                                            # if x is not tracked and has not been shot
                                            score_map[x] += a
                                            # add length of a, to weight longer combinations better
                                            # helps to continue shooting in the same direction
        return score_map.index(max(score_map)), score_map

    def prepare_monitor(self, inst, field):
        data = {
            "Score Map": field,
            "Shots": inst.game.shots,
            "Tracked Hits": [1 if i in self.tracked_hits else 0 for i in range(self.size)],
            "Board": inst.game.board
        }
        self.monitor(data, self.length, f"{self.path}/data/{self.id}_{self.round}_{self.cnt}")

    def reset(self):  # reset from game to game
        self.remaining_ships = self.ships.copy()  # all of them are alive again
        # self.distribution = self.distribution_master.copy()  # reset the score map
        self.shot = []  # or shots
        self.tracked_hits = []  # no tracked hits
        self.remove_queue = []  # there's nothing to be queued
        # self.last_updated = []  # reset spots to update
        self.last_pos = None  # nothing was shot
        self.round += 1  # next round
        self.cnt = 0  # we start at turn 0
