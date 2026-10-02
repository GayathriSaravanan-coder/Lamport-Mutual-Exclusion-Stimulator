import bisect
from typing import List, Optional
from models.request import Request


class RequestQueue:
    """Local request queue, always kept sorted by (timestamp, process_id)."""

    def __init__(self):
        self._items: List[Request] = []

    def add(self, req: Request) -> bool:
        if req in self._items:
            return False
        bisect.insort(self._items, req)
        return True

    def remove(self, req: Request) -> bool:
        if req in self._items:
            self._items.remove(req)
            return True
        return False

    def head(self) -> Optional[Request]:
        return self._items[0] if self._items else None

    def items(self) -> List[Request]:
        return list(self._items)

    def position(self, req: Request) -> Optional[int]:
        return self._items.index(req) if req in self._items else None

    def is_sorted(self) -> bool:
        """True if strictly increasing by (timestamp, process_id): sorted and no duplicates."""
        return all(a < b for a, b in zip(self._items, self._items[1:]))

    def __len__(self):
        return len(self._items)

    def __contains__(self, req):
        return req in self._items


def explain_order(a: Request, b: Request) -> str:
    """Human-readable reason why one request has priority over the other."""
    first, second = (a, b) if a < b else (b, a)
    if first.timestamp != second.timestamp:
        return (f"{first.label()} has priority over {second.label()} because its "
                f"timestamp {first.timestamp} is smaller than {second.timestamp}.")
    return (f"{first.label()} has priority over {second.label()}: the timestamps tie "
            f"({first.timestamp}), so the smaller process id wins (P{first.process_id} < P{second.process_id}).")
