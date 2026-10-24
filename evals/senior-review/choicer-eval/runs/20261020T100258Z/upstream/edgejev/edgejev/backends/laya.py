"""laya：mmBERT 编码器 + 两层 transformer head + marker 打分。

每题占 batch 的一行，选项前插 [MASK] 作为读出位；打分头已随模型导进 ONNX，
所以 readout 就是直接取图的输出。与上游 PyTorch 逐位一致（最大概率偏差 0.00000）。
"""
from ..core import BackendSpec

SPEC = BackendSpec(
    name="laya",
    layout="per_question_row",
    attention="bidirectional",
    readout="model_logits",
    runtime="onnx",
    input_names=["input_ids", "attention_mask", "marker_pos", "marker_mask", "qtype"],
    extras={"default_model": "convaiinnovations/laya-multilingual",
            "decision_marker": "type_emb.weight",
            "default_precision": "int8"},
)
