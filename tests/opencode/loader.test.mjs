// Tests for the OpenCode V2 loader, run with `node --test`. The host is a fake
// `ctx` whose transform hooks hand recording editors to the callback, the same
// shape the V2 promise plugin API gives a plugin's setup.

import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import loader, {
  createLoader,
  expandTemplate,
  resolveSelection,
  substituteRoot,
} from "../../adapters/opencode/templates/index.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE = path.join(here, "fixture");
const ROOT = FIXTURE.replaceAll("\\", "/");

// What V2's Agent.Info.default gives a new agent (packages/schema/src/agent.ts).
const V2_DEFAULTS = [
  { action: "*", resource: "*", effect: "allow" },
  { action: "external_directory", resource: "*", effect: "ask" },
];

// V2's own rule evaluation: the last matching rule wins, unmatched asks
// (packages/core/src/permission.ts). Wildcards are only `*` in these tests.
function evaluate(rules, action, resource) {
  const match = (value, pattern) => {
    // Glob with `*` only: every literal piece must appear in order.
    const pieces = pattern.split("*");
    if (pieces.length === 1) return value === pattern;
    if (!value.startsWith(pieces[0]) || !value.endsWith(pieces.at(-1))) return false;
    let at = pieces[0].length;
    for (const piece of pieces.slice(1, -1)) {
      const found = value.indexOf(piece, at);
      if (found === -1) return false;
      at = found + piece.length;
    }
    return at <= value.length - pieces.at(-1).length;
  };
  return rules.findLast((rule) => match(action, rule.action) && match(resource, rule.resource))?.effect ?? "ask";
}

function fakeContext({ options = {}, rejectSkill, existingMcp = {}, existingAgents = {} } = {}) {
  const calls = { skills: [], agents: {}, commands: [], mcp: {}, prompts: [], transforms: 0 };
  const agents = structuredClone(existingAgents);
  const ctx = {
    options,
    skill: {
      transform: async (fn) => {
        calls.transforms++;
        fn({
          add(skill) {
            if (skill.id === rejectSkill) throw new Error("rejected by host");
            calls.skills.push(skill);
          },
        });
      },
    },
    agent: {
      transform: async (fn) => {
        calls.transforms++;
        fn({
          update(id, apply) {
            const item = agents[id] ?? { id, permissions: structuredClone(V2_DEFAULTS) };
            apply(item);
            agents[id] = item;
            calls.agents[id] = item;
          },
        });
      },
    },
    command: {
      transform: async (fn) => {
        calls.transforms++;
        fn({ add: (definition) => calls.commands.push(definition) });
      },
    },
    mcp: {
      transform: async (fn) => {
        calls.transforms++;
        fn({
          get: (name) => existingMcp[name],
          set: (name, config) => {
            calls.mcp[name] = config;
          },
        });
      },
    },
    session: {
      prompt: async (input) => {
        calls.prompts.push(input);
      },
    },
  };
  return { ctx, calls };
}

async function run(context, directory = FIXTURE) {
  const log = [];
  const original = { error: console.error, warn: console.warn, log: console.log };
  console.error = console.warn = console.log = (...args) => log.push(args.join(" "));
  try {
    await createLoader(directory)(context.ctx);
  } finally {
    Object.assign(console, original);
  }
  return log;
}

const ids = (calls) => ({
  skills: calls.skills.map((s) => s.id).sort(),
  agents: Object.keys(calls.agents).sort(),
  commands: calls.commands.map((c) => c.name).sort(),
});

test("the default export is a V2 plugin definition", () => {
  assert.equal(loader.id, "daodan");
  assert.equal(typeof loader.setup, "function");
});

test("no options loads everything", async () => {
  const context = fakeContext();
  await run(context);
  assert.deepEqual(ids(context.calls), {
    skills: ["a:guide", "b:base"],
    agents: ["a:worker"],
    commands: ["a:run", "c:explain"],
  });
});

test("selection pulls in dependencies", async () => {
  const context = fakeContext({ options: { plugins: ["a"] } });
  const log = await run(context);
  assert.deepEqual(ids(context.calls).skills, ["a:guide", "b:base"]);
  assert.deepEqual(ids(context.calls).commands, ["a:run"]);
  assert.ok(log.some((line) => line.includes("b") && line.includes("required by a")), log.join("\n"));
});

test("exclude yields to a dependency", async () => {
  const context = fakeContext({ options: { plugins: ["a"], exclude: ["b"] } });
  const log = await run(context);
  assert.ok(ids(context.calls).skills.includes("b:base"));
  assert.ok(log.some((line) => line.includes("b") && line.includes("a")), log.join("\n"));
});

