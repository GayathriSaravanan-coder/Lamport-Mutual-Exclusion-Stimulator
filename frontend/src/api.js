const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function req(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const j = await res.json();
      msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch (_) {}
    throw new Error(msg);
  }
  return res.json();
}

const e = (id) => `/api/experiments/${id}`;

export const api = {
  scenarios: () => req("GET", "/api/scenarios"),
  create: (body) => req("POST", "/api/experiments", body),
  state: (id) => req("GET", `${e(id)}/state`),
  start: (id) => req("POST", `${e(id)}/start`),
  step: (id, count = 1) => req("POST", `${e(id)}/step?count=${count}`),
  play: (id) => req("POST", `${e(id)}/play`),
  pause: (id) => req("POST", `${e(id)}/pause`),
  reset: (id) => req("POST", `${e(id)}/reset`),
  request: (id, pid) => req("POST", `${e(id)}/request`, { process_id: pid }),
  silence: (id, pid) => req("POST", `${e(id)}/silence`, { process_id: pid }),
  resume: (id, pid) => req("POST", `${e(id)}/resume`, { process_id: pid }),
  delayRule: (id, rule) => req("POST", `${e(id)}/delay-rule`, rule),
  releaseDelayed: (id) => req("POST", `${e(id)}/release-delayed`),
  explanation: (id, a, b) =>
    req("GET", `${e(id)}/explanation${a && b ? `?a=${a}&b=${b}` : ""}`),
  verification: (id) => req("GET", `${e(id)}/verification`),
};
