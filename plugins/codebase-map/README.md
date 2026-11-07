# Codebase Map

**Responsabilità:** spiegare che cosa fa il codice, dove lo fa e quali parti sono collegate, con riferimenti verificabili alle sorgenti.

Funziona come prodotto autonomo. senior-review ne usa il contesto; la mappa non seleziona reviewer e non emette verdetti di correttezza.

Il disegno distingue inventario e relazioni statiche, descrizioni semantiche con provenienza, ipotesi e informazioni mancanti. Aggiorna le informazioni interessate da una modifica e carica il codice necessario alla domanda corrente.

Le sorgenti rimangono l'autorità. L'analisi statica non prova il comportamento a runtime. Gli embedding locali sono opzionali e disattivati (`skills/map/references/embeddings.md`): ricerca lessicale e grafo restano il percorso predefinito finché un esperimento non dimostra un vantaggio.

## Stato

Baseline sorgente **1.0.1** importata dal backup integrale del precedente Daodan. Il manifest è stato adattato alla nuova base a due proprietari e non dichiara dipendenze da altri plugin.

Installazione: `claude plugin install codebase-map@daodan` (marketplace `acaprino/daodan`). Ingresso: la skill `/codebase-map:map <richiesta>`; il server MCP `codebase-map` parte col plugin tramite `uv` (`.mcp.json`). Prima mappa completa di questo repository: 7 novembre 2026, profondità lite. Nei testi `${CLAUDE_PLUGIN_ROOT}` indica la radice del plugin installato; in Bash la variabile non è impostata e il percorso si ricava dalla directory della skill. Le istruzioni obbligatorie verso `report-rendering` e altri plugin assenti sono state rimosse o dichiarate non disponibili.

- Grafo dei moduli: `skills/map/scripts/modules.py`, contratto in `skills/map/references/modules.md`. Unità di build lette dai manifest di 27 ecosistemi, moduli dichiarati dal progetto in `codebase-modules.json`, moduli proposti da un modello e verificati sullo snapshot; derivato accanto allo snapshot da `snapshot.py write` e interrogabile per nome.
- Linguaggi supportati (13 canonici, 32 estensioni): Python, Java, JavaScript, TypeScript, SQL (con grafo semantico tabellare e `sqlglot` opzionale), PL/SQL, Rust, Go, Kotlin (`.kt`, `.kts`), C# (`.cs`), Vue (`.vue`), Svelte (`.svelte`) e CSS/SCSS/LESS, più ponte cross-linguaggio Tauri (`invoke` ↔ `#[tauri::command]`) e risoluzione simboli opzionale `--engine scip` o `--engine jedi` in `resolve_edges.py`.
- Python richiesto: **>= 3.12**.
- `tree-sitter` e `tree-sitter-language-pack` restano opzionali per il parsing ad alta fedeltà.
- La vista HTML storica non è disponibile: senza un renderer adattato, il report Markdown resta autoritativo.

[Disegno comune](../../docs/specs/2026-11-03-semantic-review-foundation.md) · [Riferimento del plugin](../../docs/plugins/codebase-map.md)
