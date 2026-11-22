import { nanoid } from "nanoid";

export function slug(): string {
  return nanoid(8);
}
