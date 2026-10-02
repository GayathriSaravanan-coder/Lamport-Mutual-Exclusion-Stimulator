import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from database import db

_tmp = tempfile.mkdtemp()
db.configure(os.path.join(_tmp, "test.db"))

import app as app_module  # noqa: E402


@pytest.fixture()
def client():
    db.init_db()
    with TestClient(app_module.app) as c:
        yield c


def test_full_api_flow_and_persistence(client):
    r = client.post("/api/experiments", json={"scenario": "concurrent_requests", "process_count": 3})
    assert r.status_code == 200
    exp = r.json()["state"]["id"]
    assert client.post(f"/api/experiments/{exp}/start").status_code == 200
    for _ in range(12):
        client.post(f"/api/experiments/{exp}/step")
    state = client.get(f"/api/experiments/{exp}/state").json()
    assert state["events"] and state["messages"]
    ver = client.get(f"/api/experiments/{exp}/verification").json()
    assert {p["key"] for p in ver["panels"]} >= {"mutual_exclusion", "liveness", "cs_owner"}
    assert ver["safety"] == "PASS"
    why = client.get(f"/api/experiments/{exp}/explanation").json()
    assert len(why["processes"]) == 3
    assert client.get(f"/api/experiments/{exp}/events").json()
    assert db.count_rows("events", exp) == len(state["events"])
    assert db.count_rows("messages", exp) == len(state["messages"])


def test_restore_after_restart(client):
    exp = client.post("/api/experiments", json={"scenario": "delayed_message"}).json()["state"]["id"]
    client.post(f"/api/experiments/{exp}/start")
    client.post(f"/api/experiments/{exp}/step?count=7")
    before = client.get(f"/api/experiments/{exp}/state").json()
    app_module.SIMS.clear()                                  # simulate server restart
    after = client.get(f"/api/experiments/{exp}/state").json()
    assert [e["detail"] for e in before["events"]] == [e["detail"] for e in after["events"]]
    assert before["time"] == after["time"]


def test_reset_and_errors(client):
    exp = client.post("/api/experiments", json={"scenario": "single_request"}).json()["state"]["id"]
    client.post(f"/api/experiments/{exp}/start")
    client.post(f"/api/experiments/{exp}/step?count=50")
    assert client.post(f"/api/experiments/{exp}/reset").json()["state"]["events"] == []
    assert db.count_rows("events", exp) == 0
    assert client.post("/api/experiments", json={"scenario": "nope"}).status_code == 400
    assert client.post("/api/experiments", json={"scenario": "custom", "process_count": 9}).status_code == 400
    assert client.post(f"/api/experiments/{exp}/request", json={"process_id": 99}).status_code == 400
    assert client.get("/api/experiments/999999/state").status_code == 404


def test_manual_request_silence_and_rule(client):
    exp = client.post("/api/experiments", json={"scenario": "custom", "process_count": 4}).json()["state"]["id"]
    client.post(f"/api/experiments/{exp}/silence", json={"process_id": 4})
    client.post(f"/api/experiments/{exp}/request", json={"process_id": 1})
    st = client.post(f"/api/experiments/{exp}/step?count=100").json()["state"]
    assert st["status"] == "STALLED" and st["label"] == "FAULT / DELAY EXPERIMENT"
    ver = client.get(f"/api/experiments/{exp}/verification").json()
    assert ver["liveness"] == "WARNING"
    st = client.post(f"/api/experiments/{exp}/resume", json={"process_id": 4}).json()["state"]
    st = client.post(f"/api/experiments/{exp}/step?count=100").json()["state"]
    assert st["status"] == "COMPLETED"
    r = client.post(f"/api/experiments/{exp}/delay-rule", json={"delay": 5, "message_type": "REPLY"})
    assert r.status_code == 200
