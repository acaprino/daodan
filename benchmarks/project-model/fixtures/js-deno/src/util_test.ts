import { assertEquals } from "@std/assert";
import { greet } from "@/util.ts";

Deno.test("greet", () => {
  assertEquals(greet("a"), "hello a");
});
