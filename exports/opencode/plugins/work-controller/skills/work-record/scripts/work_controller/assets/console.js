"use strict";

const state = {
  overview: { runs: [], maps: [] },
  selectedRun: "",
  selectedMap: "",
  run: null,
  map: null,
  source: null,
  paused: false,
  lastSeq: 0,
  runRequest: 0,
  mapRequest: 0,
  logRequest: 0,
  refreshTimer: null,
  overviewTimer: null,
  logAttempt: "",
  logStream: "stdout",
  logSignature: "",
};

const byId = (id) => document.getElementById(id);

let volatileToken = "";

function bootstrapToken() {
  const queryToken = new URLSearchParams(window.location.search).get("token");
  const fragmentToken = new URLSearchParams(window.location.hash.slice(1)).get("token");
  const supplied = fragmentToken || queryToken;
  if (supplied) {
    volatileToken = supplied;
    try {
      window.sessionStorage.setItem("process-controller-token", supplied);
    } catch {
      // The in-memory token remains available when storage is disabled.
    }
    window.history.replaceState(null, "", window.location.pathname);
  }
  try {
    return window.sessionStorage.getItem("process-controller-token") || volatileToken;
  } catch {
    return volatileToken;
  }
}

bootstrapToken();

function element(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined && text !== null) item.textContent = String(text);
  return item;
}

function code(value) {
  return element("code", "", value);
}

function statusBadge(status) {
  const value = status || "unknown";
  const success = new Set(["complete", "succeeded", "delivered", "admitted", "closed"]);
  const danger = new Set(["failed", "stopped", "blocked", "unknown"]);
  const warning = new Set(["pending", "in_progress", "completing"]);
  const info = new Set(["reserved", "running"]);
  let tone = "";
  if (success.has(value)) tone = " status-success";
  else if (danger.has(value)) tone = " status-danger";
  else if (warning.has(value)) tone = " status-warning";
  else if (info.has(value)) tone = " status-info";
  return element("span", `status-badge${tone}`, value.replaceAll("_", " "));
}

function appendCell(row, value, className = "") {
  const cell = element("td", className);
  if (value === null || value === undefined || value === "") {
    cell.textContent = "—";
    cell.classList.add("muted-cell");
  } else if (value instanceof Node) {
    cell.append(value);
  } else {
    cell.textContent = String(value);
  }
  row.append(cell);
  return cell;
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
}

function showError(error) {
  const banner = byId("error-banner");
  banner.textContent = `Request failed: ${error.message || error}`;
  banner.hidden = false;
}

function clearError() {
  byId("error-banner").hidden = true;
}

async function api(path) {
  const token = bootstrapToken();
  const response = await fetch(path, {
    method: "GET",
    cache: "no-store",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(token ? { "X-Process-Controller-Token": token } : {}),
    },
  });
  const text = await response.text();
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      throw new Error(`invalid JSON response (HTTP ${response.status})`);
    }
  }
  if (!response.ok) {
    throw new Error(payload?.error || `HTTP ${response.status}`);
  }
  return payload;
}

function setConnection(mode, label) {
  byId("connection-status").className = `connection-status is-${mode}`;
  byId("connection-label").textContent = label;
}

function fillOverviewSelect(id, items, selected, label) {
  const select = byId(id);
  if (!items.length) {
    select.replaceChildren(element("option", "", `No ${label} available`));
    select.disabled = true;
    return;
  }
  const options = items.map((item) => {
    const option = element("option", "", item.label);
    option.value = item.id;
    return option;
  });
  select.replaceChildren(...options);
  select.value = selected;
  select.disabled = false;
}

function renderOverview() {
  const runs = state.overview.runs.map((run) => ({
    id: run.id,
    label: `${run.id} · ${run.succeeded_jobs}/${run.total_jobs} jobs`,
  }));
  const maps = state.overview.maps.map((map) => ({
    id: map.id,
    label: `${map.id} · ${map.closed_tickets}/${map.total_tickets} closed`,
  }));
  fillOverviewSelect("run-select", runs, state.selectedRun, "runs");
  fillOverviewSelect("map-select", maps, state.selectedMap, "decision maps");
  byId("run-count").textContent = String(runs.length);
  byId("map-count").textContent = String(maps.length);
}

async function refreshOverview() {
  const data = await api("/api/overview");
  const previousRun = state.selectedRun;
  const previousMap = state.selectedMap;
  state.overview = data;
  if (!data.runs.some((run) => run.id === state.selectedRun)) {
    state.selectedRun = data.runs[0]?.id || "";
  }
  if (!data.maps.some((map) => map.id === state.selectedMap)) {
    state.selectedMap = data.maps[0]?.id || "";
  }
  renderOverview();
  return {
    runChanged: previousRun !== state.selectedRun,
    mapChanged: previousMap !== state.selectedMap,
  };
}

