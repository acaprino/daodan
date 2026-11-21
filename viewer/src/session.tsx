// What the page asks the host session and what the session answered: requests, findings and gaps.
// The server starts no model: a request waits until the session takes it (`codebase_map_ui_requests`).
import { ListAction } from '@acaprino/imago/react';
import React, { useEffect, useState } from 'react';
import { Note } from './parts.tsx';

export const POLL_MS = 2000;
type Request = { id: number; kind: string; scope: string; text: string; state: string; message?: string };
type Finding = { file?: string; line?: number; severity?: string; title?: string; premise?: string; example?: string; request: number };
const KINDS = [['review', 'Review'], ['map', 'Mappa']];
const SCOPES = [['global', 'Globale'], ['changeset', 'Changeset'], ['feature', 'Funzionalità'], ['prompt', 'Prompt libero']];
const STATES: Record<string, string> = { pending: 'in attesa della sessione', taken: 'in corso', done: 'conclusa' };

const answer = (response: Response) => response.json().catch(() => ({})).then(json =>
  (response.ok ? json : Promise.reject(new Error(json.error ?? `HTTP ${response.status}`))));
// The token comes in the address the MCP server returned; a static export has none and needs none.
const TOKEN = new URLSearchParams(window.location.search).get('token') ?? '';
const auth = TOKEN ? { 'X-Daodan-Token': TOKEN } : undefined;
export const getJson = (url: string) => fetch(url, { headers: auth }).then(answer);
const postJson = (url: string, body: unknown) =>
  fetch(url, { method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(answer);

export function Session({ onPick, onRun }: { onPick: (file: string) => void; onRun: (id: string) => void }) {
  const [requests, setRequests] = useState<Request[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [gaps, setGaps] = useState<unknown[]>([]);
  const [form, setForm] = useState({ kind: 'review', scope: 'changeset', text: '' });
  const [runId, setRunId] = useState('');
  const [error, setError] = useState('');
  const refresh = () => Promise.all([getJson('./api/requests'), getJson('./api/findings')]).then(([asked, found]) => {
    setRequests(asked.requests); setFindings(found.findings); setGaps(found.gaps);
  }).catch(() => undefined);
  useEffect(() => { refresh(); const timer = window.setInterval(refresh, POLL_MS); return () => window.clearInterval(timer); }, []);
  const fail = (reason: unknown) => setError(String((reason as Error)?.message ?? reason));
  const send = (event: React.FormEvent) => {
    event.preventDefault();
    postJson('./api/requests', form).then(() => { setError(''); setForm({ ...form, text: '' }); refresh(); }).catch(fail);
  };
  const analyze = (event: React.FormEvent) => {
    event.preventDefault();
    postJson('./api/runs', { target: '.', run_id: runId }).then(() => { setError(''); setRunId(''); onRun(runId); }).catch(fail);
  };
  const needsText = form.scope === 'feature' || form.scope === 'prompt';
  return <section className="im-auto-grid im-inset im-scroll im-scroll--bounded" aria-label="Sessione e review">
    <div className="im-section">
      <h3>Chiedi alla sessione</h3>
      <form onSubmit={send} className="im-cluster">
        <div className="im-field"><label className="im-field-label" htmlFor="request-kind">Cosa</label>
          <select id="request-kind" className="im-select" value={form.kind} onChange={event => setForm({ ...form, kind: event.target.value })}>{KINDS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
        <div className="im-field"><label className="im-field-label" htmlFor="request-scope">Perimetro</label>
          <select id="request-scope" className="im-select" value={form.scope} onChange={event => setForm({ ...form, scope: event.target.value })}>{SCOPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
        <div className="im-field"><label className="im-field-label" htmlFor="request-text">{form.scope === 'feature' ? 'Funzionalità' : 'Indicazioni'}</label>
          <span className="im-input"><input id="request-text" placeholder={form.scope === 'feature' ? 'Nome della funzionalità' : 'Indicazioni per la sessione'}
            value={form.text} required={needsText} maxLength={2000} onChange={event => setForm({ ...form, text: event.target.value })} /></span></div>
        <button type="submit" className="im-btn">Invia</button>
      </form>
      <p className="im-muted">La richiesta resta in attesa finché la sessione non la prende: chiedile «esegui le richieste della UI».</p>
      <h3>Analisi statica, senza modello</h3>
      <form onSubmit={analyze} className="im-cluster">
        <div className="im-field"><label className="im-field-label" htmlFor="run-name">Nome del run</label>
          <span className="im-input"><input id="run-name" placeholder="nome-del-run" value={runId} required pattern="[a-z0-9]+(-[a-z0-9]+)*" onChange={event => setRunId(event.target.value)} /></span></div>
        <button type="submit" className="im-btn">Crea il run</button>
      </form>
      {error && <Note tone="err" title="Richiesta non riuscita" message={error} />}
    </div>
    <div className="im-section">
      <h3>Richieste · {requests.length}</h3>
      <ul className="im-detail-list">{requests.slice().reverse().map(item => <li key={item.id} className="im-stack">
        <span><b>#{item.id}</b> {item.kind} · {item.scope}{item.text ? ` · ${item.text}` : ''}</span>
        <span className="im-chip" data-im-tone={item.state === 'done' ? 'ok' : 'info'}>{STATES[item.state] ?? item.state}</span>
        {item.message && <span className="im-muted">{item.message}</span>}
      </li>)}</ul>
      {!requests.length && <p className="im-muted">Nessuna richiesta.</p>}
    </div>
    <div className="im-section">
      <h3>Finding · {findings.length}</h3>
      <ul className="im-detail-list">{findings.map((item, index) => <li key={index}>
        <ListAction onClick={() => item.file && onPick(item.file)}
          title={<><b className={['Critical', 'High'].includes(item.severity ?? '') ? 'im-text-err' : 'im-text-warn'}>{item.severity ?? 'unknown'}</b> <code>{item.file ?? 'unknown'}:{item.line ?? '?'}</code></>}
          detail={<>{item.title ?? item.premise ?? 'unknown'}{item.example && <> · {item.example}</>}</>} />
      </li>)}</ul>
      {!findings.length && <p className="im-muted">Nessun finding: compaiono quando la sessione chiude una review.</p>}
      {gaps.length > 0 && <Note tone="warn" title={`Lacune · ${gaps.length}`} items={gaps.map((gap, index) => ({ label: String(index + 1), message: typeof gap === 'string' ? gap : JSON.stringify(gap) }))} />}
    </div>
  </section>;
}
