# Spike binding headless (Task 1)

## (a) Binding headless: OK

```json
{
  "run_id": "spike-1",
  "project_root": "C:/Users/alfio/AppData/Local/Temp/opencode/scope-resolution-spike-5z69wo6b",
  "state": {
    "completed_phases": [],
    "current_phase": 0,
    "delivery": {
      "artifacts": {
        "01-structure.md": {
          "phase": 1,
          "status": "produced"
        },
        "02-interfaces.md": {
          "phase": 2,
          "status": "produced"
        },
        "03-flows.md": {
          "phase": 3,
          "status": "produced"
        },
        "04-semantics.md": {
          "phase": 4,
          "status": "produced"
        },
        "05-risks.md": {
          "phase": 5,
          "status": "produced"
        },
        "06-documentation.md": {
          "phase": 6,
          "status": "produced"
        },
        "07-final-report.md": {
          "phase": 7,
          "status": "produced"
        },
        "08-interconnect-map.md": {
          "phase": 8,
          "reason": "not selected by the run's mode and flags",
          "status": "skipped"
        },
        "knowledge/": {
          "phase": 0,
          "status": "produced"
        }
      },
      "binding": {
        "incremental": false,
        "parent_phases": null,
        "parent_run": null,
        "project": "C:/Users/alfio/AppData/Local/Temp/opencode/scope-resolution-spike-5z69wo6b",
        "target": "."
      },
      "flags": {
        "comments": false,
        "critical": false,
        "depth": "full",
        "docs_only": false,
        "phase": null,
        "skip_interconnect": false,
        "skip_synthesis": false
      },
      "mode": "classic",
      "resume_from": null,
      "run_phases": [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7
      ],
      "schema": 1,
      "stop_after": null
    },
    "files_created": [],
    "flags": {
      "comments": false,
      "critical": false,
      "depth": "full",
      "docs_only": false,
      "phase": null
    },
    "git": null,
 
```

## (b) Moduli dichiarati esposti senza run di analisi

```json
{
  "run_id": "spike-1",
  "graph_state": "fresh",
  "state": {
    "graph": "C:\\Users\\alfio\\AppData\\Local\\Temp\\opencode\\scope-resolution-spike-5z69wo6b\\.codebase-map\\runs\\spike-1\\snapshot\\modules.json",
    "manifest": "C:\\Users\\alfio\\AppData\\Local\\Temp\\opencode\\scope-resolution-spike-5z69wo6b\\.codebase-map\\runs\\spike-1\\snapshot\\manifest.sqlite",
    "state": "fresh",
    "modules": 3
  },
  "binding": {
    "git": null,
    "logical_digest": "944fc777c52689da4a272619f5833dffa356516d75fd092dd61ea3e3f9bac871",
    "manifest": "C:\\Users\\alfio\\AppData\\Local\\Temp\\opencode\\scope-resolution-spike-5z69wo6b\\.codebase-map\\runs\\spike-1\\snapshot\\manifest.sqlite",
    "root": "C:/Users/alfio/AppData/Local/Temp/opencode/scope-resolution-spike-5z69wo6b",
    "target": "."
  },
  "coverage": {
    "ecosystems": [
      "bundler",
      "cabal",
      "cargo",
      "cmake",
      "composer",
      "daodan",
      "deno",
      "dotnet",
      "dune",
      "go",
      "gradle",
      "julia",
      "lerna",
      "maven",
      "melos",
      "mix",
      "npm",
      "nx",
      "pnpm",
      "pub",
      "python",
      "rubygems",
      "sbt",
      "stack",
      "swiftpm",
      "terraform",
      "zig"
    ],
    "edges": {
      "calls": 0,
      "contains": 2,
      "declares": 0,
      "imports": 0
    },
    "files": 5,
    "modules": {
      "build": 3,
      "declared": 0,
      "proposed": 0
    },
    "statuses": {
      "confirmed": 3,
      "incomplete": 0,
      "inferred": 0
    }
  },
  "changes": {
    "added": [
      "spike-demo",
      "tmp-alpha",
      "tmp-alphabeta"
    ],
    "changed": [],
    "removed": [],
    "unchanged": []
  },
  "modules": [
    {
      "id": "spike-demo",
      "name": "spike-demo",
      "aliases": [],
      "provenance": "build",
      "kind": "uv-workspace",
      "description": null,
      "responsibility": "",
      "status": "confirmed",
      "paths": [
        "."
      ],
      "excluded": [
        "packages/tmp_alpha",
        "packages/tmp_alphabeta"
      ],
      "coverage": {
        "files": 1,
        "members": 1,
        "resolved": 1,
        "source_files": 0
      },
      "members": [
        "."
      ],
      "conflicts": 0,
      "gaps": 0
    },
    {
      "id": "tmp-alpha",
      "name": "tmp_alpha",
      "aliases": [],
      "provenance": "build",
      "kind": "workspace-member",
      "description": null,
      "responsibility": "",
      "status": "confirmed",
      "paths": [
        "packages/tmp_alpha"
      ],
      "excluded": [],
      "coverage": {
        "files": 2,
        "members": 1,
        "resolved": 1,
        "source_files": 2
      },
      "members": [
        "packages/tmp_alpha"
      ],
      "conflicts": 0,
      "gaps": 0
    },
    {
      "id": "tmp-alphabeta",
      "name": "tmp_alphabeta",
      "aliases": [],
      "provenance": "build",
      "kind": "workspace-member",
      "description": null,
      "respo
```

