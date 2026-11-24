// The App's one model, on the browser, and what a component reads of it.
import { useSyncExternalStore } from 'react';
import { createModel } from './model.ts';

export const model = createModel({
  token: new URLSearchParams(window.location.search).get('token') ?? '',
  fetch: (path, init) => window.fetch(path, init),
  stream: address => new window.EventSource(address),
  storage: () => window.localStorage,
});

export const useModel = () => useSyncExternalStore(model.subscribe, model.snapshot);
