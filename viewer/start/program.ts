// What the page asks of the program it is inside (apps/desktop/src-tauri/src/life.rs), and nothing else.
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

// What the server does, and why where it is not there.
export type State = 'starting' | 'restarting' | 'failed' | 'stopped';
export type Told = [state: State, cause: string];

// Tells the state, and again at every change; listening first, so that none is lost.
export async function follow(tell: (told: Told) => void): Promise<void> {
  const ask = async () => tell(await invoke<Told>('start_state'));
  await listen('server-state', ask);
  await ask();
}

export const startAgain = (): Promise<void> => invoke('start_again');
