import { useEffect, useRef, useState } from "react";

export default function EventTimeline({ snap }) {
  const [tab, setTab] = useState("events");
  const [filter, setFilter] = useState(0);
  const box = useRef(null);
  const len = snap ? snap.events.length + snap.messages.length : 0;
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight; }, [len, tab]);
  if (!snap) return null;
  const events = snap.events.filter((e) => !filter || e.process_id === filter);
  const msgs = snap.messages.filter((m) => !filter || m.sender === filter || m.receiver === filter);
  return (
    <div className="card">
      <h2>Message / event timeline</h2>
      <div className="tabs">
        <span className={`tab ${tab === "events" ? "active" : ""}`} onClick={() => setTab("events")}>Events ({snap.events.length})</span>
        <span className={`tab ${tab === "messages" ? "active" : ""}`} onClick={() => setTab("messages")}>Messages ({snap.messages.length})</span>
        <select value={filter} onChange={(e) => setFilter(Number(e.target.value))}>
          <option value={0}>all processes</option>
          {snap.processes.map((p) => <option key={p.pid} value={p.pid}>P{p.pid}</option>)}
        </select>
      </div>
      <div className="tablewrap" ref={box}>
        {tab === "events" ? (
          <table>
            <thead><tr><th>#</th><th>time</th><th>process</th><th>event</th><th>clock</th><th>related</th><th>state after</th><th>what happened</th></tr></thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id} className={e.event_type === "ENTER_CRITICAL_SECTION" ? "cs" : ""}>
                  <td>{e.id}</td><td>{e.sim_time}</td><td>P{e.process_id}</td><td>{e.event_type}</td>
                  <td>{e.clock_before}→{e.logical_timestamp}</td><td>{e.related_process ? "P" + e.related_process : "-"}</td>
                  <td>{e.state}</td><td>{e.detail}</td>
                </tr>))}
              {events.length === 0 && <tr><td colSpan="8" className="hint">No events yet. Press Start, then Step.</td></tr>}
            </tbody>
          </table>
        ) : (
          <table>
            <thead><tr><th>#</th><th>type</th><th>from → to</th><th>ts</th><th>request</th><th>sent</th><th>arrives / arrived</th><th>delay</th><th>arrival #</th><th>status</th></tr></thead>
            <tbody>
              {msgs.map((m) => (
                <tr key={m.id}>
                  <td>{m.id}</td><td>{m.message_type}</td><td>P{m.sender} → P{m.receiver}</td><td>{m.timestamp}</td>
                  <td>({m.request.timestamp},P{m.request.process_id})</td><td>{m.sent_at}</td>
                  <td>{m.delivered_at ?? m.deliver_at}</td><td>{m.delay}</td><td>{m.arrival_index ?? "-"}</td>
                  <td><span className={`pill ${m.delivery_status}`}>{m.delivery_status}</span>{m.delayed && m.delivery_status !== "DELIVERED" ? <span className="pill delayed"> delayed</span> : null}</td>
                </tr>))}
              {msgs.length === 0 && <tr><td colSpan="10" className="hint">No messages yet.</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
