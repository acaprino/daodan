# Brief: reference system map of one project

You write the reference ("gold") system map of one project for Daodan's benchmark `benchmarks/system-map`.
It is the map a person who knows the product well would draw: one node for the whole system, then the parts a
person names, then the screens, groups of routes, scheduled jobs, data and external services, and the flows that
cross them. Daodan's own output will be scored against it later, so it must be right and derived on your own:
every node and every arrow cites a real line of the project.

Your prompt gives `ROOT` (the project), `OUT` (the file you write), `CASE`, the expected size and anything
specific to the project.

## Hard rules

1. Read only. Never run the project's code: no build, install, test, script, dev server, package manager or
   interpreter on a file of the project. Use Read, Grep, Glob and read-only shell commands (`ls`, `git ls-files`,
   `wc`, `git log`). No network.
2. Change nothing under `ROOT`. You write `OUT` and nothing else.
3. Never open or cite a file of secrets (`secrets.json`, a `.env` that is not a template, keys, keystores).
   Never copy a token, key or password into `OUT`.
4. Do not read analysis artifacts of Daodan or earlier maps of this project (folders such as `.codebase-map`,
   `.daodan`, `artifacts` made by a tool), except what your prompt hands you. Derive from source, manifests,
   configuration and the project's own documentation. Documentation is a hint: wherever a claim can be cited in
   code or configuration, cite it there.
5. Do not delegate to other agents.
6. The one program you may run: `python D:\Projects\daodan\benchmarks\system-map\reference.py check OUT ROOT`.
   It is Daodan's checker, it only opens files.

## Format

Read these first, they are short:

- `D:\Projects\daodan\benchmarks\system-map\README.md`, section «Riferimenti dell'intero sistema»: the fields.
- `D:\Projects\daodan\daodan\core\system_map.py`, lines 1 to 45: what a node, a flow and an arrow are, and the
  closed lists (`NODE_TYPES`, `POSITIONS`, `FLOW_TYPES`, `AREAS`, `ARROW_KINDS`). The references add the node types `filesystem`,
  `applicazione` and `lavoro a orario` and the flow type `devops`.
- `D:\Projects\daodan\docs\specs\2026-11-18-flussi-e-mappa-del-sistema.md`, the section «Parole» and
  sections 2 and 3: the meaning of every word.
- `D:\Projects\daodan\benchmarks\system-map\test_reference.py`: `GOOD` is a tiny valid reference.

`OUT` is one JSON object:

```json
{"case": "CASE", "root": "folder name", "scope": "sistema", "made": "2026-11-19",
 "nodes": [], "flows": [], "areas": [], "packages": [], "gaps": []}
```

- Node: `name`, `type`, `position` (`internal` by default, `external`, `unseen`), `inside`, `what`, `members`
  (a file, a folder, `path::Symbol`, `store:<store>/<key>`; only on an internal node, at least one), `evidence`
  (`path` or `path:line`; required on an external node), `on` (the nodes it sits on: an interface on its device,
  an entity on its database, a service on the machine or cloud service that runs it), `where` (unseen only),
  `routes` (`METHOD /path`), `proof` (at least one `{"at": "path:line", "has": "text that line holds"}`).
- Flow: `name`, `area`, `types`, `nodes`, `arrows` (`from`, `to`, `data`, `kind`, `cite` as `path:line`, `has`),
  `entries` and `effects` (`node`, `kind`, `what`).
- `areas`: each of the eight areas of `AREAS` with `present` true or false, plus any area the project has and
  the list lacks.
- `packages`: every unit the toolchain sees, `{"path", "manifest", "kind"}` (`npm-package`, `cargo-crate`,
  `python-package`, …).
- `gaps`: `{"what", "why"}` for everything you could not establish.

Paths are relative to `ROOT`, with forward slashes. `has` is an exact piece of the cited line (the checker looks
three lines around it), short and distinctive: a route, a function name, a call.

## How to model (decided by the owner of Daodan)

