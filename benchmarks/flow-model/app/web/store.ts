export interface State {
  cart: string[];
  theme: "light" | "dark";
  payment: Record<string, string>;
}

const state: State = { cart: [], theme: "light", payment: {} };
const listeners: Array<() => void> = [];

export function useStore<T>(select: (current: State) => T): T {
  return select(state);
}

export function setState(patch: Partial<State>): void {
  Object.assign(state, patch);
  for (const listener of listeners) {
    listener();
  }
}

export function subscribe(listener: () => void): void {
  listeners.push(listener);
}
