// The details in the inspector: the element chosen, or what the project is and how its map is read.
import { Button, Cluster, Column, DescriptionList, Heading, Icon, Inspector, ItemList, ItemRow, Note, Section, Text } from '@acaprino/sigrid';
import type { Entity, Envelope } from './envelope.ts';
import { childrenOf, flowsThrough, indexOf } from './projection.ts';
import type { Model } from './model.ts';
import { FLOW_ICON, FRESHNESS_LABEL, iconFor, LINK_LABEL, STATUS_LABEL, TYPE_LABEL } from './icons.ts';
import { entityName, flowTitle, projectName } from './names.ts';

const LISTED = 8;  // the files named for one technology, and the evidence of one element

// The technologies of the project, or those of one build unit (`ids`), each with the files that show it, in words.
function Technologies({ envelope, ids }: { envelope: Envelope; ids?: string[] }) {
  const shown = envelope.technologies.filter(item => !ids || ids.includes(item.id));
  if (!shown.length) return null;
  return <Section title="Tecnologie" level={3} icon={<Icon name="labels" />}>
    <DescriptionList items={shown.map(item => ({ name: item.name, value: <Column gap="xs">
      <Text>{item.type}</Text>
      {item.paths.slice(0, LISTED).map(path => <Text key={path} variant="note" pre>{path}</Text>)}
      {item.paths.length > LISTED && <Text variant="note">e altri {item.paths.length - LISTED}</Text>}
    </Column> }))} />
  </Section>;
}

function ProjectDetails({ envelope }: { envelope: Envelope }) {
  return <Column gap="lg" aria-live="polite" data-selectable="">
    <Column gap="xs">
      <Text variant="kicker">Come leggere la mappa</Text>
      <Heading size="small">{projectName(envelope) || 'Progetto'}</Heading>
      <Text as="p" variant="soft">Seleziona un nodo per vederne il ruolo, i collegamenti e i flussi che lo attraversano. Doppio clic su un nodo con un numero per entrarci.</Text>
    </Column>
    <DescriptionList items={[
      { name: 'Entità', value: envelope.entities.length },
      { name: 'Relazioni', value: envelope.relations.length },
      { name: "Flussi dai punti d'ingresso", value: envelope.flows.length },
      { name: 'Lacune dichiarate', value: envelope.gaps.length },
    ]} />
    <Text as="p" variant="muted">Nei flussi puoi leggere il sito e la provenienza della prova per ogni passaggio.</Text>
    <Technologies envelope={envelope} />
  </Column>;
}

function EntityDetails({ model, entity }: { model: Model; entity: Entity }) {
  const { state, dispatch, edges } = model;
  const envelope = state.envelope;
  const flows = flowsThrough(envelope, entity.ref, state.view);
  const canOpen = entity.type !== 'feature' && childrenOf(envelope, entity.ref, state.view).length > 0;
  const gaps = envelope.gaps.filter(gap => gap.refs.includes(entity.ref));
  const lines = Array.isArray(entity.lines) ? entity.lines.filter(Boolean).join('–') : entity.lines;
  const related = edges.filter(edge => edge.source.startsWith(`${entity.ref}@`) || edge.target.startsWith(`${entity.ref}@`));
  return <Column gap="lg" aria-live="polite" data-selectable="">
    <Column gap="xs">
      <Cluster gap="xs"><Icon name={iconFor({ nodeType: entity.node_type, type: entity.type })} />
        <Text variant="kicker">{entity.node_type ?? TYPE_LABEL[entity.type] ?? entity.type} · {entity.location === 'external' ? 'esterno' : 'interno'}</Text></Cluster>
      <Heading size="small">{entity.name}</Heading>
      {entity.description && <Text as="p" variant="soft">{entity.description}</Text>}
    </Column>
    <DescriptionList items={[
      entity.path ? { name: 'Percorso', value: `${entity.path}${lines ? `:${lines}` : ''}`, code: true } : null,
      entity.provenance ? { name: 'Provenienza', value: entity.provenance } : null,
      entity.status ? { name: 'Stato', value: STATUS_LABEL[entity.status] ?? entity.status } : null,
      entity.freshness ? { name: 'Scheda', value: FRESHNESS_LABEL[entity.freshness] ?? entity.freshness } : null,
    ]} />
    {canOpen && <Cluster><Button onClick={() => dispatch({ type: 'open', ref: entity.ref })}><Icon name="folderOpen" />Entra in {entity.name}</Button></Cluster>}
    {entity.technologies && <Technologies envelope={envelope} ids={entity.technologies} />}
    {flows.length > 0 && <Section title="Flussi che lo attraversano" level={3} icon={<Icon name={FLOW_ICON} />}>
      <ItemList aria-label="Flussi che lo attraversano">{flows.map(flow =>
        <ItemRow key={flow.ref} title={flowTitle(envelope, flow)} wrapTitle current={state.flow === flow.ref} onClick={() => dispatch({ type: 'flow', ref: flow.ref })} />)}</ItemList>
    </Section>}
    {related.length > 0 && <Section title="Collegamenti visibili" level={3} icon={<Icon name="link" />}>
      <Column as="ul" gap="xs">{related.slice(0, 20).map(edge => {
        const outgoing = edge.source.startsWith(`${entity.ref}@`);
        const other = (outgoing ? edge.target : edge.source).split('@')[0];
        return <Column as="li" key={edge.id}><Text pre>{outgoing ? '→' : '←'} {entityName(envelope, other)} <Text variant="muted">{edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', ')}</Text></Text></Column>;
      })}</Column>
    </Section>}
    {entity.evidence.length > 0 && <Section title="Evidenze" level={3} icon={<Icon name="quote" />}>
      <Column as="ul" gap="xs">{entity.evidence.slice(0, LISTED).map((item, index) =>
        <Column as="li" key={index}><Text variant="note" pre>{item.path}{item.line ? `:${item.line}` : ''}</Text></Column>)}</Column>
    </Section>}
    {gaps.length > 0 && <Note tone="warning" announce={false} title="Lacune" items={gaps.map(gap => gap.reason)} />}
  </Column>;
}

export function Details({ model, open, close }: { model: Model; open: boolean; close: () => void }) {
  const { envelope, selected } = model.state;
  const entity = selected ? indexOf(envelope).byRef.get(selected) : undefined;
  return <Inspector title={entity ? 'Dettaglio' : 'Informazioni sul progetto'} open={open} onOpenChange={next => { if (!next) close(); }}>
    {open && (entity ? <EntityDetails model={model} entity={entity} /> : <ProjectDetails envelope={envelope} />)}
  </Inspector>;
}
