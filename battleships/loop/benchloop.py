

class BenchLoop:
    """
    defines game loop, takes two classes. called from game.py
    """
    def __init__(self, p1, p2, episodes):
        self.p1 = p1  # Player 1 and 2
        self.p2 = p2
        self.episodes = episodes
        self.wins = []
        self.shots_p1 = []
        self.shots_p2 = []
        self.game_length = []
        self.config_p1 = []
        self.config_p2 = []
        self.ff_p1 = 0
        self.ff_p2 = 0
        self.cnt = 0

    def game_loop(self):
        self.p1.initialize(self.p2)
        self.p2.initialize(self.p1)
        for i in range(self.episodes):
            self.cnt = 0
            self.prepare(self.p1)
            self.prepare(self.p2)
            while 1:
                over, win = self.check_over(self.p2, self.p1, 0)
                if over:
                    break
                over, win = self.check_over(self.p1, self.p2, 1)
                if over:
                    break
                self.cnt += 1
            self.extract(win)
            self.reset(self.p1)
            self.reset(self.p2)
        return self.wins, self.shots_p1, self.shots_p2, self.game_length, self.config_p1, \
            self.config_p2, [self.ff_p1], [self.ff_p2]

    @staticmethod
    def prepare(inst):
        inst.placement()
        inst.alive_update()

    @staticmethod
    def reset(inst):
        inst.reset()
        inst.game.reset()

    @staticmethod
    def check_over(inst, other, num):
        if inst.game.get_game_over():
            return True, num
        other.shoot_nc(inst)
        if inst.game.get_game_over():
            return True, num
        return False, None

    def extract(self, win):
        self.wins.append(win)
        self.shots_p1.append(self.p2.game.get_shots())
        self.shots_p2.append(self.p1.game.get_shots())
        self.game_length.append(self.cnt+1)
        self.config_p1.append(self.p1.game.get_ships())
        self.config_p2.append(self.p2.game.get_ships())
        if self.p1.game.get_game_forfeit():
            self.ff_p1 += 1
        elif self.p2.game.get_game_forfeit():
            self.ff_p2 += 1
