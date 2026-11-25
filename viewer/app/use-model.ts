// The App's one model, on the browser, and what a component reads of it.
import { useEffect, useSyncExternalStore } from 'react';
import { TOKEN } from '../src/token.ts';
import { createModel } from './model.ts';
import type { Snapshot, Symbols } from './snapshot.ts';

export const model = createModel({
  token: TOKEN,
  fetch: (path, init) => window.fetch(path, init),
  stream: address => new window.EventSource(address),
  storage: () => window.localStorage,
});

// The whole of it: the component is drawn again at every event.
export const useModel = () => useSyncExternalStore(model.subscribe, model.snapshot);

// A field of it, or a field of a field: the component is drawn again when that one changes. Never an object made here, which would be
// another one each time it is read.
export const useModelSlice = <T>(slice: (s: Snapshot) => T): T => useSyncExternalStore(model.subscribe, () => slice(model.snapshot()));

// The symbols of the file in the details, or null: asked when the file is chosen, and again when a new graph has dropped them.
export function useSymbols(file: string | null): Symbols | null {
  const symbols = useModelSlice(s => s.symbols), found = symbols?.file === file ? symbols : null;
  useEffect(() => { if (file !== null && !found) model.loadSymbols(file); }, [file, found]);
  return found;
}
