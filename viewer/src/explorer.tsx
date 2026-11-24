// The content: one panel, with where the person is, its controls and filters, and the canvas as its body. The controls are
// there in every state and never move: those that do nothing now are disabled (R14).
import { useMemo } from 'react';
import type { ReactNode, RefObject } from 'react';
import { Button, Cluster, Column, Empty, Icon, Note, Panel, SearchField, Select, Text, useMedia } from '@acaprino/sigrid';
import type { Model } from './model.ts';
import { typesIn } from './projection.ts';
import { placeOf, shownDetails } from './state.ts';
import { TYPE_LABEL } from './icons.ts';
import { counted } from './names.ts';

type ExplorerProps = {
  model: Model; title: string; search: RefObject<HTMLInputElement | null>;
  ready: boolean;       // the map is shown: without it the body is `children` alone
  runs: ReactNode;      // the choice of the run, where there is one
  children: ReactNode;  // over the canvas, or in its place
};

export function Explorer({ model, title, search, ready, runs, children }: ExplorerProps) {
  const { state, dispatch, projection } = model;
  const { envelope, view, scope, open } = state;
  // Beside a docked inspector, and on a phone, the header has no room for the run: it goes with the filters, which wrap.
  const tight = useMedia('(width < 1200px)');
  const chosen = state.filters.types?.[0] ?? '';
  const types = useMemo(() => typesIn(envelope, view, scope, open, chosen), [envelope, view, scope, open, chosen]);
  const filtered = ready ? projection.counts.filtered : 0;
  const reset = () => dispatch({ type: 'resetFilters' });
  const info = ready && shownDetails(state) === 'project';
  const message = state.error ?? state.warning;
  const filters = <>
    <SearchField ref={search} disabled={!ready} aria-label="Cerca per nome" placeholder="Cerca per nome" value={state.filters.text ?? ''}
      onValueChange={text => dispatch({ type: 'filter', filters: { text } })} />
    <Select size="sm" aria-label="Tipo di entità" disabled={!ready} value={chosen} onValueChange={type => dispatch({ type: 'filter', filters: { types: type ? [type] : [] } })}
      options={[{ value: '', label: 'Tutti i tipi' }, ...types.map(type => ({ value: type, label: TYPE_LABEL[type] ?? type }))]} />
    {tight && runs}
    <Button variant="ghost" size="sm" disabled={filtered === 0} onClick={reset}><Icon name="clearFilter" />Azzera filtri ({counted(filtered, 'nascosto', 'nascosti')})</Button>
  </>;
  return <Panel title={title}
    subtitle={ready ? [placeOf(state).join(' / '), counted(projection.nodes.length, 'nodo', 'nodi'),
      counted(projection.edges.length, 'relazione visibile', 'relazioni visibili')].join(' · ') : undefined}
    actions={<>
      <Button variant="ghost" size="sm" disabled={!ready || scope === null} onClick={() => dispatch({ type: 'up' })}><Icon name="back" />Su</Button>
      {!tight && runs}
      <Button variant={info ? 'secondary' : 'ghost'} size="sm" aria-label="Informazioni sul progetto" aria-pressed={info} disabled={!ready}
        onClick={() => dispatch({ type: info ? 'close' : 'info' })}>{tight ? 'Informazioni' : 'Informazioni sul progetto'}</Button>
    </>}
    tools={tight ? filters : <Cluster wrap={false}>{filters}</Cluster>}>
    {children}
    {ready && <>
      {message && <Column pad="lg"><Note tone={state.error ? 'error' : 'warning'} title={<Text data-selectable="">{message}</Text>} /></Column>}
      {/* shortcut: the map is not drawn, until ticket 17 of the port puts the canvas here (GraphCanvas `fill`, in Sigrid 5.1.0) */}
      {projection.nodes.length > 0
        ? <Empty fill title="Scegli un elemento dalla barra laterale" description="Ne vedi il ruolo, i collegamenti e i flussi che lo attraversano." />
        : <Empty fill title="Nessun elemento visibile." action={filtered > 0 && <Button variant="outline" size="sm" onClick={reset}>Azzera filtri</Button>} />}
    </>}
  </Panel>;
}
