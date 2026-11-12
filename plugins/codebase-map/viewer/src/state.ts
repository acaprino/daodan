// The explorer's state and its transitions; the projection is computed from it, never stored.
import { EnvelopeError, parseEnvelope } from './envelope.ts';
import type { Envelope, View } from './envelope.ts';
import { childrenOf, indexOf, resolves } from './projection.ts';
import type { Filters } from './projection.ts';

export type ExplorerState = {
  envelope: Envelope; view: View; scope: string | null; selected: string | null; filters: Filters;
  open: string[]; flow: string | null; error: string | null; warning: string | null;
};
export type Action =
  | { type: 'select'; ref: string | null } | { type: 'open'; ref: string } | { type: 'up' }
  | { type: 'view'; view: View } | { type: 'filter'; filters: Filters } | { type: 'resetFilters' }
  | { type: 'toggleGroup'; ref: string } | { type: 'flow'; ref: string | null } | { type: 'replaceEnvelope'; json: unknown };

export function initialState(envelope: Envelope): ExplorerState {
  return { envelope, view: 'logical', scope: null, selected: null, filters: {}, open: [], flow: null, error: null, warning: null };
}

function parentOf(state: ExplorerState, ref: string): string | null {
  const groups = indexOf(state.envelope).groups[state.view].get(ref) ?? [];
  if (groups.length) return groups[0];
  const file = state.envelope.relations.find(relation => relation.kind === 'defines' && relation.target === ref);
  return file ? file.source : null;
}

export function reduce(state: ExplorerState, action: Action): ExplorerState {
  const known = (ref: string | null) => ref === null || indexOf(state.envelope).byRef.has(ref);
  switch (action.type) {
    case 'select':
      return known(action.ref) ? { ...state, selected: action.ref, error: null } : state;
    case 'open': {
      const entity = indexOf(state.envelope).byRef.get(action.ref);
      if (!entity || entity.type === 'feature' || !childrenOf(state.envelope, action.ref, state.view).length) return state;
      return { ...state, scope: action.ref, selected: null, open: [] };
    }
    case 'up':
      return state.scope === null ? state : { ...state, scope: parentOf(state, state.scope), selected: state.scope, open: [] };
    case 'view': {
      if (action.view === state.view) return state;
      const keep = state.selected !== null && resolves(state.envelope, state.selected, action.view);
      return { ...state, view: action.view, scope: null, open: [], selected: keep ? state.selected : null };
    }
    case 'filter':
      return { ...state, filters: { ...state.filters, ...action.filters } };
    case 'resetFilters':
      return { ...state, filters: {} };
    case 'toggleGroup':
      return { ...state, open: state.open.includes(action.ref) ? state.open.filter(ref => ref !== action.ref) : [...state.open, action.ref] };
    case 'flow':
      return action.ref === null || state.envelope.flows.some(flow => flow.ref === action.ref) ? { ...state, flow: action.ref } : state;
    case 'replaceEnvelope': {
      let envelope: Envelope;
      try {
        envelope = parseEnvelope(action.json);
      } catch (error) {
        return { ...state, error: error instanceof EnvelopeError ? error.message : String(error) };
      }
      const present = new Set(envelope.entities.map(entity => entity.ref));
      const vanished = [state.selected, state.scope].filter((ref): ref is string => ref !== null && !present.has(ref));
      const flow = state.flow && envelope.flows.some(item => item.ref === state.flow) ? state.flow : null;
      return {
        ...state, envelope, error: null, flow,
        selected: state.selected && present.has(state.selected) ? state.selected : null,
        scope: state.scope && present.has(state.scope) ? state.scope : null,
        open: state.open.filter(ref => present.has(ref)),
        warning: vanished.length ? `Non più presenti nel nuovo export: ${vanished.join(', ')}` : null,
      };
    }
  }
}
