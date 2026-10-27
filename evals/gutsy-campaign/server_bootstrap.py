"""Official HTTP service with an explicit experimental full-reencoding arm."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--cache-mode', choices=['full', 'intra', 'lru'], required=True)
    parser.add_argument('--requests', required=True)
    parser.add_argument('--preflight', required=True)
    parser.add_argument('--token-cache', required=True)
    args = parser.parse_args()
    from gutsy_inference.engine import Calibration, Engine
    from gutsy_inference.prompt import prefix, suffix
    from gutsy_inference.registry import Registry
    from gutsy_inference.schema import parse_request
    from gutsy_inference.server import serve

    registry = Registry(args.config)
    if args.cache_mode == 'full':
        # The public CLI cannot select use_cache=False. Keep this adaptation
        # visible, restricted to construction, and compare against official path.
        name = registry.default
        spec = registry.models[name]
        calibration = registry._resolve(spec['calibration'])
        engine = Engine(registry.backend_factory(spec), Calibration.load(calibration),
                        name=name, cache_entries=0, cache_bytes=0,
                        use_cache=False, reject_slot=True)
        engine.self_check(tol=float(spec['cache_tol']))
        registry.engines[name] = engine
    else:
        engine = registry.get()
    request_bytes = Path(args.requests).read_bytes()
    request_hash = hashlib.sha256(request_bytes).hexdigest()
    cache_path = Path(args.token_cache)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    cache_matches = (cache.get('request_hash') == request_hash and
                     cache.get('gguf') == str(registry._resolve(registry.models[registry.default]['gguf'])))
    token_rows = cache['requests'] if cache_matches else {}
    for request in ([] if cache_matches else json.loads(request_bytes)):
        state, questions, _ = parse_request(request['body'])
        pre = prefix(state)
        lengths = {}
        for question in questions:
            # Core and stress questions never exceed 16 choice options. Noul
            # catalog stress uses independent questions, not recursive shortlist.
            if len(question.options) > 16:
                raise ValueError('Campaign preflight does not claim shortlist token coverage')
            prompt = pre + suffix(question.text, question.options,
                                  engine.reject_slot and question.qtype in {'choice', 'score'})
            lengths[question.qid] = len(engine.backend.tokenize(prompt, bos=True))
        token_rows[request['id']] = {'max_prompt_tokens': max(lengths.values()),
                                     'question_prompt_tokens': lengths,
                                     'state_tokens': len(engine.backend.tokenize(pre, bos=True))}
    if not cache_matches:
        cache_path.write_text(json.dumps({'request_hash': request_hash, 'requests': token_rows,
                                         'gguf': str(registry._resolve(registry.models[registry.default]['gguf']))}),
                              encoding='utf-8')
    output = {'requests': token_rows, 'cache_mode': args.cache_mode,
              'token_cache_hit': cache_matches,
              'cache_enabled': engine.cache_enabled,
              'self_check': engine.self_check_result,
              'experimental_constructor': args.cache_mode == 'full'}
    Path(args.preflight).write_text(json.dumps(output, ensure_ascii=False), encoding='utf-8')
    serve(registry, host='127.0.0.1', port=args.port, preload=False, quiet=True)


if __name__ == '__main__':
    main()
