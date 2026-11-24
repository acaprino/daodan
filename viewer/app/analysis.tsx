// The analysis: its stages in their order, and the one chosen beside them.
import { Fragment, useEffect, useMemo, useState } from 'react';
import type { ComponentType, ReactNode } from 'react';
import { Badge, Column, ContentSplit, ItemList, ItemRow, Progress, Text } from '@acaprino/sigrid';
import { FrameContext, ScreenPanel, useFocusKept, useFrame } from './frame.tsx';
import { PremapActions, PremapScreen } from './premap-screen.tsx';
import { RepositoryActions, RepositoryScreen } from './repository-screen.tsx';
import { RunActions, RunScreen } from './run-screen.tsx';
import type { Snapshot } from './snapshot.ts';
import { STAGE_WORD, stages } from './stages.ts';
import type { Stage } from './storage.ts';
import { SynthesisActions, SynthesisScreen } from './synthesis-screen.tsx';
import { model, useModel } from './use-model.ts';

// What each stage draws and, in the window's action bar, what it leads to. The notices sit above the bar, never over the action.
const STAGE: Record<Stage, { Screen: ComponentType; actions: (s: Snapshot) => ReactNode }> = {
  repository: { Screen: RepositoryScreen, actions: () => <RepositoryActions /> },
  premap: { Screen: PremapScreen, actions: () => <PremapActions /> },
  analysis: { Screen: RunScreen, actions: () => <RunActions /> },
  synthesis: { Screen: SynthesisScreen, actions: () => <SynthesisActions /> },
};
export const analysisActions = (s: Snapshot): ReactNode => STAGE[s.kept.analysisStage].actions(s);

export function AnalysisScreen() {
  const s = useModel();
  const frame = useFrame();
  const [panes, setPanes] = useState<1 | 2>(2);
  const [shown, setShown] = useState<'aside' | 'main'>('main');  // the pane in sight where one fits
  const alone = panes === 1;
  useFocusKept(panes, shown);
  useEffect(() => {
    frame.reveal.current = alone && shown === 'aside' ? () => setShown('main') : null;
    return () => { frame.reveal.current = null; };
  }, [alone, shown]);
  const inPane = useMemo(() => (alone ? { ...frame, back: () => setShown('aside') } : frame), [frame, alone]);
  if (!s.server) {
    return <ScreenPanel title="Analisi">
      {!s.serverError && <Column pad="lg" aria-busy><Progress aria-label="Lettura dello stato del server…" value={null} /></Column>}
    </ScreenPanel>;
  }
  const { Screen } = STAGE[s.kept.analysisStage];
  const list = <Column pad="sm"><ItemList aria-label="Percorso di analisi">{stages(s).map(row => <Fragment key={row.id}>
    <ItemRow title={row.label} current={row.id === s.kept.analysisStage} disabled={row.reason !== ''}
      description={<Text pre>{row.detail}</Text>}  // `pre`: it wraps, it is never cut
      meta={row.state !== 'failed' && STAGE_WORD[row.state]} end={row.state === 'failed' && <Badge variant="destructive">{STAGE_WORD.failed}</Badge>}
      onClick={() => { model.selectStage(row.id); setShown('main'); }} />
    {/* Under the row, not in it: a row that cannot be pressed is drawn at half its strength, and why it cannot is to be read. */}
    {row.reason && <Column as="li" pad="md"><Text variant="note">{row.reason}</Text></Column>}
  </Fragment>)}</ItemList></Column>;
  return <FrameContext value={inPane}>
    <ContentSplit aside={list} asideLabel="Percorso di analisi" width="sm" show={shown} onPanesChange={setPanes}><Screen /></ContentSplit>
  </FrameContext>;
}
