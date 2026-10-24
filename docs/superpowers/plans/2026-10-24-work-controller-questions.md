# work-controller questions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The smallest loop of part 2: a missing human decision becomes a recorded question, the tasks that need it wait while independent work goes on, the user's answer is recorded with its source, and only the tasks it unblocks resume.

**Architecture:** No new schema and no new plugin. The run record's existing `questions` section gains optional fields; a wave task declares the answer it needs through its existing `consumes` list as `question:<id>`. Two new helper commands, `ask` and `answer`, write through the same locked path as `update` and print only the question they touched. State rules (a waiting task cannot run, a run cannot complete with an open question, questions are append-only) live in record validation and transitions, so legacy records keep loading. The question shape becomes one 58-word reference of `work-record`, which the interview, the brainstorm and the four task workflows follow instead of carrying their own wording.

**Tech Stack:** Python 3 standard library, `unittest`, the repository compiler.

**Spec:** `docs/superpowers/specs/2026-10-24-conversational-decisions-and-work-graphs-design.md` (sections 3 to 6, 10, 11 step 1) and `docs/adr/ADR-0002-work-controller.md`. This plan is part 2a of three; see "After this plan".

## Global Constraints

- `work-controller` declares no dependencies (ADR-0002 INV-001). Standard library only.
- Legacy records validate and resume unchanged: a question without the new fields, a question whose text has no `?`, an interview phase completed with an open question, an answer written by `update`. The first-line check runs only in `ask`; rules on state changes run only on transitions; the new optional fields (`source`, `withdrawn`) are checked only where a question is written (`init`, `plan-check`, and any write that adds or changes one), never on read, at the user's request.
- `ask` and `answer` print only the question they touched (ADR-0002 INV-004). `update`, `init`, `show` and `resume` keep their output.
- No step cap in `tests/test_skill_load_budget.py` rises. Measured with the texts below on the current `master`: `work-record/SKILL.md` 1670 (cap 1682 → 1675), `interview.md` 357 (400 → 360), `brainstorm.md` 270 (300 → 275), `continue.md` 191 (195 → 192), new `work-record/references/questions.md` 58 (cap 60); steps "change: interview and record" 3505/3565 and "brainstorm" 3046/3050 with the reference counted in both.
- Kernel text in English, no dash-aside construct.
- Never hand-edit `exports/` or the root manifests; rebuild.
- Work in place on `master` in the shared checkout, by decision of the user. Touch only this plan's files; the other session's uncommitted text-humanizer work is never edited or staged, and generated files are staged only for this change's content.
- Versions at commit time, from the then current `origin/master`: `work-controller` 1.0.0 → 1.1.0, `project-lifecycle` minor, `daodan` minor, marketplace `metadata.version` minor.
- Commit and push only on the user's go for this plan. Message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Acceptance covered

CD-01 (the coordinator reuses an applicable recorded answer; the helper returns only an open question of the same phase, because applicability is a judgment), CD-05, CD-07, CD-08 (repeated answer only), CD-10, CD-12, CD-16, and ADR-0002 EX-001's record half. Left to 2b and 2c: CD-04, CD-06, CD-09, CD-11, CD-13, CD-14, CD-17 to CD-20, EX-002 to EX-004.

## Review Focus

1. A legacy record from 39.0.x (questions without `options` or `source`, an interview phase `complete` with an open question) must still `show`, `resume` and accept updates. Pinned in Task 1, `test_legacy_question_records_still_load`.
2. An interrupted session retries `answer` with the same text: no new revision, no second entry. A different text is refused. Pinned in Task 2, `test_a_repeated_answer_changes_nothing_and_a_different_one_is_refused`.
3. Two workers raise the same decision in the same phase under two ids: the second `ask` returns the first id and writes nothing; an answered or withdrawn question is never reused for a new ask. Pinned in Task 2, `test_ask_returns_the_open_question_already_asking_it`.
4. An `update` that replaces the `questions` array and drops a question or edits an answer, the only way arrays change under `merge`. Pinned in Task 1, `test_questions_are_append_only`.
5. A user answer with quotes, a newline and accented letters, passed on Windows. Answers travel in a JSON payload, never on the command line. Pinned in Task 2, `test_answer_keeps_the_users_words_exactly`.

