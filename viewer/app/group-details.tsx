// The details of a group of the graph, in the inspector: a few facts beside the preview, all that is known of it on the graph.
import type { ReactNode } from 'react';
import { Badge, Button, Cluster, Column, Icon, Section, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList } from '@acaprino/sigrid/components';
import { Fold, FoldedList, List, Listed } from '../src/listed.tsx';
import { Mark } from '../src/mark.tsx';
import { Failed, Loading } from '../src/states.tsx';
import { CATEGORY_LABEL, MORE, number } from '../src/words.ts';
import type { Detail } from './frame.tsx';
import { isOpenGroup, markOf, nodeFacts, nodeName, opens, responsibilityOf, thingById } from './graph.ts';
import type { Graph, GraphNode, Technology, Thing } from './graph.ts';
import {
  callRows, isProven, perimeter, proofRow, recordedIn, relationRow, relationsOf, shortPath, siteOf, stateOf, symbolRows, whatIs,
} from './group.ts';
import type { Row } from './group.ts';
import { short } from './repository.ts';
import { iconOf } from './scene.ts';
import { ctx } from './snapshot.ts';
import { model, useModel, useModelSlice, useSymbols } from './use-model.ts';

const muted = (text: string): ReactNode => <Text as="p" variant="muted">{text}</Text>;
const GONE = 'Non è più nel grafo di questo run.';

function GroupFacts({ id }: { id: string }) {
  const s = useModel();
  const c = ctx(s), n = s.graph?.nodes.find(item => item.id === id);
  if (!c || !n) return muted(GONE);
  return <Column>
    {muted(`${s.graph?.grouping === 'modules' ? 'Modulo' : 'Directory'} del grafo di questo run.`)}
    <Text as="p">{responsibilityOf(n)}</Text>
    <Text as="p" variant="note">{nodeFacts(n)} · commit {short(c.commit)}</Text>
  </Column>;
}

const line = ({ name, about }: Row): ReactNode => <><Text pre>{name}</Text>{about && <Text variant="note" pre>{about}</Text>}</>;

// The frameworks and the libraries a group declares, and where.
function Stack({ projects, others = 0 }: { projects: Technology[]; others?: number }) {
  return <Section title="Tecnologie" level={3} icon={<Icon name="labels" />}>
    {projects.length > 0 ? <List label="Tecnologie" items={projects.map(project => <>
      <Cluster>
        <Mark image={model.markUrl(project.mark)} icon="package" />
        <Text variant="strong">{project.name}</Text>
        <Badge variant="secondary">{CATEGORY_LABEL[project.category] ?? project.category}</Badge>
      </Cluster>
      {project.evidence.map((at, index) => <Text key={index} variant="note" pre>{siteOf(at)}</Text>)}
    </>)} /> : muted('Nessun framework o libreria riconosciuti dal registro.')}
    {others > 0 && <Text as="p" variant="note">Altre dipendenze dichiarate: {number(others)}</Text>}
  </Section>;
}

// What is pressed goes with the failure: the focus goes to the section, which stays.
const SYMBOLS = 'group-symbols';
// A file is the lowest node: its symbols and the calls among them are read when its details are.
function FileSymbols({ file }: { file: string }) {
  const found = useSymbols(file);
  const again = () => { model.retrySymbols(file); document.getElementById(SYMBOLS)?.focus({ preventScroll: true }); };
  const symbols = found ? symbolRows(found) : [], calls = found ? callRows(found) : [];
  return <Section id={SYMBOLS} tabIndex={-1} title="Simboli e chiamate" level={3} icon={<Icon name="code" />}>
    {found?.error !== undefined ? <Failed title="Simboli non disponibili." cause={found.error} retry={again} />
      : !found || found.loading ? <Loading label="Lettura dei simboli…" />
      : <>
          {symbols.length > 0 ? <Listed label="Simboli" items={symbols.map(line)} more={MORE.symbols} />
            : muted('Nessun simbolo nell’outline.')}
          {calls.length > 0 ? <Listed label="Chiamate" items={calls.map(line)} more={MORE.calls} />
            : muted('Nessuna chiamata risolta da o verso i suoi simboli.')}
        </>}
  </Section>;
}

