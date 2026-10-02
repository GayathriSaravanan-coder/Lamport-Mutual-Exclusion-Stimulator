"""Clock consistency, reply completion, CS ownership, and the aggregate verification report."""
from models.process import CRITICAL_SECTION, WAITING
from verification.safety import mutual_exclusion
from verification.ordering import request_ordering
from verification.liveness import liveness


def clock_consistency(sim) -> dict:
    problems, checked = [], 0
    last = {}
    for ev in sim.events:
        prev = last.get(ev.process_id, 0)
        if ev.logical_timestamp < prev or ev.logical_timestamp < ev.clock_before:
            problems.append(f"P{ev.process_id}'s clock went backwards at event #{ev.id}.")
        last[ev.process_id] = ev.logical_timestamp
    by_id = {e.id: e for e in sim.events}
    for m in sim.messages.values():
        send = by_id.get(m.send_event_id)
        if send is not None:
            checked += 1
            if m.timestamp != send.logical_timestamp:
                problems.append(f"Message #{m.id} carries ts {m.timestamp} but sender's clock was {send.logical_timestamp}.")
        recv = by_id.get(m.receive_event_id)
        if recv is not None:
            checked += 1
            if recv.logical_timestamp <= m.timestamp:
                problems.append(f"Message #{m.id}: receive clock {recv.logical_timestamp} is not greater than send ts {m.timestamp}.")
    details = [f"{len(sim.events)} events and {checked} send/receive pairs checked.",
               "Rules: clocks never decrease; a received message must leave the receiver's clock > the message timestamp."]
    if problems:
        return {"key": "clock_consistency", "title": "LAMPORT CLOCK CONSISTENCY", "status": "FAIL",
                "summary": problems[0], "details": details + problems[:5]}
    return {"key": "clock_consistency", "title": "LAMPORT CLOCK CONSISTENCY", "status": "PASS",
            "summary": "Every clock is monotonic and every receive respects max(local, received)+1.", "details": details}


def reply_completion(sim) -> dict:
    problems, details = [], []
    for pid in sorted(sim.processes):
        p = sim.processes[pid]
        need = len(p.others)
        if p.state == CRITICAL_SECTION:
            ok = set(p.others) <= p.replies_received
            details.append(f"P{pid}: in CS with {len(p.replies_received)}/{need} replies")
            if not ok:
                problems.append(f"P{pid} is in the CS without all replies.")
        elif p.state == WAITING:
            missing = sorted(set(p.others) - p.replies_received)
            details.append(f"P{pid}: waiting, {len(p.replies_received)}/{need} replies (missing {['P%d' % x for x in missing]})")
    if not details:
        details.append("No process is waiting or in the CS.")
    if problems:
        return {"key": "reply_completion", "title": "REPLY COMPLETION", "status": "FAIL",
                "summary": "; ".join(problems), "details": details}
    return {"key": "reply_completion", "title": "REPLY COMPLETION", "status": "PASS",
            "summary": "Every process inside the CS holds a REPLY from every other process.", "details": details}


def cs_owner(sim) -> dict:
    holders = sim.cs_holders()
    value = ", ".join(f"P{h}" for h in holders) if holders else "NONE"
    return {"key": "cs_owner", "title": "CURRENT CS OWNER", "status": "INFO" if len(holders) <= 1 else "VIOLATION",
            "summary": value, "details": []}


def verify_all(sim) -> dict:
    panels = [mutual_exclusion(sim), clock_consistency(sim), request_ordering(sim),
              reply_completion(sim), liveness(sim), cs_owner(sim)]
    return {"panels": panels, "current_cs_owner": sim.cs_holders(),
            "safety": panels[0]["status"], "liveness": panels[4]["status"]}