---

### Task 0: Workspace

- [ ] **Step 1:** Confirm this plan's files carry no foreign edit: `git status --short` on them is empty.
- [ ] **Step 2:** Baseline: `python -m unittest discover -s tests -p "test_work_record.py" && python -m unittest discover -s tests -p "test_skill_load_budget.py"` passes before any edit.

### Task 1: Record rules for questions

**Files:**
- Modify: `plugins/work-controller/contracts/work.toml` (`[loop.questions]`, around line 111)
- Modify: `plugins/work-controller/skills/work-record/scripts/run_state.py` (`validate_questions` ~398, `validate_loop` ~780, `validate_loop_transitions` ~804, `validate_transitions` ~900, `main` plan-check branch ~1098)
- Test: `tests/test_work_record.py` (class `LoopRecordTests`)

**Interfaces:**
- Produces: contract keys `options = [2, 4]`, `sources = ["question-tool", "chat", "continue"]`, `consumer_prefix = "question:"`; module constant `QUESTION_PREFIX = "question:"`; `consumed_questions(task) -> list[str]` (ids after the prefix); `is_settled(question) -> bool` (has `answer` and no `withdrawn`); `is_open(question) -> bool` (no `answer`).

New contract block, replacing the current one:

```toml
[loop.questions]
# Questions to the user. `ask` records one before it is asked; only the user's
# own words answer it, through `answer`, and nothing is inferred. A task that
# consumes question:<id> waits until it is answered; a withdrawn question
# closes without unblocking anyone.
required = ["id", "phase", "text"]
options = [2, 4]
sources = ["question-tool", "chat", "continue"]
consumer_prefix = "question:"
```

Optional question fields: `options` (list of `{label, consequence}`, the first is the recommended one), `recommendation` (why the first), `asked_at`, `answer`, `source`, `answered_at`, `withdrawn` (`true`, only beside an answer).

- [ ] **Step 1: Write the failing tests** in `LoopRecordTests`:

