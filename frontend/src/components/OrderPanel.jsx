const lab = (r) => `(${r.timestamp},P${r.process_id})`;

export default function OrderPanel({ snap }) {
  if (!snap) return null;
  const o = snap.order;
  return (
    <div className="card">
      <h2>Logical order vs arrival order</h2>
      <div className="two">
        <div>
          <h3 style={{ fontSize: 13, marginBottom: 6 }}>LOGICAL ORDER — sorted by (timestamp, process_id)</h3>
          {o.per_process.map((p) => (
            <div key={p.pid} className={`orderbox ${p.differs ? "differs" : ""}`}>
              <b>P{p.pid}</b>: {p.logical_order.length ? p.logical_order.map((r, i) => <span className="chip" key={i}>{i + 1}. {lab(r)}</span>) : <span className="hint">no requests seen</span>}
            </div>))}
        </div>
        <div>
          <h3 style={{ fontSize: 13, marginBottom: 6 }}>ARRIVAL ORDER — as delivered by the simulated network</h3>
          {o.per_process.map((p) => (
            <div key={p.pid} className={`orderbox ${p.differs ? "differs" : ""}`}>
              <b>P{p.pid}</b>: {p.arrival_order.length ? p.arrival_order.map((r, i) => <span className="chip" key={i}>{i + 1}. {lab(r)}</span>) : <span className="hint">no requests seen</span>}
              {p.differs && <b style={{ color: "#d97706" }}> ≠ logical</b>}
            </div>))}
        </div>
      </div>
      {o.notes.map((n, i) => <div key={i} className="note" style={{ marginTop: 6 }}>{n}</div>)}
      <div className="hint" style={{ marginTop: 8 }}>{o.explanation}</div>
      <div className="hint" style={{ marginTop: 4 }}>
        All requests in logical order: {o.logical_all.map(lab).join(" < ") || "none"} ·
        Critical-section grants so far: {o.grant_order.map((g) => "P" + g.pid).join(" → ") || "none"}
      </div>
    </div>
  );
}