function closeStream() {
  if (state.source) {
    state.source.close();
    state.source = null;
  }
}

function clearRun() {
  closeStream();
  state.run = null;
  state.lastSeq = 0;
  state.logAttempt = "";
  state.logSignature = "";
  state.logRequest += 1;
  byId("run-content").hidden = true;
  byId("no-run").hidden = false;
  byId("no-run").querySelector(".empty-panel-title").textContent = "No runs available";
  byId("no-run").lastElementChild.textContent = "Start a run with the engine to inspect it here.";
  byId("run-title").textContent = "Console overview";
  byId("run-meta").textContent = "The local store contains no runs.";
  byId("pause-button").disabled = true;
  byId("log-text").textContent = "";
  setConnection("idle", "Updates idle");
}

function renderJobs(jobs) {
  const body = byId("jobs-body");
  const rows = jobs.map((job) => {
    const row = document.createElement("tr");
    appendCell(row, code(job.id));
    appendCell(row, job.type);
    appendCell(row, job.summary);
    appendCell(row, statusBadge(job.status));
    appendCell(row, `${job.attempts} / ${job.max_attempts}`);
    return row;
  });
  body.replaceChildren(...rows);
  byId("jobs-empty").hidden = jobs.length > 0;
  body.closest(".table-wrap").hidden = jobs.length === 0;
}

function renderAttempts(attempts) {
  const body = byId("attempts-body");
  const rows = attempts.map((attempt) => {
    const row = document.createElement("tr");
    appendCell(row, code(`${attempt.job_id} #${attempt.number}`)).title = attempt.id;
    appendCell(row, statusBadge(attempt.status));
    appendCell(row, attempt.holder);
    appendCell(row, formatDate(attempt.started_at));
    appendCell(row, formatDate(attempt.ended_at));
    appendCell(row, attempt.error || attempt.commit_sha || "");
    return row;
  });
  body.replaceChildren(...rows);
  byId("attempts-empty").hidden = attempts.length > 0;
  body.closest(".table-wrap").hidden = attempts.length === 0;
}

function renderArtifacts(artifacts) {
  const body = byId("artifacts-body");
  const rows = artifacts.map((artifact) => {
    const row = document.createElement("tr");
    appendCell(row, code(artifact.name));
    appendCell(row, artifact.version);
    appendCell(row, artifact.type);
    appendCell(row, code(artifact.digest));
    appendCell(row, formatBytes(artifact.size));
    appendCell(row, artifact.producer_job || "");
    appendCell(row, statusBadge(artifact.status));
    return row;
  });
  body.replaceChildren(...rows);
  byId("artifacts-empty").hidden = artifacts.length > 0;
  body.closest(".table-wrap").hidden = artifacts.length === 0;
}

function renderEvents(events) {
  const body = byId("events-body");
  const rows = events.map((event) => {
    const row = document.createElement("tr");
    appendCell(row, code(event.seq));
    appendCell(row, formatDate(event.created_at));
    appendCell(row, event.kind);
    appendCell(row, [event.job_id, event.attempt_id].filter(Boolean).join(" · "));
    appendCell(row, code(JSON.stringify(event.payload)));
    return row;
  });
  body.replaceChildren(...rows);
  byId("events-empty").hidden = events.length > 0;
  body.closest(".table-wrap").hidden = events.length === 0;
}

function renderLogAttempts() {
  const jobs = new Map(state.run.jobs.map((job) => [job.id, job.type]));
  const attempts = state.run.attempts.filter((attempt) => jobs.get(attempt.job_id) === "command");
  const signature = JSON.stringify(attempts.map((attempt) => [attempt.id, attempt.status]));
  const previous = state.logAttempt;
  if (signature !== state.logSignature) {
    const select = byId("attempt-select");
    if (!attempts.some((attempt) => attempt.id === state.logAttempt)) {
      state.logAttempt = attempts[0]?.id || "";
    }
    if (attempts.length) {
      const options = attempts.map((attempt) => {
        const option = element(
          "option",
          "",
          `${attempt.job_id} #${attempt.number} · ${attempt.status}`,
        );
        option.value = attempt.id;
        return option;
      });
      select.replaceChildren(...options);
      select.value = state.logAttempt;
    } else {
      select.replaceChildren(element("option", "", "No command attempts"));
    }
    state.logSignature = signature;
  }
  const enabled = attempts.length > 0;
  byId("attempt-select").disabled = !enabled;
  byId("stream-select").disabled = !enabled;
  byId("log-refresh").disabled = !enabled;
  if (!enabled) {
    state.logRequest += 1;
    byId("log-text").textContent = "";
    byId("log-meta").textContent = "No command attempts are available for log output.";
  }
  return previous !== state.logAttempt;
}