```python
def test_question_options_and_sources_are_validated(self):
    base = {"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}
    two = [{"label": "Keep", "consequence": "No client change"}, {"label": "Drop", "consequence": "Two clients migrate"}]
    self.assertTrue(self.plan_check({"questions": [{**base, "options": two, "recommendation": "No migration"}]})["valid"])
    self.assertIn("two to four options", self.plan_check({"questions": [{**base, "options": two[:1], "recommendation": "x"}]}, ok=False).stderr)
    self.assertIn("a label and a consequence", self.plan_check({"questions": [{**base, "options": [two[0], {"label": "Drop"}], "recommendation": "x"}]}, ok=False).stderr)
    self.assertIn("why the first option", self.plan_check({"questions": [{**base, "options": two}]}, ok=False).stderr)
    self.assertIn("is not one of", self.plan_check({"questions": [{**base, "answer": "yes", "source": "email"}]}, ok=False).stderr)
    self.assertIn("withdrawn only beside an answer", self.plan_check({"questions": [{**base, "withdrawn": True}]}, ok=False).stderr)

def test_a_task_waits_for_the_questions_it_consumes(self):
    question = {"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}
    waiting = self.task("a", "src/a.py", consumes=["question:Q1"])
    self.assertTrue(self.plan_check({"questions": [question], "waves": [self.wave("w1", waiting)]})["valid"])
    self.assertIn("does not ask Q9", self.plan_check({"questions": [question], "waves": [self.wave("w1", self.task("a", "src/a.py", consumes=["question:Q9"]))]}, ok=False).stderr)
    running = {**waiting, "status": "running"}
    self.assertIn("consumes question:Q1, which is not answered", self.plan_check({"questions": [question], "waves": [self.wave("w1", running)]}, ok=False).stderr)
    answered = {**question, "answer": "yes", "source": "chat"}
    self.assertTrue(self.plan_check({"questions": [answered], "waves": [self.wave("w1", running)]})["valid"])

def test_plan_check_resolves_questions_from_the_run(self):
    self.payload["questions"] = [{"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}]
    self.init()
    self.assertTrue(self.plan_check({"waves": [self.wave("w1", self.task("a", "src/a.py", consumes=["question:Q1"]))]})["valid"])

def test_questions_are_append_only(self):
    q1 = {"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}
    self.payload["questions"] = [q1]
    self.init()
    refused = self.invoke("update", {"questions": []}, ["--expected-revision", "0"], ok=False)
    self.assertIn("append-only", refused.stderr)
    self.assertIn("append-only", self.invoke("update", {"questions": [{**q1, "text": "Drop it?"}]}, ["--expected-revision", "0"], ok=False).stderr)
    self.invoke("update", {"questions": [{**q1, "answer": "yes"}]}, ["--expected-revision", "0"])
    self.assertIn("append-only", self.invoke("update", {"questions": [{**q1, "answer": "no"}]}, ["--expected-revision", "1"], ok=False).stderr)

def test_completion_requires_every_question_closed(self):
    self.payload["questions"] = [{"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}]
    self.init()
    done = {"status": "complete", "phases": {"audit": {"status": "complete"}},
            "deliveries": {"audit": {"status": "delivered", "output": self.report()}}}
    self.assertIn("every question answered or withdrawn: Q1", self.invoke("update", done, ["--expected-revision", "0"], ok=False).stderr)
    self.invoke("update", {"questions": [{**self.payload["questions"][0], "answer": "yes"}]}, ["--expected-revision", "0"])
    self.assertEqual(self.invoke("update", done, ["--expected-revision", "1"])["status"], "complete")

def test_legacy_question_records_still_load(self):
    self.payload["questions"] = [{"id": "Q1", "phase": "audit", "text": "undecided: keep the sync API"}]
    self.init()
    self.invoke("update", {"phases": {"audit": {"status": "complete"}}}, ["--expected-revision", "0"])
    self.assertEqual(self.invoke("show")["questions"][0]["id"], "Q1")
    resumed = self.invoke("resume", {"authorizations": self.payload["authorizations"]})
    self.assertEqual([q["id"] for q in resumed["pending_questions"]], ["Q1"])
```

- [ ] **Step 2:** `python -m unittest discover -s tests -p "test_work_record.py" -k question -k append` fails on the new assertions.
- [ ] **Step 3: Implement.**
  - `validate_questions(section, rules)`: keep the current checks; add `options` length within `rules["options"]` ("needs two to four options"), each option a dict with nonempty `label` and `consequence` ("needs a label and a consequence"), `recommendation` nonempty when `options` is present ("names why the first option is recommended"), `source` in `rules["sources"]` with the existing "is not one of" wording, `withdrawn is True` only when `answer` is present ("withdrawn only beside an answer").
  - `validate_loop(record)`: after the questions, for every wave task and every id in `consumed_questions(task)`: the id must be a recorded question (`f"Task {task['id']} consumes question:{qid}, but the record does not ask {qid}"`); a task whose status is `running`, `green` or `committed` needs `is_settled` (`f"Task {task['id']} consumes question:{qid}, which is not answered"`).
  - `validate_loop_transitions(old, new)`: each old question must reappear at the same index with every old key unchanged, and an answered one must be identical; otherwise `"Questions are append-only; a question or its answer cannot be altered or removed"`. Adding `answer` to an open question through `update` stays allowed.
  - `validate_transitions(old, new)`: on the move to `complete`, any `is_open` question refuses with `f"Completion requires every question answered or withdrawn: {', '.join(ids)}"`. The check is a transition so a completed legacy record is never re-judged.
  - `main`, `plan-check`: when the payload has no `questions` and `--run-id` names an existing run, validate against that run's questions; with neither, a consumed question is unknown.
