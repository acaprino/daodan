// What the page asks the host session and what the session answered. The server starts no model: a request waits until the
// session takes it (`codebase_map_ui_requests`).
export const POLL_MS = 2000;

const answer = (response: Response) => response.json().catch(() => ({})).then(json =>
  (response.ok ? json : Promise.reject(new Error(json.error ?? `HTTP ${response.status}`))));
// The token comes in the address the MCP server returned; a static export has none and needs none.
const TOKEN = new URLSearchParams(window.location.search).get('token') ?? '';
const auth = TOKEN ? { 'X-Daodan-Token': TOKEN } : undefined;
export const getJson = (url: string) => fetch(url, { headers: auth }).then(answer);

// shortcut: nothing is drawn (requests, findings, gaps and the two forms are on Imago at 99665814e), until ticket 18 of the port draws them on Sigrid
export function Session(_: { onPick: (file: string) => void; onRun: (id: string) => void }) {
  return null;
}
