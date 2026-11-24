// What both pages say while something is read, and where it could not be.
import type { ReactNode } from 'react';
import { Button, Column, Icon, Progress, Text } from '@acaprino/sigrid/primitives';
import { Note } from '@acaprino/sigrid/components';

export const focusContent = () => document.querySelector<HTMLElement>('main')?.focus({ preventScroll: true });

export function Loading({ label }: { label: string }) {
  return <Column aria-busy><Progress aria-label={label} value={null} /></Column>;
}

// What failed, and why. With `retry` the note goes when it is asked again, and its button with it: the focus goes to the content,
// unless `retry` takes it nearer. `actions`: what else can be done.
export function Failed({ title, cause, retry, actions }: { title: string; cause?: string | null; retry?: () => void; actions?: ReactNode }) {
  const again = () => { focusContent(); retry?.(); };
  return <Note tone="error" title={title} actions={retry && <><Button variant="outline" onClick={again}><Icon name="refresh" />Riprova</Button>{actions}</>}>
    {cause && <Text pre data-selectable="">{cause}</Text>}
  </Note>;
}
