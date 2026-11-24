// The details in the inspector: the element chosen, else the flow with its steps, else what the project is and how its map is read.
import { Button, Cluster, Column, Heading, Icon, Section, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList, ItemList, ItemRow, Note } from '@acaprino/sigrid/components';
import { Inspector } from '@acaprino/sigrid/layout';
import type { Entity, Envelope, Flow } from './envelope.ts';
import { flowsThrough, indexOf, markOfEntity } from './projection.ts';
import { List, Listed } from './listed.tsx';
import { Mark } from './mark.tsx';
import type { Model, Shown } from './model.ts';
import { FLOW_ICON } from './icons.ts';
import { bindingSite, entityName, entryName, flowTitle, headOf, kindOf, stepMeta } from './names.ts';
import { imageOf } from './server.ts';
import { canEnter, shownDetails } from './state.ts';
import { FRESHNESS_LABEL, LINK_LABEL, MORE, number, PROVENANCE_LABEL, STATUS_LABEL } from './words.ts';

// How many steps and links of a long list are in sight at first.
const STEPS = 40, LINKS = 20;

// The technologies of the project, or those of one build unit (`ids`), each with its logo and the files that show it, in words.
function Technologies({ envelope, ids }: { envelope: Envelope; ids?: string[] }) {
  const shown = envelope.technologies.filter(item => !ids || ids.includes(item.id));
  if (!shown.length) return null;
  return <Section title="Tecnologie" level={3} icon={<Icon name="labels" />}>
    <DescriptionList items={shown.map(item => ({ name: <Cluster wrap={false}><Mark image={imageOf(item.mark)} icon="labels" />{item.name}</Cluster>, value: <Column gap="xs">
      <Text>{item.type}</Text>
      {item.paths.length > 0 && <Listed label={`File di ${item.name}`} more={MORE.files} items={item.paths.map(path => <Text variant="note" pre>{path}</Text>)} />}
    </Column> }))} />
  </Section>;
}

