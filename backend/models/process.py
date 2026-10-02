from dataclasses import dataclass, field
from typing import List, Optional, Set
from engine.clock import LamportClock
from engine.queue import RequestQueue
from models.request import Request

IDLE = "IDLE"
WAITING = "WAITING"
CRITICAL_SECTION = "CRITICAL_SECTION"


@dataclass
class Process:
    pid: int
    others: List[int]
    clock: LamportClock = field(default_factory=LamportClock)
    queue: RequestQueue = field(default_factory=RequestQueue)
    state: str = IDLE
    my_request: Optional[Request] = None
    replies_received: Set[int] = field(default_factory=set)
    backlog: int = 0                 # application requests waiting for the current one to finish

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "clock": self.clock.value,
            "state": self.state,
            "queue": [r.to_dict() for r in self.queue.items()],
            "my_request": self.my_request.to_dict() if self.my_request else None,
            "replies_received": sorted(self.replies_received),
            "replies_needed": len(self.others),
            "backlog": self.backlog,
            "in_cs": self.state == CRITICAL_SECTION,
        }
