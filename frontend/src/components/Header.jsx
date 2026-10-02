export default function Header({ snap }) {
  return (
    <div className="card header">
      <div>
        <h1>LAMPORT MUTUAL EXCLUSION SIMULATOR</h1>
        <div className="sub">
          An interactive and explainable software-based simulation and experimentation environment for Lamport Mutual Exclusion.
        </div>
      </div>
      <div className="badges">
        {snap ? (
          <>
            <span className="badge">Experiment: {snap.display_id}</span>
            <span className={`badge ${snap.status}`}>Status: {snap.status}</span>
            <span className={`badge ${snap.label.startsWith("FAULT") ? "fault" : "normal"}`}>{snap.label}</span>
            <span className="badge">Time {snap.time} · Step {snap.step_count}</span>
          </>
        ) : (
          <span className="badge">No experiment yet</span>
        )}
      </div>
    </div>
  );
}
