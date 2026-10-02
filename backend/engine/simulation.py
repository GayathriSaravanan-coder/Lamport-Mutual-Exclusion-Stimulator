"""Discrete-event simulation of Lamport's mutual exclusion.

Virtual time is an integer. Three kinds of scheduled items exist:
  TRIGGER_REQUEST(pid)   - the application on process pid wants the critical section
  DELIVER(message_id)    - the network delivers a message
  TRIGGER_RELEASE(pid)   - process pid leaves the critical section
step() executes exactly ONE item (plus any critical-section entry it enables).
"""
import copy
import heapq
from typing import Dict, List, Optional

from engine import lamport
from engine.clock import LamportClock
from engine.scheduler import NetworkSimulator
from models.event import Event
from models.experiment import ExperimentConfig, DelayRule, NORMAL_DELAY
from models.message import Message, REQUEST, REPLY, RELEASE
from models.process import Process, IDLE, WAITING, CRITICAL_SECTION
from models.request import Request, RequestRecord

TRIGGER_REQUEST = "TRIGGER_REQUEST"
TRIGGER_RELEASE = "TRIGGER_RELEASE"
DELIVER = "DELIVER"


class Simulation:
    def __init__(self, exp_id: int, config: ExperimentConfig):
        config.validate()
        self.id = exp_id
        self.config = config
        self.original_config = copy.deepcopy(config)      # what gets stored / replayed
        self.net = NetworkSimulator(copy.deepcopy(config.network))
        self.silenced = set(config.network.silenced_nodes)

        n = config.process_count
        self.processes: Dict[int, Process] = {}
        for pid in range(1, n + 1):
            self.processes[pid] = Process(
                pid=pid,
                others=[q for q in range(1, n + 1) if q != pid],
                clock=LamportClock(config.initial_clocks.get(pid, 0)),
            )

        self.time = 0
        self.step_count = 0
        self._seq = 0
        self._heap: list = []
        self.messages: Dict[int, Message] = {}
        self.events: List[Event] = []
        self.requests: List[RequestRecord] = []
        self.held: list = []
        self.arrival_counter = 0
        self.status = "CREATED"
        self.started = False
        self.actions: List[dict] = []          # replayable action log
        self.last_note = "Experiment created. Press Start to load the scenario requests."

    # ------------------------------------------------------------------ helpers
    def _push(self, time: int, kind: str, payload) -> None:
        self._seq += 1
        heapq.heappush(self._heap, (time, self._seq, kind, payload))

    def _check_pid(self, pid: int) -> None:
        if pid not in self.processes:
            raise ValueError(f"unknown process P{pid}")

    def _log(self, p: Process, etype: str, clock_before: int, related=None,
             message: Optional[Message] = None, detail: str = "") -> Event:
        ev = Event(id=len(self.events) + 1, step=self.step_count, sim_time=self.time,
                   process_id=p.pid, event_type=etype, clock_before=clock_before,
                   logical_timestamp=p.clock.value, state=p.state, related_process=related,
                   message_id=message.id if message else None, detail=detail)
        self.events.append(ev)
        return ev

    def _send(self, p: Process, out: lamport.Outgoing, ev: Event) -> Message:
        delay = self.net.compute_delay(p.pid, out.receiver, out.message_type)
        t = self.net.schedule_time(self.time, p.pid, out.receiver, delay)
        eff = t - self.time
        m = Message(id=len(self.messages) + 1, sender=p.pid, receiver=out.receiver,
                    message_type=out.message_type, timestamp=out.timestamp,
                    request=out.request, sent_at=self.time, deliver_at=t, delay=eff,
                    delayed=eff > NORMAL_DELAY, send_event_id=ev.id)
        self.messages[m.id] = m
        if ev.event_type == "REPLY":
            ev.message_id = m.id
        self._push(t, DELIVER, m.id)
        return m

    def _record_for(self, pid: int, req: Request) -> Optional[RequestRecord]:
        for rec in reversed(self.requests):
            if rec.process_id == pid and rec.timestamp == req.timestamp and rec.status != "COMPLETED":
                return rec
        return None

    # ------------------------------------------------------------------ public actions
    def start(self) -> None:
        if self.started:
            return
        self.started = True
        for t, pid in self.config.scripted_requests:
            self._push(self.time + t, TRIGGER_REQUEST, pid)
        self.actions.append({"a": "start"})
        self.last_note = "Scenario loaded. Press Step or Play."
        if self.status == "CREATED":
            self.status = "PAUSED"
        self._touch_status()

    def request(self, pid: int) -> None:
        self._check_pid(pid)
        self._push(self.time, TRIGGER_REQUEST, pid)
        self.actions.append({"a": "request", "pid": pid})
        self.last_note = f"Application request generated for P{pid}."
        self._touch_status()

    def silence(self, pid: int) -> None:
        self._check_pid(pid)
        self.silenced.add(pid)
        self.actions.append({"a": "silence", "pid": pid})
        self.last_note = f"P{pid} is now silent: it receives, sends and acts on nothing."

    def resume(self, pid: int) -> None:
        self._check_pid(pid)
        self.silenced.discard(pid)
        keep, release = [], []
        for item in sorted(self.held):
            t, seq, kind, payload = item
            target = payload if kind != DELIVER else self.messages[payload].receiver
            (release if target == pid else keep).append(item)
        self.held = keep
        for t, seq, kind, payload in release:          # keep original order (FIFO safe)
            if kind == DELIVER:
                m = self.messages[payload]
                m.delivery_status = "IN_FLIGHT"
                m.deliver_at = self.time
            self._push(self.time, kind, payload)
        self.actions.append({"a": "resume", "pid": pid})
        self.last_note = f"P{pid} resumed; {len(release)} held item(s) are delivered now."
        self._touch_status()

    def add_delay_rule(self, rule: DelayRule) -> None:
        if rule.delay < 1:
            raise ValueError("delay must be >= 1")
        for pid in (rule.sender, rule.receiver):
            if pid is not None:
                self._check_pid(pid)
        self.net.cfg.selected_delays.append(rule)
        self.actions.append({"a": "rule", "rule": rule.to_dict()})
        self.last_note = f"Delay rule added (affects messages sent from now on): {rule.describe()}."

    def release_delayed(self) -> int:
        """'Resume delivery': deliver every currently delayed in-flight message now
        (and earlier messages on the same channel, so FIFO order is preserved)."""
        chans = {(m.sender, m.receiver) for m in self.messages.values()
                 if m.delivery_status == "IN_FLIGHT" and m.delayed}
        new, count = [], 0
        for (t, seq, kind, payload) in self._heap:
            if kind == DELIVER:
                m = self.messages[payload]
                if (m.sender, m.receiver) in chans and t > self.time:
                    t = self.time
                    m.deliver_at = t
                    m.delayed = False
                    count += 1
            new.append((t, seq, kind, payload))
        heapq.heapify(new)
        self._heap = new
        for ch in chans:
            if self.net.channel_last.get(ch, 0) > self.time:
                self.net.channel_last[ch] = self.time
        self.actions.append({"a": "release_delayed"})
        self.last_note = f"Delivery resumed for {count} delayed message(s)."
        return count

    def play(self) -> None:
        if self._heap and self.status in ("PAUSED", "CREATED"):
            self.status = "RUNNING"
        self.actions.append({"a": "play"})

    def pause(self) -> None:
        if self.status == "RUNNING":
            self.status = "PAUSED"
        self.actions.append({"a": "pause"})

    # ------------------------------------------------------------------ stepping
    def step(self) -> dict:
        popped = False
        result = {"progressed": False, "note": "", "time": self.time}
        while self._heap:
            time, seq, kind, payload = heapq.heappop(self._heap)
            popped = True
            self.time = max(self.time, time)
            target = payload if kind != DELIVER else self.messages[payload].receiver
            if target in self.silenced:                       # silent node: hold the item
                self.held.append((time, seq, kind, payload))
                if kind == DELIVER:
                    self.messages[payload].delivery_status = "HELD"
                continue
            self.step_count += 1
            note = self._execute(kind, payload)
            self._auto_enter()
            result.update(progressed=True, note=note, time=self.time)
            break
        if popped:
            self.actions.append({"a": "step"})
        if not result["progressed"]:
            result["note"] = ("Nothing left to do." if not self.held else
                              "Only messages for silent nodes remain (held).")
        self.last_note = result["note"]
        self._touch_status()
        return result

    def run_steps(self, count: int) -> dict:
        last = {"progressed": False, "note": "", "time": self.time}
        done = 0
        for _ in range(count):
            r = self.step()
            if not r["progressed"]:
                last = r
                break
            done += 1
            last = r
        last["steps_run"] = done
        return last

    def _execute(self, kind: str, payload) -> str:
        if kind == TRIGGER_REQUEST:
            return self._do_request(payload)
        if kind == TRIGGER_RELEASE:
            return self._do_release(payload)
        return self._do_deliver(payload)

    def _do_request(self, pid: int) -> str:
        p = self.processes[pid]
        if p.state != IDLE:
            p.backlog += 1
            return f"P{pid} is busy ({p.state}); new application request queued (backlog {p.backlog})."
        before = p.clock.value
        outs = lamport.request_cs(p)
        rec = RequestRecord(id=len(self.requests) + 1, process_id=pid,
                            timestamp=p.my_request.timestamp, requested_at=self.time)
        self.requests.append(rec)
        detail = (f"P{pid} wants the critical section: clock {before}->{p.clock.value}, "
                  f"request {p.my_request.label()} added to its own queue, "
                  f"REQUEST broadcast to {', '.join('P%d' % q for q in p.others)}.")
        ev = self._log(p, "REQUEST", before, detail=detail)
        for o in outs:
            self._send(p, o, ev)
        return detail

    def _do_release(self, pid: int) -> str:
        p = self.processes[pid]
        if p.state != CRITICAL_SECTION:
            return f"P{pid} is not in the critical section; release ignored."
        before = p.clock.value
        req = p.my_request
        rec = self._record_for(pid, req)
        outs = lamport.release_cs(p)
        if rec:
            rec.status = "COMPLETED"
            rec.released_at = self.time
        detail = (f"P{pid} leaves the critical section: clock {before}->{p.clock.value}, "
                  f"request {req.label()} removed, RELEASE broadcast.")
        ev = self._log(p, "RELEASE", before, detail=detail)
        for o in outs:
            self._send(p, o, ev)
        if p.backlog > 0:
            p.backlog -= 1
            self._push(self.time, TRIGGER_REQUEST, pid)
        return detail

    def _do_deliver(self, mid: int) -> str:
        m = self.messages[mid]
        m.delivery_status = "DELIVERED"
        m.delivered_at = self.time
        self.arrival_counter += 1
        m.arrival_index = self.arrival_counter
        p = self.processes[m.receiver]
        before = p.clock.value
        tag = f"{m.message_type} {m.request.label()} from P{m.sender}"
        if m.message_type == REQUEST:
            outs = lamport.receive_request(p, m)
            detail = (f"P{p.pid} received {tag}: clock max({before},{m.timestamp})+1 = {p.clock.value}; "
                      f"queue is now {[r.label() for r in p.queue.items()]}.")
            ev = self._log(p, "RECEIVE_REQUEST", before, related=m.sender, message=m, detail=detail)
            m.receive_event_id = ev.id
            for o in outs:
                rev = self._log(p, "REPLY", p.clock.value, related=o.receiver,
                                detail=f"P{p.pid} sends REPLY (ts={o.timestamp}) to P{o.receiver}.")
                self._send(p, o, rev)
            return detail
        if m.message_type == REPLY:
            lamport.receive_reply(p, m)
            detail = (f"P{p.pid} received {tag}: clock max({before},{m.timestamp})+1 = {p.clock.value}; "
                      f"replies {len(p.replies_received)}/{len(p.others)}.")
            ev = self._log(p, "RECEIVE_REPLY", before, related=m.sender, message=m, detail=detail)
            m.receive_event_id = ev.id
            return detail
        lamport.receive_release(p, m)
        detail = (f"P{p.pid} received {tag}: clock max({before},{m.timestamp})+1 = {p.clock.value}; "
                  f"request removed, queue is now {[r.label() for r in p.queue.items()]}.")
        ev = self._log(p, "RECEIVE_RELEASE", before, related=m.sender, message=m, detail=detail)
        m.receive_event_id = ev.id
        return detail

    def _auto_enter(self) -> None:
        """Local rule: enter the CS as soon as all entry conditions hold."""
        for pid in sorted(self.processes):
            p = self.processes[pid]
            if pid in self.silenced or not lamport.can_enter(p):
                continue
            before = p.clock.value
            lamport.enter_cs(p)
            rec = self._record_for(pid, p.my_request)
            if rec:
                rec.status = "IN_CS"
                rec.entered_at = self.time
            detail = (f"P{pid} enters the critical section: request {p.my_request.label()} is at the head "
                      f"of its queue and all {len(p.others)} REPLYs have arrived.")
            self._log(p, "ENTER_CRITICAL_SECTION", before, detail=detail)
            self._push(self.time + self.config.cs_duration, TRIGGER_RELEASE, pid)

    # ------------------------------------------------------------------ status / queries
    def _touch_status(self) -> None:
        if self._heap:
            if self.status in ("CREATED", "COMPLETED", "STALLED"):
                self.status = "PAUSED"
            return
        if not self.events:
            self.status = "PAUSED" if self.started else "CREATED"
            return
        self.status = "STALLED" if self.unresolved() or self.held else "COMPLETED"

    def in_flight(self) -> List[Message]:
        return [m for m in self.messages.values() if m.delivery_status == "IN_FLIGHT"]

    def held_messages(self) -> List[Message]:
        return [m for m in self.messages.values() if m.delivery_status == "HELD"]

    def cs_holders(self) -> List[int]:
        return [pid for pid, p in self.processes.items() if p.state == CRITICAL_SECTION]

    def waiting(self) -> List[int]:
        return [pid for pid, p in self.processes.items() if p.state == WAITING]

    def unresolved(self) -> List[int]:
        return [pid for pid, p in self.processes.items()
                if p.state != IDLE or p.backlog > 0]

    def is_fault_experiment(self) -> bool:
        return not self.net.cfg.is_normal() or bool(self.silenced)

    def label(self) -> str:
        return "FAULT / DELAY EXPERIMENT" if self.is_fault_experiment() else "NORMAL EXECUTION"

    def snapshot(self) -> dict:
        from explanation.order_view import order_comparison
        return {
            "id": self.id,
            "display_id": f"EXP-{self.id:03d}",
            "status": self.status,
            "label": self.label(),
            "time": self.time,
            "step_count": self.step_count,
            "started": self.started,
            "scenario": self.config.scenario,
            "process_count": self.config.process_count,
            "cs_duration": self.config.cs_duration,
            "network": self.net.cfg.to_dict(),
            "silenced": sorted(self.silenced),
            "pending_items": len(self._heap),
            "held_items": len(self.held),
            "last_note": self.last_note,
            "processes": [self.processes[pid].to_dict() for pid in sorted(self.processes)],
            "messages": [self.messages[i].to_dict() for i in sorted(self.messages)],
            "events": [e.to_dict() for e in self.events],
            "requests": [r.to_dict() for r in self.requests],
            "order": order_comparison(self),
            "cs_holders": self.cs_holders(),
        }


def replay(sim: Simulation, actions: List[dict]) -> Simulation:
    """Rebuild a simulation from its action log (used to restore after a server restart)."""
    for a in actions:
        kind = a["a"]
        if kind == "start":
            sim.start()
        elif kind == "step":
            sim.step()
        elif kind == "request":
            sim.request(a["pid"])
        elif kind == "silence":
            sim.silence(a["pid"])
        elif kind == "resume":
            sim.resume(a["pid"])
        elif kind == "rule":
            sim.add_delay_rule(DelayRule.from_dict(a["rule"]))
        elif kind == "release_delayed":
            sim.release_delayed()
        elif kind == "play":
            sim.play()
        elif kind == "pause":
            sim.pause()
    return sim
