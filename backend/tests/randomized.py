"""Randomized executions. Nothing here is forced: safety is judged by the real monitor."""
import random
from engine.simulation import Simulation
from models.experiment import ExperimentConfig, NetworkConfig
from verification.invariants import verify_all


def run_batch(runs=50, fifo=True, seed=2024):
    rng = random.Random(seed)
    totals = dict(executions=0, safety_violations=0, liveness_warnings=0,
                  completed_requests=0, total_requests=0, clock_failures=0)
    for i in range(runs):
        n = rng.randint(3, 8)
        net = NetworkConfig(mode="RANDOM", random_min=1, random_max=rng.randint(2, 9),
                            seed=rng.randint(0, 10 ** 6), fifo=fifo)
        reqs = [[rng.randint(0, 10), rng.randint(1, n)] for _ in range(rng.randint(1, 3 * n))]
        cfg = ExperimentConfig(process_count=n, scenario="random", network=net,
                               cs_duration=rng.randint(1, 5), scripted_requests=reqs,
                               initial_clocks={p: rng.randint(0, 6) for p in range(1, n + 1)})
        sim = Simulation(i + 1, cfg)
        sim.start()
        sim.run_steps(5000)
        report = verify_all(sim)
        totals["executions"] += 1
        totals["safety_violations"] += report["safety"] == "VIOLATION"
        totals["liveness_warnings"] += report["liveness"] == "WARNING"
        totals["clock_failures"] += next(p for p in report["panels"] if p["key"] == "clock_consistency")["status"] != "PASS"
        totals["completed_requests"] += sum(1 for r in sim.requests if r.status == "COMPLETED")
        totals["total_requests"] += len(sim.requests)
    return totals
