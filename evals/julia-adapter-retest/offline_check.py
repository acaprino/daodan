"""Exhaustive offline demonstration of the corrected adapter contract.

For every frozen case and every possible answer label this check runs the real
pinned fast-jev application and verifies:

- the label translates to exactly its action through the real library;
- transcript invariants hold and protected results stay byte-identical;
- the candidate is retained exactly as the label promises (pair removed,
  prefix only, or full output);
- the declared minimal action is the smallest one whose required facts are all
  preserved (or restorable from the declared recovery source), and any smaller
  one loses facts irrecoverably;
- the fixture repair holds (recent copies carry their own inputs), the recovery
  note matches its declared hash, and the frozen requests match a fresh
  rebuild of the adapter state and question.

No model inference happens here. Use --check to recompute and compare with the
frozen artifact instead of writing it.
"""
from __future__ import annotations

import argparse
import hashlib
import json

import adapter
import cases as cases_mod
import harness

base = harness.load_base()
RUN = harness.RUN
read = harness.read
sha = harness.sha
encoded = harness.encoded
write_path = harness.write_path


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _text_or_none(messages, use_id):
    for message in messages:
        for result in message.get('toolResults', []):
            if result['tool_use_id'] == use_id:
                return result['text']
    return None


def _has_call(messages, use_id):
    return any(call['tool_use_id'] == use_id for message in messages for call in message.get('toolUses', []))


