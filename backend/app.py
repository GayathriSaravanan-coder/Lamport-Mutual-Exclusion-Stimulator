import json
import threading
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db
from engine.scenarios import build_config, list_scenarios
from engine.simulation import Simulation, replay
from explanation.decision_explainer import explain_all
from models.experiment import DelayRule, ExperimentConfig
from verification.invariants import verify_all


@asynccontextmanager
async def lifespan(_app):
    db.init_db()
    yield


app = FastAPI(
    title="Lamport Mutual Exclusion Stimulator",
    lifespan=lifespan,
)

# Frontend CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SIMS: Dict[int, Simulation] = {}
LOCK = threading.RLock()


def get_sim(exp_id: int) -> Simulation:
    with LOCK:
        sim = SIMS.get(exp_id)

        if sim is None:
            row = db.get_experiment_row(exp_id)

            if row is None:
                raise HTTPException(
                    404,
                    f"experiment {exp_id} not found"
                )

            config = ExperimentConfig.from_dict(
                json.loads(row["network_config"])
            )

            sim = replay(
                Simulation(exp_id, config),
                json.loads(row["actions"])
            )

            SIMS[exp_id] = sim

        return sim


def _finish(
    sim: Simulation,
    result: Optional[dict] = None
) -> dict:
    db.persist(sim)

    return {
        "result": result,
        "state": sim.snapshot()
    }


def _guard(fn):
    try:
        return fn()
    except ValueError as e:
        raise HTTPException(400, str(e))


class CreateBody(BaseModel):
    process_count: Optional[int] = None
    scenario: str = "custom"
    network: Optional[dict] = None


class ProcessBody(BaseModel):
    process_id: int


class DelayRuleBody(BaseModel):
    delay: int = 5
    sender: Optional[int] = None
    receiver: Optional[int] = None
    message_type: Optional[str] = None


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "project": "Lamport Mutual Exclusion Stimulator"
    }


@app.get("/api/scenarios")
def scenarios():
    return list_scenarios()


@app.get("/api/experiments")
def experiments():
    return db.list_experiments()


@app.post("/api/experiments")
def create_experiment(body: CreateBody):
    config = _guard(
        lambda: build_config(
            body.scenario,
            body.process_count,
            body.network
        )
    )

    with LOCK:
        exp_id = db.create_experiment(config)
        sim = Simulation(exp_id, config)
        SIMS[exp_id] = sim

        return _finish(sim)


@app.get("/api/experiments/{exp_id}")
def get_experiment(exp_id: int):
    return get_sim(exp_id).snapshot()


@app.get("/api/experiments/{exp_id}/state")
def state(exp_id: int):
    return get_sim(exp_id).snapshot()


@app.post("/api/experiments/{exp_id}/start")
def start(exp_id: int):
    with LOCK:
        sim = get_sim(exp_id)
        sim.start()

        return _finish(sim)


@app.post("/api/experiments/{exp_id}/step")
def step(
    exp_id: int,
    count: int = Query(1, ge=1, le=2000)
):
    with LOCK:
        sim = get_sim(exp_id)

        result = (
            sim.step()
            if count == 1
            else sim.run_steps(count)
        )

        return _finish(sim, result)


@app.post("/api/experiments/{exp_id}/play")
def play(exp_id: int):
    with LOCK:
        sim = get_sim(exp_id)
        sim.play()

        return _finish(sim)


@app.post("/api/experiments/{exp_id}/pause")
def pause(exp_id: int):
    with LOCK:
        sim = get_sim(exp_id)
        sim.pause()

        return _finish(sim)


@app.post("/api/experiments/{exp_id}/reset")
def reset(exp_id: int):
    with LOCK:
        old = get_sim(exp_id)

        sim = Simulation(
            exp_id,
            ExperimentConfig.from_dict(
                old.original_config.to_dict()
            )
        )

        SIMS[exp_id] = sim
        db.clear_history(exp_id)

        return _finish(sim)


@app.post("/api/experiments/{exp_id}/request")
def request(
    exp_id: int,
    body: ProcessBody
):
    with LOCK:
        sim = get_sim(exp_id)

        _guard(
            lambda: sim.request(body.process_id)
        )

        return _finish(sim)


@app.post("/api/experiments/{exp_id}/silence")
def silence(
    exp_id: int,
    body: ProcessBody
):
    with LOCK:
        sim = get_sim(exp_id)

        _guard(
            lambda: sim.silence(body.process_id)
        )

        return _finish(sim)


@app.post("/api/experiments/{exp_id}/resume")
def resume(
    exp_id: int,
    body: ProcessBody
):
    with LOCK:
        sim = get_sim(exp_id)

        _guard(
            lambda: sim.resume(body.process_id)
        )

        return _finish(sim)


@app.post("/api/experiments/{exp_id}/delay-rule")
def delay_rule(
    exp_id: int,
    body: DelayRuleBody
):
    with LOCK:
        sim = get_sim(exp_id)

        rule = DelayRule(
            delay=body.delay,
            sender=body.sender,
            receiver=body.receiver,
            message_type=body.message_type
        )

        if rule.message_type not in (
            None,
            "REQUEST",
            "REPLY",
            "RELEASE"
        ):
            raise HTTPException(
                400,
                "message_type must be REQUEST, REPLY or RELEASE"
            )

        _guard(
            lambda: sim.add_delay_rule(rule)
        )

        return _finish(sim)


@app.post("/api/experiments/{exp_id}/release-delayed")
def release_delayed(exp_id: int):
    with LOCK:
        sim = get_sim(exp_id)
        n = sim.release_delayed()

        return _finish(
            sim,
            {"released": n}
        )


@app.get("/api/experiments/{exp_id}/events")
def events(exp_id: int):
    return [
        e.to_dict()
        for e in get_sim(exp_id).events
    ]


@app.get("/api/experiments/{exp_id}/explanation")
def explanation(
    exp_id: int,
    a: Optional[int] = None,
    b: Optional[int] = None
):
    sim = get_sim(exp_id)

    for x in (a, b):
        if x is not None and x not in sim.processes:
            raise HTTPException(
                400,
                f"unknown process {x}"
            )

    return explain_all(sim, a, b)


@app.get("/api/experiments/{exp_id}/verification")
def verification(exp_id: int):
    return verify_all(get_sim(exp_id))