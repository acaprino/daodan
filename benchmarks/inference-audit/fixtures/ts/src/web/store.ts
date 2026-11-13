export interface Store {
  save(row: string): string;
}
export class MemoryStore implements Store {
  save(row: string): string {
    return row;
  }
}
export class FileStore implements Store {
  save(row: string): string {
    return row + '\n';
  }
}
export function persist(store: Store): string {
  return store.save('x');
}
