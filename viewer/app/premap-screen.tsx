// What the steps found in the repository before its analysis. What it holds, in short; its tree, what it is made with and what it depends on are
// behind; what is chosen in the tree, and where all this comes from, are in the inspector.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Button, Cluster, Column, Icon, ScrollArea, Table, TableBody, TableCell, TableHead, TableHeader, TableRow, Text, ToggleGroup, ToggleGroupItem } from '@acaprino/sigrid/primitives';
import { DescriptionList, Disclosure, Empty, SearchField } from '@acaprino/sigrid/components';
import { Tree } from '@acaprino/sigrid/assemblies';
import type { TreeNode } from '@acaprino/sigrid/assemblies';
import { Fold, List } from '../src/listed.tsx';
import { Mark } from '../src/mark.tsx';
import { Failed, Loading } from '../src/states.tsx';
import { number, plural } from '../src/words.ts';
import { useFrame } from './frame.tsx';
import type { Detail } from './frame.tsx';
import {
  CHOICE_TITLE, choiceDetails, choiceOf, countFound, dependencyFacts, directoryTree, finds, inventory, keptBranches, openBranches, PROVENANCE_NOTES,
  provenanceFacts, rowOf, technologyFacts, unitTree,
} from './premap.ts';
import { RunName } from './provenance.tsx';
import { ContextFold } from './repository-screen.tsx';
import { ctx } from './snapshot.ts';
import type { Premap } from './snapshot.ts';
import { model, useModel } from './use-model.ts';

// What is chosen in the tree.
function ChoiceDetails() {
  const s = useModel();
  const c = ctx(s), choice = choiceOf(s.premap, s.kept.treeSelected);
  if (!c || !choice) return null;
  const { facts, text } = choiceDetails(choice, c);
  return <>
    {text && <Text as="p" variant="soft">{text}</Text>}
    <DescriptionList items={facts} />
  </>;
}
const CHOICE = 'premap.choice';  // the details of it are these

// As on the map, what is chosen is in the details, and closing them leaves it; another stage takes the details away.
function useChoice() {
  const s = useModel();
  const { detail, show, close } = useFrame();
  const c = ctx(s), choice = choiceOf(s.premap, s.kept.treeSelected);
  const shown = detail?.id === CHOICE, wasShown = useRef(false);
  useEffect(() => {
    if (c && choice) {
      const { icon, name } = choiceDetails(choice, c);
      show({ id: CHOICE, key: s.kept.treeSelected, title: CHOICE_TITLE[choice.kind], icon, name, content: <ChoiceDetails /> });
    } else if (shown) close();
  }, [c && choice ? s.kept.treeSelected : '']);
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
    <List label="Che cosa prova" items={PROVENANCE_NOTES.map(text => <Text>{text}</Text>)} />
  </>;
}

const PROVENANCE: Detail = { id: 'premap.provenance', title: 'Provenienza della pre-mappa', icon: 'info', name: <RunName />, content: <Provenance /> };

// The directories or the technical units, filtered by the search. Open at first where something was looked for in them, and by Ctrl+F.
function Structure({ premap }: { premap: Premap }) {
  const s = useModel();
  const { search, field, reveal } = useFrame();
  const { treeMode, treeSearch, treeSelected, treeOpen } = s.kept;
  const [open, setOpen] = useState(treeSearch !== '' || treeSelected !== '');
  useEffect(() => {
    reveal.current = open ? null : () => setOpen(true);
    return () => { reveal.current = null; };
  }, [open]);
  const physical = treeMode === 'directories';
  const tree = useMemo(() => (physical ? directoryTree(premap.files) : unitTree(premap.units)), [premap, physical]);
  const expanded = useMemo(() => openBranches(tree.nodes, treeOpen), [tree, treeOpen]);
  const selected = useMemo(() => rowOf(tree, treeSelected), [tree, treeSelected]);
  const match = useCallback((node: TreeNode, query: string) => finds(tree, node.id, query), [tree]);
  const found = useMemo(() => countFound(tree, treeSearch), [tree, treeSearch]);
  const label = physical ? 'Albero delle directory' : 'Albero delle unità tecniche';
  const choose = (row: string) => { const choice = tree.choices.get(row); if (choice) model.keep({ treeSelected: choice }); };
  return <Disclosure label="Struttura del repository" summary={plural(premap.files.length, 'file', 'file')} open={open} onOpenChange={setOpen}><Column>
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
          onClick={() => { model.keep({ treeSearch: '' }); field?.focus(); }}>Azzera ricerca</Button>} />}
  </Column></Disclosure>;
}

// A version of a dependency, and where it is read.
const version = (found: { version: string; source: string } | null) => (found
  ? <Column gap="xs"><Text>{found.version}</Text><Text variant="note">{found.source}</Text></Column> : '—');

function Dependencies({ premap }: { premap: Premap }) {
  return <Fold label="Dipendenze per unità" summary={number(premap.dependencies.length)}>
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
  </Fold>;
}

// A technology, with its logo where its registry entry has one.
function Technology({ technology: { name, mark } }: { technology: Premap['technologies'][number] }) {
  return <Cluster wrap={false}><Mark image={model.markUrl(mark)} icon="labels" />{name}</Cluster>;
}

// The first names of a list, beside its row.
const names = (list: readonly { name: string }[]) => list.slice(0, 4).map(({ name }) => name).join(', ') + (list.length > 4 ? '…' : '');

function Found({ premap }: { premap: Premap }) {
  return <>
    <Column data-selectable="">
      <DescriptionList aria-label="Inventario" items={inventory(premap).map(count => ({ name: count.name, value: <>{count.value} <Text variant="note">{count.of}</Text></> }))} />
    </Column>
    <Column gap="xs">
      <Structure premap={premap} />
      <Fold label="Tecnologie e framework" summary={names(premap.technologies)}><Column data-selectable="">
        {premap.technologies.length > 0
          ? <DescriptionList aria-label="Tecnologie e framework" items={premap.technologies.map(technology => ({ name: <Technology technology={technology} />, value: <Column gap="xs">
              <Text>{technologyFacts(technology)}</Text>
              {technology.source && <Text variant="note" pre>{technology.source}</Text>}
            </Column> }))} />
          : <Empty title="Nessuna tecnologia riconosciuta nei manifest." />}
      </Column></Fold>
      <Fold label="Linguaggi" summary={names(premap.languages)}><Column data-selectable="">
        {premap.languages.length > 0
          ? <DescriptionList aria-label="Linguaggi" items={premap.languages.map(language => ({ name: language.name, value: plural(language.files, 'file', 'file') }))} />
          : <Empty title="Nessun file sorgente riconosciuto." />}
        <Text as="p" variant="note">File sorgente dello snapshot, per linguaggio riconosciuto da Daodan.</Text>
      </Column></Fold>
      <Dependencies premap={premap} />
      <ContextFold />
    </Column>
  </>;
}

// What the step found in the repository, before its behaviour is read: under the step that writes it.
export function PremapResult() {
  const s = useModel();
  const { show } = useFrame();
  const premap = s.premap;
  useChoice();
  return <>
    <Cluster><Button variant="ghost" size="sm" disabled={!premap} onClick={() => show(PROVENANCE)}><Icon name="info" />Provenienza</Button></Cluster>
    {s.premapError
      ? <Failed title="Pre-mappa non disponibile." cause={s.premapError} retry={model.retryPremap} />
      : premap ? <Found premap={premap} />
      : <Loading label="Lettura della pre-mappa…" />}
  </>;
}
