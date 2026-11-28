// The step on the screen: its title, what it asks, and what it shows; and its foot, in the window's action bar.
// Sigrid's `Wizard` is not it: its path is a row alone, its steps go one after the other, and its buttons are in the content. What it does
// is kept: the way back is off on the first step, and the title takes the focus when the step changes.
import { useId } from 'react';
import type { KeyboardEvent, ReactNode } from 'react';
import { useFocusKept } from '@acaprino/imago';
import { useMedia } from '@acaprino/sigrid';
import { Button, Cell, Column, Heading, Icon, Spacer, Split, Text } from '@acaprino/sigrid/primitives';
import { useFrame } from './frame.tsx';
import { repositorySlug } from './repository.ts';
import { footOf, pathRows, REPOSITORY } from './path.ts';
import type { Stage } from './storage.ts';
import { model, useModel } from './use-model.ts';

const TITLE = 'step-title';
export const STEP_FORM = 'step-form';  // the fields of a step, which the solid button sends
export const focusStep = () => document.getElementById(TITLE)?.focus();

// What the solid button does, and Enter on a field of the step or on its title.
export function useGoOn(): () => void {
  const { go } = useFrame();
  return () => {
    const { off, busy, act } = footOf(model.snapshot());
    if (off || busy) return;
    if (act === 'graph') go(model.showFullGraph);
    else if (act === 'select') model.selectRepository();
    else if (act === 'verify') {
      model.verifyRepositoryUrl();
      if (!repositorySlug(model.snapshot().kept.repositoryUrl)) document.getElementById(STEP_FORM)?.querySelector('input')?.focus();
    } else model.selectStage(act);
  };
}

// Its number and title are its place on the path and its words there.
export function Step({ stage, line, end, children }: { stage: Stage; line: ReactNode; end?: ReactNode; children: ReactNode }) {
  const rows = pathRows(useModel()), at = rows.findIndex(row => row.id === stage);
  const goOn = useGoOn();
  const enter = (event: KeyboardEvent) => {
    if (event.key !== 'Enter' || event.repeat) return;
    event.preventDefault();
    goOn();
  };
  return <Column as="section" aria-labelledby={TITLE} pad="lg" gap="lg" width="page">
    <Column gap="xs">
      <Split><Heading id={TITLE} tabIndex={-1} onKeyDown={enter}>{at + 1}. {rows[at]?.label ?? stage}</Heading>{end}</Split>
      <Text as="p" variant="soft">{line}</Text>
    </Column>
    {children}
  </Column>;
}

// The foot never moves: the way back at the start, the one solid action at the end. Where the two and the note do not fit in a row, the
// note has a line of its own, which is always there.
export function StepFoot() {
  const s = useModel();
  const why = useId();
  const narrow = useMedia('(width < 620px)');
  const goOn = useGoOn();
  useFocusKept(narrow);
  const { back, label, off, busy, note } = footOf(s);
  const asks = s.kept.analysisStage === REPOSITORY;
  const said = <Text id={why} variant="note">{note}</Text>;
  const backward = <Button variant="outline" disabled={back === null} onClick={() => { if (back) model.selectStage(back); }}><Icon name="back" />Indietro</Button>;
  const forward = <Button type={asks ? 'submit' : 'button'} form={asks ? STEP_FORM : undefined} onClick={asks ? undefined : goOn}
    disabled={off} loading={busy !== ''} loadingText={busy || undefined} aria-describedby={why}>{label}</Button>;
  return narrow ? <Cell grow><Column>{said}<Split>{backward}{forward}</Split></Column></Cell>
    : <>{backward}<Spacer />{said}{forward}</>;
}
