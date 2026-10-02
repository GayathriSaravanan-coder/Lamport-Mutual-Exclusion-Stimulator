import { useState } from "react";

export default function WhyPanel({ why, snap, cmp, setCmp }) {
  const [pick, setPick] = useState(null);
  if (!snap || !why) return null;
  const pid = pick && why.processes.find((p) => p.pid === pick) ? pick : why.focus || 1;
  const ex = why.processes.find((p) => p.pid === pid) || why.processes[0];
  const pids = snap.processes.map((p) => p.pid);
  const a = cmp.a || why.comparison?.a || "";
  const b = cmp.b || why.comparison?.b || "";
  return (
    <div className="card why">
      <h2>Why? — decision explanation</h2>
      <div className="tabs">
        {why.processes.map((p) => (
          <span key={p.pid} className={`tab ${p.pid === pid ? "active" : ""} ${p.state === "CRITICAL_SECTION" ? "cs" : p.state === "WAITING" ? "wait" : ""}`}
            onClick={() => setPick(p.pid)}>P{p.pid} · {p.state === "CRITICAL_SECTION" ? "IN CS" : p.state}</span>))}
      </div>
      <h3>{ex.question}</h3>
      {ex.checks.map((c, i) => (
        <div className="check" key={i}><span className={c.ok ? "ok" : "no"}>{c.ok ? "✓" : "✗"}</span><span>{c.text}</span></div>))}
      <div className="decision">Decision: {ex.decision}</div>

      <div className="cmp">
        <h3>WHY IS ONE REQUEST AHEAD OF ANOTHER?</h3>
        <div className="row" style={{ marginTop: 6 }}>
          <label>P<select value={a} onChange={(e) => setCmp({ ...cmp, a: Number(e.target.value) })}>
            <option value="">-</option>{pids.map((p) => <option key={p} value={p}>{p}</option>)}</select></label>
          <label>vs P<select value={b} onChange={(e) => setCmp({ ...cmp, b: Number(e.target.value) })}>
            <option value="">-</option>{pids.map((p) => <option key={p} value={p}>{p}</option>)}</select></label>
        </div>
        <div>{why.comparison ? why.comparison.text : <span className="hint">Needs two processes with outstanding requests.</span>}</div>
      </div>
    </div>
  );
}
