// The repository: its address, whether it can be read, and the branch to analyse. The context in use and how it is read are behind.
import { Button, Cluster, Column, Icon, Input, Progress, Section, Select, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList, FormField, Note } from '@acaprino/sigrid/components';
import { Fold } from '../src/listed.tsx';
import { Failed } from '../src/states.tsx';
import { Activity } from './activity.tsx';
import { planOf, policyFacts } from './plan.ts';
import { accessFeedback, accessible, isPreparing, preparation, repositoryContext, repositorySlug, RESTART, sameChoice, short } from './repository.ts';
import { ctx, slug } from './snapshot.ts';
import { Step, STEP_FORM, useGoOn } from './step.tsx';
import { model, useModel } from './use-model.ts';

// The run in view: its repository, branch, commit and id, to read and copy.
function ContextFacts() {
  const s = useModel();
  const c = ctx(s);
  return c && <Column data-selectable="">
    <DescriptionList aria-label="Contesto attivo" items={repositoryContext(s).map(fact => ({ ...fact, code: true }))} />
    <Text as="p" variant="note">Checkout in sola lettura del commit {short(c.commit)}; run {c.run_id}. Nessun file del progetto viene eseguito.</Text>
  </Column>;
}

// It, behind its row.
export function ContextFold() {
  const s = useModel();
  const c = ctx(s);
  return <Fold label="Contesto attivo" summary={c ? `${slug(c)} · ${c.branch}` : 'Nessuno'}>
    {c ? <ContextFacts /> : <Text as="p" variant="muted">{isPreparing(s)
      ? 'Preparazione in corso: il contesto sarà pronto alla fine del checkout e dello snapshot.' : 'Nessuna repository selezionata sul server.'}</Text>}
  </Fold>;
}

// What the analysis may reach and where it runs, once a context is chosen (the plan is of one): the registries, the hosts approved and
// blocked, that every other host asks here, and the container engine, or why there is none.
function Policy() {
  const policy = planOf(useModel())?.policy;
  if (!policy) return null;
  return <Section title="Che cosa può fare l’analisi" level={3} icon={<Icon name="globe" />}>
    <Column data-selectable=""><DescriptionList aria-label="Politica dell’analisi" items={policyFacts(policy)} /></Column>
    <Text as="p" variant="note">Ogni azione del piano dice se esegue il codice del progetto, se lo fa nel container e quale rete usa.</Text>
  </Section>;
}

export function RepositoryScreen() {
  const s = useModel();
  const goOn = useGoOn();
  const c = ctx(s), repo = accessible(s), same = sameChoice(s), busy = isPreparing(s) || s.selecting;
  const feedback = accessFeedback(s.checked), work = preparation(s.server?.job);
  const help = repo && `Preferenza automatica: main, poi master, altrimenti il branch predefinito. ${repo.branches.length} branch letti ora da GitHub; predefinito ${repo.default || '—'}.`;
  return <Step stage="repository" line="Quale repository GitHub vuoi analizzare?">
    <form id={STEP_FORM} noValidate onSubmit={event => { event.preventDefault(); goOn(); }}>
      <Column gap="lg">
        <FormField label="URL GitHub" error={s.checkError} help="Solo repository pubbliche. Nulla del progetto viene eseguito su questa macchina.">
          <Input type="url" placeholder="https://github.com/proprietario/repository" value={s.kept.repositoryUrl}
            onChange={event => model.setRepositoryUrl(event.target.value)} />
        </FormField>
        {repo && <FormField label="Branch da analizzare" help={help}>
          <Select disabled={busy} value={s.branch} onValueChange={model.setBranch}
            options={repo.branches.map(b => ({ value: b.name, label: `${b.name} · ${short(b.commit)}` }))} />
        </FormField>}
      </Column>
    </form>
    {same && !repo && repositorySlug(s.kept.repositoryUrl) !== null && <Cluster>
      <Button variant="outline" loading={s.checking} onClick={() => { model.verifyRepositoryUrl(); }}>Cambia branch</Button>
    </Cluster>}
    {feedback && <Note tone={feedback.tone} title={feedback.title}>{feedback.message}</Note>}
    {c && !same && <Note title="Che cosa riparte">{RESTART}</Note>}
    {work?.state === 'preparing' && <Column aria-busy>
      <Text>Preparazione in corso: {[work.step, work.detail].filter(Boolean).join(' · ')}.</Text>
      <Progress aria-label="Preparazione in corso" value={null} />
    </Column>}
    {work?.state === 'failed' && <Failed title={`Preparazione non riuscita (${work.step}).`} cause={work.detail} />}
    {s.selectError && <Failed title="Selezione non riuscita." cause={s.selectError} />}
    {c && <Policy />}
    <Column gap="xs">
      <ContextFold />
      {c && <Activity events={s.events.filter(event => event.run)} />}
      <Fold label="Accesso GitHub" summary="Non connesso">
        <Text as="p" variant="soft">Login non disponibile. In questa versione Daodan legge solo repository pubbliche, senza account. Un accesso negato non dimostra che la repository sia privata: può non esistere o mancare un permesso.</Text>
      </Fold>
      <Fold label="Come viene letta la repository">
        <Text as="p" variant="soft">Daodan legge i branch e scarica quello scelto in sola lettura; nulla del progetto viene eseguito su questa macchina. L’analisi parte da sola quando il branch è pronto.</Text>
      </Fold>
    </Column>
  </Step>;
}
