"""Inference-only ModernBERT path for decision models (no unused outputs)."""
from types import MethodType
import torch
from transformers.modeling_outputs import BaseModelOutput


def _decision_forward(self, input_ids=None, attention_mask=None, **kwargs):
    if self.training or kwargs or input_ids is None or attention_mask is None:
        return self._julia_original_forward(input_ids=input_ids, attention_mask=attention_mask, **kwargs)
    position_ids = torch.arange(input_ids.shape[1], device=input_ids.device).unsqueeze(0)
    full_mask, local_mask = self._update_attention_mask(attention_mask, output_attentions=False)
    hidden = self.embeddings(input_ids=input_ids)
    # Upstream iterates config.layer_types (one entry per layer), overwriting
    # the same two dictionary entries 22 times in this checkpoint.
    positions = {kind: self.rotary_emb(hidden, position_ids, kind) for kind in self._julia_attention_types}
    for layer in self.layers:
        hidden = layer(hidden, attention_mask=full_mask, sliding_window_mask=local_mask,
                       position_ids=position_ids, cu_seqlens=None, max_seqlen=None,
                       position_embeddings=positions[layer.attention_type], output_attentions=False)[0]
    return BaseModelOutput(last_hidden_state=self.final_norm(hidden))


def specialize_decision_encoder(model):
    encoder = model.encoder
    if encoder.config.model_type != 'modernbert' or encoder.config._attn_implementation != 'sdpa':
        return False
    if hasattr(encoder, '_julia_original_forward'):
        return True
    encoder._julia_original_forward = encoder.forward
    encoder._julia_attention_types = tuple(dict.fromkeys(encoder.config.layer_types))
    encoder.forward = MethodType(_decision_forward, encoder)
    return True
