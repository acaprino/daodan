# Codebase Map

**Responsabilità:** spiegare che cosa fa il codice, dove lo fa e quali parti sono collegate, con riferimenti verificabili alle sorgenti.

Funziona come prodotto autonomo. senior-review ne usa il contesto; la mappa non seleziona reviewer e non emette verdetti di correttezza.

Il disegno distingue inventario e relazioni statiche, descrizioni semantiche con provenienza, ipotesi e informazioni mancanti. Aggiorna le informazioni interessate da una modifica e carica il codice necessario alla domanda corrente.

Le sorgenti rimangono l'autorità. L'analisi statica non prova il comportamento a runtime: il passo dinamico osserva, nel container, le chiamate che i test del progetto eseguono, e prova soltanto quelle. Gli embedding locali sono opzionali e disattivati (`skills/map/references/embeddings.md`): ricerca lessicale e grafo restano il percorso predefinito finché un esperimento non dimostra un vantaggio.

## Stato

Versione **1.0.1**. Il manifest non dichiara dipendenze da altri plugin.

Installazione: `claude plugin install codebase-map@daodan` (marketplace `acaprino/daodan`). Ingresso: la skill `/codebase-map:map <richiesta>`; il plugin non contiene codice: il server MCP `codebase-map` è il comando `daodan mcp` dell'applicazione installata a parte (`uv tool install git+https://github.com/acaprino/daodan`, `.mcp.json`). Prima mappa completa di questo repository: 7 novembre 2026, profondità lite. Nei testi `${CLAUDE_PLUGIN_ROOT}` indica la radice del plugin installato; in Bash la variabile non è impostata e il percorso si ricava dalla directory della skill.

- Grafo dei moduli: `daodan modules`, contratto in `skills/map/references/modules.md`. Unità di build lette dai manifest di 27 ecosistemi, moduli dichiarati dal progetto in `codebase-modules.json`, moduli proposti da un modello e verificati sullo snapshot; derivato accanto allo snapshot da `snapshot.py write` e interrogabile per nome.
- Linguaggi supportati (16 canonici, 63 estensioni): Python, Java, JavaScript, TypeScript, SQL (con grafo semantico tabellare e `sqlglot`), PL/SQL, Rust, Go, Kotlin (`.kt`, `.kts`), C# (`.cs`), C e C++, Vue (`.vue`), Svelte (`.svelte`), CSS/SCSS/Sass/LESS/PostCSS e i blocchi `<style>` del markup, più ponte cross-linguaggio Tauri (`invoke` ↔ `#[tauri::command]`); strumenti e licenze in [Linguaggi](../../docs/plugins/codebase-map-linguaggi.md).
- Risoluzione delle chiamate: risolutore lessicale più la pipeline che parte con ogni snapshot: un analyzer per tecnologia, il passo dinamico sui test del progetto nel container di Daodan e l'unione dei grafi ([Pipeline](../../docs/plugins/codebase-map.md#pipeline)); la copertura si legge per linguaggio ([Copertura](../../docs/plugins/codebase-map.md#copertura)).
- Python richiesto: **>= 3.12**.
- `tree-sitter`, `tree-sitter-language-pack` e `sqlglot` li installa il server MCP; uno snapshot da shell li usa se installati.
- Mappa del sistema: `codebase_map_flows` con `brief`, `map`, `about` e `levels` propone e verifica nodi con un nome, flussi e livelli; formato in `daodan/references/system-map.md`, agente `system-mapper`.
- Esploratore: `daodan visual export <run>` pubblica la vista di un run e `visual.py serve <export>` la apre su `127.0.0.1`, con viste Logica e Fisica, flussi e tipi di nodo; comandi in `skills/map/references/standalone.md`.

[Architettura](../../docs/specs/architettura.md) · [Piano](../../docs/plans/refactoring.md) · [Riferimento del plugin](../../docs/plugins/codebase-map.md)
