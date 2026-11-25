// The engine and the questions: a question on the run in view, its answer with the tools it took, the engine, and the MCP server.
import { Badge, Button, Column, Grid, Icon, Progress, Section, Text, Textarea } from '@acaprino/sigrid/primitives';
import { DescriptionList, Empty, FormField } from '@acaprino/sigrid/components';
import { Failed, Loading } from '../src/states.tsx';
import { EngineForm } from './engine-form.tsx';
import { askedWord, askFailed, askNote, lastQuestion, mcpFacts, toolUse } from './engine.ts';
import { ScreenPanel } from './frame.tsx';
import { askReason, isAsking } from './run.ts';
import { ctx, slug } from './snapshot.ts';
import { model, useModel } from './use-model.ts';

// Why the question waits, said once, beside the action.
const WHY = 'ask-why';
function EngineActions() {
  const s = useModel();
  const asking = isAsking(s), note = askNote(s);
  return <>
    {note && <Text id={WHY} variant="note">{note}</Text>}
    <Button loading={asking} disabled={!asking && askReason(s) !== ''} aria-describedby={note ? WHY : undefined} onClick={() => { model.ask(); }}>Chiedi</Button>
  </>;
}
// In the window's action bar: the question is the one solid action of the screen.
export const engineActions = () => <EngineActions />;

function Question() {
  const s = useModel();
  const c = ctx(s);
  return <Section title="Domanda sul repository" level={3} icon={<Icon name="threads" />} gap="lg">
    <FormField label="Domanda" help={c ? `Il motore usa il run ${c.run_id} di ${slug(c)}.` : 'Seleziona prima una repository: il motore la legge dal suo run.'}>
      <Textarea rows={4} placeholder="Dove viene firmato un token, e chi lo verifica?" disabled={!c} value={s.question}
        onChange={event => model.setQuestion(event.target.value)} />
    </FormField>
  </Section>;
}

// The answer is drawn as the engine wrote it: a name such as `__init__`, or the lines of a source, would not survive Markdown.
function Answer() {
  const s = useModel();
  const { asked } = s;
  const running = asked?.state === 'running', failed = askFailed(asked?.state), last = lastQuestion(s.server?.asked);
  return <Section title="Risposta" level={3} icon={<Icon name="reply" />} gap="lg"
    end={asked && <Badge variant="secondary" tone={failed ? 'danger' : undefined}>{askedWord(asked.state)}</Badge>}>
    <Column gap="lg" aria-live="polite" aria-busy={running} data-selectable="">
      {asked && asked.tools.length > 0 && <Section title="Operazioni di Daodan usate" level={4} icon={<Icon name="listOrdered" />}><DescriptionList items={asked.tools.map(toolUse)} /></Section>}
      {asked?.text && <Text as="p" pre>{asked.text}</Text>}
      {running && !asked?.text && <Column>
        <Text as="p" variant="muted">In attesa del motore…</Text>
        <Progress aria-label="In attesa del motore…" value={null} />
      </Column>}
      {!asked && (last ? <Text as="p" variant="muted" pre>{last}</Text>
        : <Empty title="Nessuna domanda" description="La risposta del motore compare qui, con le operazioni di Daodan usate." />)}
    </Column>
    {asked && failed && <Failed title={`Domanda ${askedWord(asked.state)}.`} cause={asked.cause} />}
  </Section>;
}

function McpServer() {
  const { server } = useModel();
  const facts = server && mcpFacts(server);
  return <Section title="Server MCP" level={3} icon={<Icon name="code" />}>
    {facts ? <Column data-selectable="">
      <Text as="p" variant="soft">Per una sessione tua: avvia Daodan sul checkout con questo comando.</Text>
      <DescriptionList aria-label="Server MCP" items={facts} />
    </Column> : <Text as="p" variant="muted">Disponibile dopo la selezione di una repository.</Text>}
  </Section>;
}

export function EngineScreen() {
  const s = useModel();
  if (!s.server) {
    return <ScreenPanel title="Motore e domande">
      {!s.serverError && <Column pad="lg"><Loading label="Lettura dello stato del server…" /></Column>}
    </ScreenPanel>;
  }
  return <ScreenPanel title="Motore e domande" subtitle={slug(ctx(s)) || 'Nessuna repository'}>
    <Column pad="lg" gap="xl">
      <Text as="p" variant="soft">Il motore legge la mappa solo con le operazioni di Daodan: cerca, poi legge quello che serve.</Text>
      <Grid min="lg" gap="xl">
        <Column gap="xl"><Question /><Answer /></Column>
        <Column gap="xl"><EngineForm /><McpServer /></Column>
      </Grid>
    </Column>
  </ScreenPanel>;
}
