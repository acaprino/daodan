// The pipeline page: the steps of an analysis in their order and, hanging from each, what it uses, when, with which tool and where, for
// the language, the build tool or the framework chosen; as the code runs today, or as the plan orders it. It reads no server: its data
// is written from the code's own declarations (`daodan/core/pipeline_tree.py`), so nothing here can fail to answer.
import { useEffect, useMemo, useState } from 'react';
import { AppWindow, startApp, useWindow } from '@acaprino/imago';
import type { AppView } from '@acaprino/imago';
import { useMedia } from '@acaprino/sigrid';
import { Badge, Column, Heading, Select, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList } from '@acaprino/sigrid/components';
import { Inspector, Panel } from '@acaprino/sigrid/layout';
import { GraphCanvas, GraphLegend } from '@acaprino/sigrid/graph';
import '@acaprino/sigrid/styles.css';
import '@acaprino/sigrid/graph.css';
import { DAODAN } from '../src/page.ts';
import { DATA } from './data.ts';
import { ALL, detailOf, groupsOf, legendOf, sceneOf } from './tree.ts';
import type { Mode } from './tree.ts';

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
  const [chosen, choose] = useState<string | null>(null);
  const [closed, setClosed] = useState<string[] | null>(null);  // the branches as the person left them; null: as the choice opens them
  const direction = useMedia('(width < 850px)') ? 'down' : 'right';
  useEffect(() => { window_.setTitle(document.title); }, [window_]);
  const choice = DATA.choices.find(item => item.id === tech) ?? null;
  const scene = useMemo(() => sceneOf(DATA, mode, choice), [mode, choice]);
  const detail = chosen === null ? null : detailOf(DATA, mode, chosen);
  // With every technology the steps start closed, to be opened one at a time; with one chosen its whole way is in sight.
  const collapsed = closed ?? (choice ? [] : scene.branches);
  const change = (act: () => void) => {
    act();
    choose(null);
    setClosed(null);
  };
  return <AppWindow views={VIEWS} view={mode} onView={next => change(() => setMode(next))}
    status={<>
      <Badge variant="secondary">{choice?.name ?? 'Tutte le tecnologie'}</Badge>
      <Text variant="soft">{scene.shown} voci in {scene.steps.size} step, {scene.boxed} solo nel container</Text>
    </>}
    footer={<Text>Scritta dalle dichiarazioni del codice: daodan/core/pipeline_tree.py</Text>}
    inspector={<Inspector title={detail?.title ?? 'Dettaglio'} open={detail !== null} onOpenChange={open => { if (!open) choose(null); }}>
      {detail && <Column gap="lg" data-selectable="">
        <Heading size="small"><Text pre>{detail.name}</Text></Heading>
        <DescriptionList aria-label={detail.name} items={detail.facts} />
      </Column>}
    </Inspector>}>
    <Panel title="Pipeline" subtitle={LINE[mode]}
      tools={<Select size="sm" aria-label="Tecnologia" value={tech} options={EVERY} groups={GROUPS} onValueChange={next => change(() => setTech(next))} />}>
      <Column fill pad="lg" gap="md">
        <Text as="p" variant="soft">Gli step in ordine; da ognuno pende ciò che usa, e sulla linea c’è quando parte. Scegli una voce per vedere con che cosa, a che versione e che cosa dà.</Text>
        <GraphCanvas aria-label="Pipeline di Daodan" fill search nodes={scene.nodes} edges={scene.edges} direction={direction}
          layoutKey={`${direction}|${scene.key}`} steps={scene.steps} selected={chosen} onSelect={choose}
          collapsed={collapsed} onCollapsedChange={setClosed} />
        <GraphLegend aria-label="Tipi di linea" entries={legendOf(scene)} />
      </Column>
    </Panel>
  </AppWindow>;
}

startApp(DAODAN, document.getElementById('app')!, <Pipeline />);
