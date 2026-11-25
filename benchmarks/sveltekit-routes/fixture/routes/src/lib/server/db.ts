export function find(id: string) {
	return { id, title: `Item ${id}` };
}

export function save(id: string, text: string) {
	return { id, text };
}
