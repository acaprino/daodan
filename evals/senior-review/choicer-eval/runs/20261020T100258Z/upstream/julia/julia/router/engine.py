"""Resident CPU/CUDA inference with cached encoding and length-aware batches."""
from collections import OrderedDict
import json
from pathlib import Path
import threading

import numpy as np
import torch

from ..data import sequence, validate_row
from ..probabilities import display_probabilities
from ..inference import TransformerEngine as Engine


class _TokenCache:
    def __init__(self, tokenizer, capacity):
        self.tokenizer, self.capacity = tokenizer, capacity
        self.cache = OrderedDict()

    def __getattr__(self, name):
        return getattr(self.tokenizer, name)

    def __call__(self, text, add_special_tokens=False):
        if text not in self.cache:
            ids = self.tokenizer(text, add_special_tokens=False)['input_ids']
            if self.capacity:
                self.cache[text] = tuple(ids)
                while len(self.cache) > self.capacity:
                    self.cache.popitem(last=False)
            return {'input_ids': ids}
        self.cache.move_to_end(text)
        return {'input_ids': list(self.cache[text])}


class FastEngine(Engine):
    """Same weights/serialization as Engine; no cached model predictions.

    Optional torch.compile specializes the transformer, while Bend handles CPU
    softmax/selection via ctypes. CUDA softmax stays on-device to avoid a roundtrip.
    """
    def __init__(self, checkpoint, device='cpu', max_length=None, head_length=256,
                 batch_size=16, encoding_cache=2048, token_cache=8192,
                 compile_model=False, library=None, bend_postprocess=False, transformer_backend=None,
                 strict_encoding=False, marker_only_head=None, memory_map=True, padding_ratio=1.25):
        if not 1 <= padding_ratio <= 16:
            raise ValueError('padding_ratio must be between 1 and 16')
        self.padding_ratio = padding_ratio
        if batch_size < 1 or encoding_cache < 0 or token_cache < 0:
            raise ValueError('Invalid batch/cache size')
        if transformer_backend not in (None, 'torch', 'bend', 'bend-dense'):
            raise ValueError('transformer_backend must be torch, bend, or bend-dense')
        if transformer_backend in ('bend', 'bend-dense') and (str(device) != 'cpu' or compile_model):
            raise ValueError('Bend requires eager CPU inference; compilation requires the torch backend')
        weights = Path(checkpoint) / 'model.safetensors'
        if weights.is_file():
            with weights.open('rb') as stream:
                if stream.read(80).startswith(b'version https://git-lfs.github.com/spec/v1'):
                    raise ValueError('Checkpoint contains Git LFS pointers; fetch the real model weights first')
        super().__init__(checkpoint, device, max_length, head_length, memory_map=memory_map)
        self.model.marker_only_head = (self.device.type == 'cpu' if marker_only_head is None else marker_only_head)
        self.strict_encoding = strict_encoding
        self.batch_size = batch_size
        max_length = self.collate.max_length
        self.max_length, self.head_length = max_length, head_length
        self.encoding_cache = encoding_cache
        self._encoded = OrderedDict()
        self._tokens = _TokenCache(self.tokenizer, token_cache)
        self._lock = threading.RLock()
        self.bend = None
        if bend_postprocess and self.device.type == 'cpu':
            from .native import BendReducer
            self.bend = BendReducer(library)
        if transformer_backend is None:
            transformer_backend = 'torch'
        self.transformer_backend = transformer_backend
        if transformer_backend in ('bend', 'bend-dense'):
            if next(self.model.parameters()).dtype != torch.float32:
                raise ValueError('Bend backends require FP32 weights')
            from .native import BendReducer
            from .transformer import install_bend_head
            reducer = self.bend or BendReducer(library)
            if transformer_backend == 'bend':
                install_bend_head(self.model, reducer)
            if transformer_backend == 'bend-dense':
                from .transformer import install_bend_encoder
                self.bend_projection_count = install_bend_encoder(self.model, reducer)
        from .encoder import specialize_decision_encoder
        self.encoder_specialized = specialize_decision_encoder(self.model)
        self.forward = self.model
        if compile_model:
            self.forward = torch.compile(self.model, dynamic=True)

    def clear_cache(self):
        with self._lock:
            self._encoded.clear()
            self._tokens.cache.clear()

    def _encode(self, rows):
        result = []
        for i, row in enumerate(rows):
            validate_row(row, i + 1)
            key = json.dumps([self.max_length, self.head_length, self.strict_encoding,
                              row['state'], row['question'], row['options'],
                              row.get('type', 'choice')], ensure_ascii=False, allow_nan=False)
            encoded = self._encoded.get(key)
            if encoded is None:
                encoded = sequence(self._tokens, row, self.max_length, self.head_length,
                                   strict=self.strict_encoding)
                if self.encoding_cache:
                    self._encoded[key] = encoded
                    while len(self._encoded) > self.encoding_cache:
                        self._encoded.popitem(last=False)
            else:
                self._encoded.move_to_end(key)
            result.append(encoded)
        return result

    def encoding_info(self, rows):
        """Audit the same cached encoding used by inference, without retokenizing."""
        if not self.strict_encoding:
            raise ValueError('Lossless encoding audit requires strict_encoding=True')
        with self._lock:
            return [dict(tokens=len(item['ids']), optionTokens=list(item['option_tokens']),
                         headLength=self.head_length, stateTruncated=False, optionsTruncated=False)
                    for item in self._encode(rows)]

    def _pack(self, encoded):
        length = min(self.max_length, (max(len(x['ids']) for x in encoded) + 7) // 8 * 8)
        count = max(len(x['markers']) for x in encoded)
        size = len(encoded)
        arena = np.zeros(size * (2 * length + count + 1), dtype=np.int64)
        end = size * length
        ids = arena[:end].reshape(size, length)
        ids.fill(self.tokenizer.pad_token_id)
        attention = arena[end:2 * end].reshape(size, length)
        positions = arena[2 * end:2 * end + size * count].reshape(size, count)
        qtype = arena[-size:]
        mask = np.zeros((size, count), dtype=np.bool_)
        for i, item in enumerate(encoded):
            n, k = len(item['ids']), len(item['markers'])
            ids[i, :n] = item['ids']
            attention[i, :n] = 1
            positions[i, :k] = item['markers']
            mask[i, :k] = True
            qtype[i] = item['qtype']
        host = torch.from_numpy(arena)
        marker_mask = torch.from_numpy(mask)
        if self.device.type == 'cuda':
            host = host.pin_memory().to(self.device, non_blocking=True)
            marker_mask = marker_mask.pin_memory().to(self.device, non_blocking=True)
        return dict(input_ids=host[:end].view(size, length),
                    attention_mask=host[end:2 * end].view(size, length),
                    marker_pos=host[2 * end:2 * end + size * count].view(size, count),
                    qtype=host[-size:], marker_mask=marker_mask)

    def _batch_indices(self, encoded):
        # Bound padding inflation, not just batch count: a single long request
        # must not make every short request run the entire encoder at its length.
        order = sorted(range(len(encoded)), key=lambda i: len(encoded[i]['ids']))
        group, tokens = [], 0
        for index in order:
            length = len(encoded[index]['ids'])
            if group and (len(group) == self.batch_size or
                          (len(group) + 1) * length > self.padding_ratio * (tokens + length)):
                yield group
                group, tokens = [], 0
            group.append(index)
            tokens += length
        if group:
            yield group

    def _batches(self, encoded):
        for indices in self._batch_indices(encoded):
            batch = self._pack([encoded[i] for i in indices])
            with torch.autocast(device_type=self.device.type, dtype=torch.bfloat16,
                                enabled=self.device.type == 'cuda'):
                values = self.forward(**batch)
            # Padding must never win against real very negative logits.
            values = values.masked_fill(~batch['marker_mask'], -torch.inf)
            if not (torch.isfinite(values) | ~batch['marker_mask']).all():
                raise FloatingPointError('Inference returned nonfinite logits')
            yield indices, values

    @torch.inference_mode()
    def logits(self, rows):
        with self._lock:
            encoded = self._encode(rows)
            result = [None] * len(rows)
            for indices, values in self._batches(encoded):
                host = values.cpu().tolist()
                for i, scores in zip(indices, host):
                    result[i] = scores[:len(encoded[i]['markers'])]
            return result

    @torch.inference_mode()
    def predict(self, rows=None, questions=None, *, state=None, probabilities=True):
        if questions is not None:
            from ..typed import predict_typed
            if rows is not None and state is not None:
                raise ValueError('Pass state either positionally or by keyword, not both')
            return predict_typed(self, state if rows is None else rows, questions)
        if state is not None or rows is None:
            raise ValueError('Provide legacy rows or state with questions')
        with self._lock:
            encoded = self._encode(rows)
            result = [None] * len(rows)
            for indices, values in self._batches(encoded):
                if self.bend is not None:
                    host = values.contiguous().numpy()
                    for local, i in enumerate(indices):
                        scores = host[local, :len(encoded[i]['markers'])]
                        if probabilities:
                            best, probs = self.bend.softmax(scores)
                        else:
                            best = self.bend.argmax(scores)
                        result[i] = dict(index=best)
                        if probabilities:
                            result[i]['probabilities'] = display_probabilities(probs.tolist())
                else:
                    best_device = values.argmax(-1)
                    if probabilities and self.device.type == 'cuda':
                        host = torch.cat((best_device[:, None].to(values.dtype),
                                          values.softmax(-1)), dim=1).cpu().tolist()
                        best = [int(row[0]) for row in host]
                        probs = [row[1:] for row in host]
                    else:
                        best = best_device.cpu().tolist()
                        probs = values.softmax(-1).tolist() if probabilities else None
                    for local, i in enumerate(indices):
                        result[i] = dict(index=best[local])
                        if probabilities:
                            result[i]['probabilities'] = display_probabilities(probs[local][:len(encoded[i]['markers'])])
            return result
