import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import Header from "./components/Header.jsx";
import Controls from "./components/Controls.jsx";
import ProcessCards from "./components/ProcessCards.jsx";
import SpaceTime from "./components/SpaceTime.jsx";
import EventTimeline from "./components/EventTimeline.jsx";
import OrderPanel from "./components/OrderPanel.jsx";
import WhyPanel from "./components/WhyPanel.jsx";
import VerificationPanel from "./components/VerificationPanel.jsx";

function scenarioObjective(scenarioId) {
  const objectives = {
    single_request:
      "Observe the complete Lamport REQUEST → REPLY → critical section → RELEASE cycle for one process.",

    concurrent_requests:
      "Observe how multiple concurrent requests are ordered using Lamport timestamps and process IDs.",

    same_timestamp_tie:
      "Demonstrate deterministic tie-breaking when multiple requests have the same Lamport timestamp.",

    delayed_message:
      "Demonstrate how message delay can affect liveness while preserving mutual exclusion and logical ordering.",

    out_of_order_arrival:
      "Demonstrate that network arrival order can differ from Lamport logical order.",

    multiple_waiting:
      "Observe multiple waiting processes and verify that requests enter the critical section in logical order.",

    high_contention:
      "Observe Lamport mutual exclusion under repeated competing requests from multiple processes.",

    controlled_node_silence:
      "Demonstrate how a silent node can block progress and how recovery resumes the protocol.",
  };

  return (
    objectives[scenarioId] ||
    "Run the experiment and observe Lamport clocks, message ordering, local queues and critical-section access."
  );
}

function scenarioName(scenarioId, scenarios) {
  const found = scenarios.find((s) => s.id === scenarioId);

  return (
    found?.name ||
    found?.title ||
    scenarioId?.replaceAll("_", " ") ||
    "Experiment"
  );
}

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "live", label: "Live State" },
  { id: "spacetime", label: "Space-Time & Timeline" },
  { id: "order", label: "Order & Why" },
  { id: "verify", label: "Verification & Result" },
];

