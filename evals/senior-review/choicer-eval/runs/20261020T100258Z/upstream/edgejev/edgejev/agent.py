"""运行时：只依赖 onnxruntime + tokenizers + numpy。跨 Linux / macOS / Windows。"""
import json
import os

import numpy as np
from typing import Any, Dict, Optional, Union

from . import backends, post, providers
from .core.render import to_internal
from .tokenize import Encoder

CONFIG_NAME = "edgejev.json"


class Agent:
    """本地 System One 决策。

        from edgejev import Agent
        ag = Agent("./jev-int8")
        ag.system_one("客户被扣了两次款", {
            "dept": {"type": "choice", "instructions": "转给哪个组",
                     "criteria": {"billing": "支付扣款", "technical": "程序缺陷"}}})
    """

    def __init__(self, model_dir: str, threads: Optional[int] = None,
                 provider: Optional[str] = None):
        cfg_path = os.path.join(model_dir, CONFIG_NAME)
        if not os.path.exists(cfg_path):
            raise FileNotFoundError(
                "%s 里没有 %s，这个目录需要用 `edgejev build` 生成。" % (model_dir, CONFIG_NAME))
        with open(cfg_path, encoding="utf-8") as f:
            self.cfg = json.load(f)

        self.spec = backends.get(self.cfg.get("backend", "laya"))
        self.backend = self.spec          # 兼容旧字段名
        self.runtime = self.cfg.get("runtime", self.spec.runtime)
        self.temperature = self.cfg.get("temperature", [1.0, 1.0, 1.0])
        self.temperature_by_options = self.cfg.get("temperature_by_options", {})
        self.model_name = self.cfg.get("model_name", "edgejev")

        if self.runtime == "torch-vlm":
            from .runtimes.torch_vlm import TorchVLM
            self.enc = None            # letter_prompt 布局只生成文本，不需要 tokenizer
            self.vlm = TorchVLM(self.cfg["source_model"], template=self.cfg.get("template", "plain"))
            self.provider_note = self.vlm.note
            self.slots = self.vlm.letter_slots(self.spec.layout_kw.get("slot_prefix", " "))
            return

        import onnxruntime as ort
        ids_map = {k: self.cfg[k] for k in self.cfg if k.endswith("_id")}
        ids_map["mask_token"] = self.cfg.get("mask_token", "<mask>")
        self.enc = Encoder.from_file(os.path.join(model_dir, "tokenizer.json"), ids_map)
        self.enc.special = self.cfg.get("special_ids", [])

        so = ort.SessionOptions()
        so.intra_op_num_threads = threads or (os.cpu_count() or 4)
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        provs, self.provider_note = providers.detect(provider)
        self.sess = ort.InferenceSession(
            os.path.join(model_dir, self.cfg["onnx_file"]), so, providers=provs)

    def system_one(self, state: Union[str, dict, list],
                   questions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """对一份 state 并行评估一组带类型的问题。返回与官方 /v1/systemone 同构的结果。"""
        if not questions:
            raise ValueError("questions 不能为空")
        qids = list(questions.keys())
        qs = [to_internal(questions[q]) for q in qids]

        if self.runtime == "torch-vlm":
            return self._vlm_system_one(state, qids, qs)

        prep = self.spec.prepare(self.enc, state, qs, self.cfg)
        outputs = self.sess.run(None, prep.feed)
        logits = outputs[0]
        act = None
        if len(outputs) > 1 and outputs[1].ndim == 2:
            a = outputs[1]
            a = np.exp(a - a.max(-1, keepdims=True))
            act = a / a.sum(-1, keepdims=True)

        answers = post.assemble(self.spec, qs, qids, logits, act, prep.k,
                                self.temperature, self.temperature_by_options)
        return {"model": self.model_name, "answers": answers,
                "usage": {"input_tokens": prep.input_tokens, "output_tokens": 0}}

    def _vlm_system_one(self, state, qids, qs):
        """字母槽读出：每题一次前向，取最后位置在选项字母 token 上的分布。"""
        from .runtimes.torch_vlm import _to_pil

        prep = self.spec.prepare(self.enc, state, qs, self.cfg)
        image = _to_pil(prep.meta["state"])
        answers, ntok = {}, 0
        for i, (qid, q) in enumerate(zip(qids, qs)):
            logits = self.vlm.last_logits(image, prep.meta["prompts"][i])
            ntok += self.vlm.n_input_tokens
            probs, allowed = post.vocab_slot_probs(logits, self.slots, prep.k[i])
            conf = self.spec.confidence_of(q, probs, prep.k[i])
            a = post.format_answer(self.spec, q, probs, conf, None)
            a["allowed_mass"] = round(allowed, 7)   # 量级 1e-4，4 位精度会把不同输入显示成同一个数
            answers[qid] = a
        return {"model": self.model_name, "answers": answers,
                "usage": {"input_tokens": ntok, "output_tokens": 0}}

    predict = system_one


def load(model_dir: str, **kw) -> Agent:
    return Agent(model_dir, **kw)
