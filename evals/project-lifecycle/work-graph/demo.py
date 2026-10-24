"""Persist a complete simulated editing/review run in a new owned directory."""
import argparse
import json
from pathlib import Path

from controller import Controller, compile_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory')
    args = parser.parse_args()
    root = Path(args.run_directory)
    root.mkdir(parents=True, exist_ok=False)
    plan = compile_plan([
        {'id': 'edit', 'op': 'EDIT_ARTIFACT', 'gate': 'fixture/content/v1',
         'produces': ['document'], 'writes': ['example.md']},
        {'id': 'review', 'op': 'REVIEW_LENS', 'gate': 'fixture/review/v1',
         'consumes': ['document'], 'produces': ['review']},
        {'id': 'barrier', 'op': 'WAVE_BARRIER', 'gate': 'fixture/barrier/v1',
         'consumes': ['document', 'review']},
    ], 'artifact_edit')
    controller = Controller(root)
    controller.init(plan, units=6)
    trace = []
    for step in range(3):
        aid = controller.reserve('simulated-coordinator', controller.show()['revision'])
        attempt = controller.show()['attempts'][aid]
        controller.start(aid, 'simulated-coordinator', attempt['inputs'])
        node = plan['nodes'][attempt['node']]
        outputs = {key: f'simulated-{key}' for key in node['produces']}
        controller.complete(f'completion-{step}', aid, f'fixture-candidate-{step}',
                            'pass', outputs, node['writes'])
        trace.append({'attempt': aid, 'input_digests': attempt['inputs'],
                      'used_units': controller.show()['budget']['used']})
    controller.finish()
    report = {'kind': 'simulation-only', 'trace': trace,
              'outcome': controller.show()['outcome'],
              'real_workers': False, 'real_gate_commands': False,
              'model_calls': 0}
    (root/'trace.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
