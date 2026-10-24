"""带类型的问题 -> 选项文本。所有后端共用的第一步。

choice / score / noul 三个原语的渲染规则是 Jev 生态的事实标准，各家实现只在
措辞上有细微差别，所以这里参数化而不是每个后端抄一遍。
"""
import json
from typing import Dict, List, Optional, Union

QTYPES = {"choice": 0, "score": 1, "noul": 2}
QTYPE_NAMES = {v: k for k, v in QTYPES.items()}


def serialize_state(state: Union[str, dict, list]) -> str:
    return state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)


def render_criterion(value) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "), default=str)


def to_internal(qdef: Dict) -> Dict:
    """外部 API 的问题定义 -> 内部统一形式。"""
    t = qdef["type"]
    crit = qdef.get("criteria")
    if t == "choice" and isinstance(crit, list):
        crit = {c: None for c in crit}
    ins = qdef["instructions"]
    if not isinstance(ins, str):
        ins = json.dumps(ins, ensure_ascii=False)
    return {"t": t, "ins": ins, "crit": crit}


def render_options(q: Dict, *, score_prefix: str = "level %d: ",
                   noul_false: str = "no, the statement does not hold",
                   noul_true: str = "yes, the statement holds",
                   join: str = "%s: %s") -> List[str]:
    """按标签顺序渲染选项文本。noul 恒为 [false, true]。

    三个关键字参数是各家实现唯一真正分歧的地方：score 档位前缀、noul 两极的兜底描述、
    以及「名字: 描述」的拼接方式。
    """
    t, crit = q["t"], q.get("crit")
    if t == "choice":
        return [k if v is None or v == "" else join % (k, render_criterion(v))
                for k, v in crit.items()]
    if t == "score":
        return [(score_prefix % i) + render_criterion(c) for i, c in enumerate(crit)]
    crit = crit or {}
    fc, tc = crit.get("false"), crit.get("true")
    return ["false: " + (render_criterion(fc) if fc not in (None, "") else noul_false),
            "true: " + (render_criterion(tc) if tc not in (None, "") else noul_true)]


def option_keys(q: Dict) -> List[str]:
    """选项的对外名字，用于组装返回值。"""
    if q["t"] == "choice":
        return list(q["crit"].keys())
    if q["t"] == "score":
        return [str(i) for i in range(len(q["crit"]))]
    return ["false", "true"]
