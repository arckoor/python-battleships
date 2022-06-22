
from multiprocessing import Pool
from os import cpu_count
from time import time
import json
from datetime import datetime
import pathlib
import os
import cProfile

from battleships.util.selector import Selector
from battleships.util.util import CalcUtil, JSONFlatEncoder, NoIndent
from battleships.loop.benchloop import BenchLoop


class Benchmark(CalcUtil, Selector):
    def __init__(self, size: tuple[int, int], use_spacer: bool, ships: list[int], episodes: int, proc=cpu_count()):
        super().__init__()
        self.size = size
        self.use_spacer = use_spacer
        self.ships = ships
        self.processes = proc
        self.eps = episodes // self.processes
        self.write_to_disk = bool(episodes >= 1000000)
        # result lists
        self.path = os.path.abspath(pathlib.Path(__file__).parent.resolve())
        self.shots_p1 = []
        self.config_p1 = []
        self.shots_p2 = []
        self.config_p2 = []
        self.wins = []
        self.game_length = []
        self.ff_p1 = []
        self.ff_p2 = []
        # time keeping
        self.start, self.end, self.processing_time = None, None, None
        # change these for other players
        self.n1, self.n2 = 'Dense', 'Hunter'

    def game_start(self):
        self.start = time()
        results = []
        for i, result in enumerate(Pool(processes=self.processes).imap_unordered(self.loop, range(self.processes))):
            if self.write_to_disk:
                self.write_results(result, i)  # write to file to save memory
            else:
                results.append(result)  # multi-thread, append to results

        self.end = time()
        if self.write_to_disk:
            self.parse_results()
        else:
            for result in results:
                self.concatenate(result)
        self.processing_time = time()
        self.write_config(self.config_p2)
        self.show_info()

    def concatenate(self, result):
        for i, e in enumerate(result):  # append to lists
            [self.wins, self.shots_p1, self.shots_p2, self.game_length, self.config_p1, self.config_p2, self.ff_p1,
             self.ff_p2][i].extend(e)

    def write_results(self, res, id_):
        with open(self.path + f"\\results\\{id_}.json", "w+") as file:
            json.dump(res, file)  # dump to process at later time

    def parse_results(self):  # huge episode number might result in memory problems
        for file in os.listdir(self.path + "\\results\\"):
            with open(self.path + "\\results\\" + file) as outfile:
                r = json.load(outfile)
                self.concatenate(r)

    def write_config(self, config):
        low, high = [], []
        search_low, search_high = min(self.game_length), max(self.game_length)  # find lowest and highest turn number
        for i, e in enumerate(self.game_length):  # iterate through all games
            if e == search_low:
                low.append(config[i])  # find all combinations that achieved the lowest turn number
            elif e == search_high:
                high.append(config[i])  # / the highest turn number
        data = {  # data for json
            'time': datetime.now().strftime("[ %d.%m.%Y | %H:%M:%S ]"),
            'episodes': str(len(self.game_length)),
            f'low : {search_low}': [NoIndent(e) for e in low],  # NoIndent is used for JSONFlatEncoder
            f'high: {search_high}': [NoIndent(e) for e in high]  # makes list stay in one line
        }
        with open(self.path + "/config.json", "w+") as file:
            file.write(json.dumps(data, indent=4, cls=JSONFlatEncoder))  # write to file in this directory

    def show_info(self):
        game_time = (self.end - self.start) / (self.eps * self.processes)  # calculate simulation time per game
        hit_p1, miss_p1 = self.extract_info(self.shots_p1)  # average hits and misses
        hit_p2, miss_p2 = self.extract_info(self.shots_p2)
        win_p1, win_p2, _ = self.counter(self.wins)  # count wins
        ff_p1, ff_p2 = sum(self.ff_p1), sum(self.ff_p2)
        eps = win_p1 + win_p2  # episodes played
        completed = eps // self.processes  # episodes played per process
        print(f'''
        The algorithm was run for {eps} episodes.
        Compute time was {round(self.end - self.start, 5)} seconds.
        Computing took {round(game_time, 9):.9f} seconds ({round(game_time * 1000000, 5):.5f} μs) per game.
        Algorithm was run on {self.processes} process(es), with {completed} episodes for each process.
        Result write time was {round(self.processing_time-self.end, 5)} seconds.

        Results of players:
            Stats {self.n1}:
                Mean shots: {round(hit_p1 + miss_p1, 3)}
                Mean hits: {round(hit_p1, 3)}
                Mean misses: {round(miss_p1, 3)}
                Wins: {win_p1}
                Win distribution: {self.format_float(win_p1/eps)}
                Forfeits: {ff_p1}

            Stats {self.n2}:
                Mean shots: {round(hit_p2 + miss_p2, 3)}
                Mean hits: {round(hit_p2, 3)}
                Mean misses: {round(miss_p2, 3)}
                Wins: {win_p2}
                Win distribution: {self.format_float(win_p2/eps)}
                Forfeits: {ff_p2}

            Stats Misc:
                Shortest game: {min(self.game_length)}
                Longest game: {max(self.game_length)}''')

    def loop(self, id_):  # function to be looped, constructs two players and one loop
        return BenchLoop(self.get_player(self.n1, id_), self.get_player(self.n2, id_), self.eps).game_loop()

    def test_loop(self, eps):  # dummy function that doesn't run multiple processes
        return BenchLoop(self.get_player(self.n1), self.get_player(self.n2), eps).game_loop()
        # used for testing a single game

    def get_player(self, selector, id_=0):
        return {  # inherited from util.selector.Selector
            "Random": self.random(),
            "Hunter": self.hunter(),
            "Dense": self.dense(id_),
        }[selector]

    def extract_info(self, games):
        hits, misses = [], []
        for game in games:  # iterate through all games
            _, hit, miss = self.counter(game)  # count hits and misses
            hits.append(hit)
            misses.append(miss)
        hits = self.mean(hits)  # take mean of results
        misses = self.mean(misses)
        return hits, misses


if __name__ == '__main__':
    # cProfile.run('Benchmark((10, 10), False, [5, 4, 3, 3, 2], 10000).test_loop(50)', sort="tottime")
    Benchmark((10, 10), False, [5, 4, 3, 3, 2], 10000).game_start()
