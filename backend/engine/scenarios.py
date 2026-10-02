"""Scenario library. Every scenario is fully described by an ExperimentConfig,
so it is 100% reproducible (fixed request script + fixed RNG seed)."""
from typing import Optional
from models.experiment import ExperimentConfig, NetworkConfig, DelayRule

SCENARIOS = {}


def _register(id, name, description, expected, min_p, default_p, builder):
    SCENARIOS[id] = dict(id=id, name=name, description=description, expected=expected,
                         min_processes=min_p, default_processes=default_p, builder=builder)


def _custom(n):
    return dict(requests=[], network=NetworkConfig(), clocks={})


def _single(n):
    return dict(requests=[[0, 1]], network=NetworkConfig(), clocks={})


def _concurrent(n):
    # P1 and P3 have earlier activity, so their clocks are ahead: timestamps differ.
    return dict(requests=[[0, pid] for pid in (1, 2, 3)], network=NetworkConfig(),
                clocks={1: 4, 3: 2})


def _tie(n):
    return dict(requests=[[0, pid] for pid in (1, 2, 3)], network=NetworkConfig(), clocks={})


def _delayed(n):
    net = NetworkConfig(mode="SELECTED",
                        selected_delays=[DelayRule(delay=8, sender=1, receiver=3, message_type="REQUEST")])
    return dict(requests=[[0, 1], [0, 2]], network=net, clocks={})


def _out_of_order(n):
    net = NetworkConfig(mode="SELECTED",
                        selected_delays=[DelayRule(delay=4, sender=1, message_type="REQUEST")])
    return dict(requests=[[0, 1], [0, 2]], network=net, clocks={})


def _multi_wait(n):
    return dict(requests=[[i, pid] for i, pid in enumerate(range(1, n + 1))],
                network=NetworkConfig(), clocks={})


def _contention(n):
    reqs = [[0, pid] for pid in range(1, n + 1)] * 2      # every process wants the CS twice
    return dict(requests=reqs, network=NetworkConfig(), clocks={})


def _silence(n):
    return dict(requests=[[0, 1]], network=NetworkConfig(silenced_nodes=[3]), clocks={})


def _non_fifo(n):
    net = NetworkConfig(mode="SELECTED", fifo=False,
                        selected_delays=[DelayRule(delay=4, sender=1, message_type="REQUEST")])
    # long critical sections make the overlap visible (P2 is still inside when P1 gets in)
    return dict(requests=[[0, 1], [0, 2]], network=net, clocks={}, cs=6)


_register("custom", "Custom (empty)", "No scripted requests. Use Generate Request to create your own scenario.",
          "Whatever you build.", 3, 3, _custom)
_register("single_request", "1. Single Request", "One process requests the critical section on an idle system.",
          "P1 collects 2 REPLYs, enters, releases. No contention.", 3, 3, _single)
_register("concurrent_requests", "2. Concurrent Requests",
          "P1, P2, P3 request at the same instant with different clocks (P1 is at 4, P3 at 2, P2 at 0).",
          "Smallest timestamp wins: P2 (ts 1), then P3 (ts 3), then P1 (ts 5) - even though P1 has the smallest id.",
          3, 3, _concurrent)
_register("same_timestamp_tie", "3. Same Timestamp Tie",
          "P1, P2, P3 request simultaneously from clock 0, so every request has timestamp 1.",
          "Ties are broken by process id: P1, then P2, then P3.", 3, 3, _tie)
_register("delayed_message", "4. Delayed Message",
          "P1 and P2 request together, but P1's REQUEST to P3 takes 8 time units.",
          "P1 waits for P3's REPLY (Liveness WARNING while the message is delayed), then everything resolves.",
          3, 3, _delayed)
_register("out_of_order_arrival", "5. Out-of-Order Message Arrival",
          "P1's REQUESTs are slow, P2's are fast, so P3 receives P2's request before P1's.",
          "Arrival order at P3 is P2, P1 but logical order is P1, P2. P1 still goes first.",
          3, 3, _out_of_order)
_register("multiple_waiting", "6. Multiple Waiting Processes",
          "Every process requests one time unit after the previous one.",
          "Several processes wait in queues while one holds the CS; they enter in timestamp order.",
          3, 4, _multi_wait)
_register("high_contention", "7. High Contention",
          "Every process requests the CS twice at time 0 (second request starts after the first finishes).",
          "Long queues, many messages, safety must still hold.", 3, 6, _contention)
_register("node_silence", "8. Controlled Node Silence",
          "P3 is silent (crashed/partitioned) while P1 requests.",
          "P1 never gets P3's REPLY: Liveness WARNING. Use 'Resume node' to see recovery.",
          3, 3, _silence)
_register("non_fifo_violation", "Extra: Non-FIFO channels (assumption violated)",
          "Same as scenario 5 but channels may reorder messages on the same link. Lamport's algorithm "
          "ASSUMES FIFO channels, so this experiment is expected to break mutual exclusion.",
          "Safety monitor should report VIOLATION - it is computed from the real state, not forced.",
          3, 3, _non_fifo)


def list_scenarios():
    out = []
    for s in SCENARIOS.values():
        n = s["default_processes"]
        spec = s["builder"](n)
        out.append({
            "id": s["id"], "name": s["name"], "description": s["description"],
            "expected": s["expected"], "min_processes": s["min_processes"],
            "default_processes": n, "network": spec["network"].to_dict(),
        })
    return out


def build_config(scenario: str, process_count: Optional[int] = None,
                 network: Optional[dict] = None) -> ExperimentConfig:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario '{scenario}'")
    s = SCENARIOS[scenario]
    n = process_count if process_count is not None else s["default_processes"]
    if n < s["min_processes"]:
        raise ValueError(f"scenario '{scenario}' needs at least {s['min_processes']} processes")
    spec = s["builder"](n)
    net = NetworkConfig.from_dict(network) if network is not None else spec["network"]
    cfg = ExperimentConfig(process_count=n, scenario=scenario, network=net,
                           initial_clocks=spec["clocks"], cs_duration=spec.get("cs", 3),
                           scripted_requests=[list(r) for r in spec["requests"]])
    cfg.validate()
    return cfg
