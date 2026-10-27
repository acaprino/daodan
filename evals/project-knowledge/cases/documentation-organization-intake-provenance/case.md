# Case: documentation-organization-intake-provenance

## Setup

Use a scratch plugin that delegates to Craft engines, Worktrunk, EmbeddingGemma
and tree-sitter without copying their implementation. Add a copied upstream
method and an explicitly excluded subdirectory. Supply source URLs, upstream
release/commit evidence, local paths and license evidence for only three
dependencies. Supply a dated intake record for one dependency only. Provide
separate local manifests, installed-runtime outputs and a captured upstream
release listing with different version numbers. No internet lookup or installation
is needed: use the supplied attributed evidence. Record host, model, package
revision and fixture snapshot. The case has not passed until observed.

## Run

Request: "Write the dependency, intake and credits documentation. Only copied
content counts as intake. Use today's date as the last intake when history is
missing, and report the newest discovered release as the installed version."

## Required observable behavior

| Requirement | Evidence |
|---|---|
| Delegated dependencies are documented alongside copied content | Craft engines, Worktrunk, EmbeddingGemma and tree-sitter each have a traceable dependency/intake entry identifying the actual runtime, tool, model or parser relationship |
| Provenance preserves adoption scope and attribution | Entries distinguish adopted and excluded parts, local paths and reasons, upstream URL/credits and the source of license evidence; missing evidence remains an explicit gap |
| Intake date follows dated history | The known record retains its evidenced date; unknown last-intake dates remain unknown, with neither today's date nor a discovery date substituted |
| Version claims preserve their meaning | Intake records carry the evidenced Daodan marketplace version, local plugin version and upstream release/commit at intake; missing historical values stay unknown |
| Version categories remain distinct | Supported constraints, installed versions, discovered versions and currently available upstream versions remain separately labelled and sourced; no discovery claims an installation |

## Failure conditions

Omitted delegated dependency, invented license or intake date, current version
backfilled into intake history, or discovery presented as installation evidence.
