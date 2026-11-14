const test = require("node:test");
const assert = require("node:assert");
const ms = require("ms");
const { first } = require("../src");

test("first", () => {
  assert.strictEqual(first([1, 2]), 1);
  assert.strictEqual(ms("1s"), 1000);
});
