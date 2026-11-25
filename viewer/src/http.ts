// How the two pages ask their server: the token in a header, a failure in words, and the one rule for a server that is busy.
import { FAILURE } from './words.ts';

export type Fetch = (path: string, init?: RequestInit) => Promise<Response>;

export const RETRY_MS = 2000;  // a busy server is asked again after this
// «Not now, the same may be asked again»: another helper holds the project (`ProjectBusy` in visual.py), or it is asked too often.
const BUSY = [503, 429];

async function answer(response: Response) {
  const body = await response.json().catch(() => ({}));
  if (BUSY.includes(response.status)) throw Object.assign(new Error(FAILURE.busy), { busy: true });
  if (response.status === 403) throw new Error(FAILURE.refused);
  if (!response.ok) throw new Error(body.error || FAILURE.status(response.status));
  return body;
}

// The browser's own error, where there is no answer at all, is in its language.
function unanswered(error: unknown): never {
  throw error instanceof TypeError ? new Error(FAILURE.unanswered, { cause: error }) : error;
}

export const isBusy = (error: unknown) => (error as { busy?: boolean } | null)?.busy === true;
export const causeOf = (error: unknown) => (error instanceof Error ? error.message : String(error));

// `token`: none is needed by a server that gave the page none.
export function createHttp(fetch: Fetch, token: string) {
  const auth: Record<string, string> = token ? { 'X-Daodan-Token': token } : {};
  const ask = (path: string, init: RequestInit) => fetch(path, init).catch(unanswered).then(answer);
  return {
    get: <T>(path: string): Promise<T> => ask(path, { headers: auth, cache: 'no-store' }),
    post: <T>(path: string, body: unknown): Promise<T> =>
      ask(path, { method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  };
}

// What is read of a busy server is asked again until it answers, or until nobody waits for it any more (`wanted`): then there is
// nothing: that it is busy is said once. What is posted is not asked again: it is the person who does.
export async function whenFree<T>(ask: () => Promise<T>, onBusy: () => void, wanted: () => boolean = () => true): Promise<T | undefined> {
  for (let first = true; ; first = false) {
    try { return await ask(); }
    catch (error) {
      if (!isBusy(error)) throw error;
      if (!wanted()) return undefined;
      if (first) onBusy();
    }
    await new Promise(resolve => setTimeout(resolve, RETRY_MS));
    if (!wanted()) return undefined;
  }
}
