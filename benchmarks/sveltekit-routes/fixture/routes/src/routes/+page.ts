import type { PageLoad } from './$types';

export const load: PageLoad = async ({ data }) => ({ ...data, home: true });
