"""Usage:  python run_randomized.py      (prints the randomized test summary)"""
from tests.randomized import run_batch

for label, fifo in (("FIFO channels (algorithm assumption holds)", True),
                    ("NON-FIFO channels (assumption violated)", False)):
    t = run_batch(50, fifo=fifo)
    print(f"\n{label}")
    print(f"  Total executions     : {t['executions']}")
    print(f"  Safety violations    : {t['safety_violations']}")
    print(f"  Liveness warnings    : {t['liveness_warnings']}")
    print(f"  Completed requests   : {t['completed_requests']} / {t['total_requests']}")
    print(f"  Clock check failures : {t['clock_failures']}")
