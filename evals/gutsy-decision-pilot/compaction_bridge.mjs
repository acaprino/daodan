/** Pilot adapter. The compaction algorithm is always the pinned upstream library. */
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const moduleName = process.env.FAST_JEV_MODULE || 'fast-jev-compaction';
const moduleRef = moduleName.startsWith('.') || path.isAbsolute(moduleName)
  ? pathToFileURL(path.resolve(moduleName)).href : moduleName;
const lib = await import(moduleRef);

function checkedAnswers(answers, questions) {
  for (const key of Object.keys(questions)) {
    const value = answers?.[key]?.noul;
    if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 1) {
      throw new Error(`Invalid bounded noul answer: ${key}`);
    }
  }
  return answers;
}

function pairResult(messages, call) {
  return messages[call.resultIndex].toolResults.find(r => r.tool_use_id === call.tool_use_id);
}

function invariants(before, after) {
  const text = ms => ms.filter(m => m.text.length > 0).map(m => [m.role, m.text]);
  const callIds = new Set(after.flatMap(m => m.toolUses.map(t => t.tool_use_id)));
  return {
    text_preserved: JSON.stringify(text(before)) === JSON.stringify(text(after)),
    no_orphan_results: after.every(m => (m.toolResults || []).every(r => callIds.has(r.tool_use_id))),
    input_unchanged: true,
  };
}

function prepare(payload) {
  const options = lib.resolveOptions(payload.options);
  const calls = lib.collectToolCalls(payload.messages, options.preserveRecentMessages);
  const candidates = calls.filter(c => !c.pinned);
  if (candidates.length !== 1) throw new Error(`Expected one candidate, got ${candidates.length}`);
  const fitted = lib.fitState(payload.messages, calls, options);
  const questions = lib.questionsFor(candidates[0]);
  const state = structuredClone(fitted.state);
  if (payload.arm === 'B') {
    state.candidate_results = candidates.map(call => ({
      id: call.id, tool: call.tool, input: call.input,
      result: pairResult(payload.messages, call).text,
      isError: pairResult(payload.messages, call).isError || false,
    }));
  }
  const request = lib.buildJevRequest({apiKey: 'local-pilot', model: 'gutsy-0.8b-v04-q4'}, state, questions);
  return { ...JSON.parse(request.body), calls, state_stage: fitted.stage,
    estimated_upstream_tokens: fitted.tokens, upstream_candidates: candidates.length };
}

async function apply(payload) {
  const options = lib.resolveOptions(payload.options);
  const calls = lib.collectToolCalls(payload.messages, options.preserveRecentMessages);
  const questions = Object.assign({}, ...calls.filter(c => !c.pinned).map(lib.questionsFor));
  const answers = checkedAnswers(payload.response.answers, questions);
  const original = JSON.stringify(payload.messages);
  const raw = await lib.compact(payload.messages, {ask: async () => ({answers})}, options);
  const rawInvariants = invariants(payload.messages, raw.messages);
  rawInvariants.input_unchanged = original === JSON.stringify(payload.messages);
  let protectedResult = null;
  if (payload.protect_result) {
    const guarded = structuredClone(answers);
    for (const call of calls.filter(c => !c.pinned)) {
      guarded[`result_${call.id}`] = {type: 'noul', noul: 1};
    }
    protectedResult = await lib.compact(payload.messages, {ask: async () => ({answers: guarded})}, options);
  }
  return {raw, invariants: rawInvariants, protected: protectedResult};
}

const message = (role, text = '', toolUses = [], toolResults) => ({
  role, text, toolUses, ...(toolResults ? {toolResults} : {}),
});
const call = (id, tool = 'Read') => message('assistant', '', [{tool_use_id: id, tool, input: {file_path: 'fixture.txt'}}]);
const result = id => message('user', '', [], [{tool_use_id: id, text: 'fixture value'}]);
const neutral = () => Array.from({length: 6}, () => message('assistant', 'No new facts.'));

async function contracts() {
  const checks = {};
  const opts = {goal: 'Use recorded facts.', preserveRecentMessages: 6};
  let asks = 0;
  const failIfAsked = {ask: async () => { asks++; throw new Error('Unexpected inference'); }};
  const pending = [message('user', 'Use recorded facts.'), ...neutral(), call('pending')];
  const pendingResult = await lib.compact(pending, failIfAsked, opts);
  checks.C09 = {pass: asks === 0 && JSON.stringify(pendingResult.messages) === JSON.stringify(pending), asks};

  const pinnedVariants = [
    [message('user', 'Use recorded facts.'), call('pinned'), ...neutral(), result('pinned')],
    [message('user', 'Use recorded facts.'), ...neutral(), call('pinned'), result('pinned')],
  ];
  const pinned = [];
  for (const ms of pinnedVariants) {
    const out = await lib.compact(ms, failIfAsked, opts);
    pinned.push(JSON.stringify(out.messages) === JSON.stringify(ms));
  }
  checks.C10 = {pass: pinned.every(Boolean) && asks === 0, variants: pinned, asks};

  const two = [message('user', 'Use recorded facts.'), call('one'), result('one'),
    call('two'), result('two'), ...neutral()];
  const resolved = lib.resolveOptions(opts);
  const calls = lib.collectToolCalls(two, 6);
  const fitted = lib.fitState(two, calls, resolved);
  const qTokens = Math.max(...calls.map(c => lib.estimateTokens(JSON.stringify(lib.questionsFor(c)))));
  const batchOptions = {...opts, maxRequestTokens: fitted.tokens + 20 + qTokens};
  const batchCount = lib.batchCalls(calls, fitted.tokens, lib.resolveOptions(batchOptions)).length;
  const failures = [];
  for (const mode of ['timeout', 'missing-key']) {
    const original = JSON.stringify(two);
    let count = 0;
    let returned = false;
    try {
      await lib.compact(two, {ask: async (_state, qs) => {
        count++;
        if (count === 2) {
          if (mode === 'timeout') throw new Error('Simulated timeout');
          return {answers: {}};
        }
        return {answers: Object.fromEntries(Object.keys(qs).map(k => [k, {noul: 0}]))};
      }}, batchOptions);
      returned = true;
    } catch { /* An incomplete set of batches must not return a candidate. */ }
    failures.push({mode, pass: !returned && count === 2 && original === JSON.stringify(two), asks: count});
  }
  checks.C11 = {pass: batchCount === 2 && failures.every(f => f.pass), batch_count: batchCount, failures};

  let unfitAsks = 0;
  let unfitThrown = false;
  try {
    await lib.compact(two, {ask: async () => {unfitAsks++; return {answers: {}};}}, {...opts, maxStateTokens: 1});
  } catch { unfitThrown = true; }
  checks.C12 = {pass: unfitThrown && unfitAsks === 0, asks: unfitAsks};

  const rejects = [];
  for (const value of [-0.1, 1.1, null]) {
    try { checkedAnswers({sample: {noul: value}}, {sample: {type: 'noul'}}); rejects.push(false); }
    catch { rejects.push(true); }
  }
  checks.adapter_probability_bounds = {pass: rejects.every(Boolean)};
  return {checks, pass: Object.values(checks).every(c => c.pass), implementation: 'pinned upstream compact'};
}

try {
  const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
  const output = payload.action === 'prepare' ? prepare(payload)
    : payload.action === 'apply' ? await apply(payload)
    : payload.action === 'contracts' ? await contracts()
    : (() => {throw new Error(`Unknown action ${payload.action}`);})();
  process.stdout.write(JSON.stringify(output));
} catch (error) {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
}
