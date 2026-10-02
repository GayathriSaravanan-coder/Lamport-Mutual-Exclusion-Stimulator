from dataclasses import dataclass
from typing import Optional
from models.request import Request

REQUEST = "REQUEST"
REPLY = "REPLY"
RELEASE = "RELEASE"


@dataclass
class Message:
    id: int
    sender: int
    receiver: int
    message_type: str
    timestamp: int                 # Lamport timestamp carried by the message
    request: Request               # which request this message is about
    sent_at: int                   # simulated time of sending
    deliver_at: int                # simulated time it is scheduled to arrive
    delay: int                     # effective delay (deliver_at - sent_at)
    delayed: bool = False          # True if slower than a normal network hop
    delivery_status: str = "IN_FLIGHT"   # IN_FLIGHT | DELIVERED | HELD
    delivered_at: Optional[int] = None
    arrival_index: Optional[int] = None  # global arrival sequence number
    send_event_id: Optional[int] = None
    receive_event_id: Optional[int] = None

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["request"] = self.request.to_dict()
        return d
