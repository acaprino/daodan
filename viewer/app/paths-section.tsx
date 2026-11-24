// The paths of the synthesis, a page at a time: the entries, the steps proven from one, and the writes with no entry.
import { Badge, Button, Cluster, Column, DescriptionList, Empty, Heading, Icon, ItemList, ItemRow, Section, Text } from '@acaprino/sigrid';
import { handlerSource, listingOf, paging, stepWords } from './paths.ts';
import { number, ORPHAN_WRITES, plural } from './snapshot.ts';
import type { PathPage, PathResult } from './snapshot.ts';
import { Failed, Loading } from './states.tsx';
import { model, useModel } from './use-model.ts';

// What is pressed may go with its page: the focus goes to the section, which stays.
const SECTION = 'flow-paths';
const turn = (act: () => unknown) => () => { act(); document.getElementById(SECTION)?.focus({ preventScroll: true }); };

type Shown = { page: PathPage; result: PathResult };

function Paging({ page }: { page: PathPage }) {
  const { range, previous, next } = paging(page);
  return <Cluster>
    <Text variant="note">{range}</Text>
    {previous && <Button variant="outline" size="sm" onClick={turn(model.previousPaths)}>{previous}</Button>}
    {next && <Button variant="outline" size="sm" onClick={turn(model.nextPaths)}>{next}</Button>}
  </Cluster>;
}

function Entries({ page, result: { cards = [] } }: Shown) {
  const missing = useModel().server?.mapped?.discovery?.effect_coverage?.without_entry;
  return <>
    {!!missing && <Text as="p">{plural(missing, 'scrittura', 'scritture')} senza un percorso provato da un ingresso.</Text>}
    {!cards.length ? <Empty title="Nessun ingresso classificato per questo snapshot." /> : <>
      <ItemList aria-label="Ingressi">{cards.map(card =>
        <ItemRow key={card.card_id} title={card.label || card.event} wrapTitle description={<Text pre>{card.handler} · {card.site}</Text>}
          end={<Icon name="chevron" />} onClick={turn(() => model.openPaths(card.card_id))} />)}</ItemList>
      <Paging page={page} />
    </>}
  </>;
}

function Steps({ page, result: { card, steps = [] } }: Shown) {
  const source = card && handlerSource(card);
  return <Column gap="md" data-selectable="">
    {card && <>
      <Heading size="small" level={4}>{card.label || card.event}</Heading>
      <DescriptionList aria-label="Ingresso" items={[
        { name: 'Evento', value: `${card.event} · ${card.kind}` },
        { name: 'Gestore', value: card.handler, code: true },
        source ? { name: 'Fonte del gestore', value: source } : null,
        { name: 'Ingresso', value: card.site, code: true },
      ]} />
    </>}
    {!steps.length ? <Text as="p" variant="muted">Nessun passaggio provato dal gestore.</Text> : <>
      <Column as="ol" gap="md" aria-label="Passaggi">{steps.map(step => {
        const { title, end, proof } = stepWords(step);
        return <Column as="li" key={step.n} gap="xs">
          <Cluster><Text variant="strong">{title}</Text>{end && <Badge variant="secondary">{end}</Badge>}</Cluster>
          <Text pre><Text>{step.from}</Text>{step.to && <> · {step.type} → <Text>{step.to}</Text></>}</Text>
          {proof && <Text variant="note" pre>{proof}</Text>}
          {step.reason && <Text pre>{step.reason}</Text>}
        </Column>;
      })}</Column>
      <Paging page={page} />
    </>}
  </Column>;
}

function Writes({ page, result: { effects = [], without_entry, writes, reached } }: Shown) {
  return <Column gap="md" data-selectable="">
    <Heading size="small" level={4}>Scritture senza ingresso</Heading>
    <Text as="p">{number(without_entry)} di {number(writes)} scritture senza un percorso provato da un ingresso. Con un percorso provato: {number(reached)}.</Text>
    {effects.length > 0 && <>
      <Column as="ul" gap="md" aria-label="Scritture senza ingresso">{effects.map(effect => <Column as="li" key={effect.n} gap="xs">
        <Text pre><Text>{effect.writer}</Text> → <Text>{effect.effect}</Text></Text>
        <Text variant="note" pre>{effect.site}</Text>
        <Text pre>{effect.reason}</Text>
        {effect.stopped_at && <Text pre>Le prove si fermano in {effect.stopped_at}.</Text>}
      </Column>)}</Column>
      <Paging page={page} />
    </>}
  </Column>;
}

const LISTED = { entries: Entries, steps: Steps, writes: Writes };

export function Paths() {
  const { pathPage: page } = useModel();
  const listing = listingOf(page), Listed = LISTED[listing];
  return <Section id={SECTION} tabIndex={-1} title="Percorsi per ingresso" level={3} icon={<Icon name="branch" />} gap="md"
    end={listing === 'entries'
      ? <Button variant="ghost" size="sm" onClick={turn(() => model.openPaths(ORPHAN_WRITES))}>Scritture senza ingresso</Button>
      : <Button variant="ghost" size="sm" onClick={turn(model.listPaths)}>Torna agli ingressi</Button>}>
    {page?.error ? <Failed title="Percorsi non disponibili." cause={page.error} retry={turn(model.retryPaths)} />
      : page?.result ? <Listed page={page} result={page.result} />
      : <Loading label="Lettura dei percorsi…" />}
  </Section>;
}
