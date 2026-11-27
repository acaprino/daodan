const handlers = {
  create: (id: string) => id,
  remove(id: string) {
    return id.length;
  },
};
export function dispatch(key: 'create' | 'remove', id: string) {
  return handlers[key](id);
}