- Names follow «Names» in `D:\Projects\daodan\daodan\references\system-map.md`, in Italian. Never one node per symbol.
- `inside` gives the drill-down. Exactly one node is the whole system (type `altro`, named as the product, no
  `inside`). Depth 1: the parts a person names (each app, site, server or API, admin panel, worker). Depth 2:
  what each part is made of (a screen or a group of screens, a group of routes, a job, a store). Depth 3 where a
  depth-2 node is still large. A leaf is a screen, a group of routes, a job, an entity, a store.
- A whole app or site that a person opens, holding screens and logic, is an `applicazione`. A job that a schedule
  starts is a `lavoro a orario`; a queue consumer stays a `coda`.
- A database is a part at depth 1, type `database`, internal (its members are the files that define the schema, the
  collections or the connection), `on` the service that hosts it, with its entities inside it. A store on disk stays
  inside the part that owns it.
- A part of the app is a node even when it has no manifest of its own: an admin page that a server offers from
  a subfolder is a `schermata` inside that server.
- Interfaces (`schermata`), endpoints (`servizio o API`), scheduled jobs and queue consumers, devices, external
  services and stores are nodes, because a flow enters or leaves through them.
- Above every interface sits the device it runs on: a `dispositivo` node, position `external`, evidence the
  configuration that declares the target. One node per kind of device (Browser, PC Windows, Telefono Android).
  The interface names it in `on`.
- A shell (Tauri, Electron) and the page it hosts are two nodes.
- A file or folder on disk that the program reads or writes while it runs is a `filesystem` node, whatever the
  use (archive, lock, cache, output). Files embedded at build time are code.
- Outgoing mail through SMTP is an external `servizio o API`.
- An external service (it runs elsewhere: Stripe, Firebase) is an external node; its evidence is the files that
  bind to it. A dependency (framework, library, runtime) is not a node. Every external node that is not an
  `attore`, `dispositivo` or `filesystem` has three fields: `family`, either `provider` (it makes the program work:
  Stripe is the payment processor) or `piattaforma di integrazione` (a system of others the program connects to in
  order to exchange data: Booking.com, from which a listing is imported); `role`, what it is for the program, a
  short Italian phrase («processore dei pagamenti», «invio delle email», «fonte degli annunci»); `mode`, how the
  program connects to it, a short Italian phrase («chiamate API e avvisi di ritorno», «importazione una tantum dalla
  pagina», «sincronizzazione nei due sensi», «protocollo di posta»).
- Named data (an order, a user) is an `entità`; its members are its representations (the model file, the
  collection or table as `store:<store>/<key>`). Where it lives is a `database`, `coda` or `filesystem` node,
  named in `on`.
- A part of the system whose files are outside `ROOT` is `unseen`, with `where`.
- Actors are the roles of people. What starts a flow without a person is the external service that calls or the
  device. A schedule is an entry of the service that runs it, not an actor.
- Flows: everything the system does that a person would name (`funzionale`), what runs without a person
  (`operativo`: schedules, queues, webhooks), the machinery of the running product (`tecnico`: cache, sync, error log), what builds, packages, releases or trains at
  development time (`devops`), one piece of
  information kept in several places (`dati`, arrows of kind `stessa informazione`), what passes through
  physical devices (`hardware`). In `nodes` prefer the most specific nodes. `data` is what passes, a short
  Italian noun phrase.
- Draw only an arrow you can cite: the call, the request, the route declaration, the write. A link you believe
  in and cannot find goes in `gaps`.
- Every top-level source folder and every package is owned by the members of some node, or is in `gaps` with the
  reason (generated, vendored, tooling, documentation, data).

## How to work

1. Inventory: `git ls-files` by folder, manifests, entry points, routers, navigation and menus, data models,
   schedules, configuration of external services, deployment files.
2. Draft the hierarchy top-down, then the flows. Locate with Grep, read only what decides a name, a cut or a
   citation. Do not read every file.
3. Write `OUT` early and grow it; keep it valid JSON.
4. Run the checker and correct until `problems` is empty. A problem you cannot correct means the node or the
   arrow is not proved: remove it and add a gap.
5. Read again in the code the three most important flows, arrow by arrow.

## What you answer

Counts (nodes by depth and by type, flows, arrows), the gaps, and the five modeling choices you are least sure
of. No narration of what you did.
