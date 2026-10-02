import { useEffect, useRef, useState } from "react";

const ABBR = {
  REQUEST: "REQ",
  RECEIVE_REQUEST: "rcv REQ",
  REPLY: "REP",
  RECEIVE_REPLY: "rcv REP",
  ENTER_CRITICAL_SECTION: "CS",
  RELEASE: "REL",
  RECEIVE_RELEASE: "rcv REL",
};

const MSG = {
  REQUEST: {
    c: "#2563eb",
    d: "",
    m: "aReq",
  },
  REPLY: {
    c: "#60a5fa",
    d: "6 3",
    m: "aRep",
  },
  RELEASE: {
    c: "#1e3a8a",
    d: "2 3",
    m: "aRel",
  },
};

export default function SpaceTime({ snap }) {
  const [sel, setSel] = useState(null);
  const box = useRef(null);

  const events = snap?.events || [];

  useEffect(() => {
    if (box.current) {
      box.current.scrollLeft = box.current.scrollWidth;
    }
  }, [events.length]);

  useEffect(() => {
    setSel(null);
  }, [snap?.id]);

  if (!snap) return null;

  /*
   * Increased vertical lane spacing.
   * This prevents P1/P2/P3 message arrows and labels
   * from visually overlapping.
   */
  const n = snap.process_count;
  const laneH = 100;
  const top = 48;
  const left = 72;
  const dx = 42;

  const idx = {};

  events.forEach((e, i) => {
    idx[e.id] = i;
  });

  const xOf = (i) => left + 24 + i * dx;
  const yOf = (pid) => top + (pid - 1) * laneH;

  const endX = xOf(events.length) + 10;

  const width = Math.max(endX + 80, 760);
  const height = top + (n - 1) * laneH + 70;

  const intervals = [];
  const open = {};

  events.forEach((e, i) => {
    if (e.event_type === "ENTER_CRITICAL_SECTION") {
      open[e.process_id] = i;
    }

    if (
      e.event_type === "RELEASE" &&
      open[e.process_id] !== undefined
    ) {
      intervals.push({
        pid: e.process_id,
        a: open[e.process_id],
        b: i,
      });

      delete open[e.process_id];
    }
  });

  Object.entries(open).forEach(([pid, a]) => {
    intervals.push({
      pid: +pid,
      a,
      b: events.length - 0.3,
      open: true,
    });
  });

  const ticks = [];
  let lastT = null;

  events.forEach((e, i) => {
    if (e.sim_time !== lastT) {
      ticks.push({
        i,
        t: e.sim_time,
      });

      lastT = e.sim_time;
    }
  });

  const detail = () => {
    if (!sel) {
      return (
        <span className="hint">
          Click an event or a message arrow for details.
        </span>
      );
    }

    if (sel.kind === "event") {
      const e = events.find((x) => x.id === sel.id);

      if (!e) return null;

      return (
        <div>
          <b>Event #{e.id}</b> · P{e.process_id} ·{" "}
          {e.event_type} · time {e.sim_time} · clock{" "}
          {e.clock_before}→{e.logical_timestamp}
          {e.related_process
            ? ` · related P${e.related_process}`
            : ""}{" "}
          · state after: {e.state}
          <br />
          {e.detail}
        </div>
      );
    }

    const m = snap.messages.find(
      (x) => x.id === sel.id
    );

    if (!m) return null;

    return (
      <div>
        <b>Message #{m.id}</b> · {m.message_type} P
        {m.sender}→P{m.receiver} · timestamp{" "}
        {m.timestamp} · about request (
        {m.request.timestamp},P{m.request.process_id})
        <br />
        sent at {m.sent_at}, scheduled {m.deliver_at},{" "}
        {m.delivered_at != null
          ? `arrived at ${m.delivered_at} (arrival #${m.arrival_index})`
          : "not arrived"}{" "}
        · delay {m.delay} · status {m.delivery_status}
        {m.delayed ? " · DELAYED" : ""}
      </div>
    );
  };

  return (
    <div className="card spacetime-card">
      <h2>
        Space-time diagram (generated from the real event log)
      </h2>

      <div className="legend spacetime-legend">
        <span className="legend-item">
          <i style={{ borderColor: "#2563eb" }} />
          REQUEST
        </span>

        <span className="legend-item">
          <i
            style={{
              borderColor: "#60a5fa",
              borderTopStyle: "dashed",
            }}
          />
          REPLY
        </span>

        <span className="legend-item">
          <i
            style={{
              borderColor: "#1e3a8a",
              borderTopStyle: "dotted",
            }}
          />
          RELEASE
        </span>

        <span className="legend-item">
          <i style={{ borderColor: "#d97706" }} />
          in flight / delayed
        </span>

        <span className="legend-item">
          <i style={{ borderColor: "#dc2626" }} />
          held (silent node)
        </span>

        <span className="legend-item critical-legend">
          ■ critical section
        </span>

        <span className="legend-item">
          number above a dot = Lamport clock after the event
        </span>
      </div>

      <div className="spacetime-scroll" ref={box}>
        <svg
          width={width}
          height={height}
          className="spacetime-svg"
        >
          <defs>
            {[
              ["aReq", "#2563eb"],
              ["aRep", "#60a5fa"],
              ["aRel", "#1e3a8a"],
              ["aWarn", "#d97706"],
              ["aHeld", "#dc2626"],
            ].map(([id, c]) => (
              <marker
                key={id}
                id={id}
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path
                  d="M0,0 L10,5 L0,10 z"
                  fill={c}
                />
              </marker>
            ))}
          </defs>

          {ticks.map((t) => (
            <text
              key={t.i}
              x={xOf(t.i) - 6}
              y={18}
              fontSize="10"
              fill="#94a3b8"
            >
              t={t.t}
            </text>
          ))}

          {snap.processes.map((p) => (
            <g key={p.pid}>
              <line
                x1={left - 6}
                x2={width - 10}
                y1={yOf(p.pid)}
                y2={yOf(p.pid)}
                stroke={
                  snap.silenced.includes(p.pid)
                    ? "#dc2626"
                    : "#cbd5e1"
                }
                strokeWidth="2"
                strokeDasharray={
                  snap.silenced.includes(p.pid)
                    ? "6 4"
                    : ""
                }
              />

              <text
                x={14}
                y={yOf(p.pid) + 5}
                fontSize="15"
                fontWeight="700"
                fill="#0f172a"
              >
                P{p.pid}
              </text>
            </g>
          ))}

          {intervals.map((iv, k) => (
            <rect
              key={k}
              x={xOf(iv.a) - 8}
              y={yOf(iv.pid) - 11}
              width={(iv.b - iv.a) * dx + 16}
              height={22}
              rx="4"
              fill="#dcfce7"
              stroke="#16a34a"
              opacity="0.9"
            />
          ))}

          {snap.messages.map((m) => {
            const s = MSG[m.message_type];

            const si = idx[m.send_event_id];

            if (si === undefined) return null;

            const ri = m.receive_event_id
              ? idx[m.receive_event_id]
              : undefined;

            const x1 = xOf(si);
            const y1 = yOf(m.sender);
            const y2 = yOf(m.receiver);

            const inflight = ri === undefined;
            const held =
              m.delivery_status === "HELD";

            const x2 = inflight
              ? endX
              : xOf(ri);

            const color = held
              ? "#dc2626"
              : inflight
              ? "#d97706"
              : s.c;

            const marker = held
              ? "aHeld"
              : inflight
              ? "aWarn"
              : s.m;

            const selected =
              sel &&
              sel.kind === "message" &&
              sel.id === m.id;

            return (
              <g
                key={m.id}
                onClick={() =>
                  setSel({
                    kind: "message",
                    id: m.id,
                  })
                }
                style={{ cursor: "pointer" }}
              >
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="transparent"
                  strokeWidth="12"
                />

                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={color}
                  strokeWidth={selected ? 3 : 1.4}
                  strokeDasharray={
                    inflight ? "3 3" : s.d
                  }
                  markerEnd={`url(#${marker})`}
                  opacity={selected ? 1 : 0.85}
                />
              </g>
            );
          })}

          {events.map((e, i) => {
            const cx = xOf(i);
            const cy = yOf(e.process_id);

            const recv =
              e.event_type.startsWith("RECEIVE");

            const isCS =
              e.event_type ===
              "ENTER_CRITICAL_SECTION";

            const selected =
              sel &&
              sel.kind === "event" &&
              sel.id === e.id;

            const color = isCS
              ? "#16a34a"
              : e.event_type.includes("RELEASE")
              ? "#1e3a8a"
              : e.event_type.includes("REPLY")
              ? "#60a5fa"
              : "#2563eb";

            return (
              <g
                key={e.id}
                onClick={() =>
                  setSel({
                    kind: "event",
                    id: e.id,
                  })
                }
                style={{ cursor: "pointer" }}
              >
                <circle
                  cx={cx}
                  cy={cy}
                  r={selected ? 8 : 6}
                  fill={recv ? "#fff" : color}
                  stroke={color}
                  strokeWidth="2"
                />

                <text
                  x={cx}
                  y={cy - 13}
                  fontSize="10"
                  textAnchor="middle"
                  fill="#2563eb"
                  fontWeight="700"
                >
                  {e.logical_timestamp}
                </text>

                <text
                  x={cx}
                  y={cy + 20}
                  fontSize="8.5"
                  textAnchor="middle"
                  fill="#475569"
                >
                  {ABBR[e.event_type]}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="detail">{detail()}</div>
    </div>
  );
}