"""Load kouhxp/gutsy (gutsy-0.8b-v04-q8_0.gguf) in pure PyTorch/Transformers and run gutsy_inference.Engine."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer
from transformers.models.qwen3_next.modeling_qwen3_next import (
    Qwen3NextConfig,
    Qwen3NextForCausalLM,
    Qwen3NextDynamicCache,
    apply_rotary_pos_emb,
    eager_attention_forward,
    l2norm,
    torch_causal_conv1d_update,
    torch_chunk_gated_delta_rule,
    torch_recurrent_gated_delta_rule,
)

HERE = Path(__file__).resolve().parent
SNAP = (
    HERE
    / ".cache/huggingface/hub/models--kouhxp--gutsy/snapshots/f9995fe26a337f1a4ea3f1a5ed38c9799e5a8f63"
)
sys.path.insert(0, str(SNAP / "gutsy-inference"))

from gutsy_inference.engine import Calibration, Engine  # noqa: E402
from gutsy_inference.prompt import LABELS, REJECT_LABEL  # noqa: E402


def _read_gguf(path: Path) -> tuple[dict, dict[str, tuple[list[int], int, int]], memoryview]:
    raw_bytes = path.read_bytes()
    mv = memoryview(raw_bytes)
    pos = 0

    def unpack(fmt: str):
        nonlocal pos
        size = struct.calcsize(fmt)
        val = struct.unpack_from(fmt, mv, pos)
        pos += size
        return val

    def r_str() -> str:
        (n,) = unpack("<Q")
        nonlocal pos
        s = bytes(mv[pos : pos + n]).decode("utf-8", errors="replace")
        pos += n
        return s

    def r_val(vtype: int):
        if vtype == 0:
            return unpack("<B")[0]
        if vtype == 1:
            return unpack("<b")[0]
        if vtype == 2:
            return unpack("<H")[0]
        if vtype == 3:
            return unpack("<h")[0]
        if vtype == 4:
            return unpack("<I")[0]
        if vtype == 5:
            return unpack("<i")[0]
        if vtype == 6:
            return unpack("<f")[0]
        if vtype == 7:
            return unpack("<?")[0]
        if vtype == 8:
            return r_str()
        if vtype == 9:
            at, an = unpack("<IQ")
            return [r_val(at) for _ in range(an)]
        if vtype == 10:
            return unpack("<Q")[0]
        if vtype == 11:
            return unpack("<q")[0]
        if vtype == 12:
            return unpack("<d")[0]
        raise ValueError(f"Unknown GGUF value type: {vtype}")

    magic, version, n_tensors, n_kv = unpack("<4sIQQ")
    if magic != b"GGUF":
        raise ValueError(f"Not a GGUF file: {magic}")
    kv = {}
    for _ in range(n_kv):
        k = r_str()
        (vt,) = unpack("<I")
        kv[k] = r_val(vt)
    tensors = {}
    for _ in range(n_tensors):
        name = r_str()
        (nd,) = unpack("<I")
        dims = [unpack("<Q")[0] for _ in range(nd)]
        tt, off = unpack("<IQ")
        tensors[name] = (dims, tt, off)
    alignment = kv.get("general.alignment", 32)
    data_start = ((pos + alignment - 1) // alignment) * alignment
    return kv, tensors, mv[data_start:]


def _dequant_tensor(data_mv: memoryview, dims: list[int], ttype: int, offset: int) -> torch.Tensor:
    # GGML dims are [ne0, ne1, ...]; PyTorch shape is reversed: (ne_{k-1}, ..., ne0)
    pt_shape = tuple(reversed(dims))
    n_el = 1
    for d in dims:
        n_el *= d
    if ttype == 0:  # F32
        nbytes = n_el * 4
        arr = np.frombuffer(data_mv[offset : offset + nbytes], dtype=np.float32).copy()
        return torch.from_numpy(arr.reshape(pt_shape))
    if ttype == 8:  # Q8_0: blocks of 32 elements = 2 bytes fp16 scale + 32 bytes int8
        n_blocks = n_el // 32
        nbytes = n_blocks * 34
        raw = np.frombuffer(data_mv[offset : offset + nbytes], dtype=np.uint8).reshape(n_blocks, 34)
        scales = raw[:, :2].copy().view(np.float16).astype(np.float32)  # (n_blocks, 1)
        quants = raw[:, 2:].view(np.int8).astype(np.float32)  # (n_blocks, 32)
        arr = (scales * quants).reshape(pt_shape)
        return torch.from_numpy(arr)
    raise ValueError(f"Unsupported GGML tensor type: {ttype}")


def _build_tokenizer_from_gguf(kv: dict, cache_dir: Path):
    tok_dir = cache_dir / "gutsy_tokenizer"
    tok_json = tok_dir / "tokenizer.json"
    if not tok_json.exists():
        from tokenizers import Tokenizer, models, pre_tokenizers, decoders, processors

        tokens = kv["tokenizer.ggml.tokens"]
        merges_raw = kv["tokenizer.ggml.merges"]
        token_types = kv["tokenizer.ggml.token_type"]
        vocab = {tok: idx for idx, tok in enumerate(tokens)}
        merges = [tuple(m.split(" ", 1)) for m in merges_raw]
        tok = Tokenizer(models.BPE(vocab=vocab, merges=merges, byte_fallback=False))
        # Qwen2/Qwen3.5 pre-tokenizer & ByteLevel decoder
        tok.pre_tokenizer = pre_tokenizers.Sequence(
            [
                pre_tokenizers.Split(
                    pattern=r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+",
                    behavior="isolated",
                    invert=False,
                ),
                pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False),
            ]
        )
        tok.decoder = decoders.ByteLevel()
        from tokenizers import AddedToken

        added = []
        for idx, (t_str, t_type) in enumerate(zip(tokens, token_types)):
            if t_type in (3, 4):  # control / user-defined special tokens like <|im_start|>, <|im_end|>, <think>, </think>
                added.append((idx, AddedToken(t_str, special=(t_type == 3), normalized=False)))
        for _, at in added:
            tok.add_special_tokens([at]) if at.special else tok.add_tokens([at])
        tok_dir.mkdir(parents=True, exist_ok=True)
        tok.save(str(tok_json))
    from tokenizers import Tokenizer

    return Tokenizer.from_file(str(tok_json))


def _fast_chunk_gated_delta_rule(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    g: torch.Tensor,
    beta: torch.Tensor,
    chunk_size: int = 64,
    initial_state: torch.Tensor | None = None,
    output_final_state: bool = False,
    use_qk_l2norm_in_kernel: bool = False,
):
    initial_dtype = query.dtype
    if use_qk_l2norm_in_kernel:
        query = l2norm(query, dim=-1, eps=1e-6)
        key = l2norm(key, dim=-1, eps=1e-6)
    query, key, value, beta, decay = [
        x.transpose(1, 2).contiguous().to(torch.float32) for x in (query, key, value, beta, g)
    ]
    batch_size, num_heads, sequence_length, k_head_dim = key.shape
    v_head_dim = value.shape[-1]
    # Adapt chunk_size to sequence_length when sequence_length <= 64
    if sequence_length <= 16:
        chunk_size = 16
    elif sequence_length <= 32:
        chunk_size = 32
    pad_size = (chunk_size - sequence_length % chunk_size) % chunk_size
    if pad_size:
        query = F.pad(query, (0, 0, 0, pad_size))
        key = F.pad(key, (0, 0, 0, pad_size))
        value = F.pad(value, (0, 0, 0, pad_size))
        beta = F.pad(beta, (0, pad_size))
        decay = F.pad(decay, (0, pad_size))
    total_sequence_length = sequence_length + pad_size
    num_chunks = total_sequence_length // chunk_size
    query = query * (query.shape[-1] ** -0.5)

    v_beta = value * beta.unsqueeze(-1)
    k_beta = key * beta.unsqueeze(-1)
    query, key, k_beta, v_beta = [
        x.reshape(batch_size, num_heads, num_chunks, chunk_size, x.shape[-1])
        for x in (query, key, k_beta, v_beta)
    ]
    decay = decay.reshape(batch_size, num_heads, num_chunks, chunk_size)
    strictly_upper_mask = torch.ones(chunk_size, chunk_size, dtype=torch.bool, device=query.device).triu(1)
    diag_eye = torch.eye(chunk_size, dtype=torch.float32, device=query.device)

    cum_decay = decay.cumsum(dim=3)
    pairwise_decay = (cum_decay.unsqueeze(4) - cum_decay.unsqueeze(3)).masked_fill(strictly_upper_mask, float("-inf")).exp()

    ut_system = (k_beta @ key.transpose(-1, -2)) * pairwise_decay
    # Set diagonal to 1 and upper triangle to 0 for unit lower triangular solve (I + strictly_lower(ut_system))
    ut_system = ut_system.masked_fill(strictly_upper_mask, 0.0)
    ut_system = ut_system.diagonal_scatter(torch.ones(batch_size, num_heads, num_chunks, chunk_size, dtype=torch.float32, device=query.device), dim1=-2, dim2=-1)
    intra_chunk_attn = (query @ key.transpose(-1, -2)) * pairwise_decay
    decayed_k_beta = k_beta * cum_decay.exp().unsqueeze(-1)

    new_values = torch.linalg.solve_triangular(ut_system, v_beta, upper=False, unitriangular=True)
    k_cumdecay = torch.linalg.solve_triangular(ut_system, decayed_k_beta, upper=False, unitriangular=True)

    last_recurrent_state = (
        torch.zeros(batch_size, num_heads, k_head_dim, v_head_dim, dtype=torch.float32, device=query.device)
        if initial_state is None
        else initial_state.to(torch.float32)
    )
    core_attn_out = torch.zeros_like(new_values)

    query = query * cum_decay.exp().unsqueeze(-1)
    key = key * (cum_decay[..., -1:] - cum_decay).exp().unsqueeze(-1)
    chunk_decay = cum_decay[..., -1].exp()[..., None, None]

    for i in range(num_chunks):
        v_new = new_values[:, :, i] - k_cumdecay[:, :, i] @ last_recurrent_state
        inter_chunk_attn = query[:, :, i] @ last_recurrent_state
        core_attn_out[:, :, i] = inter_chunk_attn + intra_chunk_attn[:, :, i] @ v_new
        last_recurrent_state = last_recurrent_state * chunk_decay[:, :, i] + key[:, :, i].transpose(-1, -2) @ v_new

    if not output_final_state:
        last_recurrent_state = None
    core_attn_out = core_attn_out.reshape(batch_size, num_heads, total_sequence_length, v_head_dim)[:, :, :sequence_length]
    return core_attn_out.transpose(1, 2).contiguous().to(initial_dtype), last_recurrent_state


def _patched_linear_attn_forward(
    self,
    hidden_states: torch.Tensor,
    cache_params: Qwen3NextDynamicCache | None = None,
    cache_position: torch.LongTensor | None = None,
    attention_mask: torch.Tensor | None = None,
):
    batch_size, seq_len, _ = hidden_states.shape
    has_prev = (
        cache_params is not None
        and cache_params.conv_states[self.layer_idx] is not None
        and cache_params.recurrent_states[self.layer_idx] is not None
    )
    projected_states_qkvz = self.in_proj_qkvz(hidden_states)
    projected_states_ba = self.in_proj_ba(hidden_states)
    query, key, value, z, b, a = self.fix_query_key_value_ordering(projected_states_qkvz, projected_states_ba)
    query, key, value = (x.reshape(x.shape[0], x.shape[1], -1) for x in (query, key, value))

    mixed_qkv = torch.cat((query, key, value), dim=-1).transpose(1, 2)  # (B, conv_dim, seq_len)
    pad_len = self.conv_kernel_size - 1
    if has_prev:
        prev_tail = cache_params.conv_states[self.layer_idx][:, :, -pad_len:]
        conv_in = torch.cat([prev_tail, mixed_qkv], dim=-1)
    else:
        conv_in = F.pad(mixed_qkv, (pad_len, 0))
    if cache_params is not None:
        cache_params.conv_states[self.layer_idx] = conv_in[:, :, -self.conv_kernel_size :].detach().clone()
    mixed_qkv = F.silu(F.conv1d(conv_in, self.conv1d.weight, bias=None, padding=0, groups=self.conv_dim))
    mixed_qkv = mixed_qkv.transpose(1, 2)

    query, key, value = torch.split(mixed_qkv, [self.key_dim, self.key_dim, self.value_dim], dim=-1)
    query = query.reshape(batch_size, seq_len, -1, self.head_k_dim)
    key = key.reshape(batch_size, seq_len, -1, self.head_k_dim)
    value = value.reshape(batch_size, seq_len, -1, self.head_v_dim)

    beta = b.sigmoid()
    g = -self.A_log.float().exp() * F.softplus(a.float() + self.dt_bias)
    if self.num_v_heads // self.num_k_heads > 1:
        query = query.repeat_interleave(self.num_v_heads // self.num_k_heads, dim=2)
        key = key.repeat_interleave(self.num_v_heads // self.num_k_heads, dim=2)

    init_state = cache_params.recurrent_states[self.layer_idx] if has_prev else None
    core_attn_out, last_recurrent_state = _fast_chunk_gated_delta_rule(
        query,
        key,
        value,
        g=g,
        beta=beta,
        initial_state=init_state,
        output_final_state=cache_params is not None,
        use_qk_l2norm_in_kernel=True,
    )
    if cache_params is not None:
        cache_params.recurrent_states[self.layer_idx] = last_recurrent_state

    z_shape_og = z.shape
    core_attn_out = core_attn_out.reshape(-1, core_attn_out.shape[-1])
    z = z.reshape(-1, z.shape[-1])
    core_attn_out = self.norm(core_attn_out, z)
    core_attn_out = core_attn_out.reshape(z_shape_og).reshape(batch_size, seq_len, -1)
    return self.out_proj(core_attn_out)


def _load_qwen35_from_gguf(gguf_path: Path, threads: int = 6):
    from transformers.models.qwen3_next.modeling_qwen3_next import Qwen3NextGatedDeltaNet

    Qwen3NextGatedDeltaNet.forward = _patched_linear_attn_forward
    torch.set_num_threads(threads)
    kv, tensors, data_mv = _read_gguf(gguf_path)

    cfg = Qwen3NextConfig(
        vocab_size=len(kv["tokenizer.ggml.tokens"]),
        hidden_size=int(kv["qwen35.embedding_length"]),
        intermediate_size=int(kv["qwen35.feed_forward_length"]),
        num_hidden_layers=int(kv["qwen35.block_count"]),
        num_attention_heads=int(kv["qwen35.attention.head_count"]),
        num_key_value_heads=int(kv["qwen35.attention.head_count_kv"]),
        head_dim=int(kv["qwen35.attention.key_length"]),
        rms_norm_eps=float(kv["qwen35.attention.layer_norm_rms_epsilon"]),
        linear_conv_kernel_dim=int(kv["qwen35.ssm.conv_kernel"]),
        linear_key_head_dim=int(kv["qwen35.ssm.state_size"]),
        linear_value_head_dim=int(kv["qwen35.ssm.inner_size"]) // int(kv["qwen35.ssm.time_step_rank"]),
        linear_num_key_heads=int(kv["qwen35.ssm.group_count"]),
        linear_num_value_heads=int(kv["qwen35.ssm.time_step_rank"]),
        num_experts=0,
        tie_word_embeddings=True,
        rope_parameters={
            "rope_type": "default",
            "rope_theta": float(kv["qwen35.rope.freq_base"]),
            "partial_rotary_factor": float(kv["qwen35.rope.dimension_count"])
            / float(kv["qwen35.attention.key_length"]),
        },
        attn_implementation="eager",
    )

    pt_cache = HERE / ".cache/gutsy_q8_0_state_dict.pt"
    if pt_cache.exists():
        with torch.device("meta"):
            model = Qwen3NextForCausalLM(cfg)
        sd_loaded = torch.load(pt_cache, map_location="cpu", weights_only=True, mmap=True)
        model.load_state_dict(sd_loaded, assign=True)
        inv_freq, _ = model.model.rotary_emb.compute_default_rope_parameters(cfg, device="cpu")
        model.model.rotary_emb.inv_freq = inv_freq
        model.model.rotary_emb.original_inv_freq = inv_freq.clone()
        model.eval()
        tokenizer = _build_tokenizer_from_gguf(kv, HERE / ".cache")
        return model, tokenizer

    model = Qwen3NextForCausalLM(cfg)
    model.eval()
    sd = model.state_dict()

    def get_t(name: str) -> torch.Tensor:
        dims, tt, off = tensors[name]
        return _dequant_tensor(data_mv, dims, tt, off)

    with torch.no_grad():
        emb = get_t("token_embd.weight")
        sd["model.embed_tokens.weight"].copy_(emb)
        sd["lm_head.weight"].copy_(emb)
        # Note: llama.cpp added +1 to all Qwen3NextRMSNorm weights during GGUF export
        sd["model.norm.weight"].copy_(get_t("output_norm.weight") - 1.0)

        num_k_heads = cfg.linear_num_key_heads  # 16
        num_v_heads = cfg.linear_num_value_heads  # 16
        head_k_dim = cfg.linear_key_head_dim  # 128
        head_v_dim = cfg.linear_value_head_dim  # 128
        hidden_size = cfg.hidden_size  # 1024

        for i in range(cfg.num_hidden_layers):
            p_gguf = f"blk.{i}."
            p_hf = f"model.layers.{i}."
            sd[p_hf + "input_layernorm.weight"].copy_(get_t(p_gguf + "attn_norm.weight") - 1.0)
            sd[p_hf + "post_attention_layernorm.weight"].copy_(get_t(p_gguf + "post_attention_norm.weight") - 1.0)
            sd[p_hf + "mlp.gate_proj.weight"].copy_(get_t(p_gguf + "ffn_gate.weight"))
            sd[p_hf + "mlp.up_proj.weight"].copy_(get_t(p_gguf + "ffn_up.weight"))
            sd[p_hf + "mlp.down_proj.weight"].copy_(get_t(p_gguf + "ffn_down.weight"))

            if cfg.layer_types[i] == "linear_attention":
                # In GGUF: ssm_a = -exp(A_log) -> A_log = log(-ssm_a)
                ssm_a = get_t(p_gguf + "ssm_a")
                sd[p_hf + "linear_attn.A_log"].copy_(torch.log(-ssm_a))
                sd[p_hf + "linear_attn.dt_bias"].copy_(get_t(p_gguf + "ssm_dt.bias"))
                # conv1d: GGUF shape (6144, 4) -> HF shape (6144, 1, 4)
                sd[p_hf + "linear_attn.conv1d.weight"].copy_(get_t(p_gguf + "ssm_conv1d.weight").unsqueeze(1))
                # linear_attn.norm.weight was NOT shifted by +1 in GGUF
                sd[p_hf + "linear_attn.norm.weight"].copy_(get_t(p_gguf + "ssm_norm.weight"))
                sd[p_hf + "linear_attn.out_proj.weight"].copy_(get_t(p_gguf + "ssm_out.weight"))

                # Invert the QKV + Gate split from llama.cpp Qwen3NextModel.modify_tensors:
                # GGUF has attn_qkv.weight (6144, 1024) = [q_all (2048), k_all (2048), v_all (2048)]
                # and attn_gate.weight (2048, 1024) = z_all (2048)
                qkv = get_t(p_gguf + "attn_qkv.weight")  # (6144, 1024)
                z = get_t(p_gguf + "attn_gate.weight")  # (2048, 1024)
                q, k, v = torch.split(qkv, [2048, 2048, 2048], dim=0)
                # Each is (2048, 1024) -> view as (num_k_heads=16, 128, 1024)
                q_h = q.view(num_k_heads, head_k_dim, hidden_size)
                k_h = k.view(num_k_heads, head_k_dim, hidden_size)
                v_h = v.view(num_k_heads, head_v_dim, hidden_size)
                z_h = z.view(num_k_heads, head_v_dim, hidden_size)
                qkvz = torch.cat([q_h, k_h, v_h, z_h], dim=1).reshape(8192, hidden_size)
                sd[p_hf + "linear_attn.in_proj_qkvz.weight"].copy_(qkvz)

                # beta (16, 1024) and alpha (16, 1024) -> interleaved per head [b_h, a_h] in in_proj_ba (32, 1024)
                beta_w = get_t(p_gguf + "ssm_beta.weight").view(num_k_heads, 1, hidden_size)
                alpha_w = get_t(p_gguf + "ssm_alpha.weight").view(num_k_heads, 1, hidden_size)
                ba = torch.cat([beta_w, alpha_w], dim=1).reshape(32, hidden_size)
                sd[p_hf + "linear_attn.in_proj_ba.weight"].copy_(ba)
            else:
                sd[p_hf + "self_attn.q_proj.weight"].copy_(get_t(p_gguf + "attn_q.weight"))
                sd[p_hf + "self_attn.k_proj.weight"].copy_(get_t(p_gguf + "attn_k.weight"))
                sd[p_hf + "self_attn.v_proj.weight"].copy_(get_t(p_gguf + "attn_v.weight"))
                sd[p_hf + "self_attn.o_proj.weight"].copy_(get_t(p_gguf + "attn_output.weight"))
                sd[p_hf + "self_attn.q_norm.weight"].copy_(get_t(p_gguf + "attn_q_norm.weight") - 1.0)
                sd[p_hf + "self_attn.k_norm.weight"].copy_(get_t(p_gguf + "attn_k_norm.weight") - 1.0)

    torch.save(model.state_dict(), pt_cache)
    tokenizer = _build_tokenizer_from_gguf(kv, HERE / ".cache")
    return model, tokenizer


class TorchGutsyBackend:
    """Drop-in backend for gutsy_inference.Engine using PyTorch Qwen3NextForCausalLM."""

    supports_state = True

    def __init__(self, gguf_path: Path, n_ctx: int = 8192, n_threads: int = 8):
        self.model, self.tokenizer = _load_qwen35_from_gguf(gguf_path, threads=n_threads)
        self.n_ctx = n_ctx
        self.n_vocab = self.model.config.vocab_size
        self.cache: Qwen3NextDynamicCache | None = None
        self.n_tokens = 0
        self._last_logits: np.ndarray | None = None

    def label_ids(self) -> list[int]:
        ids = []
        for lab in LABELS + [REJECT_LABEL]:
            toks = self.tokenize(lab, bos=False)
            if len(toks) != 1:
                raise ValueError(f"Label {lab!r} is not 1 token: {toks}")
            ids.append(toks[0])
        return ids

    def tokenize(self, text: str, bos: bool = False) -> list[int]:
        # Qwen3.5 has add_bos_token=False in GGUF
        return self.tokenizer.encode(text, add_special_tokens=True).ids

    def reset(self) -> None:
        self.cache = Qwen3NextDynamicCache(self.model.config)
        self.n_tokens = 0
        self._last_hidden: torch.Tensor | None = None

    def eval(self, tokens: list[int], start: int) -> None:
        if start == 0 or self.cache is None:
            self.reset()
        input_ids = torch.tensor([tokens], dtype=torch.long)
        cache_position = torch.arange(start, start + len(tokens), dtype=torch.long)
        position_ids = cache_position.unsqueeze(0)
        with torch.no_grad():
            out = self.model.model(
                input_ids=input_ids,
                position_ids=position_ids,
                past_key_values=self.cache,
                cache_position=cache_position,
                use_cache=True,
            )
            last_hidden = out.last_hidden_state[0, -1, :]  # (1024,)
            self._last_hidden = last_hidden
        self.n_tokens = start + len(tokens)

    def label_logits(self, ids: list[int]) -> np.ndarray:
        with torch.no_grad():
            w = self.model.lm_head.weight[ids]  # (len(ids), 1024)
            logits = torch.mv(w, self._last_hidden)
            return logits.detach().cpu().numpy().astype(np.float64)

    def save_seq(self):
        # Deep-copy the tensors in Qwen3NextDynamicCache
        snap = {
            "n_tokens": self.n_tokens,
            "last_hidden": None if self._last_hidden is None else self._last_hidden.clone(),
            "conv_states": [None if t is None else t.clone() for t in self.cache.conv_states],
            "recurrent_states": [None if t is None else t.clone() for t in self.cache.recurrent_states],
            "key_cache": [None if t is None else t.clone() for t in self.cache.key_cache],
            "value_cache": [None if t is None else t.clone() for t in self.cache.value_cache],
        }
        nbytes = sum(
            t.numel() * t.element_size()
            for lst in (snap["conv_states"], snap["recurrent_states"], snap["key_cache"], snap["value_cache"])
            for t in lst
            if t is not None
        )
        return snap, max(1, nbytes)

    def load_seq(self, blob: dict, tokens: list[int]) -> None:
        self.cache = Qwen3NextDynamicCache(self.model.config)
        self.cache.conv_states = [None if t is None else t.clone() for t in blob["conv_states"]]
        self.cache.recurrent_states = [None if t is None else t.clone() for t in blob["recurrent_states"]]
        self.cache.key_cache = [None if t is None else t.clone() for t in blob["key_cache"]]
        self.cache.value_cache = [None if t is None else t.clone() for t in blob["value_cache"]]
        self.n_tokens = len(tokens)
        self._last_hidden = None if blob["last_hidden"] is None else blob["last_hidden"].clone()

    def eval_batch_suffixes(self, blob: dict, pre_len: int, suffix_token_lists: list[list[int]]) -> list[np.ndarray]:
        """Evaluate B question suffixes in one batched forward pass starting from the cached prefix."""
        B = len(suffix_token_lists)
        lengths = [len(s) for s in suffix_token_lists]
        max_len = max(lengths)
        # Right-pad with 0; since all layers (conv1d, gated delta rule, causal attention) are strictly causal,
        # position lengths[b] - 1 is unaffected by any right-padding at positions >= lengths[b].
        padded = torch.zeros((B, max_len), dtype=torch.long)
        for b, s in enumerate(suffix_token_lists):
            padded[b, : len(s)] = torch.tensor(s, dtype=torch.long)

        bcache = Qwen3NextDynamicCache(self.model.config)
        bcache.conv_states = [
            None if t is None else t.expand(B, *t.shape[1:]).contiguous().clone() for t in blob["conv_states"]
        ]
        bcache.recurrent_states = [
            None if t is None else t.expand(B, *t.shape[1:]).contiguous().clone() for t in blob["recurrent_states"]
        ]
        bcache.key_cache = [
            None if t is None else t.expand(B, *t.shape[1:]).contiguous().clone() for t in blob["key_cache"]
        ]
        bcache.value_cache = [
            None if t is None else t.expand(B, *t.shape[1:]).contiguous().clone() for t in blob["value_cache"]
        ]
        cache_position = torch.arange(pre_len, pre_len + max_len, dtype=torch.long)
        position_ids = cache_position.unsqueeze(0).expand(B, -1)
        with torch.no_grad():
            out = self.model.model(
                input_ids=padded,
                position_ids=position_ids,
                past_key_values=bcache,
                cache_position=cache_position,
                use_cache=True,
            )
            w = self.model.lm_head.weight[self.label_ids()]  # (17, 1024)
            results = []
            for b, slen in enumerate(lengths):
                h = out.last_hidden_state[b, slen - 1, :]
                logits = torch.mv(w, h).detach().cpu().numpy().astype(np.float64)
                results.append(logits)
            return results


def decide_fast(engine: Engine, body: dict, batch_size: int = 11) -> dict:
    """Exact equivalent of engine.decide(body) that batches question suffixes into chunks of batch_size."""
    from gutsy_inference.prompt import prefix, suffix
    from gutsy_inference.schema import build_answer, parse_request

    t0 = time.perf_counter()
    state, questions, _ = parse_request(body)
    b: TorchGutsyBackend = engine.backend
    pre = prefix(state)
    pre_toks = b.tokenize(pre, bos=True)
    key = hashlib.sha256(pre.encode()).hexdigest()
    entry = engine.cache.get(key)
    hit = entry is not None
    if not hit:
        b.reset()
        b.eval(pre_toks, 0)
        blob, nbytes = b.save_seq()
        engine.cache.put(key, blob, nbytes)
        entry = (blob, nbytes)

    # Prepare suffix token lists for all single-call questions (len(options) <= engine.per_call)
    suffix_toks = []
    for q in questions:
        rej = engine._rej(q)
        s = suffix(q.text, q.options, rej)
        suffix_toks.append(b.tokenize(s, bos=False))

    all_logits = []
    for i in range(0, len(questions), batch_size):
        all_logits.extend(b.eval_batch_suffixes(entry[0], len(pre_toks), suffix_toks[i : i + batch_size]))

    answers = {}
    for q, logits_17 in zip(questions, all_logits):
        rej = engine._rej(q)
        n = len(q.options)
        raw_logits = np.append(logits_17[:n], logits_17[-1]) if rej else logits_17[:n]
        p = engine.calibration.probs(q.qtype, raw_logits)
        if rej:
            pr = float(p[-1])
            p_opts = p[:-1] / max(1e-12, 1.0 - pr)
        else:
            pr = None
            p_opts = p
        answers[q.qid] = build_answer(q, p_opts, pr, None)

    q_toks = sum(len(s) for s in suffix_toks)
    return {
        "model": engine.name,
        "answers": answers,
        "usage": {
            "prompt_tokens": len(pre_toks) + q_toks,
            "state_tokens": len(pre_toks),
            "evaluated_tokens": (0 if hit else len(pre_toks)) + q_toks,
            "model_calls": 1,
            "state_cached": True,
            "state_cache_hit": hit,
            "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        },
    }


if __name__ == "__main__":
    t0 = time.perf_counter()
    gguf_file = SNAP / "gutsy-0.8b-v04-q8_0.gguf"
    cal_file = SNAP / "gutsy-0.8b-v04.calibration.json"
    backend = TorchGutsyBackend(gguf_file, n_ctx=8192, n_threads=4)
    engine = Engine(
        backend,
        calibration=Calibration.load(cal_file),
        name="gutsy-0.8b-v04",
        reject_slot=True,
        shortlist=True,
    )
    chk = engine.self_check(tol=1e-3)
    print(f"Loaded in {time.perf_counter() - t0:.2f}s | self_check: {chk}")

    # Test 1: Official README shipping example
    r1 = engine.decide(
        {
            "state": "Order 1182 shipped Monday. The customer says it arrived Thursday with the box crushed.",
            "questions": {
                "decision": {
                    "type": "choice",
                    "instructions": "What should support do next?",
                    "criteria": {
                        "refund": "issue a refund",
                        "replace": "send a replacement",
                        "escalate": "a manager reviews it within 24 hours",
                    },
                }
            },
        }
    )
    print("README example:", str(r1).replace("{", "(").replace("}", ")"))

    # Test 2: model-router.html 6 examples
    routes = {
        "small": "small model: greetings, simple facts, short rewrites, formatting, quick classification",
        "large": "large model with reasoning off: needs broad knowledge, nuance or good writing, but no multi-step reasoning",
        "large_reasoning": "large model with a high reasoning budget: multi-step math or logic, proofs, debugging, complex code, plans with many constraints",
    }
    prompts = [
        "hey, what's the capital of Portugal?",
        'Make this friendlier: "Your invoice is overdue. Pay now."',
        "Explain why the Roman Republic fell, for a curious 15 year old.",
        "Prove there are infinitely many primes of the form 4k+3.",
        "My Postgres query got 40x slower after adding an index on (user_id, created_at). The planner now picks a nested loop. Why, and how do I fix it?",
        "Write a haiku about Mondays.",
    ]
    for p in prompts:
        res = engine.decide(
            {
                "state": {"user_message": p},
                "questions": {
                    "route": {
                        "type": "choice",
                        "instructions": "Route this user message to an AI model. Pick the cheapest model that will still answer it well.",
                        "criteria": routes,
                    }
                },
            }
        )
        ans = res["answers"]["route"]
        print(
            f"Prompt: {p[:55]:55s} -> {ans['choice']:16s} "
            f"(conf={ans['confidence']:.2f}, P={ans['probabilities']}, {res['usage']['latency_ms']}ms)".replace(
                "{", "("
            ).replace("}", ")")
        )
