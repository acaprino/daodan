# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy==2.4.6", "onnxruntime==1.31.0", "tokenizers==0.23.3"]
# ///
"""Optional offline embeddings. Importing this module needs only the standard library.

Use an explicitly prepared local model. Neither indexing nor queries download
weights, install packages, import project code or call a language model service.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sqlite3
import struct
import subprocess
import sys
import tempfile
import time

BACKEND_MODE = __name__ == '__main__' and sys.argv[1:] == ['--encode-stdio']
if not BACKEND_MODE:
    import confinement
    import retrieval
    from snapshot_store import open_snapshot, artifact_digest

SCHEMA = 'daodan/embedding-index/v1'
RESULT_SCHEMA = 'daodan/embedding-result/v1'
RESULT_FIELDS = frozenset({'schema', 'binding', 'document_digest', 'provider_digest', 'index',
                          'artifact_digest', 'query_digest', 'results', 'matched', 'returned', 'truncated'})
DOCUMENT_SCHEMA = 'path-name-signature-source-v1'
MODEL_NAME = 'EmbeddingGemma2'
MODEL_REVISION = 'daa72c51243991dfcaf9f9137d2c573d8f7790c0'
GRAPH = 'onnx/model_q4.onnx'
GRAPH_DATA = 'onnx/model_q4.onnx_data'
MODEL_SHA256 = 'f9eeba97acddf139b8ee2ddf04bc30dceafa88de93fadf74d7644e0d61a477a9'
MODEL_DATA_SHA256 = 'c3975f2d1ab7a1878ae31a7d7a9b7804a827aff3800b60dfceafce21cac3df49'
MODEL_DATA_BYTES = 174028800
TOKENIZER_SHA256 = '4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4'
DOCUMENT_PREFIX = 'title: none | text: '
QUERY_PREFIX = 'task: code retrieval | query: '
MAX_TOKENS = 2048
DIMENSIONS = 768


def default_model_dir():
    """One read-only model location per user/revision, shared across projects."""
    windows = platform.system() == 'Windows'
    fallback = Path.home() / ('AppData/Local' if windows else '.cache')
    base = Path(os.environ.get('LOCALAPPDATA' if windows else 'XDG_CACHE_HOME') or fallback)
    if not base.is_absolute():
        raise ValueError('shared model cache must be an absolute path')
    return base / ('Daodan' if windows else 'daodan') / 'models' / MODEL_NAME / MODEL_REVISION


class StaleEmbedding(ValueError):
    """A once-valid generation is no longer usable; lexical retrieval can continue."""


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _publish_json(path, value, *, reuse_identical=False):
    """Atomically publish new evidence without replacing any existing bytes."""
    path = Path(path)
    payload = (retrieval._json(value) + '\n').encode('utf8')
    confinement.reject_link_chain(path)
    if path.exists():
        if reuse_identical and path.read_bytes() == payload:
            return
        raise ValueError('embedding output already exists; choose a new report path')
    descriptor, name = tempfile.mkstemp(prefix='.embedding-json-', suffix='.tmp', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(payload)
        confinement.reject_link_chain(path)
        try:
            # Same-directory hard-link publication is atomic and cannot clobber
            # a destination created after the initial ownership check.
            os.link(temporary, path)
        except FileExistsError:
            confinement.reject_link_chain(path)
            if not reuse_identical or path.read_bytes() != payload:
                raise ValueError('embedding output collision; existing evidence preserved')
    finally:
        temporary.unlink()


def _profile(provider):
    profile = json.loads(retrieval._json(provider.profile))
    required = {'provider', 'model_revision', 'model_sha256', 'tokenizer_sha256',
                'runtime', 'encoder_version', 'dimensions', 'max_tokens'}
    if (not required <= profile.keys() or type(profile['dimensions']) is not int
            or not 1 <= profile['dimensions'] <= 8192 or not profile['runtime']
            or type(profile['max_tokens']) is not int or profile['max_tokens'] < 1):
        raise ValueError('invalid embedding provider profile')
    for name in ('model_sha256', 'tokenizer_sha256'):
        value = profile[name]
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('invalid embedding provider digest')
    return {**profile, 'document_schema': DOCUMENT_SCHEMA,
            'document_prefix': getattr(provider, 'document_prefix', ''),
            'query_prefix': getattr(provider, 'query_prefix', '')}


def _destination(manifest, index):
    manifest, index = retrieval._destination(manifest, index)
    if index.name in {'cards.sqlite', 'retrieval.sqlite', 'engine-edges.sqlite'}:
        raise ValueError('embedding destination would replace another evidence store')
    return manifest, index


def _inputs(store):
    docs = list(retrieval._documents(store))
    texts = {identity: '\n'.join((doc['path'], doc['name'], doc['signature'], doc['body']))
             for identity, doc, _ in docs}
    members = {identity: _sha(text.encode('utf8')) for identity, text in texts.items()}
    return texts, members, retrieval._digest(sorted((key, digest) for key, _, digest in docs))


def _pack(vector, dimensions):
    if len(vector) != dimensions or any(type(x) not in (int, float) or not math.isfinite(x) for x in vector):
        raise ValueError('invalid embedding vector dimensions or values')
    norm = math.sqrt(math.fsum(x * x for x in vector))
    if not math.isfinite(norm) or norm <= 0:
        raise ValueError('embedding vector has no finite nonzero norm')
    return struct.pack('<' + 'f' * dimensions, *(x / norm for x in vector))


def _unpack(payload, dimensions, digest):
    if len(payload) != dimensions * 4 or _sha(payload) != digest:
        raise ValueError('embedding vector digest or dimensions differ')
    vector = struct.unpack('<' + 'f' * dimensions, payload)
    norm = math.fsum(x * x for x in vector)
    if any(not math.isfinite(x) for x in vector) or abs(norm - 1) > 1e-5:
        raise ValueError('embedding vector is not finite and normalized')
    return vector


def _load(index):
    confinement.reject_link_chain(index)
    with closing(retrieval._read(index)) as db:
        try:
            metadata = json.loads(db.execute('SELECT value FROM metadata').fetchone()[0])
            if metadata.get('schema') != SCHEMA:
                raise ValueError('incompatible embedding index schema')
            members = dict(db.execute('SELECT entity_id,input_digest FROM documents'))
            vectors = {}
            for digest, payload, checksum in db.execute('SELECT input_digest,vector,checksum FROM vectors'):
                _unpack(payload, metadata['provider']['dimensions'], checksum)
                vectors[digest] = payload
            if (set(members.values()) != set(vectors) or len(members) != metadata['documents']
                    or retrieval._digest(sorted(members.items())) != metadata['inventory_digest']):
                raise ValueError('embedding inventory differs from its generation')
        except (KeyError, TypeError, IndexError, sqlite3.DatabaseError) as error:
            raise ValueError('invalid embedding index; preserve it and rebuild separately') from error
    return metadata, members, vectors


def refresh_index(manifest: Path, index: Path, *, provider) -> dict:
    """Publish a complete generation atomically; reuse only exact encoded inputs."""
    manifest, index = _destination(manifest, index)
    profile = _profile(provider)
    lock = index.with_name(index.name + '.lock')
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    temporary = None
    started = time.perf_counter()
    try:
        with open_snapshot(manifest) as store:
            retrieval._verify_tree(store)
            binding = retrieval._binding(store)
            manifest_before = artifact_digest(manifest)
            before = artifact_digest(index) if index.exists() else None
            texts, members, documents_digest = _inputs(store)
            old_members, cached = {}, {}
            if before:
                old, old_members, old_vectors = _load(index)
                if old['provider'] == profile:
                    cached = old_vectors
            pending = {members[key]: text for key, text in texts.items() if members[key] not in cached}
            vectors = {digest: cached[digest] for digest in set(members.values()) & cached.keys()}
            # Bound encoder batches and discard partial work on failure. A prior
            # complete generation remains available throughout the operation.
            items = sorted(pending.items())
            prefix = getattr(provider, 'document_prefix', '')
            for start in range(0, len(items), 16):
                batch = items[start:start + 16]
                encoded = provider.encode([prefix + text for _, text in batch])
                if len(encoded) != len(batch):
                    raise ValueError('embedding encoder returned the wrong number of vectors')
                for (digest, _), vector in zip(batch, encoded):
                    vectors[digest] = _pack(vector, profile['dimensions'])
            metadata = {'schema': SCHEMA, 'binding': binding, 'provider': profile,
                        'document_digest': documents_digest, 'documents': len(members),
                        'inventory_digest': retrieval._digest(sorted(members.items()))}
            descriptor, name = tempfile.mkstemp(prefix='.embedding-', suffix='.sqlite', dir=index.parent)
            os.close(descriptor)
            temporary = Path(name)
            with closing(sqlite3.connect(temporary)) as db:
                db.execute('CREATE TABLE metadata(value TEXT NOT NULL)')
                db.execute('CREATE TABLE documents(entity_id TEXT PRIMARY KEY,input_digest TEXT NOT NULL)')
                db.execute('CREATE TABLE vectors(input_digest TEXT PRIMARY KEY,vector BLOB NOT NULL,checksum TEXT NOT NULL)')
                db.execute('INSERT INTO metadata VALUES(?)', (retrieval._json(metadata),))
                db.executemany('INSERT INTO documents VALUES(?,?)', sorted(members.items()))
                db.executemany('INSERT INTO vectors VALUES(?,?,?)', [(key, payload, _sha(payload)) for key, payload in sorted(vectors.items())])
                db.commit()
            _load(temporary)
            retrieval._verify_tree(store)
            if artifact_digest(manifest) != manifest_before:
                raise ValueError('snapshot changed during embedding refresh')
            if (artifact_digest(index) if index.exists() else None) != before:
                raise ValueError('embedding generation changed during refresh')
            confinement.reject_link_chain(index)
            os.replace(temporary, index)
            return {**metadata, 'index': str(index), 'artifact_digest': artifact_digest(index),
                    'encoded': len(pending), 'reused': len(members) - len(pending),
                    'removed': len(old_members.keys() - members.keys()),
                    'seconds': time.perf_counter() - started}
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        lock.unlink()


def search(manifest: Path, index: Path, query: str, *, provider, limit=500) -> dict:
    if not isinstance(query, str) or len(query) > 16384 or type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError('embedding query needs text up to 16384 characters and limit 1..1000')
    manifest, index = _destination(manifest, index)
    before = artifact_digest(index)
    metadata, members, payloads = _load(index)
    if metadata['provider'] != _profile(provider):
        raise StaleEmbedding('embedding provider changed; refresh its generation')
    started = time.perf_counter()
    with open_snapshot(manifest) as store:
        if metadata['binding'] != retrieval._binding(store):
            raise StaleEmbedding('embedding snapshot changed; refresh its generation')
        retrieval._verify_tree(store)
        _, current, documents_digest = _inputs(store)
        if current != members or documents_digest != metadata['document_digest']:
            raise StaleEmbedding('embedding input inventory changed')
        encoded = provider.encode([getattr(provider, 'query_prefix', '') + query])
        if len(encoded) != 1:
            raise ValueError('embedding query returned the wrong number of vectors')
        dimensions = metadata['provider']['dimensions']
        payload = _pack(encoded[0], dimensions)
        query_vector = struct.unpack('<' + 'f' * dimensions, payload)
        scores = {}
        for digest, value in payloads.items():
            vector = struct.unpack('<' + 'f' * dimensions, value)
            scores[digest] = math.fsum(a * b for a, b in zip(query_vector, vector))
        ranked = sorted(members, key=lambda key: (-scores[members[key]], key))
        retrieval._verify_tree(store)
    if artifact_digest(index) != before:
        raise StaleEmbedding('embedding generation changed during query')
    rows = [{'entity_id': key, 'score': scores[members[key]], 'rank': rank}
            for rank, key in enumerate(ranked[:limit])]
    result = {'schema': RESULT_SCHEMA, 'binding': metadata['binding'], 'document_digest': documents_digest,
              'provider_digest': retrieval._digest(metadata['provider']), 'index': str(index),
              'artifact_digest': before, 'query_digest': _sha(query.encode('utf8')),
              'results': rows, 'matched': len(ranked), 'returned': len(rows),
              'truncated': max(0, len(ranked) - limit)}
    receipt = index.parent / ('embedding-query-' + retrieval._digest(result) + '.json')
    _publish_json(receipt, result, reuse_identical=True)
    return {**result, 'receipt': {'path': str(receipt), 'digest': artifact_digest(receipt)},
            'seconds': time.perf_counter() - started}


def validate_result(result, lexical_metadata, query, records):
    """Validate caller-supplied leads against their actual local generation."""
    required = RESULT_FIELDS | {'receipt'}
    if not isinstance(result, dict) or not required <= result.keys() or result['schema'] != RESULT_SCHEMA:
        raise ValueError('invalid embedding result contract')
    if result['query_digest'] != _sha(query.encode('utf8')):
        raise ValueError('embedding result belongs to another query')
    if (result['binding'] != lexical_metadata['binding']
            or result['document_digest'] != lexical_metadata['document_digest']):
        raise StaleEmbedding('embedding snapshot or document generation is stale')
    manifest, index = _destination(lexical_metadata['binding']['manifest'], result['index'])
    if not index.is_file() or artifact_digest(index) != result['artifact_digest']:
        raise StaleEmbedding('embedding artifact changed or is unavailable')
    metadata, members, _ = _load(index)
    if (metadata['binding'] != result['binding'] or metadata['document_digest'] != result['document_digest']
            or retrieval._digest(metadata['provider']) != result['provider_digest'] or set(members) != set(records)):
        raise StaleEmbedding('embedding generation does not match retrieval')
    rows = result['results']
    if (not isinstance(rows, list) or len(rows) > 1000 or result['returned'] != len(rows)
            or result['matched'] != len(members) or result['truncated'] != len(members) - len(rows)):
        raise ValueError('invalid embedding result counts')
    seen = set()
    for rank, row in enumerate(rows):
        if (not isinstance(row, dict) or row.get('entity_id') not in records or row['entity_id'] in seen
                or row.get('rank') != rank or type(row.get('score')) not in (int, float)
                or not math.isfinite(row['score'])):
            raise ValueError('invalid embedding rank or entity outside the inventory')
        seen.add(row['entity_id'])
    receipt = result['receipt']
    if (not isinstance(receipt, dict) or set(receipt) != {'path', 'digest'}
            or not isinstance(receipt['path'], str) or not isinstance(receipt['digest'], str)):
        raise ValueError('invalid embedding query receipt')
    path = Path(receipt['path']).absolute()
    payload = {key: result[key] for key in RESULT_FIELDS}
    expected_name = 'embedding-query-' + retrieval._digest(payload) + '.json'
    if path.parent.resolve() != index.parent.resolve() or path.name != expected_name:
        raise ValueError('embedding query receipt does not bind the supplied query/ranks')
    confinement.reject_link_chain(path)
    if not path.is_file() or artifact_digest(path) != receipt['digest']:
        raise StaleEmbedding('embedding query receipt changed or is unavailable')
    if json.loads(path.read_bytes()) != payload:
        raise ValueError('embedding result differs from its immutable query receipt')
    return rows


def _file_sha(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


class GemmaProvider:
    """Pinned EmbeddingGemma 2 text graph (q4, CPU); local bytes only, no custom model code."""
    document_prefix = DOCUMENT_PREFIX
    query_prefix = QUERY_PREFIX

    def __init__(self, model_dir=None):
        local = Path(model_dir) if model_dir is not None else default_model_dir()
        graph, data, tokenizer_path = local / GRAPH, local / GRAPH_DATA, local / 'tokenizer.json'
        if not graph.is_file() or not data.is_file() or not tokenizer_path.is_file():
            raise ValueError(f'local model is missing at {local}; explicitly prepare the pinned artifacts first')
        if data.stat().st_size != MODEL_DATA_BYTES:
            raise ValueError('local model digest/size differs from pinned EmbeddingGemma 2')
        tokenizer_bytes = tokenizer_path.read_bytes()
        if (_file_sha(graph) != MODEL_SHA256 or _file_sha(data) != MODEL_DATA_SHA256
                or _sha(tokenizer_bytes) != TOKENIZER_SHA256):
            raise ValueError('local model or tokenizer digest differs from pinned EmbeddingGemma 2')
        try:
            import numpy as np
            import onnxruntime as ort
            import tokenizers
        except ImportError as error:
            raise ValueError('optional embedding runtime unavailable; use the isolated script runtime') from error
        self.np = np
        self.tokenizer = tokenizers.Tokenizer.from_str(tokenizer_bytes.decode('utf8'))
        self.tokenizer.no_padding()
        self.tokenizer.enable_truncation(max_length=MAX_TOKENS)
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        options.inter_op_num_threads = 1
        # The weights live in an external data file beside the graph, so the
        # session loads by path; both files were verified just above.
        self.session = ort.InferenceSession(str(graph), sess_options=options, providers=['CPUExecutionProvider'])
        # The exported graph also takes image, video and audio features; text
        # encoding passes them empty.
        self.empty = np.zeros((0, 512), dtype=np.float32)
        self.profile = {'provider': 'embeddinggemma2-onnx-q4', 'model_revision': MODEL_REVISION,
                        'model_sha256': MODEL_SHA256, 'model_data_sha256': MODEL_DATA_SHA256,
                        'tokenizer_sha256': TOKENIZER_SHA256,
                        'encoder_version': 1, 'dimensions': DIMENSIONS, 'max_tokens': MAX_TOKENS,
                        'inference_batch': 1,
                        'runtime': {'python': platform.python_version(), 'platform': platform.system(),
                                    'numpy': np.__version__, 'onnxruntime': ort.__version__,
                                    'tokenizers': tokenizers.__version__, 'device': 'CPU', 'threads': [4, 1]}}

    def encode(self, texts):
        np = self.np
        result = []
        # One input per inference: no padding, and each cached vector depends
        # only on its own text.
        for text in texts:
            ids = np.asarray([self.tokenizer.encode(text).ids], dtype=np.int64)
            pooled = self.session.run(['sentence_embedding'], {
                'input_ids': ids, 'attention_mask': np.ones_like(ids), 'image_features': self.empty,
                'video_features': self.empty, 'audio_features': self.empty})[0]
            result.extend(pooled.astype(float).tolist())
        return result


def _encoding_server():
    """Private machine protocol. Never import map/parser code in this runtime."""
    try:
        initial = json.loads(sys.stdin.readline())
        directory = Path(initial['scratch']).resolve(strict=True)
        provider = GemmaProvider(initial['model_dir'])
        print(json.dumps({'status': 'ready', 'profile': provider.profile}), flush=True)
        for line in sys.stdin:
            request = json.loads(line)
            if request == {'stop': True}:
                break
            texts = request['texts']
            if (not isinstance(texts, list) or not 1 <= len(texts) <= 16
                    or any(not isinstance(text, str) or len(text) > 2_000_000 for text in texts)):
                raise ValueError('invalid bounded encoder batch')
            vectors = provider.encode(texts)
            # The stdout protocol carries only status and counts. Numeric data
            # stays in a parent-owned temporary artifact beside the index.
            output = directory / 'response.json'
            descriptor = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, 'w', encoding='utf8') as handle:
                json.dump(vectors, handle, allow_nan=False)
            print(json.dumps({'status': 'encoded', 'count': len(vectors)}), flush=True)
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), flush=True)
        return 1
    return 0


class ProcessProvider:
    """Keep native inference in an explicitly selected isolated Python process."""
    document_prefix = DOCUMENT_PREFIX
    query_prefix = QUERY_PREFIX

    def __init__(self, python, model_dir, scratch_dir, *, timeout=300):
        self.process = None
        self.timeout = timeout
        self.root = Path(scratch_dir).absolute()
        confinement.reject_link_chain(self.root)
        self.temporary = tempfile.TemporaryDirectory(prefix='.embedding-runtime-', dir=self.root)
        self.directory = Path(self.temporary.name)
        self.errors = (self.directory / 'stderr.log').open('w', encoding='utf8')
        try:
            executable = Path(python).resolve(strict=True)
            script = Path(__file__).resolve()
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
                       HF_HUB_DISABLE_TELEMETRY='1', HF_HUB_DISABLE_IMPLICIT_TOKEN='1')
            self.process = subprocess.Popen([str(executable), '-I', '-B', str(script), '--encode-stdio'],
                cwd=script.parent, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=self.errors, text=True, encoding='utf8')
            model = Path(model_dir) if model_dir is not None else default_model_dir()
            message = self._exchange({'model_dir': str(model.resolve()), 'scratch': str(self.directory)})
            if message.get('status') != 'ready':
                raise ValueError('embedding runtime did not become ready')
            self.profile = message['profile']
            _profile(self)
        except Exception:
            self.close()
            raise

    def _exchange(self, value):
        self.process.stdin.write(json.dumps(value) + '\n')
        self.process.stdin.flush()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.process.stdout.readline)
            try:
                line = future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError as error:
                self.process.kill()
                raise ValueError('embedding runtime timeout') from error
        if not line:
            raise ValueError('embedding runtime stopped before delivering a response')
        message = json.loads(line)
        if message.get('status') == 'failed':
            raise ValueError('embedding runtime: ' + message.get('error', 'unknown failure'))
        return message

    def encode(self, texts):
        message = self._exchange({'texts': texts})
        output = self.directory / 'response.json'
        confinement.reject_link_chain(output)
        try:
            result = json.loads(output.read_text(encoding='utf8'))
            if message.get('status') != 'encoded' or message.get('count') != len(texts) or len(result) != len(texts):
                raise ValueError('embedding runtime returned incomplete output')
            return result
        finally:
            if output.exists():
                output.unlink()

    def close(self):
        if self.process is not None:
            if self.process.poll() is None:
                try:
                    self.process.stdin.write('{"stop":true}\n')
                    self.process.stdin.flush()
                    self.process.wait(timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    self.process.kill()
                    self.process.wait(timeout=5)
            self.process.stdin.close()
            self.process.stdout.close()
            self.process = None
        self.errors.close()
        # TemporaryDirectory recursively removes only this validated owned child.
        if self.directory.parent.resolve() != self.root.resolve():
            raise ValueError('embedding scratch directory escaped its owner')
        confinement.reject_link_chain(self.directory)
        self.temporary.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--report-out', type=Path, required=True)
    parser.add_argument('--runtime-python', type=Path, default=Path(sys.executable))
    args = parser.parse_args(argv)
    try:
        request = json.loads(args.request.read_text(encoding='utf8'))
        if (not isinstance(request, dict) or request.get('schema') != 'daodan/embedding-request/v1' or request.get('operation') not in ('index', 'query')
                or set(request) - {'schema', 'operation', 'manifest', 'index', 'model_dir', 'query', 'limit'}):
            raise ValueError('unknown embedding request schema, operation or fields')
        manifest, index = _destination(request['manifest'], request['index'])
        output = args.report_out.absolute()
        confinement.reject_link_chain(output)
        if (output.parent.resolve() != manifest.parent.resolve() or output.suffix != '.json'
                or output.resolve() in {manifest.resolve(), index.resolve(), args.request.resolve()}):
            raise ValueError('embedding report must be a separate JSON beside its manifest')
        if output.exists():
            raise ValueError('embedding output already exists; choose a new report path')
        with ProcessProvider(args.runtime_python, request.get('model_dir'), manifest.parent) as provider:
            if request['operation'] == 'index':
                result = refresh_index(manifest, index, provider=provider)
            else:
                result = search(manifest, index, request['query'], provider=provider, limit=request.get('limit', 500))
        _publish_json(output, result)
        print(json.dumps({'status': 'complete', 'operation': request['operation'], 'report': str(output),
                          'artifact_digest': result['artifact_digest'],
                          'documents': result.get('documents', result.get('matched')), 'returned': result.get('returned')}))
        return 0
    except (ValueError, KeyError, OSError, sqlite3.DatabaseError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(_encoding_server() if BACKEND_MODE else main())
