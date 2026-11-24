// The repository: its address, whether it can be read, the branch to analyse, and the context in use.
import { useRef } from 'react';
import { Badge, Button, Cluster, Column, DescriptionList, FormField, Icon, Input, Note, Progress, Section, Select, Text } from '@acaprino/sigrid';
import { ScreenPanel } from './frame.tsx';
import { accessFeedback, accessible, isPreparing, preparation, repositoryContext, repositoryReason, repositorySlug, short } from './repository.ts';
import { ctx, slug } from './snapshot.ts';
import { model, useModel } from './use-model.ts';

// The run in view: its repository, branch, commit and id, to read and copy.
export function ContextFacts() {
  const s = useModel();
  const c = ctx(s);
  return c && <Column data-selectable="">
    <DescriptionList aria-label="Contesto attivo" items={repositoryContext(s).map(fact => ({ ...fact, code: true }))} />
    <Text as="p" variant="note">Checkout in sola lettura del commit {short(c.commit)}; run {c.run_id}. Nessun file del progetto viene eseguito.</Text>
  </Column>;
}

// Why the branch and the action wait, said once, beside the action.
const WHY = 'repository-why';
export function RepositoryActions() {
  const s = useModel();
  const busy = isPreparing(s) || s.selecting, reason = repositoryReason(s);
  return <>
    <Text id={WHY} variant="note">{reason || 'Un altro repository o branch prepara un nuovo checkout; lo stesso commit riusa l’analisi già fatta.'}</Text>
    <Button loading={busy} disabled={!busy && reason !== ''} aria-describedby={WHY} onClick={() => { model.selectRepository(); }}>Apri pre-mappa</Button>
  </>;
}

export function RepositoryScreen() {
  const s = useModel();
  const address = useRef<HTMLInputElement>(null);
  const c = ctx(s), repo = accessible(s), preparing = isPreparing(s), reason = repositoryReason(s);
  const feedback = accessFeedback(s.checked), work = preparation(s.server?.job);
  const help = ['Preferenza automatica: main, poi master, altrimenti il branch predefinito della repository.',
    repo && `${repo.branches.length} branch letti ora da GitHub; predefinito ${repo.default || '—'}.`].filter(Boolean).join(' ');
  return <ScreenPanel title="Repository" subtitle={c && `${slug(c)} · ${c.branch}`}>
    <Column pad="lg" gap="lg" width="page">
      <Text as="p" variant="soft">Inserisci un URL pubblico, verifica l’accesso e scegli il branch da analizzare.</Text>
      <Note title="Repository GitHub pubblica">Daodan legge i branch e scarica quello scelto in sola lettura; nulla del progetto viene eseguito su questa macchina. Il login GitHub non è disponibile in questa versione.</Note>
      <Section title="Repository GitHub" level={3} icon={<Icon name="globe" />} gap="lg">
        <form noValidate onSubmit={event => {
          event.preventDefault();
          model.verifyRepositoryUrl();
          if (!repositorySlug(s.kept.repositoryUrl)) address.current?.focus();
        }}>
          <Column gap="md">
            <FormField label="URL GitHub" error={s.checkError} help="Inserisci l’URL e verifica l’accesso. Senza login si aprono solo repository pubbliche.">
              <Input ref={address} type="url" placeholder="https://github.com/proprietario/repository" value={s.kept.repositoryUrl}
                onChange={event => model.setRepositoryUrl(event.target.value)} />
            </FormField>
            <Cluster><Button type="submit" variant="outline" loading={s.checking}><Icon name="check" />Verifica accesso</Button></Cluster>
          </Column>
        </form>
        {feedback && <Note tone={feedback.tone} title={feedback.title}>{feedback.message}</Note>}
        <FormField label="Branch da analizzare" help={help}>
          <Select aria-describedby={reason ? WHY : undefined} disabled={reason !== ''} placeholder="Verifica prima l’accesso"
            value={repo ? s.branch : ''} onValueChange={model.setBranch}
            options={(repo?.branches ?? []).map(b => ({ value: b.name, label: `${b.name} · ${short(b.commit)}` }))} />
        </FormField>
        {work?.state === 'preparing' && <Column aria-busy>
          <Text>Preparazione in corso: {[work.step, work.detail].filter(Boolean).join(' · ')}.</Text>
          <Progress aria-label="Preparazione in corso" value={null} />
        </Column>}
        {work?.state === 'failed' && <Note tone="error" title={`Preparazione non riuscita (${work.step}).`}><Text pre data-selectable="">{work.detail}</Text></Note>}
        {s.selectError && <Note tone="error" title="Selezione non riuscita."><Text pre data-selectable="">{s.selectError}</Text></Note>}
      </Section>
      <Section title="Contesto attivo" level={3} icon={<Icon name="branch" />}
        end={c && <Button variant="ghost" size="sm" onClick={() => model.selectStage('premap')}>Torna alla pre-mappa</Button>}>
        {c ? <ContextFacts /> : <Text as="p" variant="muted">{preparing
          ? 'Preparazione in corso: il contesto sarà pronto alla fine del checkout e dello snapshot.' : 'Nessuna repository selezionata sul server.'}</Text>}
      </Section>
      <Section title="Accesso GitHub" level={3} icon={<Icon name="key" />} end={<Badge variant="secondary">Non connesso</Badge>}>
        <Text as="p" variant="soft">Login non disponibile. In questa versione Daodan legge solo repository pubbliche, senza account. Un accesso negato non dimostra che la repository sia privata: può non esistere o mancare un permesso.</Text>
      </Section>
    </Column>
  </ScreenPanel>;
}