## (d) Forma della risposta a query di modulo con nomi simili

```json
{
  "schema": "daodan/module-query/v1",
  "query": "tmp_alpha",
  "status": "resolved",
  "reason": "one confirmed module matches the name",
  "candidates": [
    {
      "id": "tmp-alpha",
      "name": "tmp_alpha",
      "aliases": [],
      "provenance": "build",
      "kind": "workspace-member",
      "description": null,
      "responsibility": "",
      "status": "confirmed",
      "paths": [
        "packages/tmp_alpha"
      ],
      "excluded": [],
      "files": [
        "packages/tmp_alpha/__init__.py",
        "packages/tmp_alpha/alpha.py"
      ],
      "members": [
        {
          "id": "packages/tmp_alpha",
          "kind": "directory",
          "path": "packages/tmp_alpha",
          "resolved": true
        }
      ],
      "manifests": [],
      "evidence": [
        {
          "line": 6,
          "path": "pyproject.toml"
        }
      ],
      "conflicts": [],
      "gaps": [],
      "coverage": {
        "files": 2,
        "members": 1,
        "resolved": 1,
        "source_files": 2
      },
      "match": "exact",
      "relations": [
        {
          "kind": "contains",
          "direction": "incoming",
          "module": "spike-demo",
          "status": "confirmed",
          "evidence": [
            {
              "line": 6,
              "path": "pyproject.toml"
            }
          ],
          "evidence_total": 1
        }
      ],
      "read_scope": [
        {
          "module": "spike-demo",
          "name": "spike-demo",
          "relation": "contains",
          "direction": "incoming",
          "status": "confirmed",
          "paths": [
            "."
          ],
          "excluded": [
            "packages/tmp_alpha",
            "packages/tmp_alphabeta"
          ]
        }
      ]
    },
    {
      "id": "tmp-alphabeta",
      "name": "tmp_alphabeta",
      "aliases": [],
      "provenance": "build",
      "kind": "workspace-member",
      "description": null,
      "responsibility": "",
      "status": "confirmed",
      "paths": [
        "packages/tmp_alphabeta"
      ],
      "excluded": [],
      "files": [
        "packages/tmp_alphabeta/__init__.py",
        "packages/tmp_alphabeta/beta.py"
      ],
      "members": [
        {
          "id": "packages/tmp_alphabeta",
          "kind": "directory",
          "path": "packages/tmp_alphabeta",
          "resolved": true
        }
      ],
      "manifests": [],
      "evidence": [
        {
          "line": 6,
          "path": "pyproject.toml"
        }
      ],
      "conflicts": [],
      "gaps": [],
      "coverage": {
        "files": 2,
        "members": 1,
        "resolved": 1,
        "source_files": 2
      },
      "match": "partial",
      "relations": [
        {
          "kind": "contains",
          "direction": "incoming",
          "module": "spike-demo",
          "status": "confirmed",
          "evidence": [
            {
              "line": 6,
              "path": "pyproject.toml"
            
```

## (c) Ordinamento search/graph stabile su ripetizione: si

### Estratto outline

