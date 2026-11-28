// The project file in the App: a node's name and description changed by hand in its details, with its conflicts and its history;
// the project's history as details of its own; «Apri» and «Salva una copia» as commands of the palette.
import { useRef, useState } from 'react';
import { Badge, Button, Cluster, Column, Icon, Input, Section, Text, Textarea } from '@acaprino/sigrid/primitives';
import { DescriptionList, Dialog, FormField, Note } from '@acaprino/sigrid/components';
import { useCommand } from '@acaprino/sigrid/assemblies';
import { Listed } from '../src/listed.tsx';
import type { Detail } from './frame.tsx';
import { FIELDS, fieldLabel, historyOf, KEEPS, openConflicts, provenanceText, recordedText, revisionRow, valueText } from './project.ts';
import type { Conflict, Field } from './project.ts';
import { RunName } from './provenance.tsx';
import { ctx } from './snapshot.ts';
import { model, useModel, useModelSlice } from './use-model.ts';

const muted = (text: string) => <Text as="p" variant="muted">{text}</Text>;
const MORE = (count: number) => `Altre ${count} revisioni`;
const line = ({ name, about }: { name: string; about: string }) => <><Text pre>{name}</Text><Text variant="note" pre>{about}</Text></>;

// A conflict: the choice made by hand and the value that came, each with where it comes from, and the three ways out.
function ConflictNote({ conflict }: { conflict: Conflict }) {
  const busy = useModelSlice(s => s.projectBusy);
  return <Note tone="warning" announce={false} title={`${fieldLabel(conflict.field_path)}: l’analisi porta un altro valore`}
    actions={KEEPS.map(({ keep, label }) => <Button key={keep} size="sm" variant={keep === 'manual' ? 'outline' : 'ghost'}
      loading={busy === `resolve ${conflict.conflict_id}`} disabled={busy !== ''}
      onClick={() => { model.resolveConflict(conflict.conflict_id, keep); }}>{label}</Button>)}>
    <DescriptionList aria-label={`Conflitto ${conflict.conflict_id}`} items={[
      { name: 'Modifica a mano', value: valueText(conflict.value) },
      { name: 'In arrivo', value: valueText(conflict.incoming) },
      { name: 'Provenienza', value: provenanceText(conflict.provenance) },
      { name: 'Rilevato', value: `revisione ${conflict.detected_rev}` },
    ]} />
  </Note>;
}

// The window that changes a name or a description: what is written is kept in the file, by the person who wrote it.
function EditDialog({ id, field, now, onClose }: { id: string; field: Field; now: string; onClose: () => void }) {
  const [value, setValue] = useState(now);
  const busy = useModelSlice(s => s.projectBusy) === 'edit';
  const save = async () => { if (await model.changeNode(id, field, value)) onClose(); };
  return <Dialog open onOpenChange={open => { if (!open) onClose(); }} title={`Modifica: ${FIELDS[field].label.toLowerCase()}`}
    description="La modifica si salva nel file di progetto, con il tuo nome e la revisione di partenza. L’analisi seguente la conserva."
    footer={<>
      <Button variant="ghost" onClick={onClose}>Annulla</Button>
      <Button loading={busy} disabled={busy || (field === 'name' && !value.trim())} onClick={() => { save(); }}>Salva la modifica</Button>
    </>}>
    <FormField label={FIELDS[field].label}>
      {field === 'description'
        ? <Textarea autoFocus maxRows={8} value={value} onChange={event => setValue(event.target.value)} />
        : <Input autoFocus value={value} onChange={event => setValue(event.target.value)} />}
    </FormField>
  </Dialog>;
}

