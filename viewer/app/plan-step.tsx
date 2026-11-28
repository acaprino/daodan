// A step of the plan on the screen: how it is, what it does, its actions with their state and where they run, the one under way, what
// it cannot do, what it wrote, and its events. Which result is under which step is a table by id; the order and the presence of the
// steps are the plan's.
import type { ComponentType } from 'react';
import { Badge, Button, Cluster, Column, Icon, Progress, Section, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList, ItemList, ItemRow, Note } from '@acaprino/sigrid/components';
import { Fold } from '../src/listed.tsx';
import { Activity } from './activity.tsx';
import { useFrame } from './frame.tsx';
import { linksNote, passAlert } from './notices.ts';
import { actionsOf, currentAction, planSteps } from './plan.ts';
import type { ActionRow } from './plan.ts';
import { FilesResult, ModulesResult, TechnologiesResult } from './premap-screen.tsx';
import { short } from './repository.ts';
import { ContextFold } from './repository-screen.tsx';
import { ctx } from './snapshot.ts';
import { MapNote } from './states.tsx';
import { Step } from './step.tsx';
import { SynthesisResult } from './synthesis-screen.tsx';
import { model, useModel } from './use-model.ts';

// Why the links cannot be looked for now is in the note's text.
const WHY = 'links-why';
// The buttons are beside the note, not in it: a note whose tone changes is drawn anew, and would take the focus with it.
function Links() {
  const s = useModel();
  const { go } = useFrame();
  const { tone, title, message, running, reason } = linksNote(s);
  return <Column>
    <Note tone={tone} title={title}><Text pre id={WHY} data-selectable="">{message}</Text></Note>
    <Cluster>
      <Button variant="outline" loading={running} disabled={!running && reason !== ''} aria-describedby={WHY} onClick={() => { model.findLinks(); }}>
        <Icon name="play" />Trova i legami</Button>
      {reason && <Button variant="ghost" onClick={() => go(model.chooseEngine)}><Icon name="ai" />Scegli il motore</Button>}
    </Cluster>
  </Column>;
}

// Under the step of the calls: why the pass that refines their graph did not go, with «Riprova» where it failed (`app.retry`, on
// `run.pass.state === 'failed'`), the map of the system and the links between the modules.
function CallsResult() {
  const s = useModel();
  const c = ctx(s), alert = passAlert(s);
  return c && <>
    {alert && <Note tone={alert.tone} title={alert.title}
      actions={alert.retry && <Button variant="outline" onClick={() => { model.retryPass(); }}><Icon name="refresh" />Riprova</Button>}>
      <Text pre data-selectable="">{alert.message}</Text></Note>}
    <MapNote />
    <Links />
    <Column gap="xs">
      <ContextFold />
      <Fold label="Come leggere l’avanzamento">
        <Text as="p" variant="soft" data-selectable="">Avanzamento ed eventi sono quelli del run {c.run_id} sul commit {short(c.commit)}, sull’intero progetto. Il grafo cresce solo quando la pipeline scrive un artefatto.</Text>
      </Fold>
    </Column>
  </>;
}

// What a step wrote, under it; a step with no result of its own (`read_code`, `find_entry_points`, `run_and_observe`) shows its actions:
// the rows of the entry points are in the paths of `assemble_graph`, which ask for the links.
const RESULT: Record<string, ComponentType> = {
  list_files: FilesResult, recognize_stack: TechnologiesResult, find_modules: ModulesResult, link_calls: CallsResult, assemble_graph: SynthesisResult,
};

const TONE = { error: 'danger', running: 'info', done: 'success', skipped: 'success', todo: undefined } as const;

// The facts of an action, in the details.
function ActionFacts({ row }: { row: ActionRow }) {
  return <Column gap="md" data-selectable="">
    <DescriptionList aria-label="Fatti dell’azione" items={[
      { name: 'Stato', value: row.state },
      row.detail ? { name: 'Strumento', value: row.detail } : null,
      ...row.facts.map((fact, index) => ({ name: ['Codice del progetto', 'Dove', 'Rete'][index], value: fact })),
      row.command ? { name: 'Comando', value: row.command } : null,
      { name: 'Azione', value: row.id, code: true },
    ]} />
    {row.note && <Text as="p" pre>{row.note}</Text>}
  </Column>;
}

// The one control of an action: the answer it waits for on its hosts, else the window of the command it runs (`command-form.tsx`).
function ActionControl({ row }: { row: ActionRow }) {
  if (row.waiting) return <Button variant="outline" size="sm" onClick={model.showHosts}>Rispondi</Button>;
  const at = row.commandAt;
  return at && <Button variant="outline" size="sm" aria-label={`Comando: ${row.title}`} onClick={() => model.showCommand(at.kind, at.root)}>
    <Icon name="terminal" />Comando</Button>;
}

function Actions({ step }: { step: string }) {
  const s = useModel();
  const { show } = useFrame();
  const rows = actionsOf(s, step);
  if (!rows.length) return null;
  return <Section title="Azioni" level={3} icon={<Icon name="tasks" />}>
    <ItemList aria-label="Azioni del passo">{rows.map(row =>
      <ItemRow key={row.id} title={row.title} wrapTitle description={row.note ? <Text pre>{row.note}</Text> : row.detail}
        facts={[...row.facts, row.command].filter(Boolean).map(text => ({ text }))} end={<Badge variant="secondary" tone={row.tone}>{row.state}</Badge>}
        onClick={() => show({ id: 'plan.action', key: row.id, title: 'Azione del piano', icon: 'info', name: row.title, content: <ActionFacts row={row} /> })}
        control={row.waiting || row.commandAt ? <ActionControl row={row} /> : undefined} controlSide="end" />)}
    </ItemList>
  </Section>;
}

export function PlanStepScreen() {
  const s = useModel();
  const id = s.kept.analysisStage;
  const row = planSteps(s).find(step => step.id === id);
  const now = currentAction(s), Result = RESULT[id];
  const missing = actionsOf(s, id).filter(action => action.note !== '' && !action.waiting);
  if (!row) return null;
  // Keyed by the step: each one opens with its own rows closed, not with those of the step seen before.
  return <Step key={id} stage={id} line={row.what} end={<Badge variant="secondary" tone={TONE[row.status]}>{row.note.split(' · ')[0]}</Badge>}>
    {row.status === 'error' && <Note tone="error" title="Il passo non è riuscito."><Text pre data-selectable="">{row.note}</Text></Note>}
    {now && now.action.step === id && <Column>
      <Text variant="strong">{now.action.title}</Text>
      <Progress aria-label="Azione in corso" value={now.total ? Math.round(100 * now.done / now.total) : null} showValue={now.total > 0} />
    </Column>}
    <Actions step={id} />
    {missing.length > 0 && <Note tone="warning" announce={false} title="Che cosa manca"
      items={missing.map(action => `${action.title}: ${action.note}`)} />}
    {Result && <Result />}
    <Activity events={s.events.filter(event => !event.run && event.step === id)} />
  </Step>;
}