test("exclusions do not depend on their order", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(FIXTURE, "package.json"), "utf8")).daodan;
  const forward = resolveSelection(manifest, { exclude: ["a", "b"] }).selected;
  const backward = resolveSelection(manifest, { exclude: ["b", "a"] }).selected;
  assert.deepEqual(forward, ["c"]);
  assert.deepEqual(backward, ["c"]);
});

test("exclude removes an unneeded plugin", async () => {
  const context = fakeContext({ options: { exclude: ["c"] } });
  await run(context);
  assert.deepEqual(ids(context.calls).commands, ["a:run"]);
  assert.deepEqual(ids(context.calls).skills, ["a:guide", "b:base"]);
});

test("an unknown name is logged, not fatal", async () => {
  const context = fakeContext({ options: { plugins: ["zzz", "c"] } });
  const log = await run(context);
  assert.deepEqual(ids(context.calls).commands, ["c:explain"]);
  assert.ok(log.some((line) => line.includes("zzz")), log.join("\n"));
});

test("a selection of nothing but typos still loads everything", async () => {
  const context = fakeContext({ options: { plugins: ["senior-reveiw"] } });
  const log = await run(context);
  assert.deepEqual(ids(context.calls).commands, ["a:run", "c:explain"]);
  assert.ok(log.some((line) => line.includes("senior-reveiw")), log.join("\n"));
});

test("a malformed manifest registers nothing and setup resolves", async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "daodan-"));
  fs.writeFileSync(path.join(directory, "package.json"), JSON.stringify({ name: "daodan" }));
  const context = fakeContext();
  const log = await run(context, directory);
  assert.equal(context.calls.transforms, 0);
  assert.ok(log.some((line) => line.includes("[daodan]")), log.join("\n"));
});

test("a missing manifest registers nothing and setup resolves", async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "daodan-"));
  const context = fakeContext();
  await run(context, directory);
  assert.equal(context.calls.transforms, 0);
});

test("a rejected skill skips only itself", async () => {
  const context = fakeContext({ rejectSkill: "a:guide" });
  const log = await run(context);
  assert.deepEqual(ids(context.calls).skills, ["b:base"]);
  assert.ok(log.some((line) => line.includes("a:guide")), log.join("\n"));
});

test("skills carry an absolute path and a body without frontmatter", async () => {
  const context = fakeContext();
  await run(context);
  const skill = context.calls.skills.find((s) => s.id === "a:guide");
  assert.equal(skill.name, "guide");
  assert.equal(skill.description, "Guide of a");
  assert.ok(path.isAbsolute(skill.path), skill.path);
  assert.ok(skill.path.endsWith(path.join("skills", "guide", "SKILL.md")), skill.path);
  assert.ok(!skill.content.includes("description:"), skill.content);
  assert.equal(skill.content.trim(), `Run ${ROOT}/plugins/a/skills/guide/x.py`);
});

test("agent fields", async () => {
  const context = fakeContext();
  await run(context);
  const agent = context.calls.agents["a:worker"];
  assert.equal(agent.mode, "subagent");
  assert.equal(agent.description, "Worker of a");
  assert.equal(agent.system.trim(), `Work from ${ROOT}/plugins/a/skills/guide.`);
  assert.deepEqual(agent.permissions.at(-1), {
    action: "external_directory",
    resource: `${ROOT}/**`,
    effect: "allow",
  });
  assert.deepEqual(agent.permissions[0], { action: "*", resource: "*", effect: "deny" });
});

test("an agent registered before the loader is taken over", async () => {
  // Builtins and earlier packages run before this one; user config runs after
  // it (V2's ConfigAgentPlugin is a post-plugin), so it is never seen here.
  const context = fakeContext({
    existingAgents: {
      "a:worker": { id: "a:worker", mode: "primary", system: "earlier", permissions: [{ action: "x", resource: "*", effect: "allow" }] },
    },
  });
  await run(context);
  const agent = context.calls.agents["a:worker"];
  assert.equal(agent.mode, "subagent");
  assert.notEqual(agent.system, "earlier");
  assert.equal(evaluate(agent.permissions, "x", "anything"), "deny");
});

test("a restricted role denies what it did not declare", async () => {
  const context = fakeContext();
  await run(context);
  const rules = context.calls.agents["a:worker"].permissions;
  assert.equal(evaluate(rules, "read", "src/x.ts"), "allow");
  assert.equal(evaluate(rules, "shell", "rm -rf /"), "deny");
  assert.equal(evaluate(rules, "external_directory", `${ROOT}/plugins/a/skills/guide/x.md`), "allow");
  assert.equal(evaluate(rules, "external_directory", "/etc/passwd"), "deny");
});

