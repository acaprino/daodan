// The analysis: its stages in their order, and the one chosen beside them.
import { useState } from 'react';
import type { ComponentType, ReactNode } from 'react';
import { Badge, Column, ContentSplit, ItemList, ItemRow, Progress, Text } from '@acaprino/sigrid';
import { FrameContext, ScreenPanel, useFrame } from './frame.tsx';
import { PremapScreen } from './premap-screen.tsx';
import { RepositoryActions, RepositoryScreen } from './repository-screen.tsx';
import { RunScreen } from './run-screen.tsx';
import type { Snapshot } from './snapshot.ts';
import { STAGE_WORD, stages } from './stages.ts';
import type { Stage } from './storage.ts';
import { SynthesisScreen } from './synthesis-screen.tsx';
import { model, useModel } from './use-model.ts';

// What each stage draws and, in the window's action bar, what it leads to. The notices sit above the bar, never over the action.
const STAGE: Record<Stage, { Screen: ComponentType; Actions?: ComponentType }> = {
  repository: { Screen: RepositoryScreen, Actions: RepositoryActions },
  premap: { Screen: PremapScreen },
  analysis: { Screen: RunScreen },
  synthesis: { Screen: SynthesisScreen },
};
export function analysisActions(s: Snapshot): ReactNode {
  const { Actions } = STAGE[s.kept.analysisStage];
  return s.kept.screen === 'analysis' && s.server && Actions ? <Actions /> : null;
}

export function AnalysisScreen() {
  const s = useModel();
  const frame = useFrame();
  const [panes, setPanes] = useState<1 | 2>(2);
  const [shown, setShown] = useState<'aside' | 'main'>('main');  // the pane in sight where one fits
  if (!s.server) {
    return <ScreenPanel title="Analisi">
      {!s.serverError && <Column pad="lg" aria-busy><Progress aria-label="Lettura dello stato del server…" value={null} /></Column>}
    </ScreenPanel>;
  }
  const { Screen } = STAGE[s.kept.analysisStage];
  const list = <Column pad="sm"><ItemList aria-label="Percorso di analisi">{stages(s).map(row =>
    <ItemRow key={row.id} title={row.label} current={row.id === s.kept.analysisStage} disabled={row.reason !== ''}
      // `pre`: a reason wraps, it is never cut.
      description={<Text pre>{row.reason || row.detail}</Text>}
      meta={row.state !== 'failed' && STAGE_WORD[row.state]} end={row.state === 'failed' && <Badge variant="destructive">{STAGE_WORD.failed}</Badge>}
      onClick={() => { model.selectStage(row.id); setShown('main'); }} />)}
  </ItemList></Column>;
  return <FrameContext value={panes === 1 ? { ...frame, back: () => setShown('aside') } : frame}>
    <ContentSplit aside={list} asideLabel="Percorso di analisi" width="sm" show={shown} onPanesChange={setPanes}><Screen /></ContentSplit>
  </FrameContext>;
}
