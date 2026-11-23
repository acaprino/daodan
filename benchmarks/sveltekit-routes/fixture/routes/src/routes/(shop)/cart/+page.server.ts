import type { Actions } from './$types';

export const actions: Actions = {
	default: async ({ locals }) => ({ emptied: locals.user?.id })
};
