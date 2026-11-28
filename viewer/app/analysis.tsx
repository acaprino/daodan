// The analysis: a path of steps, «Repository» and then the steps of the plan, the whole of it in sight, and one step on the screen at a
// time.
import { useEffect, useRef, useState } from 'react';
import { useFocusKept } from '@acaprino/imago';
import { Cell, Column } from '@acaprino/sigrid/primitives';
import { Steps } from '@acaprino/sigrid/components';
import { ContentSplit } from '@acaprino/sigrid/layout';
import { Fold } from '../src/listed.tsx';
import { Loading } from '../src/states.tsx';
import { ScreenPanel } from './frame.tsx';
import { pathRows, REPOSITORY } from './path.ts';
import { PlanStepScreen } from './plan-step.tsx';
import { RepositoryScreen } from './repository-screen.tsx';
import { focusStep, StepFoot } from './step.tsx';
import { model, useModel } from './use-model.ts';

// In the window's action bar. The notices sit above the bar, never over the action.
export const analysisActions = () => <StepFoot />;

// Beside the step, or behind its row above it where the two do not fit side by side: a row of Sigrid's `Steps` holds the dots of all
// the steps of the plan and the name of the one on the screen, which at 390 px sticks out of nine (an open point for Sigrid).
function Path() {
  const s = useModel();
  const list = pathRows(s);
  return <Steps aria-label="Percorso di analisi"
    steps={list.map(({ label, detail, state, meta }) => ({ label, description: detail || undefined, status: state, meta: meta || undefined }))}
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
  const where = `Passo ${at} di ${rows.length}`;
  return <ContentSplit aside={<Column pad="lg"><Path /></Column>} asideLabel="Percorso" width="sm" show="main" step={720} onPanesChange={setPanes}>
    <ScreenPanel title="Analisi" subtitle={!row && where} tools={row && <Cell grow><Fold label="Percorso" summary={where}><Path /></Fold></Cell>}>
      {stage === REPOSITORY ? <RepositoryScreen /> : <PlanStepScreen />}
    </ScreenPanel>
  </ContentSplit>;
}
