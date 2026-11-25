// What the screens share: the field Ctrl+F goes to, the details, where the focus goes, and the panel each screen is drawn in.
import { createContext, useContext } from 'react';
import type { ReactNode, RefCallback, RefObject } from 'react';
import { Column } from '@acaprino/sigrid/primitives';
import { Panel } from '@acaprino/sigrid/layout';
import type { IconName } from '@acaprino/sigrid/primitives';
import type { PanelProps } from '@acaprino/sigrid/layout';
import { Failed } from '../src/states.tsx';
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
  search: RefCallback<HTMLInputElement>;       // a screen with a search gives it to its field, while it can be used
  field: HTMLInputElement | null;              // that field
  reveal: RefObject<(() => void) | null>;      // shows what the search is in, while it is hidden
  detail: Detail | null; show: (detail: Detail) => void; close: () => void;
  go: (act: () => void) => void;               // to another screen: the details close, and the content takes the focus
};

export const FrameContext = createContext<Frame | null>(null);
export function useFrame(): Frame {
  const frame = useContext(FrameContext);
  if (!frame) throw new Error('outside the frame');
  return frame;
}

// The panel of a screen. A server that cannot be reached is said at its head, on every screen.
export function ScreenPanel({ children, ...panel }: PanelProps) {
  const serverError = useModelSlice(s => s.serverError);
  return <Panel {...panel}>
    <Column fill>
      {serverError && <Column pad="lg"><Failed title="Server non raggiungibile." cause={serverError} /></Column>}
      {children}
    </Column>
  </Panel>;
}