function renderRun() {
  if (!state.run) {
    clearRun();
    return false;
  }
  const run = state.run;
  const status = run.status;
  const jobs = run.jobs;
  const counts = status.jobs;
  const succeeded = counts.succeeded || 0;
  const active = (counts.reserved || 0) + (counts.running || 0);
  const attention = (counts.failed || 0) + (counts.blocked || 0);

  byId("no-run").hidden = true;
  byId("run-content").hidden = false;
  byId("pause-button").disabled = false;
  byId("run-title").textContent = status.id;
  byId("run-meta").textContent = [
    `Revision ${status.revision}`,
    status.outcome || "No final outcome",
    `Definition ${status.definition_digest.slice(0, 16)}…`,
  ].join(" · ");
  byId("run-status").replaceChildren(statusBadge(status.status));
  byId("job-progress").max = Math.max(1, jobs.length);
  byId("job-progress").value = succeeded;
  byId("job-progress").setAttribute("aria-label", `${succeeded} of ${jobs.length} jobs succeeded`);
  byId("progress-text").textContent = `${succeeded} / ${jobs.length} succeeded`;
  byId("stat-total").textContent = String(jobs.length);
  byId("stat-succeeded").textContent = String(succeeded);
  byId("stat-active").textContent = String(active);
  byId("stat-attention").textContent = String(attention);

  const frontier = run.frontier.map((job) => element("span", "chip", `${job.id} · ${job.type}`));
  byId("frontier-list").replaceChildren(...frontier);
  byId("frontier-empty").hidden = frontier.length > 0;

  renderJobs(jobs);
  renderAttempts(run.attempts);
  renderArtifacts(run.artifacts);
  renderEvents(run.events);
  return renderLogAttempts();
}

async function loadLog() {
  const request = ++state.logRequest;
  const attempt = state.logAttempt;
  const stream = state.logStream;
  if (!attempt || !state.run) return;
  byId("log-meta").textContent = `Loading ${stream} tail…`;
  try {
    const data = await api(
      `/api/attempt/${encodeURIComponent(attempt)}/log?stream=${encodeURIComponent(stream)}&max_bytes=65536`,
    );
    if (request !== state.logRequest || attempt !== state.logAttempt || stream !== state.logStream) return;
    byId("log-text").textContent = data.text || "";
    if (!data.available) {
      byId("log-meta").textContent = `No ${stream} file is available for this attempt.`;
    } else {
      const scope = data.truncated ? "showing the final 64 KiB" : "complete stream";
      byId("log-meta").textContent = `${formatBytes(data.size)} on disk · ${scope} · UTF-8 with replacement for invalid bytes`;
    }
  } catch (error) {
    if (request !== state.logRequest) return;
    byId("log-meta").textContent = "The log could not be loaded.";
    showError(error);
  }
}

async function loadRun({ reconnect = true } = {}) {
  const runId = state.selectedRun;
  if (!runId) {
    state.runRequest += 1;
    clearRun();
    return;
  }
  if (reconnect) {
    closeStream();
    state.lastSeq = 0;
    setConnection("pending", "Loading run…");
  }
  const request = ++state.runRequest;
  try {
    const data = await api(`/api/run/${encodeURIComponent(runId)}`);
    if (request !== state.runRequest || runId !== state.selectedRun) return;
    state.run = data;
    const latestSeq = data.events.reduce((latest, event) => Math.max(latest, event.seq), 0);
    state.lastSeq = Math.max(state.lastSeq, latestSeq);
    const logSelectionChanged = renderRun();
    if (reconnect || logSelectionChanged) await loadLog();
    if (reconnect && !state.paused) connectStream();
    else if (state.paused) setConnection("paused", "Updates paused");
  } catch (error) {
    if (request !== state.runRequest) return;
    showError(error);
    if (!state.paused) setConnection("error", "Run unavailable");
  }
}

function clearMap() {
  state.map = null;
  byId("map-content").hidden = true;
  byId("no-map").hidden = false;
  byId("no-map").textContent = "No decision maps are available.";
  byId("map-heading").textContent = "Tickets";
  byId("map-status").replaceChildren();
  byId("map-meta").textContent = "The local store contains no decision maps.";
}

