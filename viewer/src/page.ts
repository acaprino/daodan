// What the pages share on Sigrid: Daodan's look, and the key its light, dark or system's choice is kept under. The pages
// have one origin, so each follows the choice made on the other.
import { colorTheme } from '@acaprino/sigrid';
import type { SchemeCommandsOptions } from '@acaprino/sigrid';

// design-check-ignore-next-line color-value: Daodan's accent, the one colour the theme is computed from
const ACCENT = '#006398';

export const LOOK: SchemeCommandsOptions = {
  theme: colorTheme({ id: 'daodan', label: 'Daodan', color: ACCENT, spot: 'balanced' }), storageKey: 'daodan.theme',
};
