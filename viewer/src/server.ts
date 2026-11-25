// The server of the map's page.
import { createHttp } from './http.ts';
import { markAddress } from './marks.ts';
import { TOKEN } from './token.ts';

export const { get, post } = createHttp((path, init) => window.fetch(path, init), TOKEN);
export const imageOf = (mark: string | null | undefined) => markAddress('./api/mark', mark, TOKEN);
