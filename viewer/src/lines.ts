// The kinds of line of the two graphs, in the order of their key: a kind has one look, on the canvas and in the key.
import type { GraphLegendEntry } from '@acaprino/sigrid/graph';

type Look = Pick<GraphLegendEntry, 'label' | 'style' | 'tone'>;
export type LineKind = 'relation' | 'data' | 'flow' | 'observed' | 'sampled' | 'uncertain';
export const LINES: Record<LineKind, Look> = {
  relation: { label: 'Relazioni', style: 'solid', tone: 'default' },
  data: { label: 'Collegamenti di dati', style: 'dashed', tone: 'default' },
  flow: { label: 'Linee del flusso', style: 'solid', tone: 'accent' },
  observed: { label: 'Osservata in esecuzione', style: 'solid', tone: 'accent' },
  sampled: { label: 'Campionata dal profiler', style: 'dashed', tone: 'accent' },
  uncertain: { label: 'Prova insufficiente', style: 'dashed', tone: 'warning' },
};

// The key of what is drawn: the kinds it has, each with how many.
export const legendOf = (kinds: readonly LineKind[]): GraphLegendEntry[] => (Object.keys(LINES) as LineKind[])
  .map(kind => ({ ...LINES[kind], count: kinds.filter(item => item === kind).length })).filter(entry => entry.count > 0);
