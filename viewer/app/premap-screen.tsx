// The pre-map: the repository before its analysis. The context and what it holds, its tree, what it is made with and what it
// depends on; what is chosen in the tree, and where all this comes from, are in the inspector.
import { useCallback, useEffect, useMemo, useRef } from 'react';
import {
  Badge, Button, Cluster, Column, DescriptionList, Empty, Grid, Heading, Icon, Note, Progress, ScrollArea, SearchField, Section, Table, TableBody,
  TableCell, TableHead, TableHeader, TableRow, Text, ToggleGroup, ToggleGroupItem, Tree,
} from '@acaprino/sigrid';
import type { TreeNode } from '@acaprino/sigrid';
import { ScreenPanel, useFrame } from './frame.tsx';
import {
  CHOICE_TITLE, choiceDetails, choiceOf, countFound, dependencyFacts, directoryTree, finds, inventory, keptBranches, openBranches, PROVENANCE_NOTES,
  provenanceFacts, rowOf, technologyFacts, unitTree,
} from './premap.ts';
import { ContextFacts } from './repository-screen.tsx';
import { ctx, number, plural } from './snapshot.ts';
import type { Premap } from './snapshot.ts';
import { model, useModel } from './use-model.ts';

export function PremapActions() {
  return <Button onClick={() => model.selectStage('analysis')}><Icon name="play" />Segui l’analisi</Button>;
}

// What is chosen in the tree.
function ChoiceDetails() {
  const s = useModel();
  const c = ctx(s), choice = choiceOf(s.premap, s.kept.treeSelected);
  if (!c || !choice) return null;
  const { icon, name, facts, text } = choiceDetails(choice, c);
  return <>
    {/* The one live region: it stays while what is chosen changes, and reads the name alone. */}
    <Cluster wrap={false} align="start" aria-live="polite" aria-atomic="true">
      <Icon name={icon} />
      <Column><Heading size="small"><Text pre>{name}</Text></Heading></Column>
    </Cluster>
    {text && <Text as="p" variant="soft">{text}</Text>}
    <DescriptionList items={facts} />
  </>;
}
const CHOICE = <ChoiceDetails />;  // one element: the inspector shows the choice when its content is this

// As on the map, what is chosen is in the details, and closing them leaves it; another stage takes the details away.
function useChoice() {
  const s = useModel();
  const { detail, show, close } = useFrame();
  const choice = choiceOf(s.premap, s.kept.treeSelected);
  const shown = detail?.content === CHOICE, wasShown = useRef(false);
  useEffect(() => {
    if (choice) show({ title: CHOICE_TITLE[choice.kind], content: CHOICE });
    else if (shown) close();
  }, [choice ? s.kept.treeSelected : '']);
  useEffect(() => {
    if (wasShown.current && !shown) model.keep({ treeSelected: '' });
    wasShown.current = shown;
  }, [shown]);
  useEffect(() => close, []);
}

function Provenance() {
  const s = useModel();
  const c = ctx(s);
  return c && <>
    <Text as="p" variant="soft">Snapshot del checkout, manifest e risultati degli strumenti di build.</Text>
    <DescriptionList items={provenanceFacts(c, s.premap)} />
    <Column as="ul" gap="md" aria-label="Che cosa prova">{PROVENANCE_NOTES.map(text => <Column as="li" key={text}><Text>{text}</Text></Column>)}</Column>
  </>;
}

// The directories or the technical units, filtered by the search.
function Structure({ premap }: { premap: Premap }) {
  const s = useModel();
  const { search } = useFrame();
  const { treeMode, treeSearch, treeSelected, treeOpen } = s.kept;
  const physical = treeMode === 'directories';
  const tree = useMemo(() => (physical ? directoryTree(premap.files) : unitTree(premap.units)), [premap, physical]);
  const expanded = useMemo(() => openBranches(tree.nodes, treeOpen), [tree, treeOpen]);
  const selected = useMemo(() => rowOf(tree, treeSelected), [tree, treeSelected]);
  const match = useCallback((node: TreeNode, query: string) => finds(tree, node.id, query), [tree]);
  const found = useMemo(() => countFound(tree, treeSearch), [tree, treeSearch]);
  const label = physical ? 'Albero delle directory' : 'Albero delle unità tecniche';
  const choose = (row: string) => { const choice = tree.choices.get(row); if (choice) model.keep({ treeSelected: choice }); };
  return <Section title="Struttura del repository" level={3} icon={<Icon name="structure" />}>
    <Text as="p" variant="note">Directory fisiche e unità tecniche restano distinte. Seleziona un file o un’unità per leggerne la provenienza.</Text>
    <ToggleGroup aria-label="Tipo di albero" value={treeMode} onValueChange={mode => model.keep({ treeMode: mode })}>
      <ToggleGroupItem value="directories">Directory</ToggleGroupItem>
      <ToggleGroupItem value="units">Unità tecniche</ToggleGroupItem>
    </ToggleGroup>
    <SearchField ref={search} aria-label="Cerca nell’albero" placeholder="Cerca percorso o unità…" value={treeSearch}
      onValueChange={text => model.keep({ treeSearch: text })} />
    <Text as="p" variant="strong" aria-live="polite">{physical ? `${ctx(s)?.repository.name ?? ''} · ${number(found)} file` : 'Unità da manifest'}</Text>
    {found > 0
      ? <ScrollArea bounded aria-label={label}>
          <Tree key={treeMode} aria-label={label} nodes={tree.nodes} query={treeSearch} match={match} selected={selected} onSelect={choose}
            expanded={expanded} onExpandedChange={open => model.keep({ treeOpen: keptBranches(tree.nodes, treeOpen, open) })} />
        </ScrollArea>
      : <Empty title="Nessun risultato." action={treeSearch.trim() !== '' && <Button variant="outline" size="sm"
          onClick={() => { model.keep({ treeSearch: '' }); search.current?.focus(); }}>Azzera ricerca</Button>} />}
  </Section>;
}

