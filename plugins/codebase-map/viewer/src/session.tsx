// What the page asks the host session and what the session answered: requests, findings and gaps.
// The server starts no model: a request waits until the session takes it (`codebase_map_ui_requests`).
import React, { useEffect, useState } from 'react';

export const POLL_MS = 2000;
type Request = { id: number; kind: string; scope: string; text: string; state: string; message?: string };
type Finding = { file?: string; line?: number; severity?: string; title?: string; premise?: string; example?: string; request: number };
const KINDS = [['review', 'Review'], ['map', 'Mappa']];
const SCOPES = [['global', 'Globale'], ['changeset', 'Changeset'], ['feature', 'Funzionalità'], ['prompt', 'Prompt libero']];
const STATES: Record<string, string> = { pending: 'in attesa della sessione', taken: 'in corso', done: 'conclusa' };

const answer = (response: Response) => response.json().catch(() => ({})).then(json =>
  (response.ok ? json : Promise.reject(new Error(json.error ?? `HTTP ${response.status}`))));
export const getJson = (url: string) => fetch(url).then(answer);
const postJson = (url: string, body: unknown) =>
  fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(answer);

export function Session({ onPick, onRun }: { onPick: (ref: string) => void; onRun: (id: string) => void }) {
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
  return <section className="session" aria-label="Sessione e review">
    <div className="block">
      <h3>Chiedi alla sessione</h3>
      <form onSubmit={send} className="ask">
        <select aria-label="Cosa" value={form.kind} onChange={event => setForm({ ...form, kind: event.target.value })}>{KINDS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
        <select aria-label="Perimetro" value={form.scope} onChange={event => setForm({ ...form, scope: event.target.value })}>{SCOPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
        <input aria-label={form.scope === 'feature' ? 'Funzionalità' : 'Indicazioni'} placeholder={form.scope === 'feature' ? 'Nome della funzionalità' : 'Indicazioni per la sessione'}
          value={form.text} required={needsText} maxLength={2000} onChange={event => setForm({ ...form, text: event.target.value })} />
        <button type="submit" className="go">Invia</button>
      </form>
      <p className="muted">La richiesta resta in attesa finché la sessione non la prende: chiedile «esegui le richieste della UI».</p>
      <h3>Analisi statica, senza modello</h3>
      <form onSubmit={analyze} className="ask">
        <input aria-label="Nome del run" placeholder="nome-del-run" value={runId} required pattern="[a-z0-9]+(-[a-z0-9]+)*" onChange={event => setRunId(event.target.value)} />
        <button type="submit" className="go">Crea il run</button>
      </form>
      {error && <p className="bad" role="alert">{error}</p>}
    </div>
    <div className="block">
      <h3>Richieste · {requests.length}</h3>
      <ul className="links">{requests.slice().reverse().map(item => <li key={item.id} className="request">
        <span><b>#{item.id}</b> {item.kind} · {item.scope}{item.text ? ` · ${item.text}` : ''}</span>
        <span className={`chip ${item.state}`}>{STATES[item.state] ?? item.state}</span>
        {item.message && <span className="muted">{item.message}</span>}
      </li>)}</ul>
      {!requests.length && <p className="muted">Nessuna richiesta.</p>}
    </div>
    <div className="block">
      <h3>Finding · {findings.length}</h3>
      <ul className="links">{findings.map((item, index) => <li key={index}>
        <button type="button" className="finding" onClick={() => item.file && onPick(`file:${item.file}`)}>
          <span><b className={`sev ${item.severity ?? ''}`}>{item.severity ?? 'unknown'}</b> <code>{item.file ?? 'unknown'}:{item.line ?? '?'}</code></span>
          <span>{item.title ?? item.premise ?? 'unknown'}</span>
          {item.example && <span className="muted">{item.example}</span>}
        </button>
      </li>)}</ul>
      {!findings.length && <p className="muted">Nessun finding: compaiono quando la sessione chiude una review.</p>}
      {gaps.length > 0 && <><h3>Lacune · {gaps.length}</h3><ul className="gaps">{gaps.map((gap, index) => <li key={index}>{typeof gap === 'string' ? gap : JSON.stringify(gap)}</li>)}</ul></>}
    </div>
  </section>;
}
