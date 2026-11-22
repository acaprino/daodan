// The few pieces of Imago's markup that both the map and its session panel write from React. Each renders the package's
// string (the one way to write it) and wires nothing of its own.
import { useEffect, useRef, useState } from 'react';
import { buttonHtml, iconMarkup, LOADING_DELAY_MS, noteHtml, panelStateHtml, showAfter } from '@acaprino/imago/ui';
import type { IconName, NoteOptions, PanelStateMarkup } from '@acaprino/imago/ui';

// A control's icon is Imago's drawing of it.
export const Icon = ({ name }: { name: IconName }) => <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: iconMarkup(name) }} />;

// A message that stays in the page: its tone, its role and its markup are Imago's.
export const Note = (options: NoteOptions) => <div dangerouslySetInnerHTML={{ __html: noteHtml(options) }} />;

export const retryHtml = buttonHtml('Riprova', 'retry', { icon: 'reload' });
export const resetHtml = buttonHtml('Azzera filtri', 'reset');

// A panel that is empty or failed: Imago's layer, with the one button it carries wired to `onAction`.
export function PanelState({ state, onAction }: { state: PanelStateMarkup; onAction?: () => void }) {
  const host = useRef<HTMLDivElement>(null);
  return <div ref={host} dangerouslySetInnerHTML={{ __html: panelStateHtml(state) }}
    onClick={event => { if (onAction && (event.target as HTMLElement).closest('button')) onAction(); }} />;
}

// Whether something that is being waited for has taken longer than the delay: under it, nothing is shown.
export function useSlow(waiting: boolean): boolean {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    setSlow(false);
    return waiting ? showAfter(LOADING_DELAY_MS, () => setSlow(true)) : undefined;
  }, [waiting]);
  return slow;
}