// What the project holds, and what of it is in view: the panel of the map says only the place and the two counts it starts from.
function ProjectDetails({ model }: { model: Model }) {
  const { state: { envelope }, projection, data } = model;
  return <>
    <Text as="p" variant="soft">Scegli un elemento per vederne il ruolo, i collegamenti e i flussi che lo attraversano. La freccia di un gruppo lo apre e lo chiude sul posto; «Entra», o un doppio clic su un gruppo chiuso, mostra soltanto quello che contiene. Un elemento si sposta trascinandolo o con Alt e una freccia, e «Riordina» rimette tutto a posto. Nei flussi leggi il sito e la provenienza della prova di ogni passaggio.</Text>
    <DescriptionList items={[
      { name: 'Entità', value: number(envelope.entities.length) },
      { name: 'Relazioni', value: number(envelope.relations.length) },
      { name: "Flussi dai punti d'ingresso", value: number(envelope.flows.length) },
      { name: 'Lacune dichiarate', value: number(envelope.gaps.length) },
    ]} />
    <Section title="In questa vista" level={3} icon={<Icon name="graph" />}>
      <DescriptionList items={[
        { name: 'Nodi', value: number(projection.nodes.length) },
        { name: 'Relazioni visibili', value: number(projection.edges.length) },
        { name: 'Collegamenti di dati (tratteggiati)', value: number(data.length) },
        { name: 'Relazioni dentro i gruppi', value: number(projection.counts.aggregated) },
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
      <Listed ordered label="Passi del flusso" first={STEPS} more={MORE.steps} items={flow.steps.map((step, index) => <>
        <Text pre>{index + 1}. {entityName(envelope, step.source)} <Text variant="strong">{LINK_LABEL[step.type] ?? step.type}</Text> {entityName(envelope, step.target)}</Text>
        <Text variant="note" pre>{stepMeta(step)}</Text>
      </>)} />
    </Section>}
    {!!flow.gaps?.length && <Section title="Dove si ferma la prova" level={3} icon={<Icon name="alert" />}>
      <List label="Dove si ferma la prova" items={flow.gaps.map(gap => <><Text variant="note" pre>{gap.site}</Text><Text pre>{gap.reason}</Text></>)} />
    </Section>}
  </>;
}

function EntityDetails({ model, show, entity }: { model: Model; show: (asked: Shown) => void; entity: Entity }) {
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
      entity.provenance ? { name: 'Provenienza', value: PROVENANCE_LABEL[entity.provenance] ?? entity.provenance } : null,
      entity.status ? { name: 'Stato', value: STATUS_LABEL[entity.status] ?? entity.status } : null,
      entity.freshness ? { name: 'Scheda', value: FRESHNESS_LABEL[entity.freshness] ?? entity.freshness } : null,
    ]} />
    {entity.technologies && <Technologies envelope={envelope} ids={entity.technologies} />}
    {flows.length > 0 && <Section title="Flussi che lo attraversano" level={3} icon={<Icon name={FLOW_ICON} />}>
      <ItemList aria-label="Flussi che lo attraversano">{flows.map(flow =>
        <ItemRow key={flow.ref} title={flowTitle(envelope, flow)} wrapTitle current={state.flow === flow.ref}
          onClick={() => { dispatch({ type: 'flow', ref: flow.ref }); show({ flow: flow.ref }); }} />)}</ItemList>
    </Section>}
    {related.length > 0 && <Section title="Collegamenti visibili" level={3} icon={<Icon name="link" />}>
      <Listed label="Collegamenti visibili" first={LINKS} more={MORE.links} items={related.map(edge => {
        const outgoing = isIt(edge.source);
        return <Text pre>{outgoing ? '→' : '←'} {labels.get(outgoing ? edge.target : edge.source)} <Text variant="muted">{edge.kinds.map(kind => LINK_LABEL[kind] ?? kind).join(', ')}</Text></Text>;
      })} />
    </Section>}
    {entity.evidence.length > 0 && <Section title="Evidenze" level={3} icon={<Icon name="quote" />}>
      <Listed label="Evidenze" more={MORE.evidence} items={entity.evidence.map(item => <Text variant="note" pre>{item.path}{item.line ? `:${item.line}` : ''}</Text>)} />
    </Section>}
    {gaps.length > 0 && <Note tone="warning" announce={false} title="Lacune" items={gaps.map(gap => gap.reason)} />}
  </>;
}

export function Details({ model, show, open, close }: { model: Model; show: (asked: Shown) => void; open: boolean; close: () => void }) {
  const { state, dispatch } = model;
  const envelope = state.envelope;
  const shown = open ? shownDetails(state) : null;
  const entity = shown === 'entity' ? indexOf(envelope).byRef.get(state.selected!) : undefined;
  const flow = shown === 'flow' ? envelope.flows.find(item => item.ref === state.flow) : undefined;
  const head = headOf(envelope, entity, flow);
  const enter = entity && canEnter(state, entity.ref)
    ? <Button size="sm" aria-label={`Entra in ${entity.name}`} onClick={() => dispatch({ type: 'open', ref: entity.ref })}><Icon name="folderOpen" />Entra</Button>
    : undefined;
  return <Inspector title={head.title} open={open} onOpenChange={next => { if (!next) close(); }} footer={enter}>
    {open && <Column gap="lg" data-selectable="">
      {/* The one live region: it stays while what is chosen changes, and reads the name alone. */}
      <Cluster wrap={false} align="start" aria-live="polite" aria-atomic="true">
        <Mark image={imageOf(entity && markOfEntity(envelope, entity))} icon={head.icon} />
        <Column><Heading size="small"><Text pre>{head.name}</Text></Heading></Column>
      </Cluster>
      {entity ? <EntityDetails key={entity.ref} model={model} show={show} entity={entity} />
        : flow ? <FlowDetails key={flow.ref} model={model} flow={flow} />
        : <ProjectDetails model={model} />}
    </Column>}
  </Inspector>;
}
