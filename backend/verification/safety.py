"""Mutual exclusion check. Computed from real state AND cross-checked against the event log."""
from models.process import CRITICAL_SECTION


def cs_history(sim) -> dict:
    """Replay the event log: how many processes were inside the CS at once?"""
    inside, max_concurrent, first_violation = set(), 0, None
    for ev in sim.events:
        if ev.event_type == "ENTER_CRITICAL_SECTION":
            inside.add(ev.process_id)
            if len(inside) > max_concurrent:
                max_concurrent = len(inside)
            if len(inside) > 1 and first_violation is None:
                first_violation = {"event_id": ev.id, "time": ev.sim_time, "processes": sorted(inside)}
        elif ev.event_type == "RELEASE":
            inside.discard(ev.process_id)
    return {"max_concurrent": max_concurrent, "first_violation": first_violation}


def mutual_exclusion(sim) -> dict:
    holders = sorted(pid for pid, p in sim.processes.items() if p.state == CRITICAL_SECTION)
    hist = cs_history(sim)
    details = [f"Processes currently in CRITICAL_SECTION: {len(holders)} "
               f"({', '.join('P%d' % h for h in holders) or 'none'}).",
               f"Highest number of processes inside the CS at once so far: {hist['max_concurrent']}."]
    if len(holders) > 1 or hist["first_violation"]:
        fv = hist["first_violation"]
        who = holders if len(holders) > 1 else (fv["processes"] if fv else [])
        details.append("Critical processes: " + ", ".join(f"P{x}" for x in who) + ".")
        if fv:
            details.append(f"First overlap happened at simulated time {fv['time']} (event #{fv['event_id']}).")
        if not sim.net.cfg.fifo:
            details.append("Cause: channels were allowed to reorder messages. Lamport's algorithm assumes "
                           "FIFO channels; a REPLY overtook the REQUEST sent before it, so the receiver "
                           "never saw the earlier request in its queue.")
        else:
            details.append("This should be impossible with FIFO channels - it indicates an algorithm bug.")
        return {"key": "mutual_exclusion", "title": "MUTUAL EXCLUSION", "status": "VIOLATION",
                "summary": "More than one process was in the critical section.", "details": details}
    return {"key": "mutual_exclusion", "title": "MUTUAL EXCLUSION", "status": "PASS",
            "summary": "At most one process has been in the critical section at any time.", "details": details}