// In a node's details: change its name or description, see what disagrees with a change, and its history.
export function NodeProject({ id, name, description }: { id: string; name: string; description: string }) {
  const s = useModel();
  const [editing, setEditing] = useState<Field | null>(null);
  const project = s.project, conflicts = openConflicts(project, id), history = historyOf(project, id);
  const ready = project !== null && s.projectBusy === '';
  return <Section title="Modifiche a mano" level={3} icon={<Icon name="rename" />}>
    <Cluster>
      <Button size="sm" variant="outline" disabled={!ready} onClick={() => setEditing('name')}><Icon name="rename" />Rinomina</Button>
      <Button size="sm" variant="ghost" disabled={!ready} onClick={() => setEditing('description')}>Modifica la descrizione</Button>
      {conflicts.length > 0 && <Badge variant="secondary" tone="warning">{conflicts.length === 1 ? 'Un conflitto' : `${conflicts.length} conflitti`}</Badge>}
    </Cluster>
    {!project && muted(s.projectError || recordedText(s.server?.project))}
    {conflicts.map(conflict => <ConflictNote key={conflict.conflict_id} conflict={conflict} />)}
    {project && (history.length > 0
      ? <Listed label="Cronologia del nodo" items={history.map(revision => line(revisionRow(revision)))} more={MORE} />
      : muted('Nessuna modifica a mano su questo nodo.'))}
    {editing && <EditDialog id={id} field={editing} now={editing === 'name' ? name : description} onClose={() => setEditing(null)} />}
  </Section>;
}

function ProjectHistory() {
  const s = useModel();
  const project = s.project, conflicts = openConflicts(project);
  if (!project) return muted(s.projectError || recordedText(s.server?.project));
  return <>
    <Text as="p" variant="muted">{recordedText(s.server?.project)} Ogni revisione dice chi l’ha fatta e da quale revisione è partita.</Text>
    {conflicts.length > 0 && <Section title="Conflitti aperti" level={3} icon={<Icon name="alert" />}>
      {conflicts.map(conflict => <Column key={conflict.conflict_id}>
        <Text variant="strong" pre>{conflict.key ?? conflict.object_id}</Text>
        <ConflictNote conflict={conflict} />
      </Column>)}
    </Section>}
    <Section title="Revisioni" level={3} icon={<Icon name="history" />}>
      <Listed label="Revisioni del progetto" items={historyOf(project).map(revision => line(revisionRow(revision)))} more={MORE} />
    </Section>
  </>;
}

export const PROJECT_HISTORY: Detail = { id: 'project', title: 'Cronologia del file di progetto', icon: 'history', name: <RunName />, content: <ProjectHistory /> };

// «Apri» and «Salva una copia»: the path of a file on this computer, where the local server reads and writes it.
type FileWork = 'open' | 'save';
const FILE_WORK: Record<FileWork, { title: string; description: string; action: string }> = {
  open: { title: 'Apri un file di progetto', action: 'Apri il file',
    description: 'Il file prende il posto di quello della repository che nomina; la sua cronologia resta e le sue modifiche valgono come le altre.' },
  save: { title: 'Salva una copia del file di progetto', action: 'Salva la copia',
    description: 'Una copia completa, con la cronologia, da passare ad altri. Il file di destinazione si sostituisce.' },
};

export function ProjectFileCommands() {
  const [work, setWork] = useState<FileWork | null>(null), [path, setPath] = useState('');
  const selected = useModelSlice(s => ctx(s) !== null), busy = useModelSlice(s => s.projectBusy);
  const opener = useRef<HTMLElement | null>(null);
  const start = (next: FileWork) => { opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : null; setPath(''); setWork(next); };
  useCommand({ id: 'daodan.project.open', label: 'Apri un file di progetto…', group: 'File', icon: <Icon name="upload" />, when: selected, run: () => start('open') });
  useCommand({ id: 'daodan.project.save', label: 'Salva una copia del file di progetto…', group: 'File', icon: <Icon name="download" />, when: selected,
    run: () => start('save') });
  const done = async () => {
    if (work && await (work === 'open' ? model.openProject(path) : model.saveProject(path))) setWork(null);
  };
  const shown = work && FILE_WORK[work];
  return <Dialog open={shown !== null} onOpenChange={open => { if (!open) setWork(null); }} restoreFocusTo={opener}
    title={shown?.title ?? ''} description={shown?.description}
    footer={<>
      <Button variant="ghost" onClick={() => setWork(null)}>Annulla</Button>
      <Button loading={busy === work} disabled={busy !== '' || !path.trim()} onClick={() => { done(); }}>{shown?.action}</Button>
    </>}>
    <FormField label="Percorso del file" help="Sul computer dove gira Daodan, per esempio /home/ada/progetti/shop.daodan.">
      <Input mono autoFocus value={path} onChange={event => setPath(event.target.value)} />
    </FormField>
  </Dialog>;
}