def analyze_case(spec, body, owner):
    prepared = owner._bridge({'action': 'prepare', 'messages': spec['messages'],
                              'options': adapter.spec_options(spec), 'arm': 'A'})
    candidate, pinned = adapter.split_calls(prepared, spec)
    use_id = candidate['tool_use_id']
    full_output = adapter.result_text(spec['messages'], use_id)
    prefix_applied = adapter.apply_answer(owner, spec, candidate['id'], 'drop_result')
    prefix_text = adapter.result_text(prefix_applied['raw']['messages'], use_id)
    state = adapter.build_state(prepared['state'], spec, prefix_text, candidate, pinned)
    required = spec['oracle']['required_facts']
    family = spec['family']
    checks = {}
    checks['state_matches_frozen'] = encoded(state) == encoded(body['state'])
    checks['prefix_truncates'] = len(prefix_text) < len(full_output)
    if family == 'prefix_only':
        checks['placement_inside_prefix'] = all(token in full_output[:300] for token in required)
    elif family == 'beyond_prefix':
        checks['placement_beyond_prefix'] = not any(token in full_output[:300] for token in required)
    elif family == 'protected_newer':
        recent = spec['recent']
        checks['recent_inputs_repaired'] = bool(recent) and recent['inputs'] != spec['candidate']['input']
        checks['current_fact_only_in_newer_read'] = bool(recent) \
            and all(token in recent['output'] for token in required) \
            and all(token not in full_output for token in required)
    elif family == 'protected_identical':
        recent = spec['recent']
        checks['duplicate_bytes_identical'] = bool(recent) and recent['output'] == full_output \
            and recent['inputs'] == spec['candidate']['input']
    elif family == 'recovery_available':
        recovery = spec['recovery']
        checks['recovery_note_consistent'] = bool(recovery) \
            and any(message['text'] == recovery['note'] for message in spec['messages']) \
            and _sha(recovery['content']) == recovery['sha256'] \
            and all(token in recovery['content'] for token in required)
    else:
        raise ValueError('Unknown family: ' + family)
    checks['protected_matches_frozen'] = [entry['text'] for entry in body['state']['retained_context']['protected_results']] \
        == [adapter.result_text(spec['messages'], call['tool_use_id']) for call in pinned]
    checks['frozen_candidate'] = body['state']['retained_context']['candidate']['full_output'] == full_output \
        and body['state']['retained_context']['candidate']['id'] == candidate['id']
    checks['frozen_prefix'] = body['state']['retained_context']['retained_prefix_if_output_dropped'] == prefix_text
    checks['frozen_goal'] = body['state']['goal'] == spec['goal']
    checks['state_context_corrected'] = body['state']['context'] == adapter.CONTEXT
    checks['frozen_question'] = body['questions']['action']['type'] == 'choice' \
        and list(body['questions']['action']['criteria'].keys()) == spec['option_order'] \
        and all(body['questions']['action']['criteria'].get(label) == adapter.OPTIONS[label]
                for label in adapter.ACTIONS)

    original_protected_sha = _sha('\n'.join(adapter.result_text(spec['messages'], call['tool_use_id'])
                                           for call in pinned))
    labels = {}
    for label in adapter.ACTIONS:
        applied = adapter.apply_answer(owner, spec, candidate['id'], label)
        messages = applied['raw']['messages']
        rendered = adapter.render(messages)
        kept = _text_or_none(messages, use_id)
        call_present = _has_call(messages, use_id)
        missing = [token for token in required if token not in rendered]
        recovery = spec['recovery']
        restorable = bool(missing) and recovery is not None \
            and all(token in recovery['content'] for token in missing) \
            and recovery['sha256'] in rendered and recovery['path'] in rendered
        lost = [token for token in missing if not restorable]
        retention = {'drop_call': kept is None and not call_present,
                     'drop_result': kept == prefix_text and call_present,
                     'keep': kept == full_output and call_present}[label]
        protected_sha = _sha('\n'.join(adapter.result_text(messages, call['tool_use_id']) for call in pinned))
        decisions = {decision['id']: decision['action'] for decision in applied['raw']['decisions']}
        labels[label] = {
            'library_action': decisions.get(candidate['id']),
            'candidate_result_present': kept is not None,
            'retention_matches_label': retention,
            'missing_facts': missing,
            'restorable_from_recovery': restorable,
            'lost_facts': lost,
            'protected_sha256': protected_sha,
            'invariants': applied['invariants'],
            'chars_before': applied['raw']['stats']['charsBefore'],
            'chars_after': applied['raw']['stats']['charsAfter'],
        }
    computed = next(label for label in adapter.ACTIONS if not labels[label]['lost_facts'])
    checks['expected_matches_computed'] = computed == spec['oracle']['expected_action']
    checks['all_labels_map_to_their_action'] = all(labels[label]['library_action'] == label for label in adapter.ACTIONS)
    checks['all_labels_invariants'] = all(all(labels[label]['invariants'].values()) for label in adapter.ACTIONS)
    checks['all_labels_retention'] = all(labels[label]['retention_matches_label'] for label in adapter.ACTIONS)
    checks['protected_untouched'] = all(labels[label]['protected_sha256'] == original_protected_sha
                                        for label in adapter.ACTIONS)
    checks['smaller_actions_lose_facts'] = all(
        labels[adapter.ACTIONS[index]]['lost_facts']
        for index in range(adapter.ACTIONS.index(computed)))
    return {
        'id': spec['id'], 'language': spec['language'], 'family': family,
        'expected': spec['oracle']['expected_action'], 'computed': computed,
        'option_order': spec['option_order'],
        'candidate_id': candidate['id'],
        'candidate_full_chars': len(full_output), 'candidate_sha256': _sha(full_output),
        'retained_prefix_chars': len(prefix_text), 'retained_prefix_sha256': _sha(prefix_text),
        'protected_ids': [call['id'] for call in pinned],
        'labels': labels, 'checks': checks,
        'pass': all(checks.values()),
    }


def guard_check():
    rejected = {}
    for probe in ('', 'drop', 'DROP_CALL', 'drop_call ', 'keep_all', 'billing'):
        try:
            adapter.decision_pair('t1', probe)
            rejected[repr(probe)] = False
        except ValueError:
            rejected[repr(probe)] = True
    distinct = len({json.dumps(adapter.decision_pair('t1', label), sort_keys=True)
                    for label in adapter.ACTIONS}) == 3
    return {'rejected_unmapped': rejected, 'distinct_pairs_for_three_labels': distinct,
            'pass': all(rejected.values()) and distinct}


