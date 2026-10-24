"""Resident CUDA inference for native Julia and CUDA INT8 checkpoints."""
import json
from pathlib import Path
import torch
from safetensors.torch import load_file
from .cuda import configure, move
from .data import Collator, validate_row
from .probabilities import display_probabilities


def context_length(checkpoint, requested):
    config = json.loads((Path(checkpoint) / 'encoder/config.json').read_text())
    limit = config['max_position_embeddings']
    value = limit if requested is None else requested
    if type(value) is not int or not 1 <= value <= limit:
        raise ValueError(f'max_length must be an integer between 1 and {limit}')
    return value


class TransformerEngine:
    def __init__(self, checkpoint, device='cuda', max_length=None, head_length=256, *, memory_map=True):
        from transformers import AutoModel, AutoTokenizer
        from .model import JuliaDecisionModel
        self.device = configure(device)
        root = Path(checkpoint)
        max_length = context_length(root, max_length)
        if (root / 'INCOMPLETE').exists():
            raise ValueError('Refusing to load an incomplete INT8 export')
        self.tokenizer = AutoTokenizer.from_pretrained(root / 'tokenizer', trust_remote_code=False)
        if (root / 'quantization.json').exists():
            if self.device.type != 'cuda':
                raise ValueError('This INT8 checkpoint requires CUDA')
            encoder = AutoModel.from_pretrained(root / 'encoder', device_map={'': self.device.index or 0},
                        attn_implementation='sdpa', trust_remote_code=False)
            config = json.loads((root / 'julia_config.json').read_text())
            self.model = JuliaDecisionModel(encoder, **{k: config[k] for k in ('head_layers', 'n_act', 'dropout')})
            heads = load_file(str(root / 'heads.safetensors'))
            expected = {k for k in self.model.state_dict() if not k.startswith('encoder.')}
            if set(heads) != expected:
                raise ValueError('INT8 decision-head tensor keys do not match checkpoint architecture')
            self.model.load_state_dict(heads, strict=False)
            for name, child in self.model.named_children():
                if name != 'encoder':
                    child.to(self.device)
        else:
            self.model = JuliaDecisionModel.from_pretrained(root, memory_map=memory_map).to(self.device)
        self.model.eval()
        self.collate = Collator(self.tokenizer, max_length, head_length)

    @torch.inference_mode()
    def logits(self, rows):
        if not rows:
            return []
        for i, row in enumerate(rows):
            validate_row(row, i + 1)
        batch = move(self.collate(rows, include_targets=False), self.device)
        with torch.autocast(device_type=self.device.type, dtype=torch.bfloat16, enabled=self.device.type == 'cuda'):
            logits = self.model(**batch)
        logits = logits.cpu()
        if not torch.isfinite(logits).all():
            raise FloatingPointError('Inference returned nonfinite logits')
        return [values[:len(row['options'])].tolist() for values, row in zip(logits, rows)]

    def predict(self, rows=None, questions=None, *, state=None):
        if questions is not None:
            from .typed import predict_typed
            if rows is not None and state is not None:
                raise ValueError('Pass state either positionally or by keyword, not both')
            return predict_typed(self, state if rows is None else rows, questions)
        if state is not None or rows is None:
            raise ValueError('Provide legacy rows or state with questions')
        result = []
        for values in self.logits(rows):
            probabilities = torch.tensor(values).softmax(-1)
            result.append(dict(index=int(probabilities.argmax()),
                               probabilities=display_probabilities(probabilities.tolist())))
        return result


def load_model(checkpoint, device='cpu', max_length=None, head_length=256, *, backend=None, **kwargs):
    """Load a Julia checkpoint through the supported resident inference runtime."""
    from .router.engine import FastEngine
    if checkpoint is None:
        raise ValueError('checkpoint is required; pass a local model directory')
    if backend not in (None, 'torch', 'bend', 'bend-dense'):
        raise ValueError('backend must be torch, bend, or bend-dense')
    return FastEngine(checkpoint, device, max_length, head_length,
                      transformer_backend=backend, **kwargs)


Engine = load_model  # Backward compatible entry point.