// A version of a dependency, and where it is read.
const version = (found: { version: string; source: string } | null) => (found
  ? <Column gap="xs"><Text>{found.version}</Text><Text variant="note">{found.source}</Text></Column> : '—');

function Dependencies({ premap }: { premap: Premap }) {
  return <Section title="Dipendenze per unità" level={3} icon={<Icon name="package" />}>
    {premap.dependencies.length > 0
      ? <Table aria-label="Dipendenze per unità" data-selectable="">
          <TableHeader><TableRow>
            <TableHead>Dipendenza</TableHead><TableHead>Unità</TableHead><TableHead>Vincolo dichiarato</TableHead><TableHead>Versione risolta</TableHead>
            <TableHead>Relazione</TableHead>
          </TableRow></TableHeader>
          <TableBody>{premap.dependencies.map((dependency, index) => {
            const { declared, resolved, relation } = dependencyFacts(dependency);
            return <TableRow key={index}>
              <TableCell><Column gap="xs"><Text variant="strong">{dependency.name}</Text><Text variant="note">{dependency.scope}</Text></Column></TableCell>
              <TableCell>{dependency.unit}</TableCell>
              <TableCell>{version(declared)}</TableCell>
              <TableCell>{version(resolved)}</TableCell>
              <TableCell>{relation}</TableCell>
            </TableRow>;
          })}</TableBody>
        </Table>
      : <Empty title="Nessuna dipendenza registrata." />}
  </Section>;
}

function Found({ premap }: { premap: Premap }) {
  return <>
    <Structure premap={premap} />
    <Grid gap="xl">
      <Section title="Linguaggi" level={3} icon={<Icon name="code" />} end={<Badge variant="secondary">Inventario</Badge>}>
        {premap.languages.length > 0
          ? <DescriptionList items={premap.languages.map(language => ({ name: language.name, value: plural(language.files, 'file', 'file') }))} />
          : <Empty title="Nessun file sorgente riconosciuto." />}
        <Text as="p" variant="note">File sorgente dello snapshot, per linguaggio riconosciuto da Daodan.</Text>
      </Section>
      <Section title="Tecnologie e framework" level={3} icon={<Icon name="labels" />} end={<Badge variant="secondary">Riconosciuti</Badge>}>
        {premap.technologies.length > 0
          ? <DescriptionList items={premap.technologies.map(technology => ({ name: technology.name, value: <Column gap="xs">
              <Text>{technologyFacts(technology)}</Text>
              {technology.source && <Text variant="note" pre>{technology.source}</Text>}
            </Column> }))} />
          : <Empty title="Nessuna tecnologia riconosciuta nei manifest." />}
      </Section>
    </Grid>
    <Dependencies premap={premap} />
  </>;
}

export function PremapScreen() {
  const s = useModel();
  const { show } = useFrame();
  const premap = s.premap;
  useChoice();
  return <ScreenPanel title="Pre-mappa" subtitle="Conosci il punto di partenza." actions={<Button variant="ghost" size="sm" disabled={!premap}
    onClick={() => show({ title: 'Provenienza della pre-mappa', content: <Provenance /> })}><Icon name="info" />Provenienza</Button>}>
    <Column pad="lg" gap="xl">
      <Grid gap="xl">
        <Section title="Contesto attivo" level={3} icon={<Icon name="branch" />}>
          <ContextFacts />
          <Cluster><Button variant="outline" size="sm" onClick={() => model.selectStage('repository')}>Cambia repository o branch</Button></Cluster>
        </Section>
        {premap && <Section title="Inventario" level={3} icon={<Icon name="bulletList" />}>
          <DescriptionList items={inventory(premap).map(count => ({ name: count.name, value: <>{count.value} <Text variant="note">{count.of}</Text></> }))} />
        </Section>}
      </Grid>
      {s.premapError
        ? <Note tone="error" title="Pre-mappa non disponibile." actions={<Button variant="outline" onClick={event => {
            event.currentTarget.closest('main')?.focus({ preventScroll: true });  // the button goes: the focus stays in the content
            model.retryPremap();
          }}><Icon name="refresh" />Riprova</Button>}><Text pre data-selectable="">{s.premapError}</Text></Note>
        : premap ? <Found premap={premap} />
        : <Column aria-busy><Progress aria-label="Lettura della pre-mappa…" value={null} /></Column>}
    </Column>
  </ScreenPanel>;
}