export default function App() {
  const [scenarios, setScenarios] = useState([]);
  const [tab, setTab] = useState("overview");

  const [form, setForm] = useState({
    scenario: "concurrent_requests",
    process_count: 3,
    network: null,
  });

  const [snap, setSnap] = useState(null);
  const [why, setWhy] = useState(null);
  const [ver, setVer] = useState(null);
  const [cmp, setCmp] = useState({ a: null, b: null });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [speed, setSpeed] = useState(800);

  useEffect(() => {
    api
      .scenarios()
      .then((list) => {
        setScenarios(list);

        const s =
          list.find((x) => x.id === "concurrent_requests") || list[0];

        if (s) {
          setForm({
            scenario: s.id,
            process_count: s.default_processes,
            network: JSON.parse(JSON.stringify(s.network)),
          });
        }
      })
      .catch(() =>
        setError(
          "Backend not reachable. Start it with: uvicorn app:app --reload --port 8000"
        )
      );
  }, []);

  const side = useCallback(async (id, c) => {
    const [w, v] = await Promise.all([
      api.explanation(id, c?.a, c?.b),
      api.verification(id),
    ]);

    setWhy(w);
    setVer(v);
  }, []);

  const act = useCallback(
    async (fn, c = cmp) => {
      setError("");
      setBusy(true);

      try {
        const res = await fn();
        const state = res.state || res;

        setSnap(state);
        await side(state.id, c);
      } catch (e) {
        setError(e.message);
      }

      setBusy(false);
    },
    [cmp, side]
  );

  useEffect(() => {
    if (snap?.status !== "RUNNING") return undefined;

    const timer = setTimeout(
      () => act(() => api.step(snap.id)),
      speed
    );

    return () => clearTimeout(timer);
  }, [snap, speed, act]);

  const id = snap?.id;

  const on = {
    speed,
    setSpeed,

    create: () =>
      act(
        () =>
          api.create({
            scenario: form.scenario,
            process_count: form.process_count,
            network: form.network,
          }),
        { a: null, b: null }
      ),

    start: () => act(() => api.start(id)),
    step: (n) => act(() => api.step(id, n)),
    play: () => act(() => api.play(id)),
    pause: () => act(() => api.pause(id)),
    reset: () => act(() => api.reset(id)),
    request: (pid) => act(() => api.request(id, pid)),
    silence: (pid) => act(() => api.silence(id, pid)),
    resume: (pid) => act(() => api.resume(id, pid)),
    rule: (r) => act(() => api.delayRule(id, r)),
    releaseDelayed: () => act(() => api.releaseDelayed(id)),
  };

  const setCompare = (c) => {
    setCmp(c);

    if (id) {
      side(id, c).catch((e) => setError(e.message));
    }
  };

  const objective = useMemo(
    () => scenarioObjective(form.scenario),
    [form.scenario]
  );

  const currentScenario = scenarioName(form.scenario, scenarios);

  const processes = snap?.processes || snap?.nodes || [];

  const processList = Array.isArray(processes)
    ? processes
    : Object.values(processes || {});

  const criticalProcesses = processList.filter(
    (p) =>
      p?.state === "CRITICAL_SECTION" ||
      p?.status === "CRITICAL_SECTION"
  );

  const waitingProcesses = processList.filter(
    (p) =>
      p?.state === "WAITING" ||
      p?.status === "WAITING"
  );

  const eventCount =
    snap?.events?.length ??
    snap?.event_count ??
    snap?.events_count ??
    0;

  const messageCount =
    snap?.messages?.length ??
    snap?.message_count ??
    snap?.messages_count ??
    0;

  const completedRequests =
    snap?.completed_requests ??
    snap?.completed ??
    ver?.completed_requests ??
    null;

  const totalRequests =
    snap?.total_requests ??
    snap?.request_count ??
    ver?.total_requests ??
    null;

  const inFlight =
    snap?.messages_in_flight ??
    snap?.in_flight ??
    snap?.network?.in_flight ??
    null;

  const violations =
    ver?.violations ??
    ver?.safety_violations ??
    0;

  const csOwner =
    snap?.cs_owner ??
    snap?.current_cs_owner ??
    (criticalProcesses.length === 1
      ? criticalProcesses[0]?.id ||
        criticalProcesses[0]?.pid
      : null);

  const executionCompleted =
    snap?.status === "COMPLETED";

  /*
   * STEP DISPLAY FIX
   */
  const rawStep =
    snap?.step ??
    snap?.step_count ??
    snap?.current_step ??
    null;

  const displayStep =
    rawStep === null || (rawStep === 0 && eventCount > 0)
      ? eventCount
      : rawStep;

  const waitingActive = waitingProcesses.length > 0;

  const inFlightActive =
    typeof inFlight === "number"
      ? inFlight > 0
      : inFlight !== null && inFlight !== "—";

  const requestsActive =
    completedRequests !== null &&
    totalRequests !== null &&
    completedRequests < totalRequests;

  const safetyPass = violations === 0;

  const livenessPass =
    executionCompleted &&
    waitingProcesses.length === 0 &&
    (typeof inFlight !== "number" || inFlight === 0);

  let conclusion;

  if (!executionCompleted) {
    conclusion =
      "Execution is still in progress. Continue stepping or run the scenario to completion to evaluate the final safety and liveness state.";
  } else if (safetyPass && livenessPass) {
    conclusion =
      "Safety: PASS · Liveness: PASS. The completed run maintained mutual exclusion and reached completion without outstanding waiting processes or in-flight messages.";
  } else if (!safetyPass) {
    conclusion =
      "Safety: CHECK REQUIRED. The completed run contains one or more recorded verification violations.";
  } else {
    conclusion =
      "Safety: PASS · Liveness: CHECK REQUIRED. Mutual exclusion was preserved, but the final execution state still contains outstanding activity.";
  }

  return (
    <div className="page">
      <Header snap={snap} />

      {error && <div className="error">{error}</div>}

      <Controls
        scenarios={scenarios}
        form={form}
        setForm={setForm}
        snap={snap}
        busy={busy}
        on={on}
      />

      {!snap && (
        <div className="card hint">
          Choose a scenario and press <b>Create experiment</b>. Then
          press <b>Run Scenario (Start)</b> and <b>Step</b>.
        </div>
      )}

      {/* ================= TAB BAR ================= */}
      <div className="page-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`page-tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ================= OVERVIEW TAB ================= */}
      {tab === "overview" && (
        <section className="card objective-card">
          <div className="objective-heading">
            <div>
              <div className="section-kicker">EXPERIMENT OBJECTIVE</div>
              <h2>{currentScenario}</h2>
            </div>
            <span className="objective-tag">DISTRIBUTED SYSTEMS</span>
          </div>

          <p>{objective}</p>

          {!snap && (
            <div className="objective-hint">
              Choose the scenario, create the experiment, then use{" "}
              <b>Run Scenario (Start)</b> and <b>Step</b> to observe
              the distributed execution.
            </div>
          )}
        </section>
      )}

      {/* ================= LIVE STATE TAB ================= */}
      {tab === "live" && (
        <>
          {snap && (
            <section className="execution-summary">
              <div className="summary-title">
                <div>
                  <span className="section-kicker">
                    LIVE EXECUTION SUMMARY
                  </span>
                  <h2>{snap.status || "READY"}</h2>
                </div>

                <div className="summary-exp">
                  {snap.id || "EXP"} · Time {snap.time ?? 0} · Step{" "}
                  {displayStep}
                </div>
              </div>

              <div className="summary-grid">
                <div className="summary-item">
                  <span>PROCESSES</span>
                  <strong>{processList.length || form.process_count}</strong>
                </div>

                <div
                  className={`summary-item ${
                    waitingActive ? "active-waiting" : ""
                  }`}
                >
                  <span>WAITING</span>
                  <strong>{waitingProcesses.length}</strong>
                </div>

                <div className="summary-item">
                  <span>CS OWNER</span>
                  <strong className={csOwner ? "green-value" : ""}>
                    {csOwner || "NONE"}
                  </strong>
                </div>

                <div className="summary-item">
                  <span>EVENTS</span>
                  <strong>{eventCount}</strong>
                </div>

                <div className="summary-item">
                  <span>MESSAGES</span>
                  <strong>{messageCount}</strong>
                </div>

                <div
                  className={`summary-item ${
                    inFlightActive ? "active-network" : ""
                  }`}
                >
                  <span>IN FLIGHT</span>
                  <strong>{inFlight ?? "—"}</strong>
                </div>

                <div
                  className={`summary-item ${
                    requestsActive ? "active-request" : ""
                  }`}
                >
                  <span>REQUESTS</span>
                  <strong>
                    {completedRequests !== null && totalRequests !== null
                      ? `${completedRequests}/${totalRequests}`
                      : "—"}
                  </strong>
                </div>

                <div className="summary-item">
                  <span>VIOLATIONS</span>
                  <strong
                    className={violations > 0 ? "red-value" : "green-value"}
                  >
                    {violations}
                  </strong>
                </div>
              </div>
            </section>
          )}

          <ProcessCards snap={snap} />
        </>
      )}

      {/* ================= SPACE-TIME & TIMELINE TAB ================= */}
      {tab === "spacetime" && (
        <>
          <SpaceTime snap={snap} />
          <EventTimeline snap={snap} />
        </>
      )}

      {/* ================= ORDER & WHY TAB ================= */}
      {tab === "order" && (
        <>
          <OrderPanel snap={snap} />

          <section className="why-highlight">
            <div className="why-highlight-heading">
              <div>
                <span className="section-kicker">EXPLAINABLE DECISION</span>
                <h2>WHY?</h2>
              </div>
              <span className="why-highlight-tag">LAMPORT REASONING</span>
            </div>

            <WhyPanel why={why} snap={snap} cmp={cmp} setCmp={setCompare} />
          </section>
        </>
      )}

      {/* ================= VERIFICATION & RESULT TAB ================= */}
      {tab === "verify" && (
        <>
          <VerificationPanel ver={ver} />

          {snap && ver && (
            <section className="card result-card">
              <div className="result-heading">
                <div>
                  <div className="section-kicker">EXPERIMENT RESULT</div>
                  <h2>
                    {executionCompleted
                      ? "Execution completed"
                      : "Live verification"}
                  </h2>
                </div>

                <span
                  className={`result-badge ${
                    executionCompleted ? "success" : "live"
                  }`}
                >
                  {executionCompleted ? "COMPLETED" : "IN PROGRESS"}
                </span>
              </div>

              <div className="result-checks">
                <div>
                  <span>✓</span>
                  Mutual exclusion is evaluated from the distributed
                  simulation state.
                </div>

                <div>
                  <span>✓</span>
                  Lamport logical ordering uses timestamps and process IDs.
                </div>

                <div>
                  <span>✓</span>
                  REQUEST, REPLY and RELEASE events are represented in the
                  execution trace.
                </div>

                <div>
                  <span>✓</span>
                  Message delays and node faults can be examined using the
                  experiment controls.
                </div>
              </div>

              <div className="result-conclusion">
                <b>Conclusion</b>
                <p>{conclusion}</p>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}