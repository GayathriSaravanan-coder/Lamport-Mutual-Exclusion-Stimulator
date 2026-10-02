"""Pure Lamport mutual-exclusion rules. No networking, no scheduling here.
Each function mutates one Process and returns the messages it wants to send."""
from dataclasses import dataclass
from typing import List
from models.message import REQUEST, REPLY, RELEASE, Message
from models.process import Process, IDLE, WAITING, CRITICAL_SECTION
from models.request import Request


@dataclass
class Outgoing:
    message_type: str
    receiver: int
    timestamp: int
    request: Request


def request_cs(p: Process) -> List[Outgoing]:
    """REQUEST: tick clock, queue own request, broadcast REQUEST."""
    ts = p.clock.tick()
    req = Request(ts, p.pid)
    p.my_request = req
    p.state = WAITING
    p.replies_received = set()
    p.queue.add(req)
    return [Outgoing(REQUEST, q, ts, req) for q in p.others]


def receive_request(p: Process, m: Message) -> List[Outgoing]:
    """RECEIVE REQUEST: clock = max+1, queue the request, send REPLY."""
    p.clock.update(m.timestamp)
    p.queue.add(m.request)
    return [Outgoing(REPLY, m.sender, p.clock.value, m.request)]


def receive_reply(p: Process, m: Message) -> None:
    """RECEIVE REPLY: clock = max+1, remember who replied (for our current request)."""
    p.clock.update(m.timestamp)
    if p.state == WAITING and p.my_request == m.request:
        p.replies_received.add(m.sender)


def entry_conditions(p: Process) -> dict:
    return {
        "waiting": p.state == WAITING,
        "at_head": p.my_request is not None and p.queue.head() == p.my_request,
        "all_replies": set(p.others) <= p.replies_received,
    }


def can_enter(p: Process) -> bool:
    return all(entry_conditions(p).values())


def enter_cs(p: Process) -> None:
    p.state = CRITICAL_SECTION


def release_cs(p: Process) -> List[Outgoing]:
    """RELEASE: tick clock, drop own request, broadcast RELEASE."""
    ts = p.clock.tick()
    req = p.my_request
    p.queue.remove(req)
    p.my_request = None
    p.state = IDLE
    p.replies_received = set()
    return [Outgoing(RELEASE, q, ts, req) for q in p.others]


def receive_release(p: Process, m: Message) -> None:
    """RECEIVE RELEASE: clock = max+1, remove the releasing process's request."""
    p.clock.update(m.timestamp)
    p.queue.remove(m.request)
