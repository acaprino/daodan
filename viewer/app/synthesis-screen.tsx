// The synthesis: the paths by entry, what the graph counts, where to start reading, and what is missing from the picture.
import { Badge, Button, Cluster, Column, Icon, Section, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList, ItemList, ItemRow, Note } from '@acaprino/sigrid/components';
import { Mark } from '../src/mark.tsx';
import { Failed, Loading } from '../src/states.tsx';
import { number, plural } from '../src/words.ts';
import { ScreenPanel, useFrame } from './frame.tsx';
import { buildCounts, levelsName, nodeFacts, nodeName, responsibilityOf, runtimeSummary } from './graph.ts';
import type { Graph } from './graph.ts';
import { Paths } from './paths-section.tsx';
import { Gaps, PROVENANCE } from './provenance.tsx';
import type { Context } from './server.ts';
import { ctx } from './snapshot.ts';
import { iconOf } from './scene.ts';
import { GraphFailed, MapNote } from './states.tsx';
import { model, useModel } from './use-model.ts';

export function SynthesisActions() {
  const { go } = useFrame();
  return <Button onClick={() => go(model.showFullGraph)}><Icon name="graph" />Esplora il grafo completo</Button>;
}

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
      : fact('Nodi esterni', graph.nodes.filter(n => n.location === 'external').length, 'Servizi riconosciuti dallo stack'),
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
        <ItemRow key={n.id} title={nodeName(n)} wrapTitle leading={<Mark image={model.markUrl(n.mark)} icon={iconOf(n)} />} description={<Text pre>{responsibilityOf(n)}</Text>}
          facts={[{ text: nodeFacts(n) }]} end={<Icon name="chevron" />} onClick={() => go(() => model.showNode(n.id))} />)}</ItemList>}
  </Section>;
}

function Dependencies() {
  const { premap, premapError } = useModel();
  return <Section title="Dipendenze dopo l’analisi" level={3} icon={<Icon name="package" />}>
    {premapError ? <Failed title="Inventario delle dipendenze non disponibile." cause={premapError} retry={model.retryPremap} />
      : !premap ? <Loading label="Lettura dell’inventario…" />
      : <Text as="p">{plural(premap.dependencies.filter(d => d.resolved_version).length, 'voce', 'voci')} con versione risolta nel modello di build.</Text>}
  </Section>;
}

function Missing() {
  const { show } = useFrame();
  return <Section title="Cosa manca al quadro" level={3} icon={<Icon name="alert" />}>
    <Gaps first={8} />
    <Cluster><Button variant="ghost" size="sm" onClick={() => show(PROVENANCE)}><Icon name="file" />Provenienza e lacune</Button></Cluster>
  </Section>;
}

function Overview({ context }: { context: Context }) {
  const { graph, graphError } = useModel();
  return <>
    {graphError && <GraphFailed />}
    {graph ? <>
      <Counts graph={graph} commit={context.commit} />
      <Responsibilities graph={graph} />
      <Dependencies />
      <Missing />
    </> : !graphError && <Loading label="Lettura del grafo…" />}
  </>;
}

export function SynthesisScreen() {
  const s = useModel();
  const c = ctx(s);
  return <ScreenPanel title="Sintesi" subtitle={s.graph && buildCounts(s.graph)}>
    {c && <Column pad="lg" gap="xl" width="page">
      <Text as="p" variant="soft">Gruppi, relazioni e lacune del grafo di questo run.</Text>
      <MapNote />
      <Paths />
      <Note title="Sintesi testuale in attesa.">Questa versione non fa scrivere una sintesi al motore: qui ci sono i conteggi, le responsabilità dichiarate e le lacune del run {c.run_id}. Le domande al motore sono in «Motore e domande».</Note>
      <Overview context={c} />
    </Column>}
  </ScreenPanel>;
}
