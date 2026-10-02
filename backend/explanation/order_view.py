"""Logical order (timestamp, pid) versus arrival order (simulated delivery sequence)."""
from engine.queue import explain_order
from models.request import Request


def order_comparison(sim) -> dict:
    per_process = []
    notes = []
    for pid in sorted(sim.processes):
        arrival = []
        for ev in sim.events:
            if ev.process_id != pid:
                continue
            if ev.event_type == "REQUEST":
                proc_req = next((r for r in sim.requests
                                 if r.process_id == pid and r.requested_at == ev.sim_time
                                 and r.timestamp == ev.logical_timestamp), None)
                if proc_req:
                    arrival.append(Request(proc_req.timestamp, pid))
            elif ev.event_type == "RECEIVE_REQUEST" and ev.message_id:
                arrival.append(sim.messages[ev.message_id].request)
        logical = sorted(arrival)
        differs = arrival != logical
        per_process.append({
            "pid": pid,
            "arrival_order": [r.to_dict() for r in arrival],
            "logical_order": [r.to_dict() for r in logical],
            "differs": differs,
        })
        if differs:
            for i, a in enumerate(arrival):
                later_smaller = next((b for b in arrival[i + 1:] if b < a), None)
                if later_smaller:
                    notes.append(f"P{pid} saw {a.label()} arrive before {later_smaller.label()}, "
                                 f"but logically it goes after: "
                                 f"{explain_order(later_smaller, a)}")
                    break
    all_requests = sorted({Request(r.timestamp, r.process_id) for r in sim.requests})
    grants = [ev for ev in sim.events if ev.event_type == "ENTER_CRITICAL_SECTION"]
    grant_order = []
    for ev in grants:
        rec = next((r for r in sim.requests if r.process_id == ev.process_id
                    and r.entered_at == ev.sim_time), None)
        grant_order.append({"pid": ev.process_id,
                            "request": rec and {"timestamp": rec.timestamp, "process_id": rec.process_id}})
    return {
        "per_process": per_process,
        "logical_all": [r.to_dict() for r in all_requests],
        "grant_order": grant_order,
        "notes": notes,
        "explanation": ("Logical order is decided by (timestamp, process_id). Arrival order is just the "
                        "simulated network delivery sequence at each process. They can differ, but every "
                        "process sorts its queue by logical order, so all processes agree on who goes first."),
    }
