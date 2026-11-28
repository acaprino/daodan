// The analysis: a path of steps, «Repository» and then the steps of the plan, the whole of it in sight, and one step on the screen at a
// time.
import { useEffect, useRef, useState } from 'react';
import { useFocusKept } from '@acaprino/imago';
import { Cell, Column } from '@acaprino/sigrid/primitives';
import { Steps } from '@acaprino/sigrid/components';
import { ContentSplit } from '@acaprino/sigrid/layout';
import { Loading } from '../src/states.tsx';
import { ScreenPanel } from './frame.tsx';
import { pathRows, REPOSITORY } from './path.ts';
import { PlanStepScreen } from './plan-step.tsx';
import { RepositoryScreen } from './repository-screen.tsx';
import { focusStep, StepFoot } from './step.tsx';
import { model, useModel } from './use-model.ts';

// In the window's action bar. The notices sit above the bar, never over the action.
export const analysisActions = () => <StepFoot />;

// Beside the step, or in a row above it where the two do not fit side by side.
function Path({ row }: { row: boolean }) {
  const s = useModel();
  const list = pathRows(s);
  return <Steps aria-label="Percorso di analisi" orientation={row ? 'horizontal' : 'vertical'}
    steps={list.map(({ label, detail, state, meta }) => ({ label, description: row ? undefined : detail || undefined, status: state, meta: meta || undefined }))}
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
  const rows = pathRows(s), row = panes === 1, at = rows.findIndex(step => step.id === stage) + 1;
  return <ContentSplit aside={<Column pad="lg"><Path row={false} /></Column>} asideLabel="Percorso" width="sm" show="main" step={720} onPanesChange={setPanes}>
    <ScreenPanel title="Analisi" subtitle={!row && `Passo ${at} di ${rows.length}`} tools={row && <Cell grow><Path row /></Cell>}>
      {stage === REPOSITORY ? <RepositoryScreen /> : <PlanStepScreen />}
    </ScreenPanel>
  </ContentSplit>;
}
