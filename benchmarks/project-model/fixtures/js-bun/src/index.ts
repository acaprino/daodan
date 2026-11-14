import { z } from "zod";

export const User = z.object({ name: z.string() });

console.log(User.parse({ name: Bun.version }));
