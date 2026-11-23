import type { Actions, PageServerLoad } from './$types';
import { fail } from '@sveltejs/kit';

export const load: PageServerLoad = async () => ({ total: 10 });

export const actions = {
	pay: async ({ request }) => {
		const data = await request.formData();
		return data.get('card') ? { paid: true } : fail(400, { missing: true });
	},
	cancel: async () => ({ cancelled: true })
} satisfies Actions;
