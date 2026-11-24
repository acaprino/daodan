// What the page asks the host session and what the session answered. The server starts no model: a request waits until the
// session takes it (`codebase_map_ui_requests`).
import { useEffect, useRef, useState } from 'react';
import type { SyntheticEvent } from 'react';
import {
  Badge, Button, Cluster, Column, Disclosure, FormField, Grid, Icon, Input, ItemList, ItemRow, Note, Progress, ScrollArea, Section, Select, Text,
} from '@acaprino/sigrid';
import {
  askedState, askedText, askedTitle, findingPlace, findingSeverity, findingText, gapText, KINDS, needsText, questionProblem, runProblem, SCOPES,
} from './requests.ts';
import type { Asked, Finding, Question } from './requests.ts';

export const POLL_MS = 2000;

const answer = (response: Response) => response.json().catch(() => ({})).then(json =>
  (response.ok ? json : Promise.reject(new Error(json.error ?? `HTTP ${response.status}`))));
// The token comes in the address the MCP server returned; a static export has none and needs none.
const TOKEN = new URLSearchParams(window.location.search).get('token') ?? '';
const auth = TOKEN ? { 'X-Daodan-Token': TOKEN } : undefined;
export const getJson = (url: string) => fetch(url, { headers: auth }).then(answer);
const postJson = (url: string, body: unknown) =>
  fetch(url, { method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(answer);

// A form that posts: it is sending until the server answers, and keeps what the server said when it refuses.
function usePost(url: string) {
  const [sending, setSending] = useState(false);
  const [failure, setFailure] = useState('');
  const post = async (body: unknown, done: () => void) => {
    setSending(true);
    setFailure('');
    try {
      await postJson(url, body);
      done();
    } catch (reason) {
      setFailure(String((reason as Error)?.message ?? reason));
    } finally {
      setSending(false);
    }
  };
  return { sending, post, refusal: failure && <Note tone="error" title="Richiesta non riuscita"><Text data-selectable="">{failure}</Text></Note> };
}

function AskForm({ onSent }: { onSent: () => void }) {
  const [form, setForm] = useState<Question>({ kind: 'review', scope: 'changeset', text: '' });
  const [problem, setProblem] = useState('');
  const field = useRef<HTMLInputElement>(null);
  const { sending, post, refusal } = usePost('./api/requests');
  const feature = form.scope === 'feature';
  const change = (part: Partial<Question>) => { setForm(current => ({ ...current, ...part })); setProblem(''); };
  const submit = (event: SyntheticEvent) => {
    event.preventDefault();
    const wrong = questionProblem(form);
    setProblem(wrong);
    if (wrong) field.current?.focus();
    else post(form, () => { change({ text: '' }); onSent(); });
  };
  return <Section title="Chiedi alla sessione" level={3} icon={<Icon name="send" />}>
    <form noValidate onSubmit={submit}><Column gap="md">
      <FormField label="Cosa"><Select value={form.kind} onValueChange={kind => change({ kind })} options={KINDS} /></FormField>
      <FormField label="Perimetro"><Select value={form.scope} onValueChange={scope => change({ scope })} options={SCOPES} /></FormField>
      <FormField label={feature ? 'Funzionalità' : 'Indicazioni'} required={needsText(form.scope)} error={problem}>
        <Input ref={field} placeholder={feature ? 'Nome della funzionalità' : 'Indicazioni per la sessione'} value={form.text} maxLength={2000}
          onChange={event => change({ text: event.target.value })} />
      </FormField>
      <Cluster><Button type="submit" variant="outline" loading={sending}>Invia</Button></Cluster>
    </Column></form>
    <Text as="p" variant="muted">La richiesta resta in attesa finché la sessione non la prende: chiedile «esegui le richieste della UI».</Text>
    {refusal}
  </Section>;
}

function RunForm({ onRun }: { onRun: (id: string) => void }) {
  const [name, setName] = useState('');
  const [problem, setProblem] = useState('');
  const field = useRef<HTMLInputElement>(null);
  const { sending, post, refusal } = usePost('./api/runs');
  const submit = (event: SyntheticEvent) => {
    event.preventDefault();
    const wrong = runProblem(name);
    setProblem(wrong);
    if (wrong) field.current?.focus();
    else post({ target: '.', run_id: name }, () => { setName(''); onRun(name); });
  };
  return <Section title="Analisi statica, senza modello" level={3} icon={<Icon name="code" />}>
    <form noValidate onSubmit={submit}><Column gap="md">
      <FormField label="Nome del run" required error={problem}>
        <Input ref={field} placeholder="nome-del-run" value={name} onChange={event => { setName(event.target.value); setProblem(''); }} />
      </FormField>
      <Cluster><Button type="submit" variant="outline" loading={sending}>Crea il run</Button></Cluster>
    </Column></form>
    {refusal}
  </Section>;
}

type SessionProps = { onPick: (file: string) => void; onRun: (id: string) => void };
type Answers = { requests: Asked[]; findings: Finding[]; gaps: unknown[] };

// The forms and the answers. It asks the server as long as it is drawn, and no longer.
function Exchange({ onPick, onRun }: SessionProps) {
  const [answers, setAnswers] = useState<Answers | null>(null);  // nothing is said of them until the server has answered once
  const refresh = () => Promise.all([getJson('./api/requests'), getJson('./api/findings')]).then(([asked, found]) => {
    setAnswers({ requests: asked.requests, findings: found.findings, gaps: found.gaps });
  }).catch(() => undefined);  // the next poll retries
  useEffect(() => { refresh(); const timer = window.setInterval(refresh, POLL_MS); return () => window.clearInterval(timer); }, []);
  return <Grid gap="xl">
    <Column gap="xl">
      <AskForm onSent={refresh} />
      <RunForm onRun={onRun} />
    </Column>
    <Section title={answers ? `Richieste · ${answers.requests.length}` : 'Richieste'} level={3} icon={<Icon name="tasks" />}>
      {!answers ? <Progress aria-label="Carico le richieste…" value={null} />
        : !answers.requests.length ? <Text as="p" variant="muted">Nessuna richiesta.</Text>
        : <ItemList aria-label="Richieste">{answers.requests.slice().reverse().map(item =>
          <ItemRow key={item.id} title={askedTitle(item)} description={askedText(item) && <Text pre>{askedText(item)}</Text>}
            end={<Badge variant="secondary">{askedState(item)}</Badge>} />)}</ItemList>}
    </Section>
    <Section title={answers ? `Finding · ${answers.findings.length}` : 'Finding'} level={3} icon={<Icon name="alert" />}>
      {!answers ? <Progress aria-label="Carico i finding…" value={null} />
        : !answers.findings.length ? <Text as="p" variant="muted">Nessun finding: compaiono quando la sessione chiude una review.</Text>
        : <ItemList aria-label="Finding">{answers.findings.map((item, index) =>
          <ItemRow key={index} title={findingPlace(item)} wrapTitle description={<Text pre>{findingText(item)}</Text>}
            end={<Badge variant="secondary">{findingSeverity(item)}</Badge>} onClick={() => { if (item.file) onPick(item.file); }} />)}</ItemList>}
      {!!answers?.gaps.length && <Note tone="warning" announce={false} data-selectable="" title={`Lacune · ${answers.gaps.length}`} items={answers.gaps.map(gapText)} />}
    </Section>
  </Grid>;
}

const LABEL = 'Sessione e review';

// In sight, where there is no map.
export function Session(props: SessionProps) {
  return <Column as="section" aria-label={LABEL}><Exchange {...props} /></Column>;
}

// Over a map, behind its row. A `Disclosure` keeps what it holds mounted: what is drawn only while it is open asks nothing
// of the server while it is closed. A long list scrolls by itself, so the map stays near.
export function SessionDisclosure(props: SessionProps) {
  const [open, setOpen] = useState(false);
  return <Disclosure label={LABEL} open={open} onOpenChange={setOpen}>
    {open && <ScrollArea bounded pad="xs" aria-label={LABEL}><Exchange {...props} /></ScrollArea>}
  </Disclosure>;
}
