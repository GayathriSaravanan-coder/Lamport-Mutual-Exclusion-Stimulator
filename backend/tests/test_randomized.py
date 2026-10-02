from tests.randomized import run_batch


def test_50_random_executions_with_fifo_channels():
    t = run_batch(50, fifo=True)
    assert t["executions"] == 50
    assert t["safety_violations"] == 0          # holds because FIFO (the algorithm's assumption) is respected
    assert t["liveness_warnings"] == 0
    assert t["clock_failures"] == 0
    assert t["completed_requests"] == t["total_requests"] > 0


def test_random_non_fifo_result_is_reported_not_forced():
    t = run_batch(50, fifo=False)
    # We do NOT assert zero: without FIFO the monitor is allowed (and expected) to find violations.
    assert t["executions"] == 50
    assert t["clock_failures"] == 0
    print("non-FIFO batch:", t)
