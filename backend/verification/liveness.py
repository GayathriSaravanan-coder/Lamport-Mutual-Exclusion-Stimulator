"""Liveness monitor: do requests progress REQUEST -> WAITING -> CRITICAL_SECTION -> RELEASE ?"""
from models.process import WAITING, CRITICAL_SECTION


def liveness(sim) -> dict:
    waiting = sim.waiting()
    in_cs = sim.cs_holders()
    backlog = [pid for pid, p in sim.processes.items() if p.backlog > 0]
    unresolved = sorted(set(waiting) | set(in_cs) | set(backlog))
    pending_triggers = len(sim._heap)
    silent = sorted(sim.silenced)
    delayed = [m for m in sim.in_flight() if m.delayed]
    held = sim.held_messages()

    def result(status, summary, details):
        return {"key": "liveness", "title": "LIVENESS", "status": status,
                "summary": summary, "details": details}

    details = [f"Waiting: {['P%d' % x for x in waiting] or 'none'}; in CS: {['P%d' % x for x in in_cs] or 'none'}; "
               f"queued application requests: {['P%d' % x for x in backlog] or 'none'}.",
               f"Messages in flight: {len(sim.in_flight())} (delayed: {len(delayed)}, held by silent nodes: {len(held)})."]
    if not unresolved:
        if sim.requests:
            done = sum(1 for r in sim.requests if r.status == "COMPLETED")
            return result("PASS", f"All {done} request(s) completed: REQUEST -> CS -> RELEASE.", details)
        return result("PASS", "No outstanding requests.", details)
    if silent:
        return result("WARNING", f"Unresolved requests while node(s) {', '.join('P%d' % x for x in silent)} are silent.", details)
    if pending_triggers == 0 and not sim.in_flight():
        return result("WARNING", "Stalled: unresolved requests but nothing is left to deliver or execute.", details)
    if waiting and (delayed or held):
        return result("WARNING", "Waiting processes are blocked behind deliberately delayed messages.", details)
    return result("IN_PROGRESS", "Requests are progressing normally.", details)
