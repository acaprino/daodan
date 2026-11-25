// What the page asks the host session and what the session answered. The server starts no model: a request waits until the
// session takes it (`codebase_map_ui_requests`).
import { useEffect, useRef, useState } from 'react';
import type { ReactNode, SyntheticEvent } from 'react';
import { Badge, Button, Cluster, Column, Grid, Icon, Input, Section, Select, Split, Text } from '@acaprino/sigrid/primitives';
import { FormField, ItemList, ItemRow, Note } from '@acaprino/sigrid/components';
import type { BadgeTone } from '@acaprino/sigrid/primitives';
import {
  askedState, askedText, askedTitle, askedTone, findingPlace, findingSeverity, findingText, findingTone, gapText, KINDS, needsText, questionProblem,
  runProblem, SCOPES,
} from './requests.ts';
import type { Asked, Finding, Question } from './requests.ts';
import { causeOf, whenFree } from './http.ts';
import { LongFold } from './listed.tsx';
import { get, post } from './server.ts';
import { Failed, Loading } from './states.tsx';

export const POLL_MS = 2000;

// A form that posts: it is sending until the server answers, and keeps what the server said when it refuses.
function usePost(url: string) {
  const [sending, setSending] = useState(false);
  const [failure, setFailure] = useState('');
  const send = async (body: unknown, done: () => void) => {
    setSending(true);
    setFailure('');
    try {
      await post(url, body);
      done();
    } catch (reason) {
      setFailure(causeOf(reason));
    } finally {
      setSending(false);
    }
  };
  return { sending, send, refusal: failure && <Failed title="Richiesta non riuscita" cause={failure} /> };
}

function AskForm({ onSent }: { onSent: () => void }) {
  const [form, setForm] = useState<Question>({ kind: 'review', scope: 'changeset', text: '' });
  const [problem, setProblem] = useState('');
  const field = useRef<HTMLInputElement>(null);
  const { sending, send, refusal } = usePost('./api/requests');
  const feature = form.scope === 'feature';
  const change = (part: Partial<Question>) => { setForm(current => ({ ...current, ...part })); setProblem(''); };
  const submit = (event: SyntheticEvent) => {
    event.preventDefault();
    const wrong = questionProblem(form);
    setProblem(wrong);
    if (wrong) field.current?.focus();
    else send(form, () => { change({ text: '' }); onSent(); });
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
  const { sending, send, refusal } = usePost('./api/runs');
  const submit = (event: SyntheticEvent) => {
    event.preventDefault();
    const wrong = runProblem(name);
    setProblem(wrong);
    if (wrong) field.current?.focus();
    else send({ target: '.', run_id: name }, () => { setName(''); onRun(name); });
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

// What a route answers, asked again as long as it is drawn, one request at a time. Each route is asked by itself, so one that
// fails hides nothing of the others; what was answered once stays in sight, and the next poll asks again.
function usePoll<T>(url: string, onBusy: () => void) {
  const [answered, setAnswered] = useState<T | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const asking = useRef(false), drawn = useRef(false);
  const ask = async () => {
    if (asking.current) return;
    asking.current = true;
    try {
      const found = await whenFree(() => get<T>(url), onBusy, () => drawn.current);
      if (found === undefined) return;
      setAnswered(found);
      setFailure(null);
    } catch (reason) {
      setFailure(causeOf(reason));
    } finally {
      asking.current = false;
    }
  };
  useEffect(() => {
    drawn.current = true;
    ask();
    const timer = window.setInterval(ask, POLL_MS);
    return () => { drawn.current = false; window.clearInterval(timer); };
  }, []);
  return { answered, failure, ask, retry: () => { setFailure(null); ask(); } };
}

// Until a route has answered once nothing is said of what it holds: it is waited for, or its failure is said while it is asked again.
function Unanswered({ poll, waiting, failed }: { poll: { failure: string | null; retry: () => void }; waiting: string; failed: string }) {
  return poll.failure === null ? <Loading label={waiting} /> : <Failed title={failed} cause={poll.failure} retry={poll.retry} />;
}

// A state or a severity: its word, in the tone Sigrid has for it.
function Word({ tone, word }: { tone?: BadgeTone; word: string }) {
  return <Badge variant="secondary" tone={tone}>{word}</Badge>;
}

// An entry that does nothing: text to read and copy, so not a row to press.
function Entry({ title, mark, text }: { title: string; mark: ReactNode; text: string }) {
  return <Column as="li" gap="xs" pad="md" data-selectable="">
    <Split gap="sm"><Text variant="strong">{title}</Text>{mark}</Split>
    {text && <Text variant="soft" pre>{text}</Text>}
  </Column>;
}

type SessionProps = { onPick: (file: string) => void; onRun: (id: string) => void; onBusy: () => void };

// The forms and the answers. It asks the server as long as it is drawn, and no longer.
function Exchange({ onPick, onRun, onBusy }: SessionProps) {
  const asked = usePoll<{ requests: Asked[] }>('./api/requests', onBusy);
  const found = usePoll<{ findings: Finding[]; gaps: unknown[] }>('./api/findings', onBusy);
  const requests = asked.answered?.requests, findings = found.answered?.findings, gaps = found.answered?.gaps ?? [];
  return <Grid gap="xl">
    <Column gap="xl">
      <AskForm onSent={asked.ask} />
      <RunForm onRun={onRun} />
    </Column>
    <Section title={requests ? `Richieste · ${requests.length}` : 'Richieste'} level={3} icon={<Icon name="tasks" />}>
      {!requests ? <Unanswered poll={asked} waiting="Carico le richieste…" failed="Richieste non lette" />
        : !requests.length ? <Text as="p" variant="muted">Nessuna richiesta.</Text>
        : <Column as="ul" gap="xs" aria-label="Richieste">{requests.slice().reverse().map(item =>
          <Entry key={item.id} title={askedTitle(item)} mark={<Word tone={askedTone(item)} word={askedState(item)} />} text={askedText(item)} />)}</Column>}
    </Section>
    <Section title={findings ? `Finding · ${findings.length}` : 'Finding'} level={3} icon={<Icon name="alert" />}>
      {!findings ? <Unanswered poll={found} waiting="Carico i finding…" failed="Finding non letti" />
        : !findings.length ? <Text as="p" variant="muted">Nessun finding: compaiono quando la sessione chiude una review.</Text>
        : <ItemList aria-label="Finding">{findings.map((item, index) => {
          const { file } = item;
          const mark = <Word tone={findingTone(item)} word={findingSeverity(item)} />;
          return file  // only one that names a file has somewhere to go
            ? <ItemRow key={index} title={findingPlace(item)} wrapTitle description={<Text pre>{findingText(item)}</Text>} end={mark} onClick={() => onPick(file)} />
            : <Entry key={index} title={findingPlace(item)} mark={mark} text={findingText(item)} />;
        })}</ItemList>}
      {gaps.length > 0 && <Note tone="warning" announce={false} data-selectable="" title={`Lacune · ${gaps.length}`} items={gaps.map(gapText)} />}
    </Section>
  </Grid>;
}

const LABEL = 'Sessione e review';

// In sight, where there is no map.
export function Session(props: SessionProps) {
  return <Column as="section" aria-label={LABEL}><Exchange {...props} /></Column>;
}

// Over a map, behind its row: what is drawn only while it is open asks nothing of the server while it is closed.
export function SessionDisclosure(props: SessionProps) {
  return <LongFold label={LABEL}><Exchange {...props} /></LongFold>;
}
