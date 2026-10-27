"""Synthetic contextual tool selection fixtures and independent set oracles.

Consumed by the pilot runner. These tool names and permissions are laboratory
data, never authority to call real services. Scoring reports the model's partial
output separately from a deterministic fallback and preserves missing answers.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math


THRESHOLD = 0.5
READ_ACTIONS = {"read_repository", "read_web", "read_issues", "read_email", "read_calendar"}


def _tool(name, description, action, properties, required):
    return {"name": name, "description": description, "action": action,
            "parameters": {"type": "object", "properties": properties,
                           "required": required, "additionalProperties": False}}


_STR = {"type": "string"}
CATALOG = [
    _tool("fs.search", "Find repository file paths or text matching a query.", "read_repository", {"query": _STR}, ["query"]),
    _tool("fs.read", "Read the complete contents of a repository file or saved patch.", "read_repository", {"path": _STR}, ["path"]),
    _tool("fs.patch", "Apply an exact patch to a repository file.", "modify_files", {"path": _STR, "patch": _STR}, ["path", "patch"]),
    _tool("test.run", "Run named tests against the current checkout and return results with candidate identity.", "execute_tests", {"target": _STR}, ["target"]),
    _tool("git.diff", "Read the patch applied to the current repository checkout.", "read_repository", {"base": _STR}, ["base"]),
    _tool("web.search", "Find public web pages and their URLs by search query.", "read_web", {"query": _STR}, ["query"]),
    _tool("web.fetch", "Read the contents of a known public web URL.", "read_web", {"url": {"type": "string", "format": "uri"}}, ["url"]),
    _tool("issue.read", "Read an existing issue and its discussion by repository and number.", "read_issues", {"repository": _STR, "number": {"type": "integer", "minimum": 1}}, ["repository", "number"]),
    _tool("issue.create", "Publish a new issue using its approved title and body.", "publish_issue", {"repository": _STR, "title": _STR, "body": _STR}, ["repository", "title", "body"]),
    _tool("email.search", "Search and read existing email conversations.", "read_email", {"query": _STR}, ["query"]),
    _tool("email.send", "Send an approved email to a specified recipient in an existing thread.", "send_email", {"recipient": _STR, "thread": _STR, "body": _STR}, ["recipient", "thread", "body"]),
    _tool("calendar.read", "Read attendee availability and existing calendar events.", "read_calendar", {"attendees": {"type": "array", "items": _STR}, "date": _STR}, ["attendees", "date"]),
    _tool("calendar.create", "Create an approved calendar event for a confirmed slot and participants.", "create_event", {"attendees": {"type": "array", "items": _STR}, "start": _STR, "end": _STR}, ["attendees", "start", "end"]),
    _tool("tools.discover", "Expose tools supplied by a registered provider.", "discover_tools", {"provider": _STR}, ["provider"]),
]


def _schema(tool):
    return {"type": "function", "function": {"name": tool["name"],
            "description": tool["description"], "parameters": deepcopy(tool["parameters"])}}


def _bytes(schemas):
    return len(json.dumps(schemas, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _case(number, goal, phase, evidence, groups, *, actions=(), split="verification",
          hidden=(), discovery=True, discover_next=False, blocked=False, aliases=False):
    allowed = READ_ACTIONS | set(actions) | ({"discover_tools"} if discovery else set())
    hidden = set(hidden)
    records = [deepcopy(t) for t in CATALOG if t["action"] in allowed and t["name"] not in hidden]
    mapping = {t["name"]: t["name"] for t in records}
    if aliases:
        records.reverse()
        mapping = {}
        for index, tool in enumerate(records):
            canonical = tool["name"]
            tool["name"] = f"capability_{index + 1:02d}"
            mapping[tool["name"]] = canonical
    exposed = {canonical: name for name, canonical in mapping.items()}
    mandatory = [exposed["tools.discover"]] if discover_next and "tools.discover" in exposed else []
    candidates = [t for t in records if mapping[t["name"]] != "tools.discover"]
    state = {"objective": goal, "phase": phase, "evidence": evidence,
             "permissions": sorted(allowed),
             "available_tools": [{"id": t["name"], "description": t["description"],
                                  "action": t["action"]} for t in records],
             "providers": [{"name": "web", "registered": True,
                            "tools_exposed": "web.fetch" in exposed}],
             "instruction": "Select capabilities needed for the current bounded phase. Provided evidence need not be fetched again. Tool availability and permissions are fixed facts."}
    questions = {t["name"]: {"type": "noul", "instructions":
        f"Is capability {t['name']} needed for the current bounded phase? {t['description']}",
        "criteria": {"true": "The capability is needed to satisfy the current phase requirements, including one valid alternative when several can serve the same requirement.",
                     "false": "The current evidence and other steps make this capability unnecessary for this phase."}}
        for t in candidates}
    all_names = {t["name"] for t in CATALOG}
    eligible_canonical = set(mapping.values())
    return {"id": f"T{number:02d}", "domain": "tools", "split": split,
            "state": state, "questions": questions,
            "oracle": {"required_groups": groups, "mapping": mapping,
                       "eligible": [t["name"] for t in records],
                       "schemas": {t["name"]: _schema(t) for t in records},
                       "prohibited": sorted(all_names - eligible_canonical),
                       "mandatory": mandatory, "discovery_required": discover_next,
                       "blocked": blocked, "threshold": THRESHOLD}}


def build_cases():
    """Return fresh, fully materialized fixtures; oracle data never enters state."""
    code = "def login(user):\n    return user['active'] and user['deleted']\n"
    cases = [
        _case(1, "Correggi l'errore di login", "diagnosis only; no changes authorized",
              "Login returns 401 instead of 200 for an active user. Repository paths are unknown; source and tests have not been inspected.",
              [["fs.search"], ["fs.read"]], split="development"),
        _case(2, "Correggi l'errore di login", "apply correction and verify",
              {"source_path": "auth.py", "complete_source": code,
               "complete_test": "def test_login():\n    assert login({'active': True, 'deleted': False}) is True\n",
               "observed_test": "test_login FAILED: expected True, got False",
               "constraint": "The supplied source and test are complete; no other files need investigation."},
              [["fs.patch"], ["test.run"]], actions=("modify_files", "execute_tests"), split="development"),
        _case(3, "Dammi il risultato della verifica", "inspect applied patch and test this exact candidate",
              "Candidate B is in the checkout. Its patch is also saved at candidate.patch. No patch inspection or test result is available yet. Verification requires both inspection and tests.",
              [["test.run"], ["git.diff", "fs.read"]], actions=("execute_tests",)),
        _case(4, "Dammi il risultato della verifica", "write the final verification report",
              {"candidate": "B", "complete_diff": "- return active and deleted\n+ return active and not deleted",
               "inspection": "Patch for B changes only the intended condition; inspection complete.",
               "tests": "Candidate B: test_login PASSED, 1/1 tests. Use these supplied verified facts; no rerun is requested."}, []),
        _case(5, "Verifica il limite attuale di questa API", "read the official current specification",
              "Official URL is https://service.example/docs/api/limits . Its contents have not been retrieved.", [["web.fetch"]]),
        _case(6, "Verifica il limite attuale di questa API", "locate and read the official current specification",
              "The service is ExampleService and the API is its public REST API. The official documentation URL is unknown and no documentation contents are supplied.",
              [["web.search"], ["web.fetch"]]),
        _case(7, "Gestisci questa segnalazione", "triage an existing public issue; no publication",
              "Public issue example/project#42 is at https://issues.example/project/42 . Its body and discussion have not been read.",
              [["issue.read", "web.fetch"]], split="development"),
        _case(8, "Gestisci questa segnalazione", "publish the approved new issue",
              {"repository": "example/project", "approved_title": "Login rejects active accounts",
               "approved_body": "Active non-deleted accounts receive 401. Reproduction and expected behavior confirmed.",
               "duplicate_check": "Completed and no duplicate found.", "authorization": "Publish this exact approved issue."},
              [["issue.create"]], actions=("publish_issue",), split="development"),
        _case(9, "Rispondi al cliente", "prepare a draft only; sending is not authorized",
              "The customer is in an existing email conversation, but its prior message, address and thread identifier are not in context. Search the saved conversation before drafting.",
              [["email.search"]]),
        _case(10, "Rispondi al cliente", "send the approved reply",
              {"recipient": "customer@example.invalid", "thread": "thread-77",
               "approved_body": "Your renewal date is 2026-11-01.",
               "authorization": "Send exactly this approved reply to the supplied recipient and thread. No further lookup is needed."},
              [["email.send"]], actions=("send_email",)),
        _case(11, "Fissa l'incontro con Marta", "propose a slot; creating an event is not authorized",
              "Marta and the requester are known participants. Their availability for 2026-11-02 is not supplied; inspect calendars before proposing a slot.",
              [["calendar.read"]]),
        _case(12, "Fissa l'incontro con Marta", "create the approved event",
              {"attendees": ["marta@example.invalid", "requester@example.invalid"],
               "start": "2026-11-02T10:00:00+01:00", "end": "2026-11-02T10:30:00+01:00",
               "availability": "Both calendars were checked and this slot is free.",
               "authorization": "Both participants confirmed this slot; create the event."},
              [["calendar.create"]], actions=("create_event",)),
    ]
    original = cases[1]
    cases.append(_case(13, original["state"]["objective"], original["state"]["phase"],
                       deepcopy(original["state"]["evidence"]), [["fs.patch"], ["test.run"]],
                       actions=("modify_files", "execute_tests"), split="development", aliases=True))
    cases.append(_case(14, "Verify the current limit of this API", cases[5]["state"]["phase"],
                       deepcopy(cases[5]["state"]["evidence"]), [["web.search"], ["web.fetch"]]))
    unavailable = ("web.search", "web.fetch")
    evidence = {"service": "ExampleService public REST API", "official_url": "unknown",
                "documentation": "not yet retrieved", "inventory": "The web provider is registered but its tools have not been exposed."}
    cases.append(_case(15, cases[5]["state"]["objective"], "discover registered provider capabilities before proceeding",
                       evidence, [["tools.discover"]], hidden=unavailable, discover_next=True))
    cases.append(_case(16, cases[5]["state"]["objective"], "capability check before proceeding",
                       evidence, [["web.search"], ["web.fetch"]], hidden=unavailable,
                       discovery=False, blocked=True))
    return cases


def _missing(groups, canonical):
    return [list(group) for group in groups if not set(group).intersection(canonical)]


def score_case(case, response):
    """Score observable answers; invalid output triggers an explicit broad fallback."""
    oracle = case["oracle"]
    mapping = oracle["mapping"]
    answers = response.get("answers", {}) if isinstance(response, dict) else {}
    if not isinstance(answers, dict):
        answers = {}
    invalid = []
    selected = []
    probabilities = {}
    for name in case["questions"]:
        answer = answers.get(name)
        value = answer.get("noul") if isinstance(answer, dict) else None
        if (not isinstance(answer, dict) or answer.get("type") != "noul"
                or isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not 0 <= value <= 1):
            invalid.append(name)
            continue
        probabilities[name] = value
        if value >= oracle["threshold"]:
            selected.append(name)
    extras = sorted(set(answers) - set(case["questions"]))
    invalid.extend(extras)
    complete = not invalid
    raw = sorted(set(selected + oracle["mandatory"]))
    # This fallback only uses validity, never hidden correctness labels.
    policy = raw if complete else sorted(set(oracle["eligible"]))
    raw_canonical = {mapping[name] for name in raw}
    policy_canonical = {mapping[name] for name in policy}
    eligible_canonical = set(mapping.values())
    missing_raw = _missing(oracle["required_groups"], raw_canonical)
    missing_policy = _missing(oracle["required_groups"], policy_canonical)
    baseline_missing = _missing(oracle["required_groups"], eligible_canonical)
    blocked = oracle["blocked"]
    # Sufficiency alone rewards selecting everything; T04 needs no tool and would pass
    # with all thirteen. Superfluous selections and the cheapest sufficient set make
    # over-selection and its schema cost observable.
    required_union = {name for group in oracle["required_groups"] for name in group}
    superfluous = sorted(raw_canonical - required_union)
    exposed = {canonical: name for name, canonical in mapping.items()}
    # A group with no exposed member (T16's hidden web tools) has no cost to count.
    minimal_bytes = sum(min((_bytes([oracle["schemas"][exposed[name]]]) for name in group
                             if name in exposed), default=0)
                        for group in oracle["required_groups"])
    return {"status": "ok" if complete else "incomplete", "complete": complete,
            "invalid_answers": invalid, "probabilities": probabilities,
            "selected_ids": raw, "selected_canonical": sorted(raw_canonical),
            "selected_count": len(raw), "superfluous_canonical": superfluous,
            "exact_sufficient": (not missing_raw and not blocked and not superfluous) if complete else None,
            "schema_bytes_minimal": minimal_bytes,
            "policy_selected_ids": policy, "mandatory_ids": list(oracle["mandatory"]),
            "required_missing": missing_raw, "policy_required_missing": missing_policy,
            "sufficiency_raw": (not missing_raw and not blocked) if complete else None,
            "sufficiency_policy": not missing_policy and not blocked,
            "baseline_sufficient": not baseline_missing and not blocked,
            "goal_completion_sufficient": not missing_policy and not (blocked or oracle["discovery_required"]),
            "fallback": "none" if complete else "all_eligible_on_invalid",
            "prohibited_included": sorted(raw_canonical.intersection(oracle["prohibited"])),
            "permission_filter_result": "all selected tools eligible; this is not model credit",
            "eligible_count": len(oracle["eligible"]), "question_count": len(case["questions"]),
            "schema_bytes_before": _bytes([oracle["schemas"][name] for name in oracle["eligible"]]),
            "schema_bytes_after": _bytes([oracle["schemas"][name] for name in raw]),
            "schema_bytes_policy": _bytes([oracle["schemas"][name] for name in policy]),
            "schema_tokens": None,
            "next_step": "blocked" if blocked else ("discovery_required" if oracle["discovery_required"] else "tools_available"),
            "blocked_expected": blocked}
