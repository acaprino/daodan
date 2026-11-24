"""Run while the image is built, with the network open: Daodan's own loader (`languages/_treesitter.py`) places the pinned grammar bundle in its cache
(`DAODAN_SHARED_DIR`) and checks its sha256, then every language the snapshot reads must give a parser. A language without one would make the
measurement call a file "not read" for a reason of the image, not of Daodan: the build fails instead."""
import sys

sys.path.insert(0, "/daodan/core")
from languages import _treesitter as t  # noqa: E402

LANGUAGES = ("python", "java", "javascript", "typescript", "tsx", "go", "csharp", "kotlin", "rust", "c", "cpp", "sql", "vue", "svelte")
bad = {language: t.load_failure(language) for language in LANGUAGES if t.get_parser(language) is None}
print("grammars without a parser:", bad)
sys.exit(1 if bad else 0)
