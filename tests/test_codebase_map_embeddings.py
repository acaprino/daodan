"""Optional embeddings retain scope, freshness, cache identity and lexical evidence."""
import copy
from contextlib import closing, nullcontext
import hashlib
import importlib.util
import json
import math
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'plugins/codebase-map/skills/map-method/scripts'
sys.path.insert(0, str(SCRIPTS))
import retrieval
import snapshot

if importlib.util.find_spec('embedding_worker'):
    import embedding_worker as worker
else:
    worker = None


class LocalEncoder:
    """A deterministic local encoder exposes exactly which inputs were encoded."""
    def __init__(self):
        self.profile = {'provider': 'fixture', 'model_revision': 'one', 'model_sha256': 'a' * 64,
                        'tokenizer_sha256': 'b' * 64, 'runtime': {'fixture': '1'},
                        'encoder_version': 1, 'dimensions': 4, 'max_tokens': 512}
        self.encoded = []

    def encode(self, texts):
        self.encoded.extend(texts)
        return [[1 + text.lower().count('invoice'), 1 + text.lower().count('revoke'),
                 1 + text.lower().count('atomic'), 1] for text in texts]


class EmbeddingTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(worker, 'P5 embedding worker is missing')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.manifest = self.root / '.codebase-map/manifest.sqlite'
        self.index = self.manifest.with_name('embeddings.sqlite')
        self.lexical = self.manifest.with_name('retrieval.sqlite')
        self.provider = LocalEncoder()
        self.write('billing.py', 'def invoice_total(items):\n    return sum(items)\n')
        self.write('sessions.py', 'def revoke_session(key):\n    return key is None\n')
        self.resnapshot()

    def write(self, name, text):
        (self.root / name).write_text(text, encoding='utf8')

    def resnapshot(self):
        snapshot.write_snapshot(self.root, self.manifest)
        retrieval.refresh_index(self.manifest, self.lexical)

    def refresh(self, dest=None):
        return worker.refresh_index(self.manifest, dest or self.index, provider=self.provider)

    def query(self, query='invoice', limit=10):
        return worker.search(self.manifest, self.index, query, provider=self.provider, limit=limit)

    def inventory(self, path=None):
        with closing(sqlite3.connect(path or self.index)) as db:
            members = list(db.execute('SELECT entity_id,input_digest FROM documents ORDER BY entity_id'))
            vectors = list(db.execute('SELECT input_digest,vector FROM vectors ORDER BY input_digest'))
        return members, vectors

    def test_unchanged_generation_reuses_all_vectors_and_keeps_manifest(self):
        before = self.manifest.read_bytes()
        first = self.refresh()
        self.assertEqual(first['documents'], 4)
        self.assertEqual(first['encoded'], 4)
        self.provider.encoded.clear()
        second = self.refresh()
        self.assertEqual(second['encoded'], 0)
        self.assertEqual(second['reused'], 4)
        self.assertEqual(self.provider.encoded, [])
        self.assertEqual(self.manifest.read_bytes(), before)

    def test_same_id_changed_body_reencodes_current_input_only(self):
        self.refresh()
        old = dict(self.inventory()[0])
        self.write('billing.py', 'def invoice_total(items):\n    return sum(items) + 7\n')
        self.resnapshot()
        changed = self.refresh()
        self.assertEqual((changed['encoded'], changed['reused']), (1, 3))
        self.assertNotEqual(old['billing.py::invoice_total'], dict(self.inventory()[0])['billing.py::invoice_total'])

    def test_profile_changes_invalidate_vectors(self):
        for key, value in [('model_revision', 'two'), ('tokenizer_sha256', 'c' * 64),
                           ('runtime', {'fixture': '2'}), ('encoder_version', 2)]:
            with self.subTest(key=key):
                self.refresh()
                self.provider.profile[key] = value
                result = self.refresh()
                self.assertEqual((result['encoded'], result['reused']), (4, 0))

    def test_rename_delete_incremental_inventory_and_replay_equal_full_rebuild(self):
        self.refresh()
        old = dict(self.inventory()[0])
        (self.root / 'billing.py').rename(self.root / 'ledger.py')
        (self.root / 'sessions.py').unlink()
        self.resnapshot()
        result = self.refresh()
        members, _ = self.inventory()
        self.assertEqual([row[0] for row in members], ['ledger.py::@file', 'ledger.py::invoice_total'])
        self.assertEqual((result['encoded'], result['removed']), (2, 4))
        self.assertNotEqual(old['billing.py::invoice_total'], dict(members)['ledger.py::invoice_total'])
        full = self.manifest.with_name('embeddings-full.sqlite')
        self.refresh(full)
        self.assertEqual(self.inventory(), self.inventory(full))
        a = self.query()
        b = worker.search(self.manifest, full, 'invoice', provider=self.provider, limit=10)
        self.assertEqual(a['results'], b['results'])

    def test_crash_keeps_previous_generation_and_releases_lock(self):
        self.refresh()
        before = self.index.read_bytes()
        self.write('billing.py', 'def invoice_total(items): return 123\n')
        self.resnapshot()
        with mock.patch.object(self.provider, 'encode', side_effect=RuntimeError('encoder crash')):
            with self.assertRaisesRegex(RuntimeError, 'encoder crash'):
                self.refresh()
        self.assertEqual(self.index.read_bytes(), before)
        self.assertFalse(self.index.with_suffix('.sqlite.lock').exists())
        self.assertFalse(list(self.index.parent.glob('.embedding-*.sqlite')))

    def test_source_change_during_encoding_retains_generation(self):
        self.refresh()
        before = self.index.read_bytes()
        self.write('billing.py', 'def invoice_total(items): return 3\n')
        self.resnapshot()
        encode = self.provider.encode
        def changing(texts):
            values = encode(texts)
            self.write('sessions.py', 'def revoke_session(key): return False\n')
            return values
        with mock.patch.object(self.provider, 'encode', changing):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                self.refresh()
        self.assertEqual(self.index.read_bytes(), before)

    def test_invalid_vectors_never_publish(self):
        for vectors in [[], [[float('nan')] * 4] * 4, [[0] * 4] * 4, [[1, 2]] * 4]:
            with self.subTest(vectors=vectors), mock.patch.object(self.provider, 'encode', return_value=vectors):
                with self.assertRaises(ValueError):
                    self.refresh()
        self.assertFalse(self.index.exists())

    def test_tampered_vector_is_rejected_before_ranking(self):
        self.refresh()
        with closing(sqlite3.connect(self.index)) as db, db:
            db.execute('UPDATE vectors SET vector=zeroblob(16)')
        with self.assertRaisesRegex(ValueError, 'vector'):
            self.query()

    def test_changed_provider_cannot_query_an_old_generation(self):
        self.refresh()
        self.provider.profile['model_revision'] = 'different'
        with self.assertRaisesRegex(ValueError, 'provider'):
            self.query()

    def test_hidden_files_and_source_drift_never_enter_results(self):
        hidden = self.root / '.hidden'
        hidden.mkdir()
        (hidden / 'secret.py').write_text('def secret(): return 1\n', encoding='utf8')
        self.refresh()
        self.assertEqual(self.query()['matched'], 4)
        self.write('sessions.py', 'def revoke_session(key): return 99\n')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            self.query()

    def test_destinations_cannot_replace_other_evidence_or_escape(self):
        for path in (self.manifest, self.lexical, self.root / 'elsewhere.sqlite',
                     self.manifest.with_name('cards.sqlite'), self.manifest.with_name('engine-edges.sqlite')):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.refresh(path)

    def test_linked_destination_is_rejected(self):
        self.refresh()
        linked = self.manifest.with_name('alias.sqlite')
        linked.symlink_to(self.index)
        with self.assertRaises(ValueError):
            self.refresh(linked)

    def test_dense_results_are_bound_bounded_and_do_not_contain_vectors(self):
        self.refresh()
        result = self.query(limit=1)
        self.assertEqual(result['schema'], 'daodan/embedding-result/v1')
        self.assertEqual((result['matched'], result['returned'], result['truncated']), (4, 1, 3))
        self.assertEqual(result['results'][0]['entity_id'], 'billing.py::invoice_total')
        self.assertTrue(math.isfinite(result['results'][0]['score']))
        self.assertNotIn('vector', json.dumps(result))

    def test_fusion_keeps_verified_exact_ahead_of_embedding_candidates(self):
        self.refresh()
        dense = self.query('invoice')
        result = retrieval.search(self.lexical, 'invoice', anchors=[{'entity_id': 'sessions.py::revoke_session'}],
                                  limit=10, embedding_result=dense)
        self.assertEqual(result['results'][0]['entity_id'], 'sessions.py::revoke_session')
        self.assertEqual(result['capabilities']['embedding'], 'available')
        self.assertIn('embedding', next(r for r in result['results'] if r['entity_id'] == 'billing.py::invoice_total')['provenance'])
        self.assertEqual(result['ranking_policy'], 'exact-rrf75-25-k60-v1')

    def test_stale_embedding_degrades_explicitly_to_identical_lexical_ranking(self):
        self.refresh()
        dense = self.query()
        self.write('sessions.py', 'def revoke_session(key): return 8\n')
        self.resnapshot()
        expected = retrieval.search(self.lexical, 'invoice', anchors=[], limit=10)
        result = retrieval.search(self.lexical, 'invoice', anchors=[], limit=10, embedding_result=dense)
        self.assertEqual(result['results'], expected['results'])
        self.assertEqual(result['capabilities']['embedding'], 'stale')
        self.assertTrue(result['gaps'])

    def test_result_for_another_query_is_rejected(self):
        self.refresh()
        with self.assertRaisesRegex(ValueError, 'query'):
            retrieval.search(self.lexical, 'different', anchors=[], limit=10, embedding_result=self.query())

    def test_outside_inventory_or_duplicate_results_are_rejected(self):
        self.refresh()
        result = self.query()
        for identity in ('outside.py::secret', result['results'][1]['entity_id']):
            bad = copy.deepcopy(result)
            bad['results'][0]['entity_id'] = identity
            with self.subTest(identity=identity), self.assertRaisesRegex(ValueError, 'embedding'):
                retrieval.search(self.lexical, 'invoice', anchors=[], limit=10, embedding_result=bad)

    def test_stale_artifact_cannot_supply_results_after_index_replacement(self):
        self.refresh()
        result = self.query()
        with closing(sqlite3.connect(self.index)) as db, db:
            db.execute("UPDATE metadata SET value=value||' '")
        plain = retrieval.search(self.lexical, 'invoice', anchors=[], limit=10)
        answer = retrieval.search(self.lexical, 'invoice', anchors=[], limit=10, embedding_result=result)
        self.assertEqual(answer['results'], plain['results'])
        self.assertEqual(answer['capabilities']['embedding'], 'stale')

    def fake_model(self, folder):
        (folder / 'onnx').mkdir(parents=True)
        (folder / worker.GRAPH).write_bytes(b'wrong graph')
        (folder / worker.GRAPH_DATA).write_bytes(b'wrong weights')
        (folder / 'tokenizer.json').write_text('{}', encoding='utf8')

    def test_offline_provider_requires_pinned_local_artifacts_before_importing_runtime(self):
        missing = self.root / 'missing-model'
        with self.assertRaisesRegex(ValueError, 'local model'):
            worker.GemmaProvider(missing)
        self.fake_model(missing)
        with self.assertRaisesRegex(ValueError, 'digest'):
            worker.GemmaProvider(missing)

    def test_documents_and_queries_carry_their_own_prefix_and_the_prefix_binds_the_cache(self):
        self.provider.document_prefix, self.provider.query_prefix = 'doc: ', 'ask: '
        self.refresh()
        self.assertTrue(self.provider.encoded and all(t.startswith('doc: ') for t in self.provider.encoded))
        self.provider.encoded.clear()
        self.query('invoice')
        self.assertEqual(self.provider.encoded, ['ask: invoice'])
        self.provider.document_prefix = 'other: '
        changed = self.refresh()
        self.assertEqual((changed['encoded'], changed['reused']), (4, 0))

    def test_invalid_query_limits_do_not_run_encoder(self):
        self.refresh()
        for query, limit in [(None, 10), ('x' * 16385, 10), ('x', True), ('x', 0), ('x', 1001)]:
            before = len(self.provider.encoded)
            with self.subTest(query=str(query)[:5], limit=limit), self.assertRaises(ValueError):
                worker.search(self.manifest, self.index, query, provider=self.provider, limit=limit)
            self.assertEqual(len(self.provider.encoded), before)

    def test_cli_report_cannot_replace_json_manifest_or_lexical_store(self):
        manifest = self.manifest.with_suffix('.json')
        snapshot.write_snapshot(self.root, manifest, format='json')
        request = self.manifest.with_name('request.json')
        request.write_text(json.dumps({'schema': 'daodan/embedding-request/v1', 'operation': 'index',
            'manifest': str(manifest), 'index': str(self.index), 'model_dir': 'missing'}), encoding='utf8')
        before = manifest.read_bytes()
        with mock.patch.object(worker, 'GemmaProvider', return_value=self.provider):
            self.assertEqual(worker.main(['--request', str(request), '--report-out', str(manifest)]), 1)
        self.assertEqual(manifest.read_bytes(), before)

    def test_process_provider_reports_missing_model_and_cleans_owned_scratch(self):
        with self.assertRaisesRegex(ValueError, 'local model'):
            with worker.ProcessProvider(sys.executable, self.root / 'missing', self.manifest.parent):
                self.fail('missing weights cannot start a provider')
        self.assertFalse(list(self.manifest.parent.glob('.embedding-runtime-*')))

    def test_omitted_model_path_reads_the_shared_system_cache(self):
        for system, vendor in [('Windows', 'Daodan'), ('Linux', 'daodan')]:
            with self.subTest(system=system):
                self.fake_model(self.root / system / vendor / 'models' / worker.MODEL_NAME / worker.MODEL_REVISION)
                with mock.patch.object(worker.platform, 'system', return_value=system), mock.patch.dict(
                    os.environ, {'LOCALAPPDATA': str(self.root / system), 'XDG_CACHE_HOME': str(self.root / system)}):
                    with self.assertRaisesRegex(ValueError, 'digest'):
                        worker.GemmaProvider()

    def test_cli_report_never_overwrites_another_existing_json_artifact(self):
        request = self.manifest.with_name('index-request.json')
        request.write_text(json.dumps({'schema': 'daodan/embedding-request/v1', 'operation': 'index',
            'manifest': str(self.manifest), 'index': str(self.index), 'model_dir': 'unused'}), encoding='utf8')
        evidence = self.manifest.with_name('query-request.json')
        evidence.write_text('{"schema":"independent-request","query":"keep this"}', encoding='utf8')
        before = evidence.read_bytes()
        with mock.patch.object(worker, 'ProcessProvider', return_value=nullcontext(self.provider)):
            status = worker.main(['--request', str(request), '--report-out', str(evidence)])
        self.assertEqual(status, 1)
        self.assertEqual(evidence.read_bytes(), before)

    def test_query_receipt_rejects_relabeling_or_reordering_valid_inventory_rows(self):
        self.refresh()
        original = self.query('invoice')
        for mutation in ('query', 'order'):
            bad = copy.deepcopy(original)
            query = 'invoice'
            if mutation == 'query':
                query = 'revoke'
                bad['query_digest'] = hashlib.sha256(query.encode()).hexdigest()
            else:
                bad['results'].reverse()
                for rank, row in enumerate(bad['results']):
                    row['rank'] = rank
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'receipt'):
                retrieval.search(self.lexical, query, anchors=[], limit=10, embedding_result=bad)


if __name__ == '__main__':
    unittest.main()