- [ ] **Step 4:** `python -m unittest discover -s tests -p "test_work_record.py"` passes, the existing question tests included.

### Task 2: `ask`, `answer` and the waiting view

**Files:**
- Modify: `plugins/work-controller/skills/work-record/scripts/run_state.py` (`main` ~1082; the update branch ~1164 becomes the shared write path)
- Test: `tests/test_work_record.py` (`LoopRecordTests`)

**Interfaces:**
- Consumes: Task 1's `consumed_questions`, `is_settled`, `is_open`, contract `sources`.
- Produces: commands `ask --payload QUESTION.json` and `answer --payload ANSWER.json` (both with `--project`, `--run-id`, optional `--session`, `--take-over`, `--out`, no `--expected-revision`: they are commutative under the writer lock); `commit_change(project, root, directory, path, session, take_over, change)` where `change(before) -> dict | None` returns the updated record or `None` for no write; `resume` output gains `waiting` (`{task_id: [open question ids]}` for pending tasks) and `replan` (task ids consuming a withdrawn question).
- Payloads: `QUESTION.json` = `{id, phase, text, options?, recommendation?}`; `ANSWER.json` = `{question, text, source, withdraw?}`.
- Outputs, nothing else: `ask` → `{question, revision, open}` plus `existing: true` and `answer` when reused; `answer` → `{question, revision, open, unblocked}` plus `replan` when withdrawn and `unchanged: true` on a repeat.

- [ ] **Step 1: Write the failing tests:**

```python
def ask(self, question, ok=True, extra=()):
    return self.invoke("ask", question, extra, ok=ok)

def answer(self, qid, text, source="question-tool", ok=True, **extra):
    return self.invoke("answer", {"question": qid, "text": text, "source": source, **extra}, ok=ok)

def test_ask_records_a_shaped_question_once(self):
    self.init()
    q1 = {"id": "Q1", "phase": "interview", "text": "Keep the sync API?\nToday `api.py:12` serves it to two clients."}
    self.assertEqual(self.ask(q1), {"question": "Q1", "revision": 1, "open": 1})
    self.assertEqual(self.ask(q1), {"question": "Q1", "revision": 1, "open": 1, "existing": True})
    self.assertIn("already asks", self.ask({**q1, "text": "Drop the sync API?"}, ok=False).stderr)
    self.assertIn("first line must be the question", self.ask({**q1, "id": "Q2", "text": "Sync API"}, ok=False).stderr)
    self.assertIn("ask records a question only", self.ask({**q1, "id": "Q3", "answer": "yes"}, ok=False).stderr)

def test_ask_returns_the_question_already_recorded(self):
    self.init()
    self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"})
    same = self.ask({"id": "Q7", "phase": "waves", "text": "keep the  SYNC api?\nother context"})
    self.assertEqual((same["question"], same["revision"], same["existing"]), ("Q1", 1, True))
    self.answer("Q1", "yes")
    reused = self.ask({"id": "Q8", "phase": "waves", "text": "Keep the sync API?"})
    self.assertEqual((reused["question"], reused["answer"]), ("Q1", "yes"))

def test_answer_unblocks_only_tasks_whose_questions_are_all_answered(self):
    self.payload["waves"] = [self.wave("w1", self.task("a", "src/a.py", consumes=["question:Q1"]),
                                              self.task("b", "src/b.py", consumes=["question:Q1", "question:Q2"]),
                                              self.task("c", "src/c.py"))]
    self.payload["questions"] = [{"id": "Q1", "phase": "interview", "text": "Keep the sync API?"},
                                 {"id": "Q2", "phase": "interview", "text": "Which clients migrate first?"}]
    self.init()
    self.assertEqual(self.answer("Q1", "yes")["unblocked"], ["a"])
    resumed = self.invoke("resume", {"authorizations": self.payload["authorizations"]})
    self.assertEqual(resumed["waiting"], {"b": ["Q2"]})
    self.assertEqual(self.answer("Q2", "web first", source="chat"), {"question": "Q2", "revision": 2, "open": 0, "unblocked": ["b"]})

def test_a_repeated_answer_changes_nothing_and_a_different_one_is_refused(self):
    self.init()
    self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"})
    self.answer("Q1", "yes")
    again = self.answer("Q1", "yes")
    self.assertEqual((again["revision"], again["unchanged"]), (2, True))
    self.assertIn("a changed answer is a new question", self.answer("Q1", "no", ok=False).stderr)
    self.assertIn("does not ask Q9", self.answer("Q9", "yes", ok=False).stderr)

def test_a_withdrawn_question_closes_without_unblocking(self):
    self.payload["waves"] = [self.wave("w1", self.task("a", "src/a.py", consumes=["question:Q1"]))]
    self.payload["questions"] = [{"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}]
    self.init()
    withdrawn = self.answer("Q1", "drop the export goal", source="chat", withdraw=True)
    self.assertEqual((withdrawn["unblocked"], withdrawn["replan"], withdrawn["open"]), ([], ["a"], 0))
    self.assertEqual(self.invoke("resume", {"authorizations": self.payload["authorizations"]})["replan"], ["a"])
    self.assertEqual(self.invoke("agenda")["tasks"][0]["questions"], 0)

def test_answer_keeps_the_users_words_exactly(self):
    self.init()
    self.ask({"id": "Q1", "phase": "interview", "text": "Quale finestra di fermo?"})
    words = 'Sì, ma "solo" lunedì\nseconda riga, perché sì'
    self.answer("Q1", words)
    stored = self.invoke("show")
    self.assertEqual((stored["questions"][0]["answer"], stored["questions"][0]["source"]), (words, "question-tool"))
    self.assertIn("answered_at", stored["questions"][0])
    self.assertEqual(stored.get("grants", []), [])

def test_ask_respects_the_task_holder(self):
    self.invoke("init", self.payload, ["--session", "s1"])
    held = self.ask({"id": "Q1", "phase": "interview", "text": "Keep the sync API?"}, ok=False, extra=["--session", "s2"])
    self.assertIn("held by session s1", held.stderr)
```

