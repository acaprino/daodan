# Benchmark: connection points between a front end and a back end

Does the connection-point model join a React front end and an Express back end into one graph, with nothing
invented and nothing lost? A connection point is a node with a kind and a key; code sites attach to it with a
role (`calls`, `exposes`). Here the kind is `http` and the key is the method plus the path, parameters as `{}`.
First measurement, one real case.

## Parameters

| Parameter | Value |
| --- | --- |
| case | [chrisvel/tududi](https://github.com/chrisvel/tududi) at `71da9d7b34dfd1600657e9c5ddf40420206fd263` (as in `benchmarks/inference-audit`) |
| perimeter | front end: the 483 `.ts`/`.tsx`/`.js` files under `frontend/` that are not tests; back end: the Express app `backend/app.js` as it loads with `NODE_ENV=test` and a database URL it never connects to |
| expected | `expected.json`: 20 links across features and 5 hard cases, written from the source before any extraction code |
| back end | `express_routes.js` (99 lines): the running app's own Express, patched before load, records every mount and route; full path through every mount, registration line, handler location from V8 (`[[FunctionLocation]]`); checked on `fixtures/express` in the container (10 of 10 routes) |
| front end | `client_http.py` (314 lines with docstrings): tree-sitter 0.26.0 and language pack 1.13.5 read the request each `fetch` sends; the index (the TypeScript graph of `inference-audit`, label `plugin`) confirms the sink and every wrapper call |
| declared rules | `rules.json`: the sink `fetch`, and `getApiPath` as a prefix rule (`/api/` unless the path has it), because its body depends on the deployment's base path |
| join, islands | `points.py` (124 lines), no language: exact and loose matches, uncertain links with candidates, one-sided keys with their reason |
| existing tools | express-list-endpoints 7.1.1 (runtime), ast-grep 0.50.0 (structural search), jsluice `0ddfab153e06` (URLs in JavaScript), swagger-jsdoc of the project (declared API) |
| graph | `graph-javascript.json.gz` and `graph-typescript.json.gz` of `inference-audit/scip-inputs/tududi/plugin` (scip-typescript 0.5.2); callable nodes: code holders and the callables reached, types and parameters left out |
| runtime | Node 22.12.0 (22.11 refuses `require()` of the ES module `jose`), `npm ci` 26.7 s, whole run 44.1 s on 2 CPU |

Run:

    modal deploy benchmarks/connection-points/modal_points.py
    python -I benchmarks/connection-points/modal_points.py tools --out results/tools-tududi.json
    python -I benchmarks/connection-points/analyze.py results/tools-tududi.json GRAPH_DIR results/tududi.json

`survey` (same file) lists the greps used to read the source for `expected.json`. Tests:
`python -B -m pytest -q -p no:cacheprovider` in this folder (20).

## Results, 14 November 2026

Code hash `40e61f0bbf63`, the same locally and in the container. Modal cost 0.038 USD for every run
(two surveys, four tool runs, one fixture check each).

### Existing tools

| Tool | Gives | Misses |
| --- | --- | --- |
| express-list-endpoints | 695 method and path pairs with every mount prefix (`/api`, `/api/v1`, `/api/caldav`); 684 the same as the recorder | no file, no line, no handler; `ALL` routes as an empty method list, trailing slashes kept (the 11 and 17 differences, all CalDAV) |
| ast-grep, `$R.$M($P, $$$A)` | 363 registrations with their line, 350 with a literal path | the mount prefix: the app mounts every module in `registerApiRoutes(basePath)` over a `Set`, so no static path is a full path; 13 paths are variables or templates; 13 registrations outside the filter it needs (receivers named other than `router`/`app`, the verb `options`) |
| ast-grep, `fetch($$$A)` | 323 call sites | the argument stays text: no prefix, no constant, no wrapper |
| jsluice | 431 strings, 12 `fetch` records with 6 URLs | every URL built by `getApiPath` (300 of the 323 `fetch` calls), no line |
| swagger-jsdoc | 44 documented operations, 42 served | 2 documented and not served: `PATCH /api/v1/task/{}/toggle_completion`, `POST /api/v1/tasks/generate-recurring` |
| runtime recorder (own) | 701 keys at 362 registration lines, each handler's file and line | 14 landing-page routes (`backend/modules/landing/routes.js`): that router is built on the first request from a landing host, never at load |

### Counts

| | |
| --- | --- |
| routes exposed (keys) | 705: 347 under `/api`, 327 under `/api/v1`, 31 others (CalDAV protocol, OAuth metadata, the SPA fallback); 323 handlers |
| HTTP call sites | 373: 316 direct `fetch`, 57 through 7 wrappers (`fetchWithCsrf` 29, three `send` 19, `post` 5, `readPublic` 2, `download` 2) |
| links joined | 361 at 360 sites, 300 routes: 360 exact, 1 loose |
| uncertain links | 5 sites: `${kind}/${uid}/attachments` and its PATCH, DELETE, POST (27, 7, 7, 4 candidates), `shares/invitations/${id}/${action}` (accept or decline) |
| routes nobody calls | 371: 311 of the `/api/v1` mirror (versioned clients), 31 others, 29 under `/api`; 34 more appear only as uncertain candidates |
| calls to routes that do not exist | 1: `frontend/utils/profileService.ts:217` `POST /api/telegram/test/{}`; no such route, and `testTelegram` has no caller |
| keys built at run time (holes) | 7: 6 locale files through `getLocalesPath()`, 1 `attachment.file_url` from data (`frontend/components/Shared/AttachmentPreview.tsx:26`) |
| not joined, reported | 1 branch of `tasksService.ts:44` (`tasks${query}&include_lists=true`, its other branch links); 7 API paths used outside a request (avatars in `<img>`, download links); 2 calls named like a wrapper the index does not link to it (`FeedbackModal.tsx:113`, `:123`) |

Of the 29 `/api` routes nobody calls: 4 downloads the browser loads through links (the 7 paths outside
requests), outside callers (Stripe webhook, MCP, health, API docs, e-mail link), and routes without a caller
in the front end (`GET /api/areas/{}`, `GET /api/inbox/{}`, `GET /api/users`, `GET /api/quotes`).

### Expected cases

25 of 25 found: 24 exact, case 1 loose (`tasks${tasksQuery}`: the variable is glued to the segment). Every
named handler (`symbol` in `expected.json`) is the function the recorder located. Hard cases: H1 two branches
of `url`, one route; H2 `fetchWithCsrf(getApiPath('admin/users'))`; H3 `/api/caldav` mounted by a router
mounted at the root, under `/api` only; H4 two parameters; H5 `GET /api/areas/{}` without callers.

### Islands, before and after

| | Callable nodes | Components | Five largest | Singletons | Largest share |
| --- | --- | --- | --- | --- | --- |
| before | 8,364 | 241 | 4,186 (front end), 3,849 (back end), 14, 11, 11 | 201 | 50.0% |
| with the points | 9,065 (+701 points) | 237 | 8,739, 14, 11, 11, 9 | 198 | 96.4% |

Front-end functions (named code holders outside tests) that reach a back-end handler: 487 of 2,009, none
before. Roots (front-end functions nothing in the front end references): 28 of 69 reach one; the others are
formatters, editor widgets the editor calls, unused exports.

A chain from a UI component to the database:

1. `frontend/components/CalDAV/ConflictResolver.tsx:39` `ConflictResolver`, calls at `:171`
2. `frontend/utils/caldavService.ts:341` `resolveConflict`, `fetch` at `:347`
3. point `POST /api/caldav/conflicts/{}/resolve`, registered at `backend/modules/caldav/api/routes.js:36`
4. `backend/modules/caldav/api/sync-controller.js:142` `SyncController#resolveConflict`, calls at `:175`
5. `backend/modules/caldav/sync/merge-phase.js:553` `MergePhase#resolveConflict`
6. `backend/modules/caldav/sync/merge-phase.js:563` `Task.findByPk`: a hole of the graph (the model is `any` to the index), read from its text

### What did not fit the model

- A site has a set of keys, not one: branches and `let` with `+=` give candidates, and both sides carry
  placeholders, so the join matches patterns, not equal strings.
- A placeholder for a value that selects the entity (`${kind}`) makes a key match 27 routes: the model's
  uncertain link holds, the static types of `kind` could narrow it and are not read.
- The method is part of the key, but `ALL` routes and an unknown method need a wildcard, and the SPA fallback
  `GET *` answers every path: matched only by it counts as a missing route.
- One handler under two keys (`/api` and `/api/v1`): "routes nobody calls" is mostly the version mirror.
- Project helpers build keys: `getApiPath` needs a declared rule; seven wrappers pass the URL through a
  parameter, so the calling site moves to their callers, which only the index links.
- The browser loads API paths without a request call (`<img src>`, links, `window.open`): no role for them yet.
- An anonymous inline handler has no node in the graph; it attaches to its file's module node.
- Exposure depends on configuration: a router built per request is invisible at load, visible to the
  static reader, which in turn misses every mount prefix.

### Not verified

- `public/sw.js` and the end-to-end tests also send requests; they are outside the perimeter.
- The 371 routes without callers are not checked one by one beyond the `/api` list above.
