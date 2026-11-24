// The explorer's state and what is projected from it, for the whole page: the sidebar, the details and the canvas read it.
import { useEffect, useMemo, useReducer, useRef } from 'react';
import { parseEnvelope, SCHEMA } from './envelope.ts';
import type { Envelope } from './envelope.ts';
import { dataLinks, flowFocus, project } from './projection.ts';
import { initialState, reduce } from './state.ts';

const EMPTY = parseEnvelope({ schema: SCHEMA, entities: [], relations: [], memberships: [] });
export type Model = ReturnType<typeof useExplorer>;

export function useExplorer(envelope: Envelope | null) {
  const [state, dispatch] = useReducer(reduce, EMPTY, initialState);
  const shown = useRef<Envelope | null>(null);
  useEffect(() => {  // the first export of a run starts clean, a later one keeps the person's place
    if (!envelope) { shown.current = null; return; }
    dispatch(shown.current ? { type: 'replaceEnvelope', json: envelope } : { type: 'load', envelope });
    shown.current = envelope;
  }, [envelope]);
  const projection = useMemo(() => project(state.envelope, state.view, state.scope, state.filters, state.open, state.selected),
    [state.envelope, state.view, state.scope, state.filters, state.open, state.selected]);
  const focus = useMemo(() => (state.flow ? flowFocus(state.envelope, state.flow, projection) : null), [state.flow, projection]);
  const data = useMemo(() => (focus ? [] : dataLinks(state.envelope, projection)), [focus, projection]);
  const edges = useMemo(() => [...projection.edges, ...data, ...(focus?.edges ?? [])], [projection, data, focus]);
  const selectedIds = new Set(state.selected ? projection.owners[state.selected] ?? [] : []);
  return { state, dispatch, projection, focus, data, edges, selectedIds, ready: envelope !== null && shown.current !== null && state.envelope !== EMPTY };
}
