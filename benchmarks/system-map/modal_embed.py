"""The embedder probe on Modal, for the models too large for a local disk (`embed_probe.py rank`).

    modal run benchmarks/system-map/modal_embed.py --queries QUERIES.json --models st:intfloat/multilingual-e5-small,...

QUERIES.json is what `embed_queries.py` writes: requests in words and names of flows and parts, no code. A model
named `st:...` is a sentence-transformers model, loaded without its own remote code; the others are model2vec.
"""
from __future__ import annotations

from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
image = (modal.Image.debian_slim(python_version="3.13")
         .pip_install("numpy", "model2vec", "sentence-transformers", "torch", extra_index_url="https://download.pytorch.org/whl/cpu")
         .add_local_file(HERE / "embed_probe.py", "/probe/embed_probe.py"))
app = modal.App("daodan-embed-probe", image=image)


@app.function(cpu=8, memory=16384, timeout=3600)
def ranked(queries: bytes, models: list[str]) -> str:
    import contextlib
    import io
    import sys
    sys.path.insert(0, "/probe")
    import embed_probe
    Path("/tmp/queries.json").write_bytes(queries)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        for model in models:  # one at a time: a model that fails to load does not hide the others
            try:
                embed_probe.rank("/tmp/queries.json", [model])
            except Exception as error:  # noqa: BLE001 - the report says which model failed and why
                print(f"{model}: FAILED {type(error).__name__}: {str(error)[:300]}")
    return out.getvalue()


@app.local_entrypoint()
def main(queries: str, models: str):
    print(ranked.remote(Path(queries).read_bytes(), models.split(",")))
