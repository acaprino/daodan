// What the screens share: the field Ctrl+F goes to, the details, where the focus goes, and the panel each screen is drawn in.
import { createContext, useContext, useLayoutEffect } from 'react';
import type { ReactNode, RefObject } from 'react';
import { Button, Column, Icon, Note, Panel, Text } from '@acaprino/sigrid';
import type { IconName, PanelProps } from '@acaprino/sigrid';
import { useModelSlice } from './use-model.ts';

// What the details show. `content` reads the model by itself, so it follows what it shows.
export type Detail = {
  id: string;                      // whose they are: a screen knows its own by it
  key?: string;                    // the thing they are of: those of another one are drawn anew
  title: string;                   // of the inspector: what they are
  icon: IconName; image?: string; name: ReactNode;  // their heading, which is announced when it changes; `image`: a logo in the icon's place
  content: ReactNode; footer?: ReactNode;
  opener?: HTMLElement | null;     // what takes the focus back when they close with it inside: what has it as they open, unless it is said
};
export type Frame = {
  search: RefObject<HTMLInputElement | null>;  // a screen with a search gives it to its field
  reveal: RefObject<(() => void) | null>;      // shows the pane the search is in, while it is hidden
  detail: Detail | null; show: (detail: Detail) => void; close: () => void;
  go: (act: () => void) => void;               // to another screen: the details close, and the content takes the focus
  back?: () => void;                           // to the list of the stages, where it and a stage do not fit side by side
};

export const FrameContext = createContext<Frame | null>(null);
export function useFrame(): Frame {
  const frame = useContext(FrameContext);
  if (!frame) throw new Error('outside the frame');
  return frame;
}

export const focusContent = () => document.querySelector<HTMLElement>('main')?.focus({ preventScroll: true });

let held: EventTarget | null = null;  // what had the focus last: once hidden or removed the page no longer says it
document.addEventListener('focusin', event => { held = event.target; });
// Where what had the focus has gone with what held it (a pane that hides, a stage that gives way to another, the screens that move to
// the foot), the content takes it. `where`: what is in sight.
export function useFocusKept(...where: unknown[]) {
  useLayoutEffect(() => {
    const at = document.activeElement === document.body ? held : document.activeElement;
    if (at instanceof Element && (!at.isConnected || at.closest('[hidden]'))) focusContent();
  }, where);
}

// The panel of a screen. A server that cannot be reached is said at its head, on every screen.
export function ScreenPanel({ actions, children, ...panel }: PanelProps) {
  const serverError = useModelSlice(s => s.serverError);
  const { back } = useFrame();
  return <Panel {...panel} actions={back ? <><Button variant="ghost" size="sm" onClick={back}><Icon name="back" />Percorso</Button>{actions}</> : actions}>
    <Column fill>
      {serverError && <Column pad="lg"><Note tone="error" title="Server non raggiungibile."><Text data-selectable="">{serverError}</Text></Note></Column>}
      {children}
    </Column>
  </Panel>;
}