def rotation_check(spec, body):
    orders = [adapter.option_order(index) for index in range(3)]
    stable = all(list({label: adapter.OPTIONS[label] for label in order}.keys()) == order for order in orders)
    variants = []
    for order in orders:
        criteria = {label: adapter.OPTIONS[label] for label in order}
        variants.append({'order': order, 'criteria_keys': list(criteria.keys()),
                         'descriptions_stable': all(criteria[label] == adapter.OPTIONS[label] for label in order)})
    return {'rotations': variants,
            'frozen_order_is_a_rotation': spec['option_order'] in orders,
            'labels_are_keyed_not_positional': stable and all(
                len({json.dumps(adapter.decision_pair('t1', label), sort_keys=True) for label in order}) == 3
                for order in orders),
            'pass': stable and spec['option_order'] in orders and len(set(map(tuple, orders))) == 3}


def fixture_check(frozen_cases):
    fresh = {spec['id']: spec for spec in cases_mod.build_specs()}
    problems = []
    if set(fresh) != set(frozen_cases):
        problems.append('case id sets differ')
    for case_id, frozen_case in frozen_cases.items():
        fresh_case = fresh.get(case_id, {})
        for key in ('language', 'family', 'goal', 'messages', 'candidate', 'recent', 'recovery', 'oracle'):
            if frozen_case.get(key) != fresh_case.get(key):
                problems.append(f'{case_id}:{key}')
        index = list(fresh).index(case_id)
        if frozen_case.get('option_order') != adapter.option_order(index):
            problems.append(f'{case_id}:option_order')
    control = cases_mod.control_spec() if hasattr(cases_mod, 'control_spec') else None
    return {'fresh_matches_frozen': not problems, 'problems': problems, 'pass': not problems}


def build_report():
    old, owner = base.dependencies()
    specs = cases_mod.build_specs()
    cases_mod.validate_specs(specs)
    frozen_cases = read(RUN / 'cases.json')
    requests = read(RUN / 'input.json')
    if len(requests) != 8:
        raise ValueError('Expected eight frozen requests')
    case_reports = {}
    for request in requests:
        spec = {spec['id']: spec for spec in specs}[request['case_id']]
        spec = {**spec, 'option_order': frozen_cases[request['case_id']]['option_order']}
        case_reports[request['id']] = analyze_case(spec, request['body'], owner)
    report = {
        'schema': 'julia-adapter-retest/offline/v1',
        'actions': {label: {'decision': {'keep_call': adapter.ANSWER_TO_DECISION[label][0],
                                         'keep_result': adapter.ANSWER_TO_DECISION[label][1]}}
                    for label in adapter.ACTIONS},
        'cases': case_reports,
        'guard': guard_check(),
        'rotation': rotation_check({**specs[0], 'option_order': frozen_cases[specs[0]['id']]['option_order']},
                                   requests[0]['body']),
        'fixture': fixture_check(frozen_cases),
    }
    failed = [case_id for case_id, entry in case_reports.items() if not entry['pass']]
    report['summary'] = {'cases': len(case_reports),
                         'labels_applied': len(case_reports) * len(adapter.ACTIONS),
                         'failed_checks': failed,
                         'guard_pass': report['guard']['pass'],
                         'rotation_pass': report['rotation']['pass'],
                         'fixture_pass': report['fixture']['pass']}
    report['pass'] = not failed and report['guard']['pass'] and report['rotation']['pass'] \
        and report['fixture']['pass']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='recompute and compare with the frozen artifact instead of writing it')
    flags = parser.parse_args()
    report = build_report()
    if flags.check:
        frozen = read(RUN / 'offline-verification.json')
        if encoded(frozen) != encoded(report):
            raise SystemExit('Frozen offline verification does not reproduce')
        print(json.dumps({'reproduced': True, 'pass': report['pass']}))
        return 0 if report['pass'] else 1
    write_path(RUN / 'offline-verification.json', report, frozen=True)
    print(json.dumps(report['summary'], indent=2))
    return 0 if report['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
