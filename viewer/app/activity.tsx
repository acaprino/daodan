// The events of the journal, the chronicle of a step or of the run, behind their row: the newest first. Those in sight are announced as
// they come; the others are drawn only while their row is open.
import { useMemo } from 'react';
import { Badge, Cluster, Column, Icon, Text } from '@acaprino/sigrid/primitives';
import type { IconName } from '@acaprino/sigrid/primitives';
import { Fold, LongFold } from '../src/listed.tsx';
import { MORE, plural } from '../src/words.ts';
import { logItems } from './notices.ts';
import type { LogItem } from './notices.ts';
import type { RunEvent } from './server.ts';

const LOG_ICON: Record<LogItem['type'], IconName> = { error: 'error', gap: 'alert', '': 'info' };
const FIRST = 8;  // how many events are in sight at first

function LogRow({ item }: { item: LogItem }) {
  return <Column as="li" gap="xs">
    <Cluster>
      <Icon name={LOG_ICON[item.type]} />
      <Text variant="strong">{item.title}</Text>
      {item.type && <Badge tone={item.type === 'error' ? 'danger' : 'warning'}>{item.type === 'error' ? 'Errore' : 'Attenzione'}</Badge>}
      {item.at && <Text variant="note"><time dateTime={item.at}>{new Date(item.at).toLocaleTimeString('it-IT')}</time></Text>}
    </Cluster>
    {item.detail && <Text variant="note" pre>{item.detail}</Text>}
  </Column>;
}

export function Activity({ events }: { events: readonly RunEvent[] }) {
  const items = useMemo(() => logItems({ events }), [events]);
  const row = (item: LogItem, index: number) => <LogRow key={index} item={item} />;  // an event keeps its place in the run
  const rows = items.map(row).reverse();
  const rest = rows.slice(FIRST);
  const more = MORE.events(rest.length);
  return <Fold label="Eventi" summary={plural(items.length, 'evento', 'eventi')}>
    <Column gap="md">
      {!rows.length && <Text as="p" variant="muted">Nessun evento ancora.</Text>}
      <Column as="ul" gap="md" aria-label="Ultimi eventi" aria-live="polite" aria-relevant="additions" data-selectable="">{rows.slice(0, FIRST)}</Column>
      {rest.length > 0 && <LongFold label={more}><Column as="ul" gap="md" aria-label={more} data-selectable="">{rest}</Column></LongFold>}
    </Column>
  </Fold>;
}
