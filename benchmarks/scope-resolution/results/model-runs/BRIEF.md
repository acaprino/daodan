# Brief: Phase 0 (sessione del modello)

Stabilisci *che cosa* rivedere per la richiesta ricevuta. Non rivedere il codice.

## Regole della sessione

- Con gli strumenti di lettura apri solo questo file. Il progetto di prova si legge solo con `mapcli.py`.
- Non aprire altro in `benchmarks/scope-resolution/`, `docs/` o `plugins/`.
- Non caricare skill e non lanciare altri agenti.
- Dichiara nel report ogni violazione.

## Procedura

Translate the request into the files to review.

1. **Find.** Take the names from the request: files, functions, modules,
   errors, terms. For each, the cheapest tool: explicit file → none; module →
   `codebase_map_modules`; name or word → `codebase_map_search`; flow →
   `codebase_map_graph`, one hop at a time from files already confirmed. Retry
   an empty search once with a synonym; a missing or stale index is not an
   empty search, it is a missing prerequisite.
2. **Confirm.** Respect explicit limits ("only this file", a diff); otherwise
   names are starting points and include only files pertinent to the request,
   with the line that shows it: `codebase_map_outline` for symbols,
   `codebase_map_read` only the part that decides. A request about a change
   includes the callers it affects (`codebase_map_edit_impact`). The graph does
   not see dynamic links or copies: do not invent them, search by name and read;
   if they cannot be confirmed, say so.
3. **Stop** when evidence suffices, when no leads remain, or at about 6
   queries and 10 reads. Always say why.
4. **Answer** with one of three outcomes: `resolved` (the files, each with its
   evidence); `partial` (the files found, what the request still needs and why); `clarify`
   (the request may mean two different things: the candidates and the question).

The scope is what the review judges; what it reads to judge is later context.
Everything else is your judgment, stated.

## Strumenti

Dalla cartella `D:\Projects\daodan\benchmarks\scope-resolution` esegui `python -B mapcli.py SESSION <comando>`.
Usa sempre il tuo SESSION. `PATH` è relativo al progetto, per esempio `packages/x/y.py`.

| Strumento | Comando | Domanda a cui risponde |
|---|---|---|
| `codebase_map_modules` | `modules [--query NOME]` | Quali moduli esistono, quali file ha il modulo X? |
| `codebase_map_search` | `search "QUERY" --lineage anchor:NOME` | Dove compare questo nome, errore o termine? |
| `codebase_map_graph` | `graph PATH [PATH ...] --hops 1` | Da questi file, chi chiama chi? |
| `codebase_map_outline` | `outline PATH` | Quali simboli definisce questo file? |
| `codebase_map_read` | `read PATH [--symbols a,b] [--ranges 10-40]` | Mostrami questo pezzo di codice |
| `codebase_map_edit_impact` | `impact PATH::Simbolo` | Se cambio questo simbolo, chi è coinvolto? |

`read` con il solo `PATH` restituisce solo le righe fuori dai simboli: per il corpo di una funzione usa `--symbols` o `--ranges`.
`--lineage` raggruppa le ricerche dello stesso nome, così una riformulazione si riconosce. Ogni comando accetta
`--why TESTO`, la tua motivazione in una riga.

## Esito: scrivi `final.json`

Scrivi `D:\Projects\daodan\benchmarks\scope-resolution\results\model-runs\SESSION\final.json` con solo questo JSON:

```json
{
  "outcome": "resolved | partial | clarify",
  "stop_reason": "perché ti sei fermato, in una frase",
  "perimeter": [{"path": "packages/...py", "why": "la riga o il simbolo che lo dimostra"}],
  "exclusions": [{"path": "packages/...py", "why": "perché lo hai escluso"}],
  "unresolved_calls": [{"caller": "path::simbolo", "callee": "nome", "resolution": "unresolved"}],
  "candidates": [{"target": "packages/...py", "why": "perché è un candidato"}],
  "question": "la domanda, oppure null",
  "residual": ["ciò che manca, oppure lista vuota"]
}
```

`candidates` e `question` valgono solo per `clarify`; altrimenti `null`. Non citare file che non hai visto con gli strumenti.

## Report finale (massimo 5 righe)

Esito, file, eventuali violazioni delle regole, e il punto in cui la procedura non ti ha permesso di decidere.
