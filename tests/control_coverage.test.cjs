"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const recorder = readFileSync(path.join(__dirname, "../daodan/core/dynamic/control_coverage.js"), "utf8");

// Unit fixture for the recorder's public API. Event trust and the composed path
// are explicit inputs; browser dispatch and Playwright injection are separate tests.
function page() {
  const listeners = new Map();
  const nodes = [];
  const mutations = [];
  const document = {
    querySelectorAll: selector => nodes.filter(el => el.matches(selector)),
  };
  const context = {
    document, location: { href: "https://private.invalid/cart" }, ShadowRoot: class {},
    addEventListener(type, fn) {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(fn);
    },
    MutationObserver: class {
      observe() {}
      takeRecords() { return mutations.splice(0); }
    },
    Element: class {
      constructor(localName, parent) { Object.assign(this, { localName, parent }); }
      getRootNode() { return document; }
      closest() { return null; }
      matches(selector) {
        if (selector === ":disabled") return this.disabled;
        const tags = selector.split(",");
        return tags.includes(this.localName) ||
          (this.localName === "input" && this.type !== "hidden" && tags.includes("input:not([type=hidden i])"));
      }
    },
  };
  context.window = context.top = context;
  vm.runInNewContext(recorder, context);
  return {
    api: context.__daodanControls,
    mutate() { mutations.push({}); },
    go(url) { context.location.href = url; },
    add(tag, parent) {
      const el = new context.Element(tag, parent);
      nodes.push(el);
      mutations.push({});
      return el;
    },
    send(type, target, props = {}) {
      const path = [];
      for (let el = target; el; el = el.parent) path.push(el);
      const event = { target, composedPath: () => path, isTrusted: true, button: 0, ...props };
      for (const fn of listeners.get(type) ?? []) fn(event);
      if (type === "click") for (const el of path) el.onclick?.(event);
    },
    report() { return structuredClone(context.__daodanControls.report()); },
  };
}

test("only the exercised button is covered, even with a shared handler", () => {
  const p = page();
  const first = p.add("button"), second = p.add("button"), icon = p.add("span", first);
  let calls = 0;
  first.onclick = second.onclick = () => { calls++; };
  const [a, b] = p.report().pending;
  assert.notEqual(a.control, b.control);
  p.send("click", icon);
  p.send("click", icon);
  p.send("click", second, { isTrusted: false });
  assert.equal(calls, 3);
  assert.deepEqual(p.report(), { observed: [a], pending: [b] });
  assert.equal(p.api.shouldExplore(first, "click"), false);
  assert.equal(p.api.shouldExplore(second, "click"), true);
  p.mutate();
  assert.equal(p.api.shouldExplore(first, "click"), true);
  p.send("click", first);
  const entries = p.report().observed;
  assert.equal(entries.length, 2);
  assert.equal(entries[0].control, entries[1].control);
  assert.notEqual(entries[0].state, entries[1].state);
});

test("ambiguous, disabled and modified clicks supply no evidence", () => {
  const p = page();
  const first = p.add("button"), nested = p.add("button", first), disabled = p.add("button");
  disabled.disabled = true;
  p.send("click", nested);
  p.send("click", first, { ctrlKey: true });
  p.send("click", disabled);
  const { observed, pending } = p.report();
  assert.deepEqual(observed, []);
  assert.equal(pending.length, 2);
});

test("a checkbox change covers its source state and needs a matched trusted gesture", () => {
  const p = page();
  const checkbox = p.add("input");
  Object.assign(checkbox, { type: "checkbox", checked: false });
  const [before] = p.report().pending;
  p.send("pointerdown", checkbox);
  checkbox.checked = true;
  p.send("click", checkbox);
  p.send("input", checkbox);
  p.send("change", checkbox);
  const { observed, pending: [after] } = p.report();
  assert.deepEqual(observed, [before]);
  assert.equal(before.event, "change");
  assert.equal(before.control, after.control);
  assert.notEqual(before.state, after.state);
  assert.equal(p.api.shouldExplore(checkbox, "change"), true);
  p.send("input", checkbox);
  p.send("change", checkbox);
  assert.deepEqual(p.report().observed, [before]);
});

test("live property and URL changes reopen coverage without a mutation notification", () => {
  const p = page();
  const button = p.add("button"), field = p.add("textarea");
  p.send("click", button);
  assert.equal(p.api.shouldExplore(button, "click"), false);
  field.value = "private form value";
  assert.equal(p.api.shouldExplore(button, "click"), true);
  p.send("click", button);
  p.go("https://private.invalid/other");
  assert.equal(p.api.shouldExplore(button, "click"), true);
  const { pending, observed } = p.report();
  for (const row of [...observed, ...pending]) {
    assert.deepEqual(Object.keys(row).sort(), ["control", "event", "state"]);
    assert.ok(Number.isInteger(row.control) && Number.isInteger(row.state));
    assert.ok(["click", "change"].includes(row.event));
  }
});

test("pagehide retains the last interactive state and pageshow reopens coverage", () => {
  const p = page(), button = p.add("button");
  p.send("click", button);
  const before = p.report();
  p.send("pagehide", button);
  assert.deepEqual(p.report(), before);
  p.send("pageshow", button);
  assert.equal(p.api.shouldExplore(button, "click"), true);
});

test("the document bounds observations before exporting and leaves overflow eligible", () => {
  const p = page(), button = p.add("button");
  for (let i = 0; i < 4100; i++) { p.mutate(); p.send("click", button); }
  const report = p.report();
  assert.equal(report.observed.length, 4096);
  assert.equal(report.truncated, true);
  assert.equal(p.api.shouldExplore(button, "click"), true);
  for (let i = 0; i < 4100; i++) p.add("button");
  assert.equal(p.report().pending.length, 4096);
});
