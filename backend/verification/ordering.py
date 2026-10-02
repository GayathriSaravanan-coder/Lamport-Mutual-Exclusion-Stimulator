"""Request-queue ordering check."""
from models.process import CRITICAL_SECTION


def request_ordering(sim) -> dict:
    problems, details = [], []
    for pid in sorted(sim.processes):
        p = sim.processes[pid]
        items = p.queue.items()
        details.append(f"P{pid} queue: {[r.label() for r in items]}")
        if not p.queue.is_sorted():
            problems.append(f"P{pid}'s queue is not strictly sorted by (timestamp, process_id).")
        if p.state == CRITICAL_SECTION and p.queue.head() != p.my_request:
            problems.append(f"P{pid} is in the CS but its request is not at the head of its queue.")
    if problems:
        return {"key": "request_ordering", "title": "REQUEST ORDERING", "status": "FAIL",
                "summary": "; ".join(problems), "details": details}
    return {"key": "request_ordering", "title": "REQUEST ORDERING", "status": "PASS",
            "summary": "Every local queue is sorted by (timestamp, process_id); CS holder is at its queue head.",
            "details": details}
