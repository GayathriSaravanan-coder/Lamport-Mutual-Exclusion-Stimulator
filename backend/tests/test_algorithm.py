from engine.clock import LamportClock
from engine.queue import RequestQueue
from engine import lamport
from models.process import Process, WAITING, IDLE, CRITICAL_SECTION
from models.request import Request
from tests.helpers import make, run_all, grants
from verification.invariants import verify_all, clock_consistency, reply_completion
from verification.safety import mutual_exclusion
from verification.liveness import liveness


def test_09_lamport_clock_update():
    c = LamportClock(3)
    assert c.tick() == 4
    assert c.update(10) == 11          # max(4, 10) + 1
    assert c.update(2) == 12           # max(11, 2) + 1


def test_10_queue_ordering_and_pid_tiebreak():
    q = RequestQueue()
    for r in (Request(5, 1), Request(1, 3), Request(1, 2), Request(3, 1)):
        q.add(r)
    assert q.items() == [Request(1, 2), Request(1, 3), Request(3, 1), Request(5, 1)]
    assert q.head() == Request(1, 2)
    assert q.is_sorted()
    assert q.add(Request(1, 2)) is False   # no duplicates
    q.remove(Request(1, 2))
    assert q.head() == Request(1, 3)


def test_request_rule():
    p = Process(pid=1, others=[2, 3])
    outs = lamport.request_cs(p)
    assert p.state == WAITING and p.clock.value == 1
    assert p.queue.head() == Request(1, 1)
    assert sorted(o.receiver for o in outs) == [2, 3]
    assert not lamport.can_enter(p)        # no replies yet


def test_01_single_request():
    sim = run_all(make("single_request"))
    assert grants(sim) == [1]
    assert sim.status == "COMPLETED"
    types = [e.event_type for e in sim.events if e.process_id == 1]
    assert types[0] == "REQUEST" and "ENTER_CRITICAL_SECTION" in types and types[-1] == "RECEIVE_REPLY" or "RELEASE" in types


def test_02_concurrent_requests_use_timestamp_order():
    sim = run_all(make("concurrent_requests"))
    assert grants(sim) == [2, 3, 1]        # ts 1, 3, 5 - NOT pid order


def test_03_04_same_timestamp_pid_tiebreak():
    sim = run_all(make("same_timestamp_tie"))
    stamps = {r.process_id: r.timestamp for r in sim.requests}
    assert set(stamps.values()) == {1}
    assert grants(sim) == [1, 2, 3]


def test_05_delayed_message_shows_liveness_warning_then_recovers():
    sim = make("delayed_message"); sim.start()
    seen_warning = False
    while sim.step()["progressed"]:
        if liveness(sim)["status"] == "WARNING":
            seen_warning = True
    assert seen_warning
    assert liveness(sim)["status"] == "PASS"
    assert grants(sim) == [1, 2]


def test_06_out_of_order_arrival_differs_from_logical_order():
    sim = run_all(make("out_of_order_arrival"))
    p3 = next(x for x in sim.snapshot()["order"]["per_process"] if x["pid"] == 3)
    assert p3["differs"] is True
    assert p3["arrival_order"][0]["process_id"] == 2      # P2's request arrived first at P3
    assert p3["logical_order"][0]["process_id"] == 1      # but P1 is logically first
    assert grants(sim) == [1, 2]
    assert mutual_exclusion(sim)["status"] == "PASS"


def test_07_multiple_waiting_processes():
    sim = make("multiple_waiting"); sim.start()
    max_waiting = 0
    while sim.step()["progressed"]:
        max_waiting = max(max_waiting, len(sim.waiting()))
    assert max_waiting >= 3
    assert sorted(grants(sim)) == [1, 2, 3, 4]


def test_08_release_removes_request_everywhere():
    sim = run_all(make("single_request"))
    assert all(len(p.queue) == 0 for p in sim.processes.values())
    assert sim.processes[1].state == IDLE


def test_11_reply_completion_required_for_entry():
    sim = make("single_request"); sim.start()
    while sim.step()["progressed"]:
        for p in sim.processes.values():
            if p.state == CRITICAL_SECTION:
                assert set(p.others) <= p.replies_received
    assert reply_completion(sim)["status"] == "PASS"


def test_12_safety_invariant_is_computed_not_hardcoded():
    fifo = run_all(make("out_of_order_arrival"))
    assert mutual_exclusion(fifo)["status"] == "PASS"
    broken = run_all(make("non_fifo_violation"))
    assert mutual_exclusion(broken)["status"] == "VIOLATION"
    assert "Critical processes" in " ".join(mutual_exclusion(broken)["details"])


def test_13_liveness_node_silence_then_resume():
    sim = make("node_silence"); sim.start(); sim.run_steps(100)
    assert sim.status == "STALLED"
    assert liveness(sim)["status"] == "WARNING"
    sim.resume(3); sim.run_steps(100)
    assert sim.status == "COMPLETED"
    assert liveness(sim)["status"] == "PASS"
    assert grants(sim) == [1]


def test_14_reset_is_reproducible():
    from engine.simulation import Simulation
    from models.experiment import ExperimentConfig
    a = run_all(make("high_contention"))
    cfg = ExperimentConfig.from_dict(a.original_config.to_dict())
    b = run_all(Simulation(2, cfg))
    assert [e.detail for e in a.events] == [e.detail for e in b.events]


def test_15_every_scenario_runs_and_clocks_are_consistent():
    from engine.scenarios import SCENARIOS
    for sid in SCENARIOS:
        sim = run_all(make(sid))
        assert clock_consistency(sim)["status"] == "PASS", sid
        if sid != "node_silence":
            assert sim.status in ("COMPLETED", "PAUSED"), sid


def test_release_delayed_resumes_delivery():
    sim = make("delayed_message"); sim.start(); sim.run_steps(6)
    assert liveness(sim)["status"] == "WARNING"
    assert sim.release_delayed() >= 1
    sim.run_steps(200)
    assert sim.status == "COMPLETED"
    assert liveness(sim)["status"] == "PASS"


def test_backlog_second_request_after_first_completes():
    sim = make("custom"); sim.start()
    sim.request(1); sim.request(1)
    sim.run_steps(500)
    assert grants(sim) == [1, 1]


def test_explanations_reference_live_state():
    from explanation.decision_explainer import explain_process
    sim = make("same_timestamp_tie"); sim.start()
    while not sim.cs_holders():
        assert sim.step()["progressed"]
    texts = {pid: explain_process(sim, pid) for pid in (1, 2, 3)}
    holder = sim.cs_holders()
    assert holder == [1]
    assert texts[1]["question"] == "WHY DID P1 ENTER?"
    assert texts[2]["question"] == "WHY IS P2 WAITING?"
    assert any(not c["ok"] for c in texts[2]["checks"])
    assert "P1" in " ".join(c["text"] for c in texts[2]["checks"])
