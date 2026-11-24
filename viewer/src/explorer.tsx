// The map in the content: where the person is, the filters, and the canvas.
import type { RefObject } from 'react';
import { Button, Cluster, Column, Empty, FormField, Icon, Note, SearchField, Select, Text } from '@acaprino/sigrid';
import type { Model } from './model.ts';
import { indexOf } from './projection.ts';
import { TYPE_LABEL } from './icons.ts';

export function Explorer({ model, search }: { model: Model; search: RefObject<HTMLInputElement | null> }) {
  const { state, dispatch, projection } = model;
  const scopeName = state.scope ? indexOf(state.envelope).byRef.get(state.scope)?.name ?? state.scope : null;
  const types = [...new Set(projection.nodes.map(node => node.type))].sort();
  const filtered = projection.counts.filtered;
  const reset = () => dispatch({ type: 'resetFilters' });
  const message = state.error ?? state.warning;
  return <Column gap="lg">
    {message && <Note tone={state.error ? 'error' : 'warning'} title={message} />}
    <Cluster as="nav" aria-label="Posizione">
      <Button variant="ghost" size="sm" onClick={() => dispatch({ type: 'root' })}>Sistema</Button>
      {scopeName && <><Icon name="chevron" /><Text aria-current="page">{scopeName}</Text>
        <Button variant="ghost" size="sm" onClick={() => dispatch({ type: 'up' })}><Icon name="back" />Su</Button></>}
    </Cluster>
    <Cluster gap="md" align="end">
      <FormField label="Cerca per nome">
        <SearchField ref={search} placeholder="Nome di un elemento" value={state.filters.text ?? ''} onValueChange={text => dispatch({ type: 'filter', filters: { text } })} />
      </FormField>
      <FormField label="Tipo di entità">
        <Select aria-label="Tipo di entità" value={state.filters.types?.[0] ?? ''} onValueChange={type => dispatch({ type: 'filter', filters: { types: type ? [type] : [] } })}
          options={[{ value: '', label: 'Tutti i tipi' }, ...types.map(type => ({ value: type, label: TYPE_LABEL[type] ?? type }))]} />
      </FormField>
      {filtered > 0 && <Button variant="ghost" onClick={reset}><Icon name="clearFilter" />Azzera filtri ({filtered} nascosti)</Button>}
    </Cluster>
    {/* shortcut: what is in view is counted and not drawn, until ticket 17 of the port puts the canvas here (GraphCanvas `fill`, in Sigrid's next release) */}
    {projection.nodes.length > 0
      ? <Empty title={`${projection.nodes.length} nodi · ${projection.edges.length} relazioni visibili`} />
      : <Empty title="Nessun elemento visibile." action={filtered > 0 && <Button variant="outline" onClick={reset}>Azzera filtri</Button>} />}
  </Column>;
}
