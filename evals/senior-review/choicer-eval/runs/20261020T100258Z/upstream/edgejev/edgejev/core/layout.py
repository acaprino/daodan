"""布局：把 (state, 带类型的问题) 摆成 token 序列，并标出每个选项的读出位置。

四种布局覆盖了目前所有开源 Jev 复现：

* `per_question_row` —— 每题一条序列（batch 的一行），选项前插一个标记 token，
  读该标记位的隐状态。编码器骨干走这条（laya、jevlike）。
* `packed_branches` —— 一条序列装下 state + 所有问题分支，靠 block-causal 掩码隔离，
  读每个选项结束符的隐状态、用 <decide> 位做 query。解码器骨干走这条（kev）。
* `prefix_tree` —— 同样一条序列，但每个候选是一片互相隔离的叶子，读叶子末尾 EOS 的
  隐状态，没有 <decide> 位。等价于上游「每个候选独立跑一条路径」，前缀只算一遍（NanoJev）。
* `letter_prompt` —— 把选项渲染成 `A. 名字: 描述` 的文本清单，读最后一个位置在
  字母 token 上的分布。不需要训练专门的打分头，任何 base LM 都能用（PlayJev、OpenJev）。

产出统一成 `Encoded`：模型输入 + 每题选项数 + 读出位置。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .render import render_options, serialize_state


@dataclass
class Encoded:
    feed: Dict[str, Any]          # 模型输入
    k: List[int]                  # 每题的选项数
    input_tokens: int = 0
    meta: Dict = field(default_factory=dict)


# ------------------------------------------------------------- per-question row
def per_question_row(enc, state, questions, cfg, *, render_kw=None,
                     head_template="%s question: %s", opt_token_budget=48):
    """[CLS] <type> question: 指令 [SEP] [MARK] opt0 [MARK] opt1 ... [SEP] state [SEP]"""
    from .render import QTYPES

    max_len = cfg.get("max_len", 1024)
    head_max_len = cfg.get("head_max_len", 256)
    mt = enc.mask_token
    rows = []
    for q in questions:
        opts = render_options(q, **(render_kw or {}))
        ins = str(q["ins"]).replace(mt, " ")
        head_ids = enc.ids(head_template % (q["t"], ins))
        opt_ids = [[enc.mask_id] + enc.ids(" " + o.replace(mt, " "))[:opt_token_budget]
                   for o in opts]
        budget = head_max_len - sum(len(o) for o in opt_ids)
        if budget < 16:
            per = max(4, (head_max_len - 16) // max(1, len(opt_ids)))
            opt_ids = [o[:per] for o in opt_ids]
            budget = head_max_len - sum(len(o) for o in opt_ids)
        head_ids = head_ids[: max(8, budget)]

        ids = [enc.cls_id] + head_ids + [enc.sep_id]
        markers = []
        for o in opt_ids:
            markers.append(len(ids))
            ids.extend(o)
        ids.append(enc.sep_id)
        room = max(0, max_len - len(ids) - 1)
        ids = ids + enc.ids(serialize_state(state).replace(mt, " "))[:room] + [enc.sep_id]
        ids = ids[:max_len]
        markers = [m for m in markers if m < max_len]
        if len(markers) != len(opts):
            raise ValueError("选项超出 head_max_len=%d" % head_max_len)
        rows.append((ids, markers, QTYPES[q["t"]]))

    n = len(rows)
    L = max(len(r[0]) for r in rows)
    K = max(len(r[1]) for r in rows)
    ids = np.full((n, L), enc.pad_id, dtype=np.int64)
    att = np.zeros((n, L), dtype=np.int64)
    mpos = np.zeros((n, K), dtype=np.int64)
    mmask = np.zeros((n, K), dtype=bool)
    for i, (seq, mk, _) in enumerate(rows):
        ids[i, :len(seq)] = seq
        att[i, :len(seq)] = 1
        mpos[i, :len(mk)] = mk
        mmask[i, :len(mk)] = True
    return Encoded(
        feed={"input_ids": ids, "attention_mask": att, "marker_pos": mpos,
              "marker_mask": mmask,
              "qtype": np.array([r[2] for r in rows], dtype=np.int64)},
        k=[len(r[1]) for r in rows], input_tokens=int(att.sum()))


# -------------------------------------------------------------- packed branches
def packed_branches(enc, state, questions, cfg, *, render_kw=None):
    """[<state> state...] + 每题 [<q> 指令 <opt> o </opt> ... <decide>]，一条序列装下。

    位置 id 在每个分支重新从 len(state) 起算；选项 span 共享同一段位置、
    <decide> 落在最长 span 之后的固定位置，于是选项顺序不影响结果。
    """
    from .masks import OPT_DECIDE, OPT_NONE

    max_state = cfg.get("max_state", 384)
    max_branch = cfg.get("max_branch", 1024)
    isolate = cfg.get("option_isolation", True)
    sp = enc.special            # (state, q, opt, /opt, decide) 五个分隔符 id

    st = enc.user_ids(serialize_state(state))[: max_state - 1]
    ids = [sp[0]] + st
    seg = [0] * len(ids)
    pos = list(range(len(ids)))
    opt = [OPT_NONE] * len(ids)
    p0 = len(ids)
    decide_idx, opt_idx, ks = [], [], []

    for qi, q in enumerate(questions, start=1):
        opts = render_options(q, **(render_kw or {}))
        instr = [sp[1]] + enc.user_ids(str(q["ins"]))
        spans = [[sp[2]] + enc.user_ids(o) + [sp[3]] for o in opts]
        br = instr + [t for s_ in spans for t in s_] + [sp[4]]
        if len(br) > max_branch - p0:
            raise ValueError("第 %d 题的分支过长：%d" % (qi, len(br)))
        base = len(ids)
        br_opt = [OPT_NONE] * len(instr) + [j for j, s_ in enumerate(spans) for _ in s_] + [OPT_DECIDE]
        if isolate:
            longest = max(len(s_) for s_ in spans)
            br_pos = (list(range(p0, p0 + len(instr)))
                      + [p0 + len(instr) + i for s_ in spans for i in range(len(s_))]
                      + [p0 + len(instr) + longest])
        else:
            br_pos = list(range(p0, p0 + len(br)))
        ends, cursor = [], len(instr)
        for s_ in spans:
            cursor += len(s_)
            ends.append(cursor - 1)
        ids += br; seg += [qi] * len(br); pos += br_pos; opt += br_opt
        decide_idx.append(base + len(br) - 1)
        opt_idx.append([base + e for e in ends])
        ks.append(len(opts))

    from .masks import block_causal
    L = len(ids)
    K = max(ks)
    oi = np.zeros((len(ks), K), dtype=np.int64)
    om = np.zeros((len(ks), K), dtype=bool)
    for i, row in enumerate(opt_idx):
        oi[i, :len(row)] = row
        om[i, :len(row)] = True
    mask = block_causal([seg], opts=[opt] if isolate else None)
    return Encoded(
        feed={"input_ids": np.array([ids], dtype=np.int64),
              "position_ids": np.array([pos], dtype=np.int64),
              "attn_mask_4d": mask.astype(np.float32),
              "decide_idx": np.array(decide_idx, dtype=np.int64),
              "opt_idx": oi, "opt_mask": om},
        k=ks, input_tokens=L)


# ------------------------------------------------------------------ prefix tree
def prefix_tree(enc, state, questions, cfg, *, render_kw=None,
                state_template="State:\n%s\n",
                question_template="Question type: %s\nQuestion:\n%s\n",
                candidate_template="Candidate:\n%s\nDecision:",
                type_names=None, noul_candidate="The proposition is true.",
                noul_criterion_template="%s criterion: %s\n"):
    """state -> 每题的问题段 -> 每个候选一条叶子路径，读叶子末尾 EOS 的隐状态。

    上游（NanoJev）是每个候选单独跑一条 `state + 问题 + 候选 + EOS` 的因果序列，
    state 有多少候选就重复算多少遍。这里把公共前缀只放一次：候选 span 之间互不可见、
    position id 都从前缀末尾接着数，于是每片叶子看到的 token 和位置与独立路径完全一致，
    结果相同而前缀只算一遍。各段分开 tokenize，与上游逐段 encode 的边界对齐。

    score 的每个档位只渲染自己的描述，不带序号；noul 只有一条「命题为真」路径，
    图里读成 logits [0, z]。
    """
    from .masks import OPT_NONE, block_causal
    from .render import QTYPES, render_criterion

    max_len = cfg.get("max_len", 8192)
    names = type_names or {}

    # state 不截断：上游训练时就不截断，实测截掉尾部会翻转 argmax。超长直接报错。
    ids = enc.user_ids(state_template % serialize_state(state))
    seg = [0] * len(ids)
    pos = list(range(len(ids)))
    opt = [OPT_NONE] * len(ids)
    p0 = len(ids)
    leaf_idx, ks = [], []

    for qi, q in enumerate(questions, start=1):
        t, crit = q["t"], q.get("crit")
        head = question_template % (names.get(t, t), q["ins"])
        if t == "choice":
            texts = render_options(q, **(render_kw or {}))
        elif t == "score":
            texts = [render_criterion(c) for c in crit]
        else:
            texts = [noul_candidate]
            for key, label in (("false", "False"), ("true", "True")):
                if (crit or {}).get(key) not in (None, ""):
                    head += noul_criterion_template % (label, render_criterion(crit[key]))
        instr = enc.user_ids(head)
        spans = [enc.user_ids(candidate_template % c) + [enc.eos_id] for c in texts]

        p1 = p0 + len(instr)
        ids += instr; seg += [qi] * len(instr); opt += [OPT_NONE] * len(instr)
        pos += list(range(p0, p1))
        leaves = []
        for j, s_ in enumerate(spans):
            ids += s_; seg += [qi] * len(s_); opt += [j] * len(s_)
            pos += list(range(p1, p1 + len(s_)))
            leaves.append(len(ids) - 1)
        leaf_idx.append(leaves)
        ks.append(2 if t == "noul" else len(texts))

    L = len(ids)
    if L > max_len:
        raise ValueError("序列 %d token，超过 max_len=%d" % (L, max_len))
    K = max(ks)
    li = np.zeros((len(ks), K), dtype=np.int64)
    lm = np.zeros((len(ks), K), dtype=bool)
    for i, row in enumerate(leaf_idx):
        li[i, :len(row)] = row
        lm[i, :len(row)] = True
    return Encoded(
        feed={"input_ids": np.array([ids], dtype=np.int64),
              "position_ids": np.array([pos], dtype=np.int64),
              "attn_mask_4d": block_causal([seg], opts=[opt]).astype(np.float32),
              "leaf_idx": li, "leaf_mask": lm,
              "qtype": np.array([QTYPES[q["t"]] for q in questions], dtype=np.int64)},
        k=ks, input_tokens=L)


LAYOUTS = {"per_question_row": per_question_row, "packed_branches": packed_branches,
           "prefix_tree": prefix_tree}


# --------------------------------------------------------------- letter prompt
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def letter_prompt(enc, state, questions, cfg, *, render_kw=None,
                  system="", instructions_default="", state_template="<state>\n%s\n</state>",
                  frame_placeholder="", answer_cue="Answer:", slot_prefix=" "):
    """把选项渲染成 `A. 名字: 描述` 的清单，读出位在序列最后一个位置。

    不需要训练打分头——任何 base LM 都能用，代价是概率来自词表而非专用 readout，
    绝对质量分散（`allowed_mass` 通常在 1e-4 量级），有判别力的是字母之间的相对排序。
    """
    prompts, ks = [], []
    for q in questions:
        opts = render_options(q, **(render_kw or {}))
        if len(opts) > len(LETTERS):
            raise ValueError("%d 个选项超出 %d 个字母槽" % (len(opts), len(LETTERS)))
        block = "\n".join("%s. %s" % (LETTERS[i], o) for i, o in enumerate(opts))
        letters = ", ".join(LETTERS[: len(opts)])
        body = ("Question: %s\n\nOptions:\n%s\n\nAnswer with one letter: %s."
                % (q["ins"] or instructions_default, block, letters))
        prompts.append("%s\n\n%s\n\n%s\n%s"
                       % (system, state_template % frame_placeholder, body, answer_cue))
        ks.append(len(opts))
    return Encoded(feed={}, k=ks, input_tokens=0,
                   meta={"prompts": prompts, "state": state, "slot_prefix": slot_prefix})


LAYOUTS["letter_prompt"] = letter_prompt
