"""Costruisce la copia del plugin di un braccio: `daodan/review`, i ruoli candidati e una variante del catalogo.

    python benchmarks/stack-reviewers/plugin_copy.py S1-foglia OUT

`OUT` non deve esistere. `composition.py --plugin-root OUT` lega poi i job del braccio.
"""

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1] / "daodan/review"


def build(variant: str, out: Path) -> Path:
    shutil.copytree(REVIEW, out)
    for role in sorted((HERE / "roles").glob("*.md")):
        shutil.copy(role, out / "roles" / role.name)
    shutil.copy(HERE / "catalogs" / f"{variant}.toml", out / "catalog.toml")
    return out


if __name__ == "__main__":
    print(build(sys.argv[1], Path(sys.argv[2])))
