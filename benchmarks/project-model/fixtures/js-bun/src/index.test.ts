import { expect, test } from "bun:test";
import { User } from "./index";

test("user", () => {
  expect(User.parse({ name: "a" }).name).toBe("a");
});
