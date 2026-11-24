// The details in the inspector: the element chosen, else the flow with its steps, else what the project is and how its map is read.
import type { ReactNode } from 'react';
import { Button, Cluster, Column, DescriptionList, Disclosure, Heading, Icon, Inspector, ItemList, ItemRow, Note, Section, Text } from '@acaprino/sigrid';
import type { Entity, Envelope, Flow } from './envelope.ts';
import { childrenOf, flowsThrough, indexOf } from './projection.ts';
import type { Model } from './model.ts';
import { FLOW_ICON, FRESHNESS_LABEL, LINK_LABEL, STATUS_LABEL } from './icons.ts';
import { bindingSite, entityName, entryName, flowTitle, headOf, kindOf, MORE, stepMeta } from './names.ts';
import { shownDetails } from './state.ts';

// How many entries of a long list are in sight at first.
const FIRST = { steps: 40, links: 20, evidence: 8, files: 8 };

// Text to read and copy, so not rows to press. Nothing is cut off in silence: the first entries are in sight, and the others
// behind a row that says how many they are.
function Listed({ label, kind, items, ordered = false }: { label: string; kind: keyof typeof FIRST; items: ReactNode[]; ordered?: boolean }) {
  const list = (name: string, part: ReactNode[]) => <Column as={ordered ? 'ol' : 'ul'} gap={ordered ? 'md' : 'xs'} aria-label={name}>
    {part.map((item, index) => <Column as="li" key={index} gap="xs">{item}</Column>)}</Column>;
  const rest = items.slice(FIRST[kind]);
  const more = MORE[kind](rest.length);
  return <>
    {list(label, items.slice(0, FIRST[kind]))}
    {rest.length > 0 && <Disclosure label={more}>{list(more, rest)}</Disclosure>}
  </>;
}

// The technologies of the project, or those of one build unit (`ids`), each with the files that show it, in words.
function Technologies({ envelope, ids }: { envelope: Envelope; ids?: string[] }) {
  const shown = envelope.technologies.filter(item => !ids || ids.includes(item.id));
  if (!shown.length) return null;
  return <Section title="Tecnologie" level={3} icon={<Icon name="labels" />}>
    <DescriptionList items={shown.map(item => ({ name: item.name, value: <Column gap="xs">
      <Text>{item.type}</Text>
      {item.paths.length > 0 && <Listed label={`File di ${item.name}`} kind="files" items={item.paths.map(path => <Text variant="note" pre>{path}</Text>)} />}
    </Column> }))} />
  </Section>;
}

// What the project holds, and what of it is in view: the panel of the map says only the place and the two counts it starts from.
function ProjectDetails({ model }: { model: Model }) {
  const { state: { envelope }, projection, data } = model;
  return <>
    <Text as="p" variant="soft">Scegli un elemento per vederne il ruolo, i collegamenti e i flussi che lo attraversano. «Entra», o un doppio clic, apre quello che contiene. Nei flussi leggi il sito e la provenienza della prova di ogni passaggio.</Text>
    <DescriptionList items={[
      { name: 'Entità', value: envelope.entities.length },
      { name: 'Relazioni', value: envelope.relations.length },
      { name: "Flussi dai punti d'ingresso", value: envelope.flows.length },
      { name: 'Lacune dichiarate', value: envelope.gaps.length },
    ]} />
    <Section title="In questa vista" level={3} icon={<Icon name="graph" />}>
      <DescriptionList items={[
        { name: 'Nodi', value: projection.nodes.length },
        { name: 'Relazioni visibili', value: projection.edges.length },
        { name: 'Collegamenti di dati (tratteggiati)', value: data.length },
        { name: 'Relazioni dentro i gruppi', value: projection.counts.aggregated },
      ]} />
    </Section>
    <Technologies envelope={envelope} />
  </>;
}

// What a flow goes through, in order, and where its proof stops.
function FlowDetails({ model, flow }: { model: Model; flow: Flow }) {
  const { state: { envelope }, focus } = model;
  const site = bindingSite(flow);
  return <>
    <DescriptionList items={[
      { name: 'Ingresso', value: entryName(flow) },
      site ? { name: 'Sito', value: site, code: true } : null,
      { name: 'Passi', value: flow.steps.length },
      { name: 'Nodi in vista', value: focus?.nodes.length ?? 0 },
      flow.complete ? null : { name: 'Stato', value: 'incompleto' },
    ]} />
    {flow.steps.length > 0 && <Section title="Passi" level={3} icon={<Icon name="listOrdered" />}>
      <Listed ordered label="Passi del flusso" kind="steps" items={flow.steps.map((step, index) => <>
        <Text pre>{index + 1}. {entityName(envelope, step.source)} <Text variant="strong">{LINK_LABEL[step.type] ?? step.type}</Text> {entityName(envelope, step.target)}</Text>
        <Text variant="note" pre>{stepMeta(step)}</Text>
      </>)} />
    </Section>}
    {!!flow.gaps?.length && <Section title="Dove si ferma la prova" level={3} icon={<Icon name="alert" />}>
      <Column as="ul" gap="sm" aria-label="Dove si ferma la prova">{flow.gaps.map((gap, index) =>
        <Column as="li" key={index} gap="xs"><Text variant="note" pre>{gap.site}</Text><Text pre>{gap.reason}</Text></Column>)}</Column>
    </Section>}
  </>;
}

