// What the screens share: the field Ctrl+F goes to, the inspector, and the panel each is drawn in.
import { createContext, useContext } from 'react';
import type { ReactNode, RefObject } from 'react';
import { Button, Column, Icon, Note, Panel, Text } from '@acaprino/sigrid';
import type { PanelProps } from '@acaprino/sigrid';
import { useModel } from './use-model.ts';

// What the inspector shows. `content` reads the model by itself, so it follows what it shows.
export type Detail = { title: string; content: ReactNode; footer?: ReactNode };
export type Frame = {
  search: RefObject<HTMLInputElement | null>;  // a screen with a search gives it to its field
  detail: Detail | null; show: (detail: Detail) => void; close: () => void;
  back?: () => void;                           // to the list of the stages, where it and a stage do not fit side by side
};

export const FrameContext = createContext<Frame | null>(null);
export function useFrame(): Frame {
  const frame = useContext(FrameContext);
  if (!frame) throw new Error('outside the frame');
  return frame;
}

// The panel of a screen. A server that cannot be reached is said at its head, on every screen.
export function ScreenPanel({ actions, children, ...panel }: PanelProps) {
  const { serverError } = useModel();
  const { back } = useFrame();
  return <Panel {...panel} actions={back ? <><Button variant="ghost" size="sm" onClick={back}><Icon name="back" />Percorso</Button>{actions}</> : actions}>
    <Column fill>
      {serverError && <Column pad="lg"><Note tone="error" title="Server non raggiungibile."><Text data-selectable="">{serverError}</Text></Note></Column>}
      {children}
    </Column>
  </Panel>;
}
