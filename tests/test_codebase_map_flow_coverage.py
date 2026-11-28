"""What remains provable from a saved runtime observation and from a bounded flow."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'daodan/core'))
import flows
import system_brief


def test_logical_edges_keep_the_conflict_on_its_observation():
    start = 'web.ts::start'
    base = {'from': start, 'to': 'save.ts::save', 'type': 'chiama', 'origin': 'osservato',
            'resolver': 'sampler@1', 'confidence': 'sampled'}
    edges = [{**base, 'site': 'web.ts:2', 'conflict': False}, {**base, 'site': 'web.ts:3', 'conflict': True}]
    modules = {'web.ts': 'ui', 'save.ts': 'core'}
    for order in (edges, edges[::-1]):
        flow = flows.trace({'edges': order, 'gaps': []}, start, 'from')
        view = flows.at_level(flow, 'moduli', modules)
        assert {(e['site'], e['conflict'], e['links']) for e in view['edges']} == {
            ('web.ts:2', False, 1), ('web.ts:3', True, 1)}


def test_bytes_are_for_each_final_unit_and_its_optional_context():
    links = {'edges': [], 'gaps': [], 'entries': [], 'stores': {}}
    sizes = {'a.py': 8, 'b.py': 4, 'big.py': 15}
    result = flows.units(links, sizes, ['.'], 12)
    assert [(u['files'], u['bytes']) for u in result['units']] == [(['a.py', 'b.py'], 12), (['big.py'], 15)]
    entries = [{'symbol': symbol} for symbol in ('a.py::a', 'b.py::b')]
    shared = [{'from': e['symbol'], 'to': 'shared.py::c', 'type': 'chiama'} for e in entries]
    sizes = {'a.py': 8, 'b.py': 8, 'shared.py': 4}
    result = flows.units({**links, 'entries': entries, 'edges': shared}, sizes, ['.'], 12, share=1)
    unit, = [u for u in result['units'] if u.get('context')]
    assert (unit['bytes'], unit['context_bytes']) == (8, 4)


def test_budget_points_to_the_first_unfollowed_evidence():
    edges = [{'from': a, 'to': b, 'site': site, 'type': 'chiama'} for a, b, site in
             [('a.py::entry', 'a.py::save', 'a.py:3'), ('a.py::save', 'a.py::write', 'a.py:5')]]
    flow = flows.trace({'edges': edges, 'gaps': []}, 'a.py::entry', 'from', max_edges=1)
    assert flow['stopped'] == 'budget'
    assert flow['stopped_at'] == edges[1]
    assert flow['stopped_at'] not in flow['edges']


def test_brief_uses_saved_control_counts_without_assigning_a_call_to_a_control(tmp_path):
    manifest = tmp_path / 'manifest.sqlite'
    journal = manifest.with_name(system_brief.pipeline.events.JOURNAL)
    journal.touch()
    recorded = {'state': 'observed', 'ui_controls': [
        {'status': 'observed', 'documents': 2, 'observed': 3, 'pending': 1},
        {'status': 'partial', 'documents': 1, 'observed': 1, 'pending': 2}]}
    edges = [{'origin': 'osservato', 'confidence': 'sampled', 'conflict': True},
             {'origin': 'osservato', 'confidence': 'observed'}, {'origin': 'diretto'}]
    with patch.object(system_brief.pipeline, 'runtime', return_value=recorded) as receipt:
        assert system_brief._observations(manifest, edges) == (True, {
            'calls': {'observed': 1, 'sampled': 1}, 'conflicts': 1,
            'ui_controls': {'documents': 3, 'observed': 4, 'pending': 3, 'runs': {'observed': 1, 'partial': 1}}})
        receipt.assert_called_once_with(manifest)
    journal.unlink()
    with patch.object(system_brief.pipeline, 'runtime', side_effect=AssertionError('no journal')):
        assert system_brief._observations(manifest, []) == (False, {})


def test_reopened_brief_shows_gestures_and_keeps_the_handler_unknown(tmp_path):
    from test_codebase_map_dynamic import write_project

    _, manifest = write_project(tmp_path, {'app.py': 'raise AssertionError("target executed")\n'})
    bus = system_brief.pipeline.events.Bus(manifest.with_name(system_brief.pipeline.events.JOURNAL))
    ui = [{'status': 'partial', 'documents': 1, 'observed': 2, 'pending': 3}]
    bus.emit('graph.ready', 'recorded container output', step='union', ui_controls=ui)
    with patch('container.find_engine', side_effect=AssertionError('launched a new run')):
        for _ in range(2):
            value = system_brief.brief(manifest, [])
            assert value['steps']['dinamico'] and value['entries'] == 0
            assert value['observations'] == {'ui_controls': {'documents': 1, 'observed': 2, 'pending': 3,
                                                              'runs': {'partial': 1}}}
            text, _ = system_brief._text(value, system_brief.LIMIT, system_brief.HOLDERS)
            assert '2 observed, 3 pending' in text and 'these counts identify no handler' in text


def test_two_dynamic_runs_reuse_control_evidence_and_count_source_opens(tmp_path):
    from unittest.mock import Mock
    from test_codebase_map_dynamic import dynamic, fake, static_store, step, write_project

    project, manifest = write_project(tmp_path, {'app.py': 'raise AssertionError("target executed")\n'})
    static_store(manifest)
    controls = {'status': 'observed', 'documents': 1, 'observed': 2, 'pending': 1}
    suite = {'root': '.', 'runner': 'playwright'}
    observer = fake({'state': 'ran', 'sites': [], 'runs': [{**suite, 'state': 'ran', 'controls': controls}], 'gaps': []})
    observer.plan = Mock(return_value={'runs': [suite], 'gaps': []})
    observer.observe = Mock(wraps=observer.observe)
    opened = Path.open
    measurements = []
    with patch.object(dynamic, 'observers', return_value=[observer]):
        for _ in range(2):
            sources = []
            def measured(path, mode='r', *args, **kwargs):
                if 'r' in mode and path.is_relative_to(project):
                    sources.append(path.relative_to(project).as_posix())
                return opened(path, mode, *args, **kwargs)
            with patch.object(Path, 'open', measured):
                result, _, engine = step(manifest)
            assert result['ui_controls'] == [{'root': '.', **controls}]
            measurements.append((sources, observer.plan.call_count, engine.call_count, observer.observe.call_count))
            observer.plan.reset_mock()
            observer.observe.reset_mock()
    cold, warm = measurements
    print('dynamic source opens, plans, engine requests and observer runs (recorded output):', measurements)
    assert set(cold[0]) == {'app.py'} and cold[1:] == (1, 1, 1)
    assert set(warm[0]) <= {'app.py'} and len(warm[0]) <= 1
    assert warm[1] <= 1 and warm[2:] == (0, 0)


def test_unreached_symbols_include_isolated_declarations_and_count_a_shared_handler_once():
    entry, other, save = 'ui/app.py::click', 'ui/app.py::shortcut', 'core/db.py::save'
    hidden, uncertain, conflict = ('core/db.py::' + name for name in ('isolated', 'sample', 'conflict'))
    symbols = {'ui/app.py': {entry, other}, 'core/db.py': {save, hidden, uncertain, conflict}}
    edges = [{'type': 'chiama', 'from': root, 'to': save} for root in (entry, other)] + [
        {'type': 'chiama', 'from': save, 'to': uncertain, 'confidence': 'sampled'},
        {'type': 'chiama', 'from': save, 'to': conflict, 'confidence': 'observed', 'conflict': True},
        {'type': 'attiva', 'from': other, 'to': uncertain, 'handler_confidence': 'sampled'}]
    entries = [{'symbol': entry}, {'symbol': other}, {'symbol': uncertain, 'handler_confidence': 'sampled'}]
    counts = flows._symbol_coverage(symbols, entries, edges)
    assert counts == {'core': {'unreached': 3, 'total': 4}, 'ui': {'unreached': 0, 'total': 2}}


def test_brief_shows_unreachable_named_symbols_in_each_directory_with_the_denominator(tmp_path):
    from test_codebase_map_dynamic import write_project

    _, manifest = write_project(tmp_path, {'a/one.py': 'def idle():\n    pass\n',
                                           'b/two.py': 'def one():\n    pass\ndef two():\n    pass\n'})
    value = system_brief.brief(manifest, [])
    assert value['symbol_coverage'] == {'a': {'unreached': 1, 'total': 1}, 'b': {'unreached': 2, 'total': 2}}
    text, _ = system_brief._text(value, system_brief.LIMIT, system_brief.HOLDERS)
    assert 'b: 2 of 2 named symbols unreached' in text
    assert 'a: 1 of 1 named symbols unreached' in text
