// The synthesis: what the graph counts, the paths by entry and where to start reading; what is missing from the picture is behind.
import { Badge, Button, Cluster, Column, Icon, Section, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList, ItemList, ItemRow } from '@acaprino/sigrid/components';
import { Fold } from '../src/listed.tsx';
import { Mark } from '../src/mark.tsx';
import { Failed, Loading } from '../src/states.tsx';
import { number, plural } from '../src/words.ts';
import { ExplorerLink } from './explorer-link.tsx';
import { useFrame } from './frame.tsx';
import { buildCounts, levelsName, markOf, nodeFacts, nodeName, responsibilityOf, runtimeSummary } from './graph.ts';
import type { Graph } from './graph.ts';
import { Paths } from './paths-section.tsx';
import { planGaps } from './plan.ts';
import { Preview } from './preview.tsx';
import { Gaps, PROVENANCE } from './provenance.tsx';
import type { Context } from './server.ts';
import { complete, ctx } from './snapshot.ts';
import { iconOf } from './scene.ts';
import { GraphFailed, MapNote } from './states.tsx';
import { model, useModel } from './use-model.ts';

// What the graph counts, each with what it is of.
function Counts({ graph, commit }: { graph: Graph; commit: string }) {
  const modules = graph.grouping === 'modules';
  const fact = (name: string, count: number, about: string) =>
    ({ name, value: <Column gap="xs"><Text>{number(count)}</Text><Text variant="note">{about}</Text></Column> });
  return <Column data-selectable=""><DescriptionList aria-label="Conteggi del grafo" items={[
    fact(modules ? 'Moduli' : 'Directory con file', graph.nodes.length, 'Gruppi del grafo'),
    fact('Relazioni nel grafo', graph.edges.length, runtimeSummary(graph.edges) || 'Tra i gruppi visualizzati'),
    fact('File nel grafo', graph.files, `Snapshot del commit ${commit.slice(0, 7)}`),
    modules ? fact('File senza modulo', graph.unassigned.count, 'Lacuna esplicita del grafo')
      : fact('Nodi esterni', graph.nodes.filter(n => n.location === 'external').length, 'Servizi riconosciuti fra le tecnologie'),
  ]} /></Column>;
}

// The largest groups, to start from: the one pressed is shown on the graph.
function Responsibilities({ graph }: { graph: Graph }) {
  const { go } = useFrame();
  const largest = [...graph.nodes].sort((a, b) => b.files.length - a.files.length).slice(0, 3);
  const levels = levelsName(graph);
  return <Section title="Responsabilità da esplorare" level={3} icon={<Icon name="layers" />} end={levels && <Badge variant="secondary">{levels}</Badge>}>
    {!largest.length ? <Text as="p" variant="muted">Nessun gruppo nel grafo.</Text>
      : <ItemList aria-label="Responsabilità da esplorare">{largest.map(n =>
        <ItemRow key={n.id} title={nodeName(n)} wrapTitle leading={<Mark image={model.markUrl(markOf(n))} icon={iconOf(n)} />} description={<Text pre>{responsibilityOf(n)}</Text>}
          facts={[{ text: nodeFacts(n) }]} end={<Icon name="chevron" />} onClick={() => go(() => model.showNode(n.id))} />)}</ItemList>}
  </Section>;
}

function Dependencies() {
  const { premap, premapError } = useModel();
  return <Fold label="Dipendenze dopo l’analisi">
    {premapError ? <Failed title="Inventario delle dipendenze non disponibile." cause={premapError} retry={model.retryPremap} />
      : !premap ? <Loading label="Lettura dell’inventario…" />
      : <Text as="p">{plural(premap.dependencies.filter(d => d.resolved_version).length, 'voce', 'voci')} con versione risolta nel modello di build.</Text>}
  </Fold>;
}

// How many the gaps are is on the row: what is missing is never out of sight.
function Missing() {
  const s = useModel();
  const { show } = useFrame();
  return <Fold label="Cosa manca al quadro" summary={plural(planGaps(s).length, 'lacuna', 'lacune')}>
    <Column>
      <Gaps first={8} />
      <Cluster><Button variant="ghost" size="sm" onClick={() => show(PROVENANCE)}><Icon name="file" />Provenienza e lacune</Button></Cluster>
    </Column>
  </Fold>;
}

function Result({ context }: { context: Context }) {
  const { graph, graphError } = useModel();
  return <>
    {graphError ? <GraphFailed /> : !graph && <Loading label="Lettura del grafo…" />}
    {graph && <Counts graph={graph} commit={context.commit} />}
    <Paths />
    {graph && <Responsibilities graph={graph} />}
    <Column gap="xs">
      <Missing />
      <Dependencies />
      <Fold label="Sintesi testuale" summary="In attesa">
        <Text as="p" variant="soft">Questa versione non fa scrivere una sintesi al motore: qui ci sono i conteggi, le responsabilità dichiarate e le lacune del run {context.run_id}. Le domande al motore sono in «Motore e domande».</Text>
      </Fold>
    </Column>
  </>;
}

// What the graph of this run says, under the step that assembles it: the graph as it takes shape, and once the pipeline is over
// its counts, paths, groups and gaps.
export function SynthesisResult() {
  const s = useModel();
  const c = ctx(s);
  if (!c) return null;
  return <>
    <Cluster><ExplorerLink /></Cluster>
    <Fold label="Grafo in costruzione" summary={buildCounts(s.graph)}><Preview /></Fold>
    {complete(s) ? <><MapNote /><Result context={c} /></>
      : <Text as="p" variant="muted">Il quadro del grafo è pronto da leggere quando la pipeline è conclusa.</Text>}
  </>;
}
