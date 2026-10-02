import random
from models.experiment import NetworkConfig, NORMAL_DELAY


class NetworkSimulator:
    """Decides WHEN a message arrives. It never touches the Lamport rules."""

    def __init__(self, cfg: NetworkConfig):
        self.cfg = cfg
        self.rng = random.Random(cfg.seed)
        self.channel_last = {}          # (sender, receiver) -> last scheduled arrival time

    def compute_delay(self, sender: int, receiver: int, mtype: str) -> int:
        for rule in reversed(self.cfg.selected_delays):     # latest rule wins
            if rule.matches(sender, receiver, mtype):
                return max(1, rule.delay)
        if self.cfg.mode == "FIXED":
            return max(1, self.cfg.fixed_delay)
        if self.cfg.mode == "RANDOM":
            return self.rng.randint(self.cfg.random_min, self.cfg.random_max)
        return NORMAL_DELAY

    def schedule_time(self, now: int, sender: int, receiver: int, delay: int) -> int:
        t = now + delay
        if self.cfg.fifo:               # FIFO channel: never overtake an earlier message
            t = max(t, self.channel_last.get((sender, receiver), 0))
            self.channel_last[(sender, receiver)] = t
        return t
