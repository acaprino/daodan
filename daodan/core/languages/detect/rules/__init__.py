"""The rules that are not data: one class per file, with the card a rule of `language-rules.toml` has (`id`,
`extensions`, `why`, `source`, `yes`, `no`), the Linguist names it may answer (`languages`), and
`decide(text) -> a Linguist name, or None when it has nothing to say`. `yes` pairs each sample with its answer."""
from .header import HeaderLanguage
from .sql_rowtype import SqlRowtype

CLASSES = (SqlRowtype(), HeaderLanguage())