test("an unrestricted role keeps V2's defaults and reaches its package", async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "daodan-"));
  fs.cpSync(FIXTURE, directory, { recursive: true });
  const manifestPath = path.join(directory, "package.json");
  const document = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  document.daodan.plugins.a.agents[0].permissions = [
    { action: "external_directory", resource: "<package-root>/**", effect: "allow" },
  ];
  fs.writeFileSync(manifestPath, JSON.stringify(document));
  const context = fakeContext();
  await run(context, directory);
  const rules = context.calls.agents["a:worker"].permissions;
  const root = directory.replaceAll("\\", "/");
  assert.equal(evaluate(rules, "read", "src/x.ts"), "allow");
  assert.equal(evaluate(rules, "edit", "src/x.ts"), "allow");
  assert.equal(evaluate(rules, "external_directory", `${root}/plugins/a/skills/guide/x.md`), "allow");
  assert.equal(evaluate(rules, "external_directory", "/etc/passwd"), "ask");
});

test("MCP registered with the plugin root substituted", async () => {
  const context = fakeContext();
  await run(context);
  assert.deepEqual(context.calls.mcp.srv, {
    type: "local",
    command: ["uv", "run", `${ROOT}/plugins/a/skills/guide/server.py`],
  });
});

test("existing MCP server left alone", async () => {
  const context = fakeContext({ existingMcp: { srv: { type: "local", command: ["mine"] } } });
  const log = await run(context);
  assert.equal(context.calls.mcp.srv, undefined);
  assert.ok(log.some((line) => line.includes("srv")), log.join("\n"));
});

test("command execute prompts with the expanded body", async () => {
  const context = fakeContext();
  await run(context);
  const command = context.calls.commands.find((c) => c.name === "a:run");
  assert.equal(command.description, "Run a");
  await command.execute({ sessionID: "s", prompt: { text: "x y", extra: 1 }, delivery: "d" });
  const [sent] = context.calls.prompts;
  assert.equal(sent.sessionID, "s");
  assert.equal(sent.delivery, "d");
  assert.equal(sent.extra, 1);
  assert.equal(sent.text, `Run x y in ${ROOT}/plugins/a.`);
});

test("a command reads its template at invocation time", async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "daodan-"));
  fs.cpSync(FIXTURE, directory, { recursive: true });
  const context = fakeContext();
  await run(context, directory);
  const file = path.join(directory, "plugins", "c", "commands", "explain.md");
  fs.writeFileSync(file, "---\ndescription: Explain\n---\n\nExplain again.\n");
  const command = context.calls.commands.find((c) => c.name === "c:explain");
  await command.execute({ sessionID: "s", prompt: { text: "" }, delivery: "d" });
  assert.equal(context.calls.prompts[0].text, "Explain again.");
});

test("$ARGUMENTS", () => {
  assert.equal(expandTemplate("Review $ARGUMENTS.", "src a.ts"), "Review src a.ts.");
});

test("positional and quotes", () => {
  assert.equal(
    expandTemplate("Check $1. Focus on $2.", 'src/auth.ts "error handling"'),
    "Check src/auth.ts. Focus on error handling.",
  );
});

test("last positional consumes the rest", () => {
  assert.equal(expandTemplate("Compare $1 with $2.", "api stable branch"), "Compare api with stable branch.");
});

test("a missing position is empty and the result is trimmed", () => {
  assert.equal(expandTemplate("A $1 B $2", "x"), "A x B");
});

test("no placeholder appends the arguments", () => {
  assert.equal(expandTemplate("Explain.", "src/c.ts"), "Explain.\n\nsrc/c.ts");
  assert.equal(expandTemplate("Explain.", "  "), "Explain.");
});

test("$ARGUMENTS and positionals together", () => {
  // `$1` is the highest positional present, so it takes everything, as in V2.
  assert.equal(expandTemplate("$1 then all: $ARGUMENTS", "one two"), "one two then all: one two");
  assert.equal(expandTemplate("$1, $2 | $ARGUMENTS", "a b c"), "a, b c | a b c");
});

test("$ARGUMENTS receives the input as typed", () => {
  assert.equal(expandTemplate("[$ARGUMENTS]", "  spaced  "), "[  spaced  ]");
});

test("windows-style root", () => {
  assert.equal(
    substituteRoot("<plugin-root>/skills/a and <package-root>/**", "C:\\Users\\me\\pkg\\plugins\\a", "C:\\Users\\me\\pkg"),
    "C:/Users/me/pkg/plugins/a/skills/a and C:/Users/me/pkg/**",
  );
});

test("resolveSelection is pure and ordered", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(FIXTURE, "package.json"), "utf8")).daodan;
  assert.deepEqual(resolveSelection(manifest, {}).selected, ["a", "b", "c"]);
  assert.deepEqual(resolveSelection(manifest, { plugins: ["a"] }).selected, ["a", "b"]);
});
