// The analysis: a path of steps, the whole of it in sight, and one step on the screen at a time.
import { useEffect, useRef, useState } from 'react';
import type { ComponentType } from 'react';
import { useFocusKept } from '@acaprino/imago';
import { Cell, Column } from '@acaprino/sigrid/primitives';
import { Steps } from '@acaprino/sigrid/components';
import { ContentSplit } from '@acaprino/sigrid/layout';
import { Loading } from '../src/states.tsx';
import { ScreenPanel } from './frame.tsx';
import { PremapScreen } from './premap-screen.tsx';
import { RepositoryScreen } from './repository-screen.tsx';
import { RunScreen } from './run-screen.tsx';
import { stages } from './stages.ts';
import { focusStep, StepFoot } from './step.tsx';
import { STAGES } from './storage.ts';
import type { Stage } from './storage.ts';
import { SynthesisScreen } from './synthesis-screen.tsx';
import { model, useModel } from './use-model.ts';

const SCREEN: Record<Stage, ComponentType> = { repository: RepositoryScreen, premap: PremapScreen, analysis: RunScreen, synthesis: SynthesisScreen };
// In the window's action bar. The notices sit above the bar, never over the action.
export const analysisActions = () => <StepFoot />;

// Beside the step, or in a row above it where the two do not fit side by side.
function Path({ row }: { row: boolean }) {
  const s = useModel();
  const list = stages(s);
  return <Steps aria-label="Percorso di analisi" orientation={row ? 'horizontal' : 'vertical'}
    steps={list.map(({ label, detail, state, meta, reason }) => ({
      label, description: row || reason ? undefined : detail, status: state, meta: meta || undefined, disabled: reason !== '', reason,
    }))}
    current={list.findIndex(step => step.id === s.kept.analysisStage)} onStepSelect={index => model.selectStage(list[index].id)} />;
}

export function AnalysisScreen() {
  const s = useModel();
  const [panes, setPanes] = useState<1 | 2>(2);
  const stage = s.kept.analysisStage, last = useRef(stage);
  useFocusKept(panes);
  // Another step: its title takes the focus, unless the person is in the bar or in a dialog. Never as the screen opens.
  useEffect(() => {
    if (last.current === stage) return;
    last.current = stage;
    if (!document.activeElement?.closest('header, [role="dialog"]')) focusStep();
  }, [stage]);
  if (!s.server) {
    return <ScreenPanel title="Analisi">
      {!s.serverError && <Column pad="lg"><Loading label="Lettura dello stato del server…" /></Column>}
    </ScreenPanel>;
  }
  const row = panes === 1, at = STAGES.indexOf(stage) + 1, Screen = SCREEN[stage];
  return <ContentSplit aside={<Column pad="lg"><Path row={false} /></Column>} asideLabel="Percorso" width="sm" show="main" step={720} onPanesChange={setPanes}>
    <ScreenPanel title="Analisi" subtitle={!row && `Passo ${at} di ${STAGES.length}`} tools={row && <Cell grow><Path row /></Cell>}><Screen /></ScreenPanel>
  </ContentSplit>;
}