// A file of the group, with the relations recorded in it.
function FileRow({ graph, path }: { graph: Graph; path: string }) {
  const rows = recordedIn(graph, path);
  return <Fold label={shortPath(path)}>
    <Column>
      <Text pre>{path}</Text>
      <Text as="p" variant="note">La pagina mostra la provenienza registrata, senza aprire o eseguire il sorgente.</Text>
      <Text variant="strong">Relazioni registrate</Text>
      {rows.length > 0
        ? <Listed label={`Relazioni registrate di ${path}`} items={rows.map(line)} more={MORE.relations} />
        : muted('Nessuna relazione tra gruppi cita questo file.')}
    </Column>
  </Fold>;
}

const FILES = 4;  // how many files of a group are in sight at first
function Files({ graph, n }: { graph: Graph; n: GraphNode }) {
  return <Section title="File del gruppo" level={3} icon={<Icon name="file" />}>
    {n.files.slice(0, FILES).map(path => <FileRow key={path} graph={graph} path={path} />)}
    {!n.files.length && muted(n.location === 'external' ? 'Gruppo esterno: nessun file locale.' : 'Nessun file assegnato.')}
    {n.files.length > FILES
      && <FoldedList label={`Tutti i ${number(n.files.length)} file`} items={n.files.map(path => <Text variant="note" pre>{path}</Text>)} />}
  </Section>;
}

function GroupDetails({ id }: { id: string }) {
  const graph = useModelSlice(s => s.graph), thing = thingById(graph, id);
  if (!graph || !thing) return muted(GONE);
  const n = isOpenGroup(thing) ? null : thing, evidence = n?.evidence ?? [];
  const related = relationsOf(graph, id), proven = related.filter(isProven);
  return <>
    <Column>
      <Cluster><Text variant="muted">{whatIs(thing)}</Text><Badge variant="secondary">{stateOf(thing)}</Badge></Cluster>
      {n && <Text as="p">{responsibilityOf(n)}</Text>}
    </Column>
    <Section title="Perimetro" level={3} icon={<Icon name="graph" />}>
      <DescriptionList aria-label="Perimetro" items={perimeter(graph, thing)} />
      {related.length > 0
        && <FoldedList label={`Relazioni del gruppo (${number(related.length)})`} items={related.map(edge => line(relationRow(graph, id, edge)))} />}
      {proven.length > 0
        && <FoldedList label={`Prove delle chiamate (${number(proven.length)})`} items={proven.map(edge => line(proofRow(graph, edge)))} />}
    </Section>
    {thing.projects && <Stack projects={thing.projects} others={thing.other_dependencies} />}
    {thing.kind === 'file' && <FileSymbols file={id} />}
    {n && <Section title="Evidenze" level={3} icon={<Icon name="quote" />}>
      {evidence.length > 0
        ? <Listed label="Evidenze" items={evidence.map(at => <Text variant="note" pre>{siteOf(at)}</Text>)}
            more={MORE.evidence} />
        : muted('Nessuna evidenza dichiarata.')}
    </Section>}
    {n && n.kind !== 'symbol' && <Files graph={graph} n={n} />}
  </>;
}

// Opens the group in place, or closes it: one button, which keeps the focus.
function GroupToggle({ id }: { id: string }) {
  const graph = useModelSlice(s => s.graph), thing = thingById(graph, id);
  const open = thing !== undefined && isOpenGroup(thing);
  return <Button size="sm" variant={open ? 'outline' : 'default'} disabled={!thing} onClick={() => model.toggleGroup(id)}>
    <Icon name="layers" />{open ? 'Chiudi il gruppo' : 'Apri sul posto'}
  </Button>;
}

const GROUP = 'graph.group';
const face = (thing: Thing) => ({
  id: GROUP, key: thing.id, title: 'Dettaglio del gruppo', icon: iconOf(thing), name: nodeName(thing),
  image: model.markUrl(markOf(thing)),
});
// Beside the preview.
export const groupDetail = (n: GraphNode, footer?: ReactNode): Detail => ({ ...face(n), content: <GroupFacts id={n.id} />, footer });
// On the graph.
export const graphDetail = (thing: Thing): Detail =>
  ({ ...face(thing), content: <GroupDetails id={thing.id} />, footer: (isOpenGroup(thing) || opens(thing)) && <GroupToggle id={thing.id} /> });
// The group the details are of.
export const groupOf = (detail: Detail | null): string | null => (detail?.id === GROUP ? detail.key ?? null : null);
