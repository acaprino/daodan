# Which tool answers which question

For whoever has to choose a tool on a bound run. Parameters and return shapes
are in `mcp.md`; this page says what each tool is for. Examples use the small
orders app in `benchmarks/scope-resolution/app/`, with paths shortened.

| Tool | Question it answers | Example | What it does not do |
|---|---|---|---|
| `codebase_map_search` | Where does this name, error text or domain word appear? | `search("sconto")` → `rates.py::volume_discount`, `pricing.py::compute_discount`, plus `@file` hits | Does not read source or follow calls. It also matches docstrings, and identifiers split into subtokens: `search("VAT_RATE")` ranks `rates.py::shipping_rate` first. A `gaps` entry naming `codebase_map_index` is a broken index, not an empty search |
| `codebase_map_modules` | Which modules exist, or which files belong to module X? | `modules(query="shipping")` → `resolved`, files `packages/shipping/*` | Does not search inside files. `needs_clarification`: several modules match. `incomplete`: members still to confirm. `unknown`: no match. Descriptions locate code; they do not prove behavior |
| `codebase_map_outline` | Which symbols does this file define, and at which lines? | `outline(path="pricing.py")` → `vat_amount 6-8`, `compute_discount 11-14`, `compute_total 17-20` | No bodies, no imports. Past `limit` the listing is truncated, so it is not complete |
| `codebase_map_graph` | Starting from these files, who calls whom? | `graph(paths=["service.py"], hops=1)` → `checkout → pricing.compute_total`, `checkout → ledger.record`; `self._pipeline.step` unresolved | `paths` takes files, never `file::symbol`. A dynamic call or a registry lookup stays `unresolved`: the edge is unproven, not absent |
| `codebase_map_read` | Show me this piece of source. | `read([{"path": "refunds.py", "symbols": ["vat_portion"]}])` | With only a path it returns the lines outside symbols, no function bodies: ask for `symbols`, `ranges` or `full_file`. A range past the end of the file is an error |
| `codebase_map_edit_impact` | If I change this symbol, who is affected? | `edit_impact(["pricing.py::compute_discount"])` → caller `pricing.py::compute_total`; the same call on `compute_total` → `service.py::OrderService.checkout` | Evidence and leads, never a verdict. One hop of callers per call; `hops=2` adds second-hop signatures. Use it when the request is about a change |
| `codebase_map_symbols_at` | Which symbol contains these lines? | `symbols_at([{"path": "pricing.py", "ranges": [{"start": 11, "end": 14}]}])` → `compute_discount`; with a `git diff` and the base run → every symbol the diff touches, on both sides | Does not search or widen a scope. A line outside every symbol is a declared gap (`outside-symbols`). Useful only with a diff or exact lines |
| `codebase_map_stale_callers` | Between two runs, which callers of changed symbols must be edited or re-validated? | `stale_callers(run, base_run)` → RED (edit), GREEN (validate), do-not-touch | Needs a base run. GREEN guides validation; it does not end reading |
| `codebase_map_scope` | What does the inventory cover, and what is excluded? | `scope()` → file counts, languages, declared exclusions | Starts no analysis. Only for "whole project" requests |

A Python module-level constant is not a symbol: `outline` does not list it,
`symbols_at` reports a gap and `edit_impact` returns it in `unknown_targets`.
Find it with `search` and confirm it with `read`.

Choosing, cheapest first: an explicit file needs no tool; a module name goes to
`modules`; a name, error or domain word goes to `search`; a flow expands with
`graph` one hop at a time from files already confirmed; `read` decides membership
and confirms dynamic links; `edit_impact` only when the request is about a change;
`symbols_at` only with a diff or exact lines. The loop with measurements is in
`locate.md`.
