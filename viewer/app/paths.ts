// A page of the paths in words: what it lists, which part of the list is in view, and each step with its proof.
import { number, proofLabel } from '../src/words.ts';
import { ORPHAN_WRITES } from './snapshot.ts';
import type { PathCard, PathPage, PathStep } from './snapshot.ts';

export type Listing = 'entries' | 'steps' | 'writes';
export const listingOf = (page: PathPage | null): Listing => (page?.id === ORPHAN_WRITES ? 'writes' : page?.id ? 'steps' : 'entries');

const NOUN: Record<Listing, string> = { entries: 'Ingressi', steps: 'Passaggi', writes: 'Scritture' };
// The words of the buttons are empty where there is no page before this one, or after it.
export function paging(page: PathPage): { range: string; previous: string; next: string } {
  const listing = listingOf(page), noun = NOUN[listing], result = page.result;
  const rows = (listing === 'writes' ? result?.effects : listing === 'steps' ? result?.steps : result?.cards)?.length ?? 0;
  return {
    range: `${noun} ${number(page.offset + 1)}–${number(page.offset + rows)} di ${number(result?.count)}`,
    previous: page.previous && page.previous.id === page.id ? `${noun} precedenti` : '',
    next: typeof result?.next_offset === 'number' ? `${noun} ${listing === 'writes' ? 'successive' : 'successivi'}` : '',
  };
}

const proofOf = (confidence: string | undefined, conflict = false) => proofLabel(confidence, conflict) || confidence;
const END: Record<string, string> = { lacuna: 'Lacuna', effetto: 'Effetto' };
// `end` is what the path ends with at this step, if it ends there.
export const stepWords = (step: PathStep): { title: string; end: string; proof: string } => ({
  title: `Passaggio ${number(step.n)}${step.parent ? ` · dal passo ${number(step.parent)}` : ''}`,
  end: END[step.end ?? ''] ?? '',
  proof: [step.site, proofOf(step.confidence, step.conflict), step.origin, step.resolver].filter(Boolean).join(' · '),
});
// What says which handler an entry has.
export const handlerSource = (card: PathCard) => [card.handler_source, proofOf(card.handler_confidence)].filter(Boolean).join(' · ');
