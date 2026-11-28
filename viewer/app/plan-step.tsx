// A step of the plan on the screen: how it is, what it does, its actions with their state and where they run, the one under way, what
// it cannot do, and what it wrote. Which result is under which step is a table by id; the order and the presence of the steps are
// the plan's.
import type { ComponentType } from 'react';
import { Badge, Button, Column, Icon, Progress, Section, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList, ItemList, ItemRow, Note } from '@acaprino/sigrid/components';
import { useFrame } from './frame.tsx';
import { actionsOf, currentAction, planSteps } from './plan.ts';
import type { ActionRow } from './plan.ts';
import { FilesResult, ModulesResult, TechnologiesResult } from './premap-screen.tsx';
import { PassResult } from './run-screen.tsx';
import { Step } from './step.tsx';
import { SynthesisResult } from './synthesis-screen.tsx';
import { model, useModel } from './use-model.ts';

// What a step wrote, under it; a step with no result of its own (`read_code`, `find_entry_points`, `run_and_observe`) shows its actions:
// the rows of the entry points are in the paths of `assemble_graph`, which ask for the links.
const RESULT: Record<string, ComponentType> = {
  list_files: FilesResult, recognize_stack: TechnologiesResult, find_modules: ModulesResult, link_calls: PassResult, assemble_graph: SynthesisResult,
};

const TONE = { error: 'danger', running: 'info', done: 'success', skipped: 'success', todo: undefined } as const;

// The facts of an action, in the details.
function ActionFacts({ row }: { row: ActionRow }) {
  return <Column gap="md" data-selectable="">
    <DescriptionList aria-label="Fatti dell’azione" items={[
      { name: 'Stato', value: row.state },
      row.detail ? { name: 'Strumento', value: row.detail } : null,
      ...row.facts.map((fact, index) => ({ name: ['Codice del progetto', 'Dove', 'Rete'][index], value: fact })),
      { name: 'Azione', value: row.id, code: true },
    ]} />
    {row.note && <Text as="p" pre>{row.note}</Text>}
  </Column>;
}

function Actions({ step }: { step: string }) {
  const s = useModel();
  const { show } = useFrame();
  const rows = actionsOf(s, step);
  if (!rows.length) return null;
  return <Section title="Azioni" level={3} icon={<Icon name="tasks" />}>
    <ItemList aria-label="Azioni del passo">{rows.map(row =>
      <ItemRow key={row.id} title={row.title} wrapTitle description={row.note ? <Text pre>{row.note}</Text> : row.detail}
        facts={row.facts.map(text => ({ text }))} end={<Badge variant="secondary" tone={row.tone}>{row.state}</Badge>}
        onClick={() => show({ id: 'plan.action', key: row.id, title: 'Azione del piano', icon: 'info', name: row.title, content: <ActionFacts row={row} /> })}
        control={row.waiting ? <Button variant="outline" size="sm" onClick={model.showHosts}>Rispondi</Button> : undefined} controlSide="end" />)}
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
  return <Step stage={id} line={row.what} end={<Badge variant="secondary" tone={TONE[row.status]}>{row.note.split(' · ')[0]}</Badge>}>
    {row.status === 'error' && <Note tone="error" title="Il passo non è riuscito."><Text pre data-selectable="">{row.note}</Text></Note>}
    {now && now.action.step === id && <Column>
      <Text variant="strong">{now.action.title}</Text>
      <Progress aria-label="Azione in corso" value={now.total ? Math.round(100 * now.done / now.total) : null} showValue={now.total > 0} />
    </Column>}
    <Actions step={id} />
    {missing.length > 0 && <Note tone="warning" announce={false} title="Che cosa manca"
      items={missing.map(action => `${action.title}: ${action.note}`)} />}
    {Result && <Result />}
  </Step>;
}