function renderMap() {
  if (!state.map) {
    clearMap();
    return;
  }
  const map = state.map;
  const tickets = map.tickets;
  const closed = tickets.filter((ticket) => ticket.status === "closed").length;
  byId("map-content").hidden = false;
  byId("no-map").hidden = true;
  byId("map-heading").textContent = map.status.id;
  byId("map-status").replaceChildren(statusBadge(map.status.status));
  byId("map-meta").textContent = `${closed} / ${tickets.length} tickets closed`;
  byId("map-destination").textContent = map.status.destination;
  byId("map-next").textContent = map.status.next
    ? `${map.status.next.id} · ${map.status.next.kind}`
    : "No open ticket is currently eligible";
  const rows = tickets.map((ticket) => {
    const row = document.createElement("tr");
    appendCell(row, code(ticket.id));
    appendCell(row, ticket.kind);
    appendCell(row, ticket.summary);
    appendCell(row, statusBadge(ticket.status));
    appendCell(row, ticket.holder);
    appendCell(row, ticket.blocked_by.join(", "));
    appendCell(row, ticket.run_id ? code(ticket.run_id) : "");
    return row;
  });
  byId("tickets-body").replaceChildren(...rows);
  byId("tickets-empty").hidden = tickets.length > 0;
  byId("tickets-body").closest(".table-wrap").hidden = tickets.length === 0;
}

async function loadMap() {
  const mapId = state.selectedMap;
  if (!mapId) {
    state.mapRequest += 1;
    clearMap();
    return;
  }
  const request = ++state.mapRequest;
  try {
    const data = await api(`/api/map/${encodeURIComponent(mapId)}`);
    if (request !== state.mapRequest || mapId !== state.selectedMap) return;
    state.map = data;
    renderMap();
  } catch (error) {
    if (request === state.mapRequest) showError(error);
  }
}

function scheduleRunRefresh() {
  clearTimeout(state.refreshTimer);
  state.refreshTimer = setTimeout(() => loadRun({ reconnect: false }), 180);
}

function scheduleOverviewRefresh() {
  clearTimeout(state.overviewTimer);
  state.overviewTimer = setTimeout(async () => {
    try {
      const changed = await refreshOverview();
      if (changed.runChanged) await loadRun({ reconnect: true });
      if (changed.mapChanged) await loadMap();
    } catch (error) {
      showError(error);
    }
  }, 700);
}

function connectStream() {
  closeStream();
  if (state.paused || !state.selectedRun) return;
  if (typeof EventSource === "undefined") {
    setConnection("error", "SSE unsupported");
    return;
  }
  const runId = state.selectedRun;
  const params = new URLSearchParams({ run_id: runId, after: String(state.lastSeq) });
  const token = bootstrapToken();
  if (token) params.set("token", token);
  const source = new EventSource(`/api/events/stream?${params.toString()}`);
  state.source = source;
  setConnection("pending", "Connecting…");

  source.onopen = () => {
    if (state.source === source) setConnection("live", "Live updates");
  };
  source.addEventListener("ready", () => {
    if (state.source === source) setConnection("live", "Live updates");
  });
  source.addEventListener("update", (message) => {
    if (state.source !== source || runId !== state.selectedRun) return;
    try {
      const event = JSON.parse(message.data);
      state.lastSeq = Math.max(state.lastSeq, Number(event.seq) || 0);
      setConnection("live", "Live updates");
      scheduleRunRefresh();
      scheduleOverviewRefresh();
    } catch (error) {
      showError(error);
    }
  });
  source.addEventListener("stream-error", () => {
    if (state.source === source) setConnection("error", "Stream interrupted");
  });
  source.onerror = () => {
    if (state.source === source && !state.paused) setConnection("pending", "Reconnecting…");
  };
}

async function refreshAll() {
  const button = byId("refresh-button");
  button.disabled = true;
  byId("main-content").setAttribute("aria-busy", "true");
  clearError();
  try {
    await refreshOverview();
    await Promise.all([loadRun({ reconnect: true }), loadMap()]);
  } catch (error) {
    showError(error);
  } finally {
    button.disabled = false;
    byId("main-content").removeAttribute("aria-busy");
  }
}

byId("run-select").addEventListener("change", (event) => {
  state.selectedRun = event.target.value;
  state.logAttempt = "";
  state.logSignature = "";
  clearError();
  loadRun({ reconnect: true });
});

byId("map-select").addEventListener("change", (event) => {
  state.selectedMap = event.target.value;
  clearError();
  loadMap();
});

byId("attempt-select").addEventListener("change", (event) => {
  state.logAttempt = event.target.value;
  loadLog();
});

byId("stream-select").addEventListener("change", (event) => {
  state.logStream = event.target.value;
  loadLog();
});

byId("log-refresh").addEventListener("click", loadLog);
byId("refresh-button").addEventListener("click", refreshAll);
byId("pause-button").addEventListener("click", () => {
  state.paused = !state.paused;
  const button = byId("pause-button");
  button.setAttribute("aria-pressed", String(state.paused));
  button.textContent = state.paused ? "Resume updates" : "Pause updates";
  if (state.paused) {
    closeStream();
    setConnection("paused", "Updates paused");
  } else {
    loadRun({ reconnect: true });
  }
});

window.addEventListener("beforeunload", closeStream);
setConnection("idle", "Updates idle");
refreshAll();
