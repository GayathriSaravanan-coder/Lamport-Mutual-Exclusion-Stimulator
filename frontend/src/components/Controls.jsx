import { useState } from "react";

export default function Controls({ scenarios, form, setForm, snap, busy, on }) {
  const [reqPid, setReqPid] = useState(1);
  const [rule, setRule] = useState({
    sender: "",
    receiver: "",
    message_type: "",
    delay: 6,
  });
  const [target, setTarget] = useState(3);

  const sc = scenarios.find((s) => s.id === form.scenario);
  const net = form.network || {};

  const setNet = (patch) =>
    setForm({ ...form, network: { ...net, ...patch } });

  const n = snap ? snap.process_count : form.process_count;
  const pids = Array.from({ length: n }, (_, i) => i + 1);

  const has = !!snap;
  const running = snap?.status === "RUNNING";
  const finished = snap?.status === "COMPLETED";

  const pickScenario = (id) => {
    const s = scenarios.find((x) => x.id === id);

    setForm({
      scenario: id,
      process_count: s.default_processes,
      network: JSON.parse(JSON.stringify(s.network)),
    });
  };

  const num = (v) => (v === "" ? null : Number(v));

  return (
    <div className="card controls-card">
      <h2>Experiment controls</h2>

      {/* Configuration row */}
      <div className="control-row">
        <label className="control-field">
          <span>Scenario</span>
          <select
            value={form.scenario}
            onChange={(e) => pickScenario(e.target.value)}
          >
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>

        <label className="control-field">
          <span>Processes</span>
          <select
            value={form.process_count}
            onChange={(e) =>
              setForm({
                ...form,
                process_count: Number(e.target.value),
              })
            }
          >
            {[3, 4, 5, 6, 7, 8]
              .filter((k) => !sc || k >= sc.min_processes)
              .map((k) => (
                <option key={k}>{k}</option>
              ))}
          </select>
        </label>

        <label className="control-field">
          <span>Network</span>
          <select
            value={net.mode || "NORMAL"}
            onChange={(e) => setNet({ mode: e.target.value })}
          >
            <option value="NORMAL">Normal</option>
            <option value="FIXED">Fixed delay</option>
            <option value="RANDOM">Random delay</option>
            <option value="SELECTED">Selected message delay</option>
          </select>
        </label>

        {net.mode === "FIXED" && (
          <label className="control-field small-field">
            <span>Delay</span>
            <input
              type="number"
              min="1"
              value={net.fixed_delay}
              onChange={(e) =>
                setNet({ fixed_delay: Number(e.target.value) })
              }
            />
          </label>
        )}

        {net.mode === "RANDOM" && (
          <>
            <label className="control-field small-field">
              <span>Min</span>
              <input
                type="number"
                min="1"
                value={net.random_min}
                onChange={(e) =>
                  setNet({ random_min: Number(e.target.value) })
                }
              />
            </label>

            <label className="control-field small-field">
              <span>Max</span>
              <input
                type="number"
                min="1"
                value={net.random_max}
                onChange={(e) =>
                  setNet({ random_max: Number(e.target.value) })
                }
              />
            </label>

            <label className="control-field small-field">
              <span>Seed</span>
              <input
                type="number"
                value={net.seed}
                onChange={(e) =>
                  setNet({ seed: Number(e.target.value) })
                }
              />
            </label>
          </>
        )}

        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={net.fifo !== false}
            onChange={(e) => setNet({ fifo: e.target.checked })}
          />
          <span>FIFO channels</span>
        </label>

        <button
          className="primary create-btn"
          disabled={busy}
          onClick={on.create}
        >
          Create experiment
        </button>
      </div>

      {sc && (
        <div className="hint">
          {sc.description} <b>Expected:</b> {sc.expected}
        </div>
      )}

      {form.network?.selected_delays?.length > 0 && (
        <div className="hint">
          Scenario delay rules:{" "}
          {form.network.selected_delays
            .map(
              (r) =>
                `${r.message_type || "any"} ${
                  r.sender ? "P" + r.sender : "any"
                }→${r.receiver ? "P" + r.receiver : "any"} = ${r.delay}`
            )
            .join("; ")}
          {form.network.silenced_nodes?.length > 0 &&
            ` · Silent: ${form.network.silenced_nodes
              .map((p) => "P" + p)
              .join(", ")}`}
        </div>
      )}

      {form.network?.silenced_nodes?.length > 0 &&
        !form.network?.selected_delays?.length && (
          <div className="hint">
            Silent at start:{" "}
            {form.network.silenced_nodes.map((p) => "P" + p).join(", ")}
          </div>
        )}

      <hr className="control-divider" />

      {/* Execution controls */}
      <div className="control-row action-row">
        <button
          disabled={!has || busy || snap.started}
          onClick={on.start}
        >
          Run Scenario (Start)
        </button>

        <button
          disabled={!has || busy || running}
          onClick={() => on.step(1)}
        >
          Step
        </button>

        <button
          disabled={!has || busy || running || snap.pending_items === 0}
          onClick={() => on.step(500)}
        >
          Run to end
        </button>

        <button
          disabled={!has || busy || running || snap.pending_items === 0}
          onClick={on.play}
        >
          Play
        </button>

        <button disabled={!has || !running} onClick={on.pause}>
          Pause
        </button>

        <button
          className="danger"
          disabled={!has || busy}
          onClick={on.reset}
        >
          Reset
        </button>

        <span className="sep" />

        <label className="inline-field">
          <span>Generate request from</span>
          <select
            value={reqPid}
            onChange={(e) => setReqPid(Number(e.target.value))}
          >
            {pids.map((p) => (
              <option key={p} value={p}>
                P{p}
              </option>
            ))}
          </select>
        </label>

        <button
          disabled={!has || busy}
          onClick={() => on.request(reqPid)}
        >
          Generate Request
        </button>

        <label className="inline-field">
          <span>Speed</span>
          <select
            value={on.speed}
            onChange={(e) => on.setSpeed(Number(e.target.value))}
          >
            <option value={1400}>Slow</option>
            <option value={800}>Normal</option>
            <option value={300}>Fast</option>
          </select>
        </label>
      </div>

      {/* Fault tools */}
      <div className="control-row fault-row">
        <span className="hint fault-title">
          <b>Fault / delay tools:</b>
        </span>

        <label className="inline-field">
          <span>Message</span>
          <select
            value={rule.message_type}
            onChange={(e) =>
              setRule({
                ...rule,
                message_type: e.target.value,
              })
            }
          >
            <option value="">Any msg</option>
            <option>REQUEST</option>
            <option>REPLY</option>
            <option>RELEASE</option>
          </select>
        </label>

        <label className="inline-field">
          <span>From</span>
          <select
            value={rule.sender}
            onChange={(e) =>
              setRule({
                ...rule,
                sender: e.target.value,
              })
            }
          >
            <option value="">Any</option>
            {pids.map((p) => (
              <option key={p} value={p}>
                P{p}
              </option>
            ))}
          </select>
        </label>

        <label className="inline-field">
          <span>To</span>
          <select
            value={rule.receiver}
            onChange={(e) =>
              setRule({
                ...rule,
                receiver: e.target.value,
              })
            }
          >
            <option value="">Any</option>
            {pids.map((p) => (
              <option key={p} value={p}>
                P{p}
              </option>
            ))}
          </select>
        </label>

        <label className="inline-field">
          <span>Delay by</span>
          <input
            type="number"
            min="1"
            value={rule.delay}
            onChange={(e) =>
              setRule({
                ...rule,
                delay: Number(e.target.value),
              })
            }
          />
        </label>

        <button
          disabled={!has || busy}
          onClick={() =>
            on.rule({
              delay: rule.delay,
              sender: num(rule.sender),
              receiver: num(rule.receiver),
              message_type: rule.message_type || null,
            })
          }
        >
          Add delay rule
        </button>

        <button
          disabled={!has || busy}
          onClick={on.releaseDelayed}
        >
          Resume delivery
        </button>

        <span className="sep" />

        <label className="inline-field">
          <span>Node</span>
          <select
            value={target}
            onChange={(e) => setTarget(Number(e.target.value))}
          >
            {pids.map((p) => (
              <option key={p} value={p}>
                P{p}
              </option>
            ))}
          </select>
        </label>

        <button
          disabled={!has || busy}
          onClick={() => on.silence(target)}
        >
          Silence node
        </button>

        <button
          disabled={!has || busy}
          onClick={() => on.resume(target)}
        >
          Resume node
        </button>
      </div>

      {has && (
        <div className="note">
          {snap.last_note}
          {finished ? " — experiment finished." : ""}
        </div>
      )}
    </div>
  );
}