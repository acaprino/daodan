// The app both pages are, for Imago's shell: Daodan's accent, its Italian, and the keys its choices are kept under. The pages
// have one origin, so each follows the choice made on the other.
import { defineApp } from '@acaprino/imago';
import { SHELL_WORDS, WORDS } from './words.ts';

export const DAODAN = defineApp({
  id: 'daodan', name: 'Daodan', lang: 'it',
  // design-check-ignore-next-line color-value: Daodan's accent, the one colour the theme is computed from
  accent: '#006398',
  words: { sigrid: WORDS, shell: SHELL_WORDS },
  storage: { scheme: 'daodan.theme', zoom: 'daodan.zoom', sidebar: 'daodan.sidebar' },
});
