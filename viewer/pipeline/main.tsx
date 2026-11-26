// The pipeline page: the steps of an analysis as a path and, for the step chosen, what it uses, when, with which tool and where, for
// the language, the build tool or the framework chosen; as the code runs today, or as the plan orders it. It reads no server: its data
// is written from the code's declarations (`daodan/core/pipeline_tree.py`), so nothing here can fail to answer.
import { useEffect, useMemo, useState } from 'react';
import { AppWindow, startApp, useFocusKept, useWindow } from '@acaprino/imago';
import type { AppView } from '@acaprino/imago';
import { Badge, Column, Heading, Icon, Select, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList, Disclosure, Empty, ItemList, ItemRow, Steps } from '@acaprino/sigrid/components';
import { ContentSplit, Inspector, Panel } from '@acaprino/sigrid/layout';
import '@acaprino/sigrid/styles.css';
import { DAODAN } from '../src/page.ts';
import { DATA } from './data.ts';
import { ALL, countOf, detailOf, groupsOf, itemsOf, lineOf, pathOf, rowId, stepId } from './tree.ts';
import type { Mode, Row } from './tree.ts';

const VIEWS: AppView<Mode>[] = [
  { id: 'today', label: 'Oggi nel codice', icon: 'code', command: 'Vai a Oggi nel codice' },
  { id: 'plan', label: 'Piano', icon: 'structure', command: 'Vai al Piano' },
];
const EVERY = [{ value: ALL, label: 'Tutte le tecnologie' }], GROUPS = groupsOf(DATA);
const LINE: Record<Mode, string> = { today: 'Come gira oggi', plan: 'Come la ordina il piano: nel codice non c’è ancora' };

function Pipeline() {
  const window_ = useWindow();
  const [mode, setMode] = useState<Mode>('today');
  const [tech, setTech] = useState(ALL);
  const [kept, setAt] = useState(0);  // the step on the screen, by its place in the path
  const [chosen, choose] = useState<string | null>(null);
  const [panes, setPanes] = useState<1 | 2>(2);
  useFocusKept(panes);
  useEffect(() => { window_.setTitle(document.title); }, [window_]);
  const choice = DATA.choices.find(item => item.id === tech) ?? null;
  const path = useMemo(() => pathOf(DATA, mode, choice), [mode, choice]);
  const at = Math.min(kept, path.steps.length - 1), step = path.steps[at];
  const detail = chosen === null ? null : detailOf(DATA, mode, chosen);
  // The details are of a thing in the list on the screen: another list closes them.
  const change = (act: () => void) => {
    act();
    choose(null);
  };
  // In a column at every width: in a row too narrow for the names only the step on the screen keeps its name, which is its button.
  const steps = <Steps aria-label="Step della pipeline" steps={itemsOf(path)} current={at} onStepSelect={next => change(() => setAt(next))} />;
  const list = (name: string, rows: Row[]) => <ItemList aria-label={name}>{rows.map(row => {
    const line = lineOf(row, mode);
    return <ItemRow key={row.name} title={line.title} wrapTitle description={line.tool} facts={line.facts}
      leading={<Icon name={line.contained ? 'package' : 'device'} />} current={chosen === rowId(row)} onClick={() => choose(rowId(row))} />;
  })}</ItemList>;
  return <AppWindow views={VIEWS} view={mode} onView={next => change(() => setMode(next))}
    status={<>
      <Badge variant="secondary">{choice?.name ?? 'Tutte le tecnologie'}</Badge>
      <Text variant="soft">{path.shown} voci in {path.steps.length} step, {path.boxed} solo nel container</Text>
    </>}
    footer={<Text>Scritta dalle dichiarazioni del codice: daodan/core/pipeline_tree.py</Text>}
    inspector={<Inspector title="Dettaglio" open={detail !== null} onOpenChange={open => { if (!open) choose(null); }}>
      {detail && <Column gap="lg" data-selectable="">
        <Heading size="small"><Text pre>{detail.name}</Text></Heading>
        <DescriptionList aria-label={detail.name} items={detail.facts} />
      </Column>}
    </Inspector>}>
    <ContentSplit aside={<Column pad="lg">{steps}</Column>} asideLabel="Step" width="md" show="main" step={720} onPanesChange={setPanes}>
      <Panel title={`${at + 1}. ${step.title}`} subtitle={LINE[mode]}
        actions={<Select size="sm" aria-label="Tecnologia" value={tech} options={EVERY} groups={GROUPS} onValueChange={next => change(() => setTech(next))} />}>
        <Column pad="lg" gap="lg">
          {panes === 1 && steps}
          <DescriptionList aria-label={step.title} items={detailOf(DATA, mode, stepId(step.key))!.facts} />
          {step.rows.length ? list(`Che cosa usa: ${step.title}`, step.rows)
            : <Empty title={`Niente di specifico per ${choice?.name ?? 'questa scelta'} in questo step`} description="Scegli un altro step, o un’altra tecnologia." />}
          {path.beside.filter(part => part.rows.length > 0).map(part =>
            <Disclosure key={part.key} label={part.title} summary={countOf(part.rows)}>
              <Column gap="md">
                <Text as="p" variant="soft">{part.what}</Text>
                {list(part.title, part.rows)}
              </Column>
            </Disclosure>)}
        </Column>
      </Panel>
    </ContentSplit>
  </AppWindow>;
}

startApp(DAODAN, document.getElementById('app')!, <Pipeline />);