```json
{
  "schema": "xray/source-reading/v1",
  "root": "C:/Users/alfio/AppData/Local/Temp/opencode/scope-resolution-spike-5z69wo6b",
  "target": ".",
  "scope": {
    "git_ignore": "unavailable",
    "skipped": {
      "dot_directories": [],
      "git_ignored": 0
    }
  },
  "inventory": {
    "files": 5,
    "schema": 1,
    "created_at": "2026-11-05T09:22:43Z",
    "parser_fingerprint": "4f79c2144dad4cd6c07d35c3a37cb90c0084da04fddf6c25d24c4e97503dd075"
  },
  "items": [
    {
      "path": "packages/tmp_alpha/alpha.py",
      "symbol": "alpha_entry",
      "kind": "function",
      "start": 4,
      "end": 5,
      "span_precision": "exact",
      "language": "python",
      "status": "parsed",
      "lines": 6,
      "parser_notes": [
        "parser=stdlib-ast"
      ]
    }
  ],
  "matched": 1,
  "truncated": false,
  "run_id": "spike-1"
}
```

### Estratto graph

```json
{
  "schema": "xray/source-graph/v1",
  "root": "C:/Users/alfio/AppData/Local/Temp/opencode/scope-resolution-spike-5z69wo6b",
  "target": ".",
  "scope": {
    "git_ignore": "unavailable",
    "skipped": {
      "dot_directories": [],
      "git_ignored": 0
    }
  },
  "inventory": {
    "files": 5,
    "schema": 1,
    "created_at": "2026-11-05T09:22:43Z",
    "parser_fingerprint": "4f79c2144dad4cd6c07d35c3a37cb90c0084da04fddf6c25d24c4e97503dd075"
  },
  "manifest_digest": "944fc777c52689da4a272619f5833dffa356516d75fd092dd61ea3e3f9bac871",
  "query": {
    "hops": 1,
    "limit": 100,
    "path_count": 1,
    "whole_inventory": false,
    "paths": [
      "packages/tmp_alpha/alpha.py"
    ]
  },
  "totals": {
    "query_paths": 1,
    "calls": 1,
    "declarations": 1,
    "imports": 0,
    "coverage": 5,
    "import_cycles": 0,
    "transitive_importers": 0,
    "pagerank": 5,
    "cycle_members": 0,
    "requests": 1,
    "request_ranges": 1
  },
  "truncated": [],
  "calls": [
    {
      "scope": "scope-function@4:0",
      "parts": [
        "beta_helper"
      ],
      "kind": "call",
      "span": [
        5,
        11,
        5,
        22
      ],
      "caller": "packages/tmp_alpha/alpha.py::function@4:0",
      "id": "packages/tmp_alpha/alpha.py::reference#0",
      "file": "packages/tmp_alpha/alpha.py",
      "target_id": null,
      "resolution": "unresolved",
      "reason": "import-target-missing-or-ambiguous",
      "resolver": "builtin-lexical",
      "k
```

### Estratto read

```json
{
  "schema": "xray/source-reading/v1",
  "root": "C:/Users/alfio/AppData/Local/Temp/opencode/scope-resolution-spike-5z69wo6b",
  "target": ".",
  "scope": {
    "git_ignore": "unavailable",
    "skipped": {
      "dot_directories": [],
      "git_ignored": 0
    }
  },
  "inventory": {
    "files": 5,
    "schema": 1,
    "created_at": "2026-11-05T09:22:43Z",
    "parser_fingerprint": "4f79c2144dad4cd6c07d35c3a37cb90c0084da04fddf6c25d24c4e97503dd075"
  },
  "files": [
    {
      "path": "packages/tmp_alpha/alpha.py",
      "raw_hash": "d042f0ec90ce9cf7a66cc2d20a69299a1adaeeac09c94f2724393c92848f2fb9",
      "hash": "sha256:2061971cdb344895",
      "status": "parsed",
      "parser_profile": {
        "language": "python",
        "backend": "stdlib-ast"
      },
      "parser_notes": [
        "parser=stdlib-ast"
      ],
      "notes": [],
      "blocks": [
        {
          "start": 1,
          "end": 3,
          "reason": "context-and-selection",
          "source": "1: from tmp_alphabeta.beta import beta_helper\n2: \n3: \n"
        },
        {
          "start": 6,
          "end": 6,
          "reason": "context-and-selection",
          "source": "6: \n"
        }
      ]
    }
  ],
  "metrics": {
    "source_bytes_read": 108,
    "source_lines_emitted": 4,
    "source_characters_emitted": 46
  },
  "run_id": "spike-1"
}
```
