import { style, globalStyle } from '@vanilla-extract/css';
export const card = style({
  padding: 4,
  selectors: { '.dark &': { color: 'white' } },
});
globalStyle('.prose a', { color: 'var(--ink)' });
