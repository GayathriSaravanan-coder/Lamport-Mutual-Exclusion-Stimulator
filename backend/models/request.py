from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, order=True)
class Request:
    """A Lamport request. `order=True` gives lexicographic ordering on
    (timestamp, process_id) - exactly the total order used by the algorithm."""
    timestamp: int
    process_id: int

    def label(self) -> str:
        return f"({self.timestamp},P{self.process_id})"

    def to_dict(self) -> dict:
        return {"timestamp": self.timestamp, "process_id": self.process_id}


@dataclass
class RequestRecord:
    """Bookkeeping row for the `requests` table (history of every request)."""
    id: int
    process_id: int
    timestamp: int
    status: str = "WAITING"          # WAITING -> IN_CS -> COMPLETED
    requested_at: int = 0
    entered_at: Optional[int] = None
    released_at: Optional[int] = None

    def to_dict(self) -> dict:
        return dict(self.__dict__)