- [ ] **Step 2:** `python -m unittest discover -s tests -p "test_work_record.py" -k ask -k answer -k withdrawn` fails ("invalid choice: 'ask'").
- [ ] **Step 3: Implement.**
  - Extract the body of the `update` branch into `commit_change`: lock, read and validate, refuse a complete run, call `change`, then on a dict bump revision, set `updated_at`, rebind `candidate`, validate with `current=True`, `validate_transitions`, `plan_agenda`, atomic write and agenda. `update` passes a `change` that checks `--expected-revision` and merges the patch; its behavior and output are unchanged.
  - `ask`: payload keys within `{id, phase, text, options, recommendation}`, else `"ask records a question only; answers go through answer"`. The first line of `text`, stripped, ends with one of `QUESTION_MARKS = ("?", "？", "؟")`, else `"The first line must be the question"`. Same id: identical → `existing`; different → `f"Question {id} already asks something else"`. Another question whose first line matches after `" ".join(line.split()).casefold()` → return it as `existing`, with its `answer` when it has one, and write nothing. Otherwise append with `asked_at`.
  - `answer`: unknown id → `f"The record does not ask {qid}"`; `source` from the contract; already answered with the same `text`, `source` and `withdraw` → `unchanged`, no write; otherwise `f"Question {qid} is answered; a changed answer is a new question"`. Set `answer`, `source`, `answered_at` and, for `withdraw`, `withdrawn: true`. `unblocked` lists pending tasks that consume this question and whose every consumed question is now settled; `replan` lists the tasks that consume a withdrawn one. `open` counts `is_open` questions.
  - `resume`: add `waiting` and `replan` computed the same way.
- [ ] **Step 4:** `python -m unittest discover -s tests -p "test_work_record.py"` passes.

### Task 3: The question rule and its consumers

