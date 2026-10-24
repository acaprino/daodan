"""Validated decision JSONL and the upstream-compatible marker serialization."""
import hashlib
import json
import math
from pathlib import Path

import torch
from torch.utils.data import Dataset

QTYPES = {'choice': 0, 'score': 1, 'noul': 2}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_row(row, line):
    prefix = f'JSONL line {line}: '
    if not isinstance(row, dict):
        raise ValueError(prefix + 'request must be a JSON object')
    if not isinstance(row.get('state'), (str, dict, list)) or not isinstance(row.get('question'), str):
        raise ValueError(prefix + 'state must be text/JSON and question must be text')
    options = row.get('options')
    if not isinstance(options, list) or not 2 <= len(options) <= 20 or not all(isinstance(x, str) and x for x in options):
        raise ValueError(prefix + 'options must contain 2–20 nonempty rendered descriptions')
    if row.get('type', 'choice') not in QTYPES:
        raise ValueError(prefix + 'type must be choice, score, or noul')
    if row.get('type') == 'noul' and len(options) != 2:
        raise ValueError(prefix + 'noul options must be ordered [false, true]')
    if 'target' in row and (type(row['target']) is not int or not 0 <= row['target'] < len(options)):
        raise ValueError(prefix + 'target must index the supplied option list')
    teacher = row.get('teacher_logits')
    if teacher is not None and (
        not isinstance(teacher, list)
        or len(teacher) != len(options)
        or not all(type(x) in (int, float) and math.isfinite(x) for x in teacher)
    ):
        raise ValueError(prefix + 'teacher logits must be finite and match option count/order')


class Decisions(Dataset):
    def __init__(self, path, require_target=True, require_teacher=False):
        self.rows = []
        with open(path) as stream:
            for line, text in enumerate(stream, 1):
                if not text.strip():
                    continue
                try:
                    row = json.loads(text)
                except json.JSONDecodeError as error:
                    raise ValueError(f'{path}:{line}: invalid JSON: {error.msg}') from error
                validate_row(row, line)
                if require_target and 'target' not in row:
                    raise ValueError(f'{path}:{line}: training requires target')
                if require_teacher and 'teacher_logits' not in row:
                    raise ValueError(f'{path}:{line}: distillation requires teacher_logits')
                self.rows.append(row)
        if not self.rows:
            raise ValueError(f'{path}: dataset contains no rows')
        flags = {'teacher_logits' in row for row in self.rows}
        if len(flags) != 1:
            raise ValueError('Dataset mixes rows with and without teacher logits')

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        return self.rows[index]


def sequence(tokenizer, row, max_length=8192, head_length=256, *, strict=False):
    if head_length + 4 >= max_length:
        raise ValueError('max_length must leave room beyond the question head')
    if any(x is None for x in (tokenizer.mask_token_id, tokenizer.cls_token_id, tokenizer.sep_token_id)):
        raise ValueError('Tokenizer must define MASK, CLS and SEP IDs')
    state = row['state'] if isinstance(row['state'], str) else json.dumps(row['state'], ensure_ascii=False)
    if strict and any(tokenizer.mask_token in text for text in [state, row['question'], *row['options']]):
        raise ValueError('Reserved model marker in request')
    clean = lambda text: text.replace(tokenizer.mask_token, ' ')
    encode = lambda text: tokenizer(text, add_special_tokens=False)['input_ids']
    head = encode(f"{row.get('type', 'choice')} question: {clean(row['question'])}")
    option_ids = [encode(' ' + clean(x)) for x in row['options']]
    if strict and any(len(x) > 48 for x in option_ids):
        raise ValueError('Option exceeds 48-token model contract')
    options = [[tokenizer.mask_token_id] + x[:48] for x in option_ids]
    budget = head_length - sum(map(len, options))
    if budget < 16:
        per_option = max(4, (head_length - 16) // len(options))
        options = [x[:per_option] for x in options]
        budget = head_length - sum(map(len, options))
    if strict and (len(head) > budget or any(len(x) != len(y) + 1 for x, y in zip(options, option_ids))):
        raise ValueError('Question/options exceed lossless head budget')
    ids = [tokenizer.cls_token_id] + head[:max(8, budget)] + [tokenizer.sep_token_id]
    markers = []
    for option in options:
        markers.append(len(ids))
        ids.extend(option)
    ids.append(tokenizer.sep_token_id)
    state_ids = encode(clean(state))
    room = max_length - len(ids) - 1
    if room < 1:
        raise ValueError('Question/options exceed sequence budget; shorten descriptions')
    if strict and len(state_ids) > room:
        raise ValueError('Game state exceeds lossless context budget')
    result = dict(ids=ids + state_ids[:room] + [tokenizer.sep_token_id], markers=markers,
                  qtype=QTYPES[row.get('type', 'choice')], truncated=len(state_ids) > room)
    if strict:
        result['option_tokens'] = list(map(len, option_ids))
    return result


class Collator:
    def __init__(self, tokenizer, max_length=8192, head_length=256):
        self.tokenizer, self.max_length, self.head_length = tokenizer, max_length, head_length

    def __call__(self, rows, *, include_targets=True):
        encoded = [row['_encoded'] if '_encoded' in row else sequence(
            self.tokenizer, row, self.max_length, self.head_length) for row in rows]
        length = min(self.max_length, ((max(len(x['ids']) for x in encoded) + 7) // 8) * 8)
        count = max(len(x['markers']) for x in encoded)
        ids = torch.full((len(rows), length), self.tokenizer.pad_token_id, dtype=torch.long)
        attention = torch.zeros_like(ids)
        positions = torch.zeros((len(rows), count), dtype=torch.long)
        mask = torch.zeros_like(positions, dtype=torch.bool)
        has_teacher = include_targets and all('teacher_logits' in row for row in rows)
        teacher = torch.zeros_like(positions, dtype=torch.float32) if has_teacher else None
        for i, (row, item) in enumerate(zip(rows, encoded)):
            n, k = len(item['ids']), len(item['markers'])
            ids[i, :n] = torch.tensor(item['ids'])
            attention[i, :n] = 1
            positions[i, :k] = torch.tensor(item['markers'])
            mask[i, :k] = True
            if has_teacher:
                teacher[i, :k] = torch.tensor(row['teacher_logits'])
        batch = dict(input_ids=ids, attention_mask=attention, marker_pos=positions,
                     marker_mask=mask, qtype=torch.tensor([x['qtype'] for x in encoded]))
        if include_targets and all('target' in row for row in rows):
            batch['labels'] = torch.tensor([row['target'] for row in rows])
        if has_teacher:
            batch['teacher_logits'] = teacher
        return batch
