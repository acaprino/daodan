// The explorer's state and its transitions; the projection is computed from it, never stored.
import type { Envelope, View } from './envelope.ts';
import { childrenOf, indexOf, resolves } from './projection.ts';
import type { Filters } from './projection.ts';

export type ExplorerState = {
  envelope: Envelope; view: View; scope: string | null; selected: string | null; filters: Filters;
  open: string[]; flow: string | null; panel: Panel; warning: string | null;
};
// What the inspector shows when no element is chosen: the flow or the project, the one asked for last.
export type Panel = 'flow' | 'project' | null;
export type Action =
  | { type: 'select'; ref: string | null } | { type: 'open'; ref: string } | { type: 'up' } | { type: 'root' }
  | { type: 'view'; view: View } | { type: 'filter'; filters: Filters } | { type: 'resetFilters' }
  | { type: 'toggleGroup'; ref: string } | { type: 'flow'; ref: string | null } | { type: 'replaceEnvelope'; envelope: Envelope }
  | { type: 'load'; envelope: Envelope } | { type: 'info' } | { type: 'close' };

export function initialState(envelope: Envelope): ExplorerState {
  return { envelope, view: 'logical', scope: null, selected: null, filters: {}, open: [], flow: null, panel: null, warning: null };
}

// What the inspector shows: the element chosen first, then the flow or the project.
export function shownDetails(state: ExplorerState): 'entity' | Panel {
  return state.selected === null ? state.panel : 'entity';
}

// A chosen element takes the project's information away for good: it does not come back when the element is left.
const underChoice = (panel: Panel): Panel => (panel === 'project' ? null : panel);

function parentOf(state: ExplorerState, ref: string): string | null {
  const groups = indexOf(state.envelope).groups[state.view].get(ref) ?? [];
  if (groups.length) return groups[0];
  const file = state.envelope.relations.find(relation => relation.kind === 'defines' && relation.target === ref);
  return file ? file.source : null;
}

// Where the person is, from the system down to the scope: the way «Su» goes back, step by step.
export function placeOf(state: ExplorerState): string[] {
  const names: string[] = [], seen = new Set<string>();
  let ref = state.scope;
  while (ref !== null && !seen.has(ref)) {
    seen.add(ref);
    names.unshift(indexOf(state.envelope).byRef.get(ref)?.name ?? ref);
    ref = parentOf(state, ref);
  }
  return ['Sistema', ...names];
}

export function reduce(state: ExplorerState, action: Action): ExplorerState {
  if (action.type === 'load') return initialState(action.envelope);  // another run: nothing of the last one is kept
  const known = (ref: string | null) => ref === null || indexOf(state.envelope).byRef.has(ref);
  switch (action.type) {
    case 'select':
      if (!known(action.ref)) return state;
      return { ...state, selected: action.ref, panel: action.ref === null ? state.panel : underChoice(state.panel) };
    case 'open': {
      const entity = indexOf(state.envelope).byRef.get(action.ref);
      if (!entity || entity.type === 'feature' || !childrenOf(state.envelope, action.ref, state.view).length) return state;
      return { ...state, scope: action.ref, selected: null, open: [] };
    }
    case 'up':
      return state.scope === null ? state
        : { ...state, scope: parentOf(state, state.scope), selected: state.scope, panel: underChoice(state.panel), open: [] };
    case 'root':
      return { ...state, scope: null, selected: null, open: [] };
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
      if (action.ref === null) return { ...state, flow: null, panel: state.panel === 'flow' ? null : state.panel };
      return state.envelope.flows.some(flow => flow.ref === action.ref) ? { ...state, flow: action.ref, panel: 'flow' } : state;
    case 'info':
      return { ...state, selected: null, panel: 'project' };
    case 'close':  // the flow stays chosen: pressing its place shows its steps again
      return { ...state, selected: null, panel: null };
    case 'replaceEnvelope': {
      const { envelope } = action;
      const present = new Set(envelope.entities.map(entity => entity.ref));
      const vanished = [state.selected, state.scope].filter((ref): ref is string => ref !== null && !present.has(ref));
      const flow = state.flow && envelope.flows.some(item => item.ref === state.flow) ? state.flow : null;
      return {
        ...state, envelope, flow, panel: state.panel === 'flow' && !flow ? null : state.panel,
        selected: state.selected && present.has(state.selected) ? state.selected : null,
        scope: state.scope && present.has(state.scope) ? state.scope : null,
        open: state.open.filter(ref => present.has(ref)),
        warning: vanished.length ? `Non più presenti nel nuovo export: ${vanished.join(', ')}` : null,
      };
    }
  }
}
