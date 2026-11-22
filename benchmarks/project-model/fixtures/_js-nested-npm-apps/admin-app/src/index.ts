import { z } from "zod";

export const Admin = z.object({ id: z.number() });

export function admin(id: number) {
  return Admin.parse({ id });
}
