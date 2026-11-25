// Lists to read and copy, so not rows to press, and what opens in place: what is under a closed row is not drawn.
import { useState } from 'react';
import type { ReactNode } from 'react';
import { Column, ScrollArea } from '@acaprino/sigrid/primitives';
import { Disclosure } from '@acaprino/sigrid/components';

type ListProps = { label: string; items: readonly ReactNode[]; ordered?: boolean };

export function List({ label, items, ordered = false }: ListProps) {
  return <Column as={ordered ? 'ol' : 'ul'} gap={ordered ? 'md' : 'sm'} aria-label={label}>
    {items.map((item, index) => <Column as="li" key={index} gap="xs">{item}</Column>)}</Column>;
}

export function Fold({ label, children }: { label: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return <Disclosure label={label} open={open} onOpenChange={setOpen}>{open && children}</Disclosure>;
}

// Behind its row, a long one scrolls by itself, so that what follows stays near.
export function LongFold({ label, children }: { label: string; children: ReactNode }) {
  return <Fold label={label}><ScrollArea bounded pad="xs" aria-label={label}>{children}</ScrollArea></Fold>;
}

export function FoldedList(list: ListProps) {
  return <LongFold label={list.label}><List {...list} /></LongFold>;
}

// Nothing is cut off in silence: the first entries of a list, and the others behind a row that says how many they are (`more`).
export function Listed({ items, first = 8, more, ...list }: ListProps & { first?: number; more: (count: number) => string }) {
  const rest = items.slice(first);
  return <>
    <List {...list} items={items.slice(0, first)} />
    {rest.length > 0 && <FoldedList {...list} label={more(rest.length)} items={rest} />}
  </>;
}
