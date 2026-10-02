from dataclasses import dataclass
from typing import Optional


@dataclass
class Event:
    id: int
    step: int
    sim_time: int
    process_id: int
    event_type: str        # REQUEST, RECEIVE_REQUEST, REPLY, RECEIVE_REPLY,
                           # ENTER_CRITICAL_SECTION, RELEASE, RECEIVE_RELEASE
    clock_before: int
    logical_timestamp: int  # Lamport clock AFTER the event
    state: str              # process state after the event
    related_process: Optional[int] = None
    message_id: Optional[int] = None
    detail: str = ""

    def to_dict(self) -> dict:
        return dict(self.__dict__)
