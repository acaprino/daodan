# Second holdout: click 8.1.8

Frozen on 2026-10-25, in phase 1 of the [context packet redesign](../../../../docs/superpowers/specs/2026-10-25-context-packet-redesign.md),
because the Starlette queries were consumed while the defects were diagnosed and now serve
only as a paired before/after regression.

- Corpus: the `click` package of `click-8.1.8-py3-none-any.whl` (BSD-3-Clause), 16 Python
  files, 349 891 characters. File and wheel hashes are in `corpus-sha256.json`; reproduce
  with `pip download click==8.1.8 --no-deps --only-binary=:all:` and compare.
- Chosen for a domain unlike Starlette's (command-line parsing rather than HTTP) and a
  larger size. No query, gold, tuning or design decision may read it before the phase 4
  benchmark. Queries and gold are written blind in phase 4 and checked by a second pass,
  as for the first holdout.
