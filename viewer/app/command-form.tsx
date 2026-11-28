// The window of the commands: those the person or the assistant stated for the folders of the project, each with who stated it,
// «Conferma» for a proposal and its removal; and the form that sets the person's own for a kind and a folder, which runs at the
// next analysis, in the container. It opens from an action of the plan that runs a command (`model.showCommand`), and from the
// palette, which is where a folder with no action of its own (a start the pre-map did not find, the tests of a folder) is set.
import { Badge, Button, Cluster, Column, Icon, Input, Section, Select, Text, Textarea } from '@acaprino/sigrid/primitives';
import { DescriptionList, Dialog, FormField } from '@acaprino/sigrid/components';
import { useCommand } from '@acaprino/sigrid/assemblies';
import { commandFacts, draftErrors, gradeOf, isReady, KINDS, titleOf, workOf } from './commands.ts';
import type { DraftErrors } from './commands.ts';
import type { Command, CommandKind } from './server.ts';
import { ctx } from './snapshot.ts';
import { model, useModel } from './use-model.ts';

// The form is in the window's body and its button in the footer: the button names the form.
const FORM = 'daodan-command-form';

// A command kept: what it does and where, its words, who stated it; «Conferma» while it is the assistant's.
function Kept({ command, busy }: { command: Command; busy: string }) {
  const grade = gradeOf(command), title = titleOf(command);
  return <Section title={title} level={3} icon={<Icon name="terminal" />} end={<Badge variant="secondary" tone={grade.tone}>{grade.badge}</Badge>}>
    <DescriptionList aria-label={title} items={commandFacts(command)} />
    <Cluster>
      {command.by === 'assistant' && <Button size="sm" variant="outline" aria-label={`Conferma il comando: ${title}`}
        loading={busy === workOf('confirm', command)} disabled={busy !== ''} onClick={() => { model.confirmCommand(command); }}>
        <Icon name="check" />Conferma</Button>}
      <Button size="sm" variant="ghost" aria-label={`Togli il comando: ${title}`}
        loading={busy === workOf('remove', command)} disabled={busy !== ''} onClick={() => { model.removeCommand(command); }}>
        <Icon name="delete" />Togli il comando</Button>
    </Cluster>
  </Section>;
}

export function CommandDialog() {
  const s = useModel();
  const draft = s.commandDraft, busy = s.commandBusy, kept = s.server?.commands ?? [];
  useCommand({ id: 'daodan.commands', label: 'Comandi del progetto…', group: 'Analisi', icon: <Icon name="terminal" />,
    when: ctx(s) !== null && draft === null, run: () => model.showCommand('tests', '.') });
  const errors: DraftErrors = draft ? draftErrors(draft) : {};
  return <Dialog open={draft !== null} onOpenChange={open => { if (!open) model.hideCommand(); }} width="lg"
    title="Comandi del progetto"
    description="Il comando che imposti passa davanti a quelli della CI e del progetto, e gira alla prossima analisi, solo nel container. Quello proposto dall’assistente aspetta la tua conferma."
    footer={<>
      <Button variant="ghost" disabled={busy !== ''} onClick={model.hideCommand}>Chiudi</Button>
      <Button type="submit" form={FORM} loading={busy === 'set'} disabled={busy !== '' || !draft || !isReady(draft)}>
        <Icon name="check" />Imposta il comando</Button>
    </>}>
    {draft && <Column gap="lg" data-selectable="">
      {kept.length === 0 && <Text as="p" variant="muted">Nessun comando impostato o proposto per questo progetto.</Text>}
      {kept.map(command => <Kept key={JSON.stringify([command.kind, command.root, command.runner])} command={command} busy={busy} />)}
      <Section title="Il tuo comando" level={3} icon={<Icon name="rename" />}>
        <form id={FORM} noValidate onSubmit={event => { event.preventDefault(); model.setCommand(); }}>
          <Column gap="md">
            <FormField label="Che cosa fa">
              <Select value={draft.kind} options={[...KINDS]} onValueChange={value => model.editCommand({ kind: value as CommandKind })} />
            </FormField>
            <FormField label="Cartella" help="Dalla radice del progetto: «.» è la radice." error={errors.root}>
              <Input mono value={draft.root} onChange={event => model.editCommand({ root: event.target.value })} />
            </FormField>
            <FormField label="Comando" help="Una parola per riga, come il programma le riceve: npm, run, dev.">
              <Textarea mono rows={3} maxRows={8} value={draft.words} onChange={event => model.editCommand({ words: event.target.value })} />
            </FormField>
            {draft.kind === 'starts' && <FormField label="Porta" help="Facoltativa: quella su cui l’app risponde." error={errors.port}>
              <Input short="xs" inputMode="numeric" value={draft.port} onChange={event => model.editCommand({ port: event.target.value })} />
            </FormField>}
          </Column>
        </form>
      </Section>
    </Column>}
  </Dialog>;
}
