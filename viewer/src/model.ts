// The explorer's state and what is projected from it, for the whole page: the sidebar, the details and the canvas read it.
import { useEffect, useMemo, useReducer, useRef } from 'react';
import { parseEnvelope, SCHEMA } from './envelope.ts';
import type { Envelope } from './envelope.ts';
import { dataLinks, flowFocus, keptBy, project } from './projection.ts';
import { initialState, reduce } from './state.ts';

const EMPTY = parseEnvelope({ schema: SCHEMA, entities: [], relations: [], memberships: [] });
// What the page is doing: there is no run, its export cannot be read, it is being read, or it is shown.
export type Phase = 'none' | 'failed' | 'loading' | 'ready';
export type Model = ReturnType<typeof useExplorer>;
// What was last asked for outside the canvas, to bring into its view: an element, or the nodes of a flow.
export type Shown = { ref: string } | { flow: string };

export function useExplorer(envelope: Envelope | null) {
  const [state, dispatch] = useReducer(reduce, EMPTY, initialState);
  const shown = useRef<Envelope | null>(null);
  useEffect(() => {  // the first export of a run starts clean, a later one keeps the person's place
    if (!envelope) { shown.current = null; return; }
    dispatch(shown.current ? { type: 'replaceEnvelope', envelope } : { type: 'load', envelope });
    shown.current = envelope;
  }, [envelope]);
  // Of a choice only what the filters would hide changes what is projected: any other choice builds nothing again.
  const kept = keptBy(state.envelope, state.filters, state.selected);
  const projection = useMemo(() => project(state.envelope, state.view, state.scope, state.filters, state.open, kept),
    [state.envelope, state.view, state.scope, state.filters, state.open, kept]);
  const focus = useMemo(() => (state.flow ? flowFocus(state.envelope, state.flow, projection) : null), [state.flow, projection]);
  const data = useMemo(() => (focus ? [] : dataLinks(state.envelope, projection)), [focus, projection]);
  const edges = useMemo(() => [...projection.edges, ...data, ...(focus?.edges ?? [])], [projection, data, focus]);
  const selectedIds = new Set(state.selected ? projection.owners[state.selected] ?? [] : []);
  return { state, dispatch, projection, focus, data, edges, selectedIds, ready: envelope !== null && shown.current !== null && state.envelope !== EMPTY };
}
