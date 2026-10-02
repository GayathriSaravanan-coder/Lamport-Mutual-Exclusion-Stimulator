from engine.simulation import Simulation
from engine.scenarios import build_config
from models.experiment import ExperimentConfig, NetworkConfig, DelayRule


def make(scenario="custom", n=None, network=None, exp_id=1):
    return Simulation(exp_id, build_config(scenario, n, network))


def run_all(sim, limit=3000):
    sim.start()
    sim.run_steps(limit)
    return sim


def grants(sim):
    return [e.process_id for e in sim.events if e.event_type == "ENTER_CRITICAL_SECTION"]
