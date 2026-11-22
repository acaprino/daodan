import { z } from "zod";

export const Owner = z.object({ name: z.string() });

export function owner(name: string) {
  return Owner.parse({ name });
}
