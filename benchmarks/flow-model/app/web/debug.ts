import { apiGet } from "./api.ts";

export async function probe(path: string): Promise<unknown> {
  return apiGet(path);
}
