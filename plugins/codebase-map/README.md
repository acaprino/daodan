# Codebase Map

**Responsabilità:** spiegare che cosa fa il codice, dove lo fa e quali parti sono collegate, con riferimenti verificabili alle sorgenti.

Funziona come prodotto autonomo. senior-review ne usa il contesto; la mappa non seleziona reviewer e non emette verdetti di correttezza.

Il disegno distingue inventario, relazioni statiche e osservate, descrizioni semantiche con provenienza, ipotesi e informazioni mancanti. Aggiorna le informazioni interessate da una modifica e carica il codice necessario alla domanda corrente.

Le sorgenti rimangono l'autorità. L'analisi è l'intera pipeline, non il solo passo statico: ciò che parser e indicizzatori lasciano aperto lo prende il passo dinamico, che nel container osserva le chiamate che i test e l'app del progetto eseguono, e prova soltanto quelle; ciò che resta dopo l'ultimo passo è un buco dichiarato. I passi, che cosa ognuno lascia aperto e dove è misurato: [Pipeline](../../docs/plugins/codebase-map.md#pipeline). Gli embedding locali sono opzionali e disattivati (`skills/map/references/embeddings.md`): ricerca lessicale e grafo restano il percorso predefinito finché un esperimento non dimostra un vantaggio.

## Stato

Versione **1.0.1**. Il manifest non dichiara dipendenze da altri plugin.

Installazione: `claude plugin install codebase-map@daodan` (marketplace `acaprino/daodan`). Ingresso: la skill `/codebase-map:map <richiesta>`; il plugin non contiene codice: il server MCP `codebase-map` è il comando `daodan mcp` dell'applicazione installata a parte (`uv tool install git+https://github.com/acaprino/daodan`, `.mcp.json`), e ogni strumento di `daodan/core/` parte come `daodan <nome>`. Nei testi `${CLAUDE_PLUGIN_ROOT}` indica la radice del plugin installato; in Bash la variabile non è impostata e il percorso si ricava dalla directory della skill.

- Grafo dei moduli: `daodan modules`, contratto in `skills/map/references/modules.md`. Unità di build lette dai manifest (quanti e di quali ecosistemi: [Supporto](../../docs/plugins/codebase-map-supporto.md)), moduli dichiarati dal progetto in `codebase-modules.json`, moduli proposti da un modello e verificati sullo snapshot; derivato accanto allo snapshot da `daodan snapshot write` e interrogabile per nome.
- Linguaggi supportati (17, 63 estensioni): Python, Java, JavaScript, TypeScript, SQL (con grafo semantico tabellare e `sqlglot`), PL/SQL, Rust, Go, Kotlin (`.kt`, `.kts`), C# (`.cs`), C e C++, Vue (`.vue`), Svelte (`.svelte`), Astro (`.astro`), CSS/SCSS/Sass/LESS/PostCSS e i blocchi `<style>` del markup, più ponte cross-linguaggio Tauri (`invoke` ↔ `#[tauri::command]`); parser, analyzer, osservatori, strumenti e licenze in [Linguaggi](../../docs/plugins/codebase-map-linguaggi.md).
- Risoluzione delle chiamate: risolutore lessicale più la pipeline che parte con ogni snapshot: un analyzer per tecnologia, il passo dinamico sui test e sull'app del progetto nel container di Daodan e l'unione dei grafi ([Pipeline](../../docs/plugins/codebase-map.md#pipeline)); la copertura si legge per linguaggio ([Copertura](../../docs/plugins/codebase-map.md#copertura)).
- Python richiesto: **>= 3.12**.
- `tree-sitter`, `tree-sitter-language-pack` e `sqlglot` arrivano con l'applicazione installata, alle versioni fissate in `pyproject.toml`.
- Mappa del sistema: `codebase_map_flows` con `brief`, `map`, `about` e `levels` propone e verifica nodi con un nome, flussi e livelli; formato in `daodan/references/system-map.md`, agente `system-mapper`, che i due ingressi dispacciano a fine analisi.
- Esploratore: `daodan visual export <run>` pubblica la vista di un run e `daodan visual serve <export>` la apre su `127.0.0.1`, con viste Logica e Fisica, flussi e tipi di nodo; comandi in `skills/map/references/standalone.md`.

[Disegno comune](../../docs/specs/2026-11-03-semantic-review-foundation.md) · [Riferimento del plugin](../../docs/plugins/codebase-map.md)
