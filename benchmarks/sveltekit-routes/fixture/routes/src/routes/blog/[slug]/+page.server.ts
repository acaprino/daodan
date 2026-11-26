import type { Actions, PageServerLoad } from './$types';
import { find, save } from '$lib/server/db';

export const load: PageServerLoad = async ({ params }) => find(params.slug);

export const actions: Actions = {
	comment: async ({ request, params }) => {
		const data = await request.formData();
		return save(params.slug, String(data.get('text')));
	},
	like: async ({ params }) => ({ liked: params.slug })
};
