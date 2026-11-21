// What both pages do the same way: the keys and commands of Imago (`mountApp`), and the look and theme the user picks.
// The choice is kept in `localStorage`, which the two pages share (one origin), so each follows the other.
import { applyLook, parseLook, parseTheme } from '@acaprino/imago/shell';
import type { Look, ThemeChoice } from '@acaprino/imago/shell';
import { mountApp } from '@acaprino/imago/ui';
import type { AppearanceOptions, Registry, StandardLabels } from '@acaprino/imago/ui';

export const graphControls = { zoomIn: 'Ingrandisci', zoomOut: 'Riduci', fit: 'Inquadra tutto' };
export const LABELS: StandardLabels = {
  palette: 'Comandi', search: 'Cerca in questa vista', palettePlaceholder: 'Cerca un comando', paletteEmpty: 'Nessun comando',
};
const APPEARANCE_LABELS = {
  group: 'Aspetto', smooth: 'Aspetto Smooth', oni: 'Aspetto ONI', system: 'Tema come il sistema', light: 'Tema chiaro', dark: 'Tema scuro',
};
const LOOK_KEY = 'daodan.look', THEME_KEY = 'daodan.theme';
type Choice = { look: Look; theme: ThemeChoice };

// The stored choice; a missing, stale or corrupt value, or a storage that throws, is Smooth and the system theme.
export function readAppearance(storage: Pick<Storage, 'getItem'> | null): Choice {
  const read = (key: string) => { try { return storage?.getItem(key); } catch { return null; } };
  return { look: parseLook(read(LOOK_KEY)), theme: parseTheme(read(THEME_KEY)) };
}

export const storageOrNull = (): Storage | null => { try { return window.localStorage; } catch { return null; } };

const apply = (root: HTMLElement, choice: Choice) => applyLook(root, { app: 'daodan', ...choice, glass: false });

// The look at the start of a page, before its first paint.
export function applyStored(root: HTMLElement, storage: Pick<Storage, 'getItem'> | null) {
  apply(root, readAppearance(storage));
}

// `mountApp`'s `appearance`: the choice is read from the storage when it changes elsewhere, kept here when it is made.
export function appearanceOptions(root: HTMLElement, storage: Storage | null): AppearanceOptions & { reload: () => void } {
  let choice = readAppearance(storage);
  return {
    get: () => choice,
    set: next => {
      choice = next;
      try { storage?.setItem(LOOK_KEY, next.look); storage?.setItem(THEME_KEY, next.theme); } catch { /* the choice lasts this opening */ }
      apply(root, choice);
    },
    reload: () => { choice = readAppearance(storage); apply(root, choice); },
    labels: APPEARANCE_LABELS,
  };
}

// Mounts the shell's keys and commands, applies the stored look and keeps it in step with the system and the other page.
// The returned function undoes it all (React mounts an effect twice in development).
export function mountPage(shell: HTMLElement, registry: Registry, options: { search: () => void }): () => void {
  const root = document.documentElement;
  const appearance = appearanceOptions(root, storageOrNull());
  appearance.reload();
  const unmount = mountApp(shell, registry, { search: options.search, labels: LABELS, appearance });
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  const stored = (event: StorageEvent) => { if (event.key === null || event.key === LOOK_KEY || event.key === THEME_KEY) appearance.reload(); };
  media.addEventListener('change', appearance.reload);
  window.addEventListener('storage', stored);
  return () => {
    window.removeEventListener('storage', stored);
    media.removeEventListener('change', appearance.reload);
    unmount();
  };
}
