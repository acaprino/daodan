import type { Actions } from './$types';

export async function load() {
	return { title: 'Log in' };
}

export const actions: Actions = {
	default: async function ({ request }) {
		const data = await request.formData();
		return { user: data.get('user') };
	}
};
