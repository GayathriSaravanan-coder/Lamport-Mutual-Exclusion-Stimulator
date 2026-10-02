"""Dynamic WHY explanations. Everything is derived from the live simulation state."""
from engine import lamport
from engine.queue import explain_order
from models.process import IDLE, WAITING, CRITICAL_SECTION


def _check(ok: bool, text: str) -> dict:
    return {"ok": ok, "text": text}


def _why_missing(sim, p, q) -> str:
    if q in sim.silenced:
        return f"P{q} is silent (node-silence experiment), so it cannot reply"
    req = next((m for m in sim.messages.values() if m.message_type == "REQUEST"
                and m.sender == p.pid and m.receiver == q and m.request == p.my_request), None)
    if req is None:
        return f"REQUEST to P{q} was never sent"
    if req.delivery_status == "HELD":
        return f"REQUEST to P{q} is held because P{q} is silent"
    if req.delivery_status == "IN_FLIGHT":
        extra = " (delayed)" if req.delayed else ""
        return f"REQUEST to P{q} is still in transit{extra}, arrives at t={req.deliver_at}"
    rep = next((m for m in sim.messages.values() if m.message_type == "REPLY"
                and m.sender == q and m.receiver == p.pid and m.request == p.my_request), None)
    if rep is None:
        return f"P{q} has not sent its REPLY yet"
    if rep.delivery_status == "HELD":
        return f"REPLY from P{q} is held"
    extra = " (delayed)" if rep.delayed else ""
    return f"REPLY from P{q} is in transit{extra}, arrives at t={rep.deliver_at}"


def _explain_waiting(sim, p) -> dict:
    cond = lamport.entry_conditions(p)
    checks = [_check(True, f"P{p.pid} has requested access: request {p.my_request.label()} is outstanding")]
    got, need = len(p.replies_received), len(p.others)
    if cond["all_replies"]:
        checks.append(_check(True, f"REPLY received from all {need} other processes"))
    else:
        missing = sorted(set(p.others) - p.replies_received)
        why = "; ".join(_why_missing(sim, p, q) for q in missing)
        checks.append(_check(False, f"Only {got}/{need} REPLYs received - missing from "
                                    f"{', '.join('P%d' % q for q in missing)}: {why}"))
    head = p.queue.head()
    if cond["at_head"]:
        checks.append(_check(True, "Own request is at the head of the local queue - no earlier request has priority"))
    else:
        ahead = [r for r in p.queue.items() if r < p.my_request]
        holder = sim.cs_holders()
        txt = (f"Own request is NOT at the head of the queue: {', '.join(r.label() for r in ahead)} "
               f"come(s) first. {explain_order(head, p.my_request)}")
        if holder:
            txt += f" P{holder[0]} currently holds the critical section."
        checks.append(_check(False, txt))
    decision = (f"P{p.pid} satisfies every condition and enters on the next step." if all(c["ok"] for c in checks)
                else f"P{p.pid} cannot enter yet.")
    return {"pid": p.pid, "state": p.state, "question": f"WHY IS P{p.pid} WAITING?",
            "checks": checks, "decision": decision}


def _explain_entered(sim, p) -> dict:
    cond = lamport.entry_conditions(p)
    rec = next((r for r in reversed(sim.requests)
                if r.process_id == p.pid and r.status == "IN_CS"), None)
    checks = [
        _check(True, f"P{p.pid} was in WAITING state with request {p.my_request.label()}"),
        _check(cond["at_head"], "Its request is at the head of its local queue - no earlier request has priority"),
        _check(cond["all_replies"], f"It received REPLY from every other process ({len(p.replies_received)}/{len(p.others)})"),
    ]
    others = [q for q in sim.cs_holders() if q != p.pid]
    checks.append(_check(not others, "No other process is inside the critical section" if not others
                         else f"Another process is also inside the CS: {', '.join('P%d' % q for q in others)}"))
    when = f" It entered at simulated time {rec.entered_at}." if rec and rec.entered_at is not None else ""
    decision = (f"P{p.pid} is allowed to hold the critical section.{when}" if all(c["ok"] for c in checks)
                else f"P{p.pid} holds the critical section, but a condition is violated - see the failed check.")
    return {"pid": p.pid, "state": p.state, "question": f"WHY DID P{p.pid} ENTER?",
            "checks": checks, "decision": decision}


def _explain_idle(sim, p) -> dict:
    foreign = [r for r in p.queue.items()]
    checks = [_check(True, f"P{p.pid} has no outstanding request")]
    if foreign:
        checks.append(_check(True, f"Its queue holds other processes' requests: {', '.join(r.label() for r in foreign)}"))
    else:
        checks.append(_check(True, "Its local queue is empty"))
    if p.backlog:
        checks.append(_check(False, f"{p.backlog} application request(s) are waiting behind the current one"))
    return {"pid": p.pid, "state": p.state, "question": f"WHY IS P{p.pid} IDLE?", "checks": checks,
            "decision": f"P{p.pid} will only act when it receives a message or the application asks for the CS."}


def explain_process(sim, pid: int) -> dict:
    p = sim.processes[pid]
    if p.state == CRITICAL_SECTION:
        return _explain_entered(sim, p)
    if p.state == WAITING:
        return _explain_waiting(sim, p)
    return _explain_idle(sim, p)


def compare_processes(sim, a: int, b: int) -> dict:
    """WHY IS Pa's REQUEST AHEAD OF Pb's ?"""
    ra, rb = sim.processes[a].my_request, sim.processes[b].my_request
    if ra is None or rb is None:
        idle = [x for x, r in ((a, ra), (b, rb)) if r is None]
        return {"a": a, "b": b, "text": f"{', '.join('P%d' % x for x in idle)} has no outstanding request, "
                                        f"so there is nothing to compare."}
    ahead = a if ra < rb else b
    return {"a": a, "b": b, "ahead": ahead, "text": explain_order(ra, rb)}


def explain_all(sim, a: int = None, b: int = None) -> dict:
    procs = [explain_process(sim, pid) for pid in sorted(sim.processes)]
    pending = sorted((p.my_request, pid) for pid, p in sim.processes.items() if p.my_request)
    if a is None or b is None:
        if len(pending) >= 2:
            a, b = pending[0][1], pending[1][1]
    comparison = compare_processes(sim, a, b) if a and b and a != b else None
    focus = (sim.cs_holders() or sim.waiting() or [None])[0]
    return {"processes": procs, "comparison": comparison, "focus": focus, "last_event": sim.last_note}
