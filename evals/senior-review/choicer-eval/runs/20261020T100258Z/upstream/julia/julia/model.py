"""Marker based decision model and checkpoint serialization."""
import json
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint
from safetensors.torch import load_file, save_file
from transformers import AutoConfig, AutoModel


class JuliaDecisionModel(nn.Module):
    def __init__(self, encoder, head_layers=2, n_act=2, dropout=.1):
        super().__init__()
        self.encoder = encoder
        width = encoder.config.hidden_size
        self.settings = dict(head_layers=head_layers, n_act=n_act, dropout=dropout)
        layer = nn.TransformerEncoderLayer(width, max(1, width // 64), 4 * width,
                                          dropout, batch_first=True, norm_first=True)
        self.head = nn.TransformerEncoder(layer, head_layers, enable_nested_tensor=False) if head_layers else None
        self.type_emb = nn.Embedding(3, width)
        self.scorer = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, width), nn.GELU(), nn.Linear(width, 1))
        self.act_head = nn.Sequential(nn.Linear(width + 4, 256), nn.GELU(), nn.Linear(256, n_act))
        self.register_buffer('temperature', torch.ones(3))
        self.head_checkpointing = False
        self.marker_only_head = False
        self.encoder.config.reference_compile = False

    @classmethod
    def from_backbone(cls, path, revision=None, head_layers=2):
        encoder = AutoModel.from_pretrained(path, revision=revision, trust_remote_code=False,
                                          attn_implementation='sdpa')
        return cls(encoder, head_layers=head_layers)

    def forward(self, input_ids, attention_mask, marker_pos, marker_mask, qtype, return_actions=False):
        hidden = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        hidden = hidden + self.type_emb(qtype)[:, None, :]
        # Only option positions (and CLS for the action head) are consumed.
        # The final block can keep full K/V context while avoiding unused queries
        # and feed-forward outputs. Training retains the original dropout path.
        selected = marker_pos
        if return_actions:
            selected = torch.cat((torch.zeros_like(marker_pos[:, :1]), marker_pos), dim=1)
        sparse = (self.marker_only_head and not self.training and self.head is not None
                  and len(self.head.layers) > 0
                  and type(self.head.layers[-1]) is nn.TransformerEncoderLayer)
        if self.head is not None:
            padding = ~attention_mask.bool()
            for i, layer in enumerate(self.head.layers):
                if sparse and i == len(self.head.layers) - 1:
                    hidden = self._selected_head(layer, hidden, selected, attention_mask)
                elif self.head_checkpointing and self.training:
                    hidden = checkpoint(layer, hidden, src_key_padding_mask=padding, use_reentrant=False)
                else:
                    hidden = layer(hidden, src_key_padding_mask=padding)
        if not sparse:
            positions = selected[:, :, None].expand(-1, -1, hidden.shape[-1])
            hidden = hidden.gather(1, positions)
        markers = hidden[:, 1:] if return_actions else hidden
        scores = self.scorer(markers).squeeze(-1).float()
        scores = scores.masked_fill(~marker_mask, -1e4)
        if not return_actions:
            return scores
        probability = scores.detach().softmax(-1)
        top = probability.topk(min(2, probability.shape[1]), dim=-1).values
        if top.shape[1] == 1:
            top = torch.cat((top, torch.zeros_like(top)), dim=-1)
        count = marker_mask.sum(-1).clamp_min(2).float()
        entropy = -(probability * probability.clamp_min(1e-9).log()).sum(-1) / count.log()
        features = torch.stack((top[:, 0], top[:, 0] - top[:, 1], entropy, count / 255), -1)
        actions = self.act_head(torch.cat((hidden[:, 0].float(), features), -1))
        return scores, actions

    @staticmethod
    def _selected_head(layer, hidden, selected, attention_mask):
        """Exact pre-norm block restricted to selected output positions (eval only)."""
        width = hidden.shape[-1]
        positions = selected[:, :, None].expand(-1, -1, width)
        normalized = layer.norm1(hidden)
        attn = layer.self_attn
        query = F.linear(normalized.gather(1, positions),
                         attn.in_proj_weight[:width], attn.in_proj_bias[:width])
        key, value = F.linear(normalized, attn.in_proj_weight[width:],
                              attn.in_proj_bias[width:]).chunk(2, dim=-1)
        batch = hidden.shape[0]
        heads = attn.num_heads
        split = lambda x: x.reshape(batch, -1, heads, width // heads).transpose(1, 2)
        attended = F.scaled_dot_product_attention(
            split(query), split(key), split(value),
            attn_mask=attention_mask[:, None, None, :].bool(), dropout_p=0.)
        attended = attended.transpose(1, 2).reshape(batch, selected.shape[1], width)
        result = hidden.gather(1, positions) + attn.out_proj(attended)
        return result + layer.linear2(layer.activation(layer.linear1(layer.norm2(result))))

    def save_pretrained(self, directory):
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        self.encoder.config.save_pretrained(root / 'encoder')
        config = dict(format_version=1, architecture='JuliaDecisionModel',
                      weight_dtype=str(next(self.parameters()).dtype).replace('torch.', ''), **self.settings)
        (root / 'julia_config.json').write_text(json.dumps(config, indent=2) + '\n')
        save_file({k: v.detach().cpu().contiguous() for k, v in self.state_dict().items()},
                  str(root / 'model.safetensors'), metadata={'format': 'pt', 'family': 'julia'})

    @classmethod
    def from_pretrained(cls, directory, *, memory_map=False):
        root = Path(directory)
        if (root / 'julia_config.json').exists():
            config = json.loads((root / 'julia_config.json').read_text())
            if config['format_version'] != 1:
                raise ValueError('Unsupported Julia checkpoint format')
            settings = {k: config[k] for k in ('head_layers', 'n_act', 'dropout')}
        else:
            config = json.loads((root / 'rl_agent_config.json').read_text())
            settings = dict(head_layers=config['head_layers'], n_act=len(config.get('act_costs', {})) + 1)
        encoder_config = AutoConfig.from_pretrained(root / 'encoder', trust_remote_code=False)
        encoder_config.reference_compile = False
        try:
            from transformers.initialization import no_init_weights
        except ImportError:
            from transformers.modeling_utils import no_init_weights
        with no_init_weights():
            encoder = AutoModel.from_config(encoder_config, attn_implementation='sdpa', trust_remote_code=False)
            model = cls(encoder, **settings)
        if not memory_map and config.get('weight_dtype') == 'bfloat16':
            model.to(dtype=torch.bfloat16)
        # Inference can retain safetensors' private file-backed storage rather than
        # copying the entire (mostly unused vocabulary) embedding into anonymous RAM.
        # The default copy path remains available for training and mutable checkpoints.
        model.load_state_dict(load_file(str(root / 'model.safetensors')),
                              strict=True, assign=memory_map)
        return model
