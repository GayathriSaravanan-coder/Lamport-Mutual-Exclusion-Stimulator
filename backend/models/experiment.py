from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

NORMAL_DELAY = 1                       # delay of an ordinary network hop
MODES = ("NORMAL", "FIXED", "RANDOM", "SELECTED")
MESSAGE_TYPES = ("REQUEST", "REPLY", "RELEASE")
MIN_PROCESSES, MAX_PROCESSES = 3, 8


@dataclass
class DelayRule:
    """Delay for selected messages. None = wildcard."""
    delay: int = 5
    sender: Optional[int] = None
    receiver: Optional[int] = None
    message_type: Optional[str] = None

    def matches(self, sender: int, receiver: int, mtype: str) -> bool:
        return ((self.sender is None or self.sender == sender)
                and (self.receiver is None or self.receiver == receiver)
                and (self.message_type is None or self.message_type == mtype))

    def describe(self) -> str:
        s = f"P{self.sender}" if self.sender else "any"
        r = f"P{self.receiver}" if self.receiver else "any"
        t = self.message_type or "any message"
        return f"{t} {s}->{r} delayed to {self.delay}"

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "DelayRule":
        return DelayRule(delay=int(d.get("delay", 5)), sender=d.get("sender"),
                         receiver=d.get("receiver"), message_type=d.get("message_type"))


@dataclass
class NetworkConfig:
    mode: str = "NORMAL"
    fixed_delay: int = 3
    random_min: int = 1
    random_max: int = 6
    seed: int = 42
    fifo: bool = True                      # Lamport's algorithm ASSUMES FIFO channels
    selected_delays: List[DelayRule] = field(default_factory=list)
    silenced_nodes: List[int] = field(default_factory=list)

    def validate(self, process_count: int) -> None:
        if self.mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if self.fixed_delay < 1 or self.random_min < 1 or self.random_max < self.random_min:
            raise ValueError("delays must be >= 1 and random_max >= random_min")
        for r in self.selected_delays:
            if r.delay < 1:
                raise ValueError("delay must be >= 1")
            if r.message_type not in (None,) + MESSAGE_TYPES:
                raise ValueError("bad message type in delay rule")
            for pid in (r.sender, r.receiver):
                if pid is not None and not 1 <= pid <= process_count:
                    raise ValueError("delay rule refers to unknown process")
        for pid in self.silenced_nodes:
            if not 1 <= pid <= process_count:
                raise ValueError("silenced node out of range")

    def is_normal(self) -> bool:
        return (self.mode in ("NORMAL", "SELECTED") and not self.selected_delays
                and not self.silenced_nodes and self.fifo)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["selected_delays"] = [r.to_dict() for r in self.selected_delays]
        return d

    @staticmethod
    def from_dict(d: Optional[dict]) -> "NetworkConfig":
        d = d or {}
        return NetworkConfig(
            mode=d.get("mode", "NORMAL"),
            fixed_delay=int(d.get("fixed_delay", 3)),
            random_min=int(d.get("random_min", 1)),
            random_max=int(d.get("random_max", 6)),
            seed=int(d.get("seed", 42)),
            fifo=bool(d.get("fifo", True)),
            selected_delays=[DelayRule.from_dict(r) for r in d.get("selected_delays", [])],
            silenced_nodes=[int(x) for x in d.get("silenced_nodes", [])],
        )


@dataclass
class ExperimentConfig:
    process_count: int = 3
    scenario: str = "custom"
    network: NetworkConfig = field(default_factory=NetworkConfig)
    cs_duration: int = 3                                   # simulated time spent in the CS
    initial_clocks: Dict[int, int] = field(default_factory=dict)
    scripted_requests: List[List[int]] = field(default_factory=list)   # [[time, pid], ...]

    def validate(self) -> None:
        if not MIN_PROCESSES <= self.process_count <= MAX_PROCESSES:
            raise ValueError(f"process_count must be {MIN_PROCESSES}-{MAX_PROCESSES}")
        if self.cs_duration < 1:
            raise ValueError("cs_duration must be >= 1")
        self.network.validate(self.process_count)
        for t, pid in self.scripted_requests:
            if not 1 <= pid <= self.process_count:
                raise ValueError("scripted request for unknown process")

    def to_dict(self) -> dict:
        return {
            "process_count": self.process_count,
            "scenario": self.scenario,
            "network": self.network.to_dict(),
            "cs_duration": self.cs_duration,
            "initial_clocks": {str(k): v for k, v in self.initial_clocks.items()},
            "scripted_requests": [list(x) for x in self.scripted_requests],
        }

    @staticmethod
    def from_dict(d: dict) -> "ExperimentConfig":
        return ExperimentConfig(
            process_count=int(d["process_count"]),
            scenario=d.get("scenario", "custom"),
            network=NetworkConfig.from_dict(d.get("network")),
            cs_duration=int(d.get("cs_duration", 3)),
            initial_clocks={int(k): int(v) for k, v in d.get("initial_clocks", {}).items()},
            scripted_requests=[[int(t), int(p)] for t, p in d.get("scripted_requests", [])],
        )
