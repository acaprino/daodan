"""Score claim support from the source lines each arm delivered.

usage: claims.py RESULT CLAIMS OUT

RESULT is an evaluate.py result whose arms record delivered `lines` as [start, end] runs.
A claim is supported when every group in `all` has at least one alternative span whose
lines were all delivered. The `ready` arm credits a packet only when its status is ready.
Scenarios absent from the result (the cookie explanation is not one of the 24 queries)
are reported as not scored.
"""
import json
from pathlib import Path
import statistics
import sys


def covered(runs, span):
    return any(start <= span['start'] and span['end'] <= end for start, end in runs.get(span['path'], []))


def supported(claim, runs):
    return all(any(covered(runs, span) for span in group['any']) for group in claim['all'])


def main():
    result = json.loads(Path(sys.argv[1]).read_bytes())
    gold = json.loads(Path(sys.argv[2]).read_bytes())
    rows = {r['id']: r for r in result['rows']}
    report = {'schema': 'daodan/context-claims-score/v1', 'anchor_mode': result.get('anchor_mode'),
              'scored': [], 'not_scored': [], 'budgets': {}}
    for scenario in gold['scenarios']:
        (report['scored'] if scenario['id'] in rows else report['not_scored']).append(scenario['id'])
    for budget in sorted({b for r in rows.values() for b in r['arms']}, key=int):
        arms = {}
        for name in ('text', 'scope+packet', 'scope+packet:ready'):
            per_scenario = {}
            for scenario in gold['scenarios']:
                row = rows.get(scenario['id'])
                if row is None:
                    continue
                packet = row['arms'][budget].get('scope+packet', {})
                if name == 'scope+packet:ready':
                    runs = packet.get('lines', {}) if packet.get('status') == 'ready' else {}
                else:
                    runs = row['arms'][budget].get(name, {}).get('lines', {})
                hits = [supported(claim, runs) for claim in scenario['claims']]
                per_scenario[scenario['id']] = {'supported': sum(hits), 'claims': len(hits)}
            total = sum(v['claims'] for v in per_scenario.values())
            arms[name] = {'supported': sum(v['supported'] for v in per_scenario.values()), 'claims': total,
                          'share': statistics.mean([v['supported'] / v['claims'] for v in per_scenario.values()])
                          if per_scenario else None, 'scenarios': per_scenario}
        report['budgets'][budget] = arms
    Path(sys.argv[3]).write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps({b: {a: f"{v['supported']}/{v['claims']}" for a, v in arms.items()}
                      for b, arms in report['budgets'].items()}))


if __name__ == '__main__':
    main()
