export default function ProcessCards({ snap }) {
  if (!snap) return null;

  return (
    <div className="card process-card-section">
      <h2>Simulated processes</h2>

      <div className="cards process-grid">
        {snap.processes.map((p) => {
          const silent = snap.silenced.includes(p.pid);

          return (
            <div
              key={p.pid}
              className={`pcard ${p.state} ${
                silent ? "silent" : ""
              }`}
            >
              <div className="process-header">
                <h3>P{p.pid}</h3>

                <span className="st">
                  {p.state}
                  {silent ? " · SILENT" : ""}
                </span>
              </div>

              <div className="process-info">
                <div className="kv">
                  <span>Clock:</span>
                  <span className="clock">{p.clock}</span>
                </div>

                <div className="kv queue-row">
                  <span>Queue:</span>

                  <div className="queue-items">
                    {p.queue.length === 0 ? (
                      <span className="empty-value">[ empty ]</span>
                    ) : (
                      p.queue.map((r) => (
                        <span
                          key={`${r.timestamp}-${r.process_id}`}
                          className={`qitem ${
                            p.my_request &&
                            p.my_request.process_id ===
                              r.process_id &&
                            p.my_request.timestamp ===
                              r.timestamp
                              ? "mine"
                              : ""
                          }`}
                        >
                          P{r.process_id}@{r.timestamp}
                        </span>
                      ))
                    )}
                  </div>
                </div>

                <div className="kv">
                  <span>Replies:</span>

                  <span>
                    {p.replies_received.length}/
                    {p.replies_needed}

                    {p.state === "WAITING" &&
                      p.replies_received.length > 0 && (
                        <span className="reply-detail">
                          {" "}
                          (from{" "}
                          {p.replies_received
                            .map((x) => "P" + x)
                            .join(", ")}
                          )
                        </span>
                      )}
                  </span>
                </div>

                {p.my_request && (
                  <div className="kv">
                    <span>Request:</span>
                    <span>
                      ({p.my_request.timestamp}, P
                      {p.my_request.process_id})
                    </span>
                  </div>
                )}

                {p.backlog > 0 && (
                  <div className="kv">
                    <span>App requests queued:</span>
                    <span>{p.backlog}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}