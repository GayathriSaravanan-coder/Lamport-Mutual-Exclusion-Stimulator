export default function VerificationPanel({ ver }) {
  if (!ver) return null;
  return (
    <div className="card">
      <h2>Correctness verification (computed from the live simulation state)</h2>
      <div className="vgrid">
        {ver.panels.map((p) => (
          <div key={p.key} className={`vcard ${p.status}`}>
            <h3>{p.title}</h3>
            <div className="status">{p.key === "cs_owner" ? p.summary : p.status.replace("_", " ")}</div>
            {p.key !== "cs_owner" && <div style={{ fontSize: 13 }}>{p.summary}</div>}
            {p.details.length > 0 && <ul>{p.details.map((d, i) => <li key={i}>{d}</li>)}</ul>}
          </div>))}
      </div>
    </div>
  );
}