function EntityDetails({ model, entity }: { model: Model; entity: Entity }) {
  const { state, dispatch, projection } = model;
  const envelope = state.envelope;
  const flows = flowsThrough(envelope, entity.ref, state.view);
  const gaps = envelope.gaps.filter(gap => gap.refs.includes(entity.ref));
  const lines = Array.isArray(entity.lines) ? entity.lines.filter(Boolean).join('–') : entity.lines;
  const isIt = (id: string) => id.startsWith(`${entity.ref}@`);
  const labels = new Map(projection.nodes.map(node => [node.id, node.label]));
  const related = projection.edges.filter(edge => isIt(edge.source) || isIt(edge.target));
  return <>
    {entity.description && <Text as="p" variant="soft">{entity.description}</Text>}
    <DescriptionList items={[
      { name: 'Tipo', value: kindOf(entity) },
      { name: 'Posizione', value: entity.location === 'external' ? 'esterno' : 'interno' },
      entity.path ? { name: 'Percorso', value: `${entity.path}${lines ? `:${lines}` : ''}`, code: true } : null,
      entity.provenance ? { name: 'Provenienza', value: entity.provenance } : null,
      entity.status ? { name: 'Stato', value: STATUS_LABEL[entity.status] ?? entity.status } : null,
      entity.freshness ? { name: 'Scheda', value: FRESHNESS_LABEL[entity.freshness] ?? entity.freshness } : null,
    ]} />
    {entity.technologies && <Technologies envelope={envelope} ids={entity.technologies} />}
    {flows.length > 0 && <Section title="Flussi che lo attraversano" level={3} icon={<Icon name={FLOW_ICON} />}>
      <ItemList aria-label="Flussi che lo attraversano">{flows.map(flow =>
        <ItemRow key={flow.ref} title={flowTitle(envelope, flow)} wrapTitle current={state.flow === flow.ref} onClick={() => dispatch({ type: 'flow', ref: flow.ref })} />)}</ItemList>
    </Section>}
    {related.length > 0 && <Section title="Collegamenti visibili" level={3} icon={<Icon name="link" />}>
      <Listed label="Collegamenti visibili" kind="links" items={related.map(edge => {
        const outgoing = isIt(edge.source);
        return <Text pre>{outgoing ? '→' : '←'} {labels.get(outgoing ? edge.target : edge.source)} <Text variant="muted">{edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', ')}</Text></Text>;
      })} />
    </Section>}
    {entity.evidence.length > 0 && <Section title="Evidenze" level={3} icon={<Icon name="quote" />}>
      <Listed label="Evidenze" kind="evidence" items={entity.evidence.map(item => <Text variant="note" pre>{item.path}{item.line ? `:${item.line}` : ''}</Text>)} />
    </Section>}
    {gaps.length > 0 && <Note tone="warning" announce={false} title="Lacune" items={gaps.map(gap => gap.reason)} />}
  </>;
}

export function Details({ model, open, close }: { model: Model; open: boolean; close: () => void }) {
  const { state, dispatch } = model;
  const envelope = state.envelope;
  const shown = open ? shownDetails(state) : null;
  const entity = shown === 'entity' ? indexOf(envelope).byRef.get(state.selected!) : undefined;
  const flow = shown === 'flow' ? envelope.flows.find(item => item.ref === state.flow) : undefined;
  const head = headOf(envelope, entity, flow);
  const enter = entity && entity.type !== 'feature' && childrenOf(envelope, entity.ref, state.view).length > 0
    ? <Button size="sm" aria-label={`Entra in ${entity.name}`} onClick={() => dispatch({ type: 'open', ref: entity.ref })}><Icon name="folderOpen" />Entra</Button>
    : undefined;
  return <Inspector title={head.title} open={open} onOpenChange={next => { if (!next) close(); }} footer={enter}>
    {open && <Column gap="lg" data-selectable="">
      {/* The one live region: it stays while what is chosen changes, and reads the name alone. */}
      <Cluster wrap={false} align="start" aria-live="polite" aria-atomic="true">
        <Icon name={head.icon} />
        <Column><Heading size="small"><Text pre>{head.name}</Text></Heading></Column>
      </Cluster>
      {entity ? <EntityDetails key={entity.ref} model={model} entity={entity} />
        : flow ? <FlowDetails key={flow.ref} model={model} flow={flow} />
        : <ProjectDetails model={model} />}
    </Column>}
  </Inspector>;
}