**Files:**
- Create: `plugins/work-controller/skills/work-record/references/questions.md`
- Modify: `plugins/work-controller/skills/work-record/SKILL.md` (description, CLI block ~78, agenda sentence ~86, `questions` row ~137), `plugins/work-controller/roles/isolated-worker.md` (Contract list)
- Modify: `plugins/project-lifecycle/skills/lifecycle-method/references/{interview,brainstorm,continue,waves}.md`
- Modify: `plugins/daodan/workflows/{continue-task,fix-bug,new-feature,refactor-code}.md` (the "ask each with the host's question tool" sentence)
- Test: `tests/test_skill_load_budget.py`, `tests/test_work_record.py`

**Interfaces:** consumes Task 2's command names and payload names.

`references/questions.md`, exact copy (58 words):

```markdown
# Questions

Record each question with `ask` before asking it. First line: one decision,
as a question. Then the facts it needs, anchored and repeated. Two to four
options with their consequence, the recommended first with its reason. Cut
words, never constraints, risks, irreversible effects or costs. Only the
user's own words answer, and only what they state.
```

Replacement copy:

- `SKILL.md` description: append "questions to the user" to the list of what it owns. CLI block, after the `agenda` line: `ask --project ROOT --run-id ID --payload QUESTION.json` and `answer --project ROOT --run-id ID --payload ANSWER.json`. The agenda sentence becomes "`agenda.json` beside `runs/` holds one row per task." (status.md already lists the row's fields). The row becomes `| `questions` | read `references/questions.md` before asking | a changed or removed question or answer |`.
- `isolated-worker.md`, after the "Missing ownership" bullet: "- Missing human decision: stop the part that needs it and report the question, its evidence and the tasks it holds; never ask the user."
- `interview.md`: the paragraph from "Ask one question at a time" to "resume that run with answers." becomes "Ask as the work record's question rule says, one per turn, anchored to a file/line and concrete current/proposed inputs and outputs. Close design branches." The last line becomes "Undecided questions stay open in the record for plan review to raise again."
- `brainstorm.md`, both paragraphs of "## Talk" become: "Ask as the work record's question rule says, one per turn, anchored to real code: "today `path:line` does X; should the idea change that?", about purpose, users, constraints and success, never what the code already settles. When the idea is clear, ask which of two or three alternatives to take, each costed in modules and files, records extended or superseded, tests, risks and waves; one giving a concept a second owner is named as such."
- `continue.md` step 3: "Text given with the command answers the pending questions in order: record each with `answer`, source `continue`, before anything else. A question still unanswered is asked again, one per turn."
- `waves.md`, after "`resource_locks`, `produces`, `consumes`": add ", `question:<id>` among them for an answer it needs, which holds it until answered".
- The four workflows: "ask each with the host's question tool, or record it in the run and close the turn listing it" becomes "record each with the work record's `ask`, then ask it with the host's question tool or list it and close the turn; a yes to an authorization is also a grant".

- [ ] **Step 1: Write the failing tests.** In `tests/test_skill_load_budget.py`: `QUESTIONS = PROTOCOL.parent / "references/questions.md"`, `UNIT_CAPS[QUESTIONS] = 60`, add `QUESTIONS` to the "change: interview and record" and "brainstorm" steps, lower the four caps named in Global Constraints. In `tests/test_work_record.py`:

```python
def test_the_question_rule_ships_with_the_skill(self):
    skill = SCRIPT.parents[1]
    rule = (skill / "references/questions.md").read_text(encoding="utf-8")
    self.assertIn("`ask`", rule)
    self.assertIn("references/questions.md", (skill / "SKILL.md").read_text(encoding="utf-8"))
```

- [ ] **Step 2:** `python -m unittest discover -s tests -p "test_skill_load_budget.py" && python -m unittest discover -s tests -p "test_work_record.py"` fails (missing file, caps above counts).
- [ ] **Step 3:** Apply the copy above.
- [ ] **Step 4:** Both suites pass; `grep -rn "host's question tool, or record" plugins` returns nothing.

### Task 4: Documentation, build, gates and delivery

**Files:**
- Modify: `docs/plugins/work-controller.md` (a paragraph outside the generated markers: questions, `question:<id>`, the two commands, what stays for 2b and 2c), `CLAUDE.md` line 46 ("work-controller is the shared leaf for run records, snapshots, delivery accounting, candidate gates, recovery and the questions a run waits on.")
- Modify: the three `plugin.toml` versions and `metadata.version` in `.claude-plugin/marketplace.json`
- Generated: `exports/`, root manifests, `docs/catalog.md`, `AGENTS.md`

- [ ] **Step 1:** Bump versions from the current `origin/master` values.
- [ ] **Step 2:** `python scripts/sync_codex_instructions.py`, `python scripts/daodan_build.py`, `python scripts/sync_plugin_docs.py`.
- [ ] **Step 3:** Every gate passes: `daodan_build.py --check --support`, `sync_plugin_docs.py --check`, `sync_codex_instructions.py --check`, `lint_dependency_graph.py`, `lint_bundled_paths.py`, `lint_plugin_registration.py`, `lint_fact_anchors.py`, `lint_host_vocabulary.py`, `adapters/copilot/policies/xray-guard/test_xray_guard.py`, `check_version_bumps.py origin/master HEAD`, then `python -m unittest discover -s tests` (about 16 minutes; expected "OK (skipped=N)").
- [ ] **Step 4:** A whole-branch review of the diff against the files it makes stale (spec section 11 still says the record lacks waiting and validity; the 2026-10-20 graph spec), not only the touched files.
- [ ] **Step 5:** On the user's go: commit "Make a run wait on the questions it asks" with the trailer, staging only this change, push to `master`, confirm `consistency`, `publish-marketplaces` and the new release tag.

## Not in this plan

- Decision map and tickets (2b): `map open|next|claim|close` on `graphlib`, execution tickets linked to agenda rows, closure only after the run's gates, the README paragraph and the Wayfinder inspiration row in `upstream-sync`.
- Graph composition and selective invalidation (2c): a changed decision on work already done, the validity of an answer, archetypes and the LLM proposal of ADR-0001.
- Other askers keep their path for now: `senior-review:investigation-method` writes `questions` through `update`, and its step has 16 free words, not the 58 the rule needs; authorization prompts in python-development, repo-hygiene and text-humanizer stay grants.
- Bounded output of `update`, `init`, `show` and `resume` (INV-004 for the old commands): 52 test call sites read the full record; a separate change with measured savings.

## After this plan

1. **2b, decision map:** a map in `.daodan/maps/<id>/` whose decision tickets are this plan's questions and whose execution tickets point at runs; `next` prints only the frontier ticket and its question.
2. **2c, work graphs:** compose a run's tasks from the consumer's archetypes, propose with the LLM only when none fits, replan only the nodes a new answer invalidates.

## Execution notes

Deviations made during execution, after the whole-change review of 2026-10-24:

- `options` and `recommendation` were dropped from the payload and the contract: no method was told to write them, and the options already live in the question text the rule shapes. The tasks above still describe them; the shipped code does not.
- `ask` returns an existing question only when it is open, in the same phase, with the same first line. An answered or withdrawn question is never reused for a new ask, because whether an earlier answer still applies is the coordinator's judgment. A repeated `answer` compares text and withdrawal, not the source.
- The steps for `ask` and `answer`, with their payload fields, moved into `references/questions.md` (93 words, cap 95), the unit only asking steps load; the four workflows point to it. `lifecycle-method/SKILL.md` lost its copy of the takeover rule, which `work-record/SKILL.md` states in the same steps (cap 630 → 585), to keep the brainstorm step at 3050/3050.
- `finish.md` asks open questions first; `worker-brief.md` lets `NEEDS_REPLAN` carry a missing human decision with its evidence.
- `repo-hygiene` `tidy.md` asks its apply authorization by the same rule, `ask` then `answer` and a grant, at the user's request (repo-hygiene 2.2.0, still without dependencies).

