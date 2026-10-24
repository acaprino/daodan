# Audit text-humanizer (D:\Projects\daodan) — run 20261024-text-humanizer-daodan

Modalità: sola lettura sul repo oggetto. Nessuna modifica, nessun rebuild, nessun commit.
Data: 24 ottobre 2026. Ambiente: Windows, Python 3.14.8, git disponibile, rete disponibile.

## Candidate

- Repo oggetto: D:\Projects\daodan, HEAD `cd942b0b980b9e73df6c7efab14be442eee9c076` ("Regenerate the project-lifecycle packages that master no longer reproduced").
- Working tree: 290 voci dirty all'inizio, 293 alla fine (delta attribuito alla sessione concorrente attiva su project-protocol; verificato con diff dei due `git status`). **Nessun percorso text-humanizer è dirty.**
- Ultimo commit che tocca il plugin: `297750780` "Commit the specialist reviewers, code context and usage ledger work" (24 ott 2026, 11:44 +0200), che contiene la riconciliazione selettiva con blader/humanizer v3.1.0.
- Evidenze del run di riconciliazione: `.daodan/runs/20261023-humanizer-upstream/` (head registrato `2f55484a…`, plugin 2.1.0, marketplace 38.8.5 al momento).
- Versioni attuali: plugin text-humanizer `2.1.0`; marketplace `38.10.1`; skill `anti-ai-writing-patterns`.
- Repository consumatore esaminato: D:\Projects\shinatama, HEAD `ced065ee` (24 ott 2026), working tree pulito.

## Esito sintetico

Nessun finding Critico. Il kernel del plugin è internamente coerente (conteggi 25/26, date, attribuzioni, licenza, regola dash) e i cinque export riproducono dai sorgenti; la parte fragile è l'integrazione: due riferimenti a un comando inesistente nei consumatori Shinatama, alcune affermazioni di consumo non supportate dagli artefatti, lacune di specifica sul write-back e lacune oggettive dei test.

## Findings

### F1 — Importante — Riferimenti a `/text-humanizer:humanize-text`, comando che non esiste più

- Evidenza:
  - `D:\Projects\shinatama\plugins\digital-marketing\workflows\llm-seo-audit.md:98`: "Humanizing AI-sounding copy to raise E-E-A-T -> `/text-humanizer:humanize-text`".
  - `D:\Projects\shinatama\plugins\digital-marketing\roles\llm-seo-optimize.md:231`: stessa rotta.
  - Presente anche negli export Shinatama: es. `D:\Projects\shinatama\exports\claude\plugins\digital-marketing\commands\llm-seo-audit.md:165`, `…\agents\llm-seo-optimize.md:298` e negli analoghi copilot/codex/opencode/pi.
  - Il plugin text-humanizer non ha comandi: `D:\Projects\daodan\plugins\text-humanizer\plugin.toml:17` (`workflows = []`) e i cinque package non contengono alcuna directory `commands/`.
  - L'entry corrente è `daodan:humanize-text`: `D:\Projects\daodan\plugins\daodan\plugin.toml:60`; render daodan `exports\opencode\package.json:637-641` (`"name": "daodan:humanize-text"`).
  - Date: i file Shinatama sono fermi al 15 ott 2026 (git log: `ae8c0b75`); la consolidazione dei comandi in `daodan` è del 19 ott 2026 (`8ed4a5680`).
- Impatto: la rotta suggerita all'utente è morta su tutti e cinque gli host; il passaggio di umanizzazione del flusso E-E-A-T viene perso o genera un comando non trovato.
- Classificazione: fatto verificato. Confidence: alta.

### F2 — Minore — Documentazione Shinatama non aggiornata dopo lo spostamento del plugin (link rotto e attribuzione errata)

- Evidenza:
  - `D:\Projects\shinatama\docs\plugins\digital-marketing.md:60` rimanda a `[text-humanizer](text-humanizer.md)`; il file `D:\Projects\shinatama\docs\plugins\text-humanizer.md` **non esiste** (verificato). La stessa riga ripete il comando inesistente di F1.
  - `D:\Projects\shinatama\docs\plugins\business.md:7`: "Two local plugins are hard dependencies: `text-humanizer`, whose agent `business-planner` runs over the final GTM strategy document". `business-planner` è un ruolo del plugin business (`plugins\business\roles\business-planner.md:59-63`), non di text-humanizer; e text-humanizer è dipendenza **esterna** (`text-humanizer@daodan`, `docs\catalog.md:53`, `plugins\business\plugin.toml:12`), non "local".
- Impatto: link 404 e proprietà dei ruoli/dipendenze invertita in pagina di consultazione.
- Classificazione: fatto verificato. Confidence: alta.

### F3 — Minore — La descrizione del plugin e la sua pagina docs sovrastimano il consumo da parte di project-lifecycle

- Evidenza:
  - `D:\Projects\daodan\plugins\text-humanizer\plugin.toml:4`: "consumed by project-knowledge and project-lifecycle, and by digital-marketing and business in Shinatama"; `docs\plugins\text-humanizer.md:3` e `:118` ripetono il consumo da project-lifecycle ("reuses the voice editor when an authorized knowledge operation needs it").
  - `plugins\project-lifecycle\plugin.toml:12` non dichiara text-humanizer; grep di `humanizer|humanize|voice` su tutto `plugins\project-lifecycle` → 0 occorrenze; la sua closure lo include solo transitivamente via project-knowledge (`docs\plugins\project-lifecycle.md:134-136`: Direct local senza text-humanizer, Local closure (19) con lui; `docs\plugins\project-knowledge.md:110` lo ha come direct).
  - Contraddizione fra tabelle: `D:\Projects\shinatama\AGENTS.md:412` elenca text-humanizer fra le direct required di project-lifecycle; `D:\Projects\daodan\AGENTS.md` (riga project-lifecycle) non lo elenca.
- Impatto: affermazione vera solo in senso transitivo; un audit di dipendenze o una campagna di aggiornamento può essere instradato male. Nessun impatto a runtime (la closure è soddisfatta via project-knowledge).
- Classificazione: fatto verificato. Confidence: alta.

### F4 — Minore — Il metodo dichiara un consumatore `text-only` che non esiste negli artefatti consumatori

- Evidenza:
  - `D:\Projects\daodan\docs\plugins\text-humanizer.md:30`: "`text-only`, which callers such as project-knowledge use"; `:116`: "The brief identifies text-only or in-place delivery".
  - In `plugins\project-knowledge` nessun file contiene `text-only` né istruzioni su reply format o score (verificato con grep su docs/plugin/ruoli/metodi; `references\guide-method.md:37-41`, `skills\readme-craft\SKILL.md:38-40`). Il formato è supportato dal ruolo (`roles\text-humanizer.md:25,46`) ma nessun consumatore lo richiede.
- Impatto: documentazione dell'integrazione inesatta; il rischio concreto è basso perché il ruolo applica il default `report`.
- Classificazione: fatto verificato (la capacità esiste; la frase sul consumatore no). Confidence: alta.

### F5 — Minore — Write-back su file: proprietario implicito, nessun requisito su encoding/EOL, nessuna verifica post-scrittura, mutazione non tracciata nel contratto

- Evidenza:
  - `references\humanize.md:25`: il brief al worker dice "do not write or edit any file".
  - `:35-47`: Step 3, "ask once through the host's question tool"; "Write only after the user picks 1 or 2, and write only the body inside the Final text fence … exactly as it stands". Il soggetto che scrive non è nominato (solo l'imperativo); nessuna richiesta di preservare BOM, fine-riga (CRLF), newline finale, né di verificare che il file sia cambiato.
  - `workflows\humanize-text.toml:4-20`: fasi `scope`+`review`, unico artifact `humanize-text-report`; la scrittura sul file di destinazione non ha fase/artifact/verifica.
  - `roles\text-humanizer.md:20`: il ruolo scriverebbe "when the brief asks" (è il percorso usato da business-planner, `business\roles\business-planner.md:63`); nel flusso humanize-text il brief lo vieta, coerentemente con il design documentato (`docs\plugins\text-humanizer.md:107`).
  - OpenCode: le entry command in `exports\opencode\package.json:637-641` non dichiarano permessi; il permesso di scrittura dipende dall'agente di sessione (non verificabile staticamente).
- Impatto (ipotesi, non riprodotta): su un host dove l'orchestratore non ha permesso di scrittura, "Overwrite" può non produrre nulla senza errore; l'overwrite del fence può normalizzare silenziosamente EOL/BOM; nessun controllo che il file sia stato aggiornato.
- Classificazione: lacuna di contratto verificata; failure mode ipotetica. Confidence: media.

### F6 — Minore — Lacune oggettive dei test

- `D:\Projects\daodan\tests\test_text_humanizer_contract.py:23-24`: `assertNotRegex(r"\b24 (?:AI writing|catalogued|patterns)")` **non** intercetta "24 local patterns" (probe: `False`), la forma dominante dei conteggi (plugin.toml:4, ruolo:4/16, humanize.md:3, pattern-catalog.md:3). Una regressione a "24 local patterns" passerebbe.
- Il conteggio "25" non è fissato in plugin.toml, docs, humanize.md, pattern-catalog.md, descrizioni di mercato: il test controlla solo la numerazione 1..25 delle righe nel SKILL (`:18-19`).
- `pattern-catalog.md:100-111` condensa i pattern 16-24 in una sezione unica; `SKILL.md:27` promette "Before/after specimens for all 25 local patterns" e nessun test verifica uno specimen per pattern.
- La parità export è verificata solo per `italiano.md`, `pattern-catalog.md`, `upstream-license.txt` (`:49-60`); SKILL.md e body del ruolo sono coperti solo dal drift gate del build, non da un test unitario.
- Classificazione: fatti verificati. Confidence: alta. Impatto: falsa sicurezza su regressioni di conteggio/contenuto.

### F7 — Osservazione — Qualità dell'italiano nel profilo (giudizio; naturalezza non provabile staticamente)

Letto integralmente `references\italiano.md` (125 righe). Valutazione complessiva positiva: grammatica corretta, esempi realistici (ticket, email, istruzioni, voce personale), guardie anti-meccanicità ben fatte (righe 9-12, 69, 73, 121-125). Punti concreti:

- riga 7: "Valuta il passaggio" — "passaggio" è calco di "passage"; in italiano naturale "il brano".
- riga 10: "Non spezzare ogni subordinata" — impreciso: si spezza il periodo, non la subordinata; l'intento è "non trasformare ogni subordinata in una frase a sé".
- riga 12: "Rileggi il risultato come un testo intero" — suona tradotto; "nel suo insieme" è più idiomatico.
- righe 82-85 (esempio bandiera): il testo "After" ("La nostra piattaforma affianca le aziende nell'innovazione") trasforma affermazioni vaghe ("partner strategico", "sottolineando l'importanza dell'innovazione") in un rapporto diretto: borderline rispetto alla regola di fedeltà (non potenziare) proprio nell'esempio guida.
- righe 24-28 (typography): la norma sulle virgolette è attribuita genericamente alle "editorial norms" della Crusca, senza fonte specifica, mentre la riga 16 cita Ferrari con URL e data; nell'ambito di un profilo che cita puntualmente, è una asimmetria di tracciabilità.
- Dichiarazione di limite: la naturalezza reale dell'output LLM non è provabile staticamente; questo è un giudizio editoriale sulle istruzioni, non una misura del comportamento.

### F8 — Osservazione — Pattern 11 (sinonimi) trattato come tell a valle, mentre il catalogo lo dichiara non diagnostico

- Evidenza: `SKILL.md:88` e `pattern-catalog.md:69` ("This is not diagnostic of AI writing"), `italiano.md:69` (la variazione è normale, soprattutto in italiano).
- Contraddizioni a valle: `pattern-catalog.md:163` elenca il taglio di "synonym cycling" sotto il pattern 11 nell'esempio end-to-end, dove i termini citati ("catalyst/partner/foundation") sono più copula/metaphor stacking già coperto da 8; `D:\Projects\shinatama\plugins\digital-marketing\skills\review-reply-method\SKILL.md:95` elenca "synonym cycling" fra i tell da applicare a ogni risposta.
- Impatto: possibile rimozione meccanica di variazione stilistica; rischio concreto basso (registro business), ma è esattamente la classe di errore che la riconciliazione ha cercato di evitare.

### F9 — Osservazione (ipotesi, UNVERIFIED) — Dispatch cross-marketplace di business verso text-humanizer su Codex/Pi senza risorsa generata nel pacchetto consumatore

- `D:\Projects\shinatama\plugins\business\roles\business-planner.md:63` ordina di dispacciare `text-humanizer:text-humanizer` in contesto isolato, con istruzione di scrittura in place.
- Il pacchetto consumatore per gli host senza agent nominati non contiene né `contracts/` né alcuna dispatch resource per quel ruolo: in `exports\codex\plugins\business` e `exports\pi\plugins\business` (verificato con listing) non esiste nulla del genere, perché il provider è in un altro marketplace.
- Il binding host dei consumatori istruisce a risolvere il body del ruolo dal provider installato e a recuperare i provider foreign; non è stato eseguito alcun host.
- Impatto possibile: la fase di umanizzazione dipende dalla capacità del modello di trovare e passare il body del ruolo del pacchetto esterno. Da provare su host reale.

## Copertura

| Area | Cosa | Stato | Note |
|---|---|---|---|
| Kernel text-humanizer | plugin.toml, ruolo, SKILL.md, humanize.md, pattern-catalog.md, italiano.md, license | VERIFIED | letti integralmente; conteggi 1..25, 25/26; nessun "24" residuo; sha256 ruolo |
| Contratti metodo/ruolo/humanize | brief, seconda passata, guardie fedeltà, autorizzazione scrittura, casi limite | VERIFIED con lacune | F5 |
| Export 5 host | contenuti SKILL/ruolo/reference/licenze | VERIFIED | build --check senza drift per i 5 pacchetti; parità reference; attribution presente in tutti; dispatch resource codex/pi con sha del ruolo identico |
| Cataloghi/manifest | 3 marketplace, package.json Pi, package.json OpenCode, plugin.json per host | VERIFIED | 2.1.0 ovunque, descrizione identica, componenti registrati |
| Entry humanize-text | workflow md/toml + harness renderizzati | VERIFIED staticamente | 13 test di binding OK; esecuzione host NOT RUN |
| Test | test_text_humanizer_contract, test_daodan_operational_binding | VERIFIED eseguiti | 5/5 OK; 13/13 OK (74,7 s); lacune F6 |
| Consumatori daodan | project-knowledge, project-lifecycle | VERIFIED staticamente | F3, F4 |
| Consumatori Shinatama | digital-marketing, business | VERIFIED staticamente | F1, F2, F8, F9 |
| Profilo italiano | contenuto | VERIFIED (giudizio) | naturalezza non provabile staticamente |
| Attribuzioni esterne | blader/humanizer pin, Wikipedia, Crusca | VERIFIED via rete | dati sotto |
| Host reali / LLM | installazione ed esecuzione su Claude/Copilot/Codex/Pi/OpenCode; rewrite reali | NOT RUN | nessuna prova eseguita |
| Gate globali repo | build, docs | FAILED (non-text-humanizer) | drift da lavoro concorrente |

### Verifiche eseguite (comandi e esiti reali)

- `python -B scripts\daodan_build.py --check` → exit 1. Drift: `exports\{claude,copilot,opencode}\plugins\{project-protocol,senior-review,skill-catalog}`, `exports\{codex,pi}\plugins\{daodan,project-protocol,senior-review,skill-catalog}`, i 3 `marketplace.json`. **Nessun pacchetto text-humanizer nella lista.**
- `python -B scripts\sync_plugin_docs.py --check` → exit 1. Drift: `docs\catalog.md`, `docs\plugins\project-protocol.md`. La pagina `docs\plugins\text-humanizer.md` non è in drift.
- `lint_dependency_graph.py` → OK (22 plugin, 950 reference, 8 pass).
- `lint_bundled_paths.py` → OK (446 file, 219 reference `${CLAUDE_PLUGIN_ROOT}` risolte).
- `lint_plugin_registration.py` → OK; `lint_fact_anchors.py` → OK (10/10); `lint_host_vocabulary.py` → OK.
- `python -B -m unittest discover -s tests -p "test_text_humanizer_contract.py" -v` → 5 test OK.
- `python -B -m unittest discover -s tests -p "test_daodan_operational_binding.py" -v` → 13 test OK (74,7 s).
- Probe in sola lettura: regex del guard test inefficace su "24 local patterns" (False); scan conteggi (nessun 24 fuori posto); parità `humanize.md` sui 5 export (identica dopo rimozione wrapper); scan em-dash nel kernel (solo riferimenti al carattere e specimen); sha256 del ruolo = `41f62d79…` = `source-sha256` della dispatch resource codex; `coreDigest` identico nei 5 provenance.
- Rete (sola lettura): GitHub API → commit pin `8c307f36…` del 16 ott 2026; `raw.githubusercontent.com` al pin → metadata `version: "3.1.0"`, 26 pattern numerati; Wikipedia oldid 1377577399 → revisione del 30 settembre 2026; Accademia della Crusca → Angela Ferrari, "La semplicità sintattica in prospettiva testuale…", 19 marzo 2021.
- Git/repo: HEAD `cd942b0b`; ultimo commit del plugin `297750780`; prima aggiunta del plugin `58e1dfef1` "Extract text-humanizer into a standalone leaf plugin (v13.3.0)" del 28 lug 2026 (claim "13.3.0" verificata); working tree non toccato dai miei check (delta status = scritture concorrenti).
- Disco: prima C 6,2 GB / D 22,9 GB liberi; dopo C 6,2 / D 22,92 GB. File temporanei di probe rimossi (nessun impatto misurabile).

### Non eseguite (dichiarate)

- Suita unitaria completa (`unittest discover -s tests`) e `check_version_bumps.py` (richiede range di commit; lavoro già pubblicato), `sync_codex_instructions.py --check`, test della policy xray Copilot: fuori dal perimetro richiesto o dipendenti da stato concorrente.
- Nessuna installazione host, nessun run reale su Claude/Copilot/Codex/Pi/OpenCode, nessun rewrite LLM, nessun accesso a database/produzione.
- Nessuna verifica di rendering UI/a11y (non applicabile: plugin Markdown senza UI).

## Limiti

1. La naturalezza e la correttezza dell'italiano **prodotto** non sono verificabili staticamente; F7 è un giudizio editoriale sulle istruzioni.
2. F5 e F9 sono lacune di contratto/ipotesi operative; le failure mode non sono state riprodotte su host.
3. I gate globali del repo sono rossi per lavoro concorrente non correlato: non certifico l'intero albero, solo la riproducibilità dei pacchetti text-humanizer e la coerenza dei loro riferimenti.
4. Il repo oggetto è in scrittura concorrente (293 voci dirty, +3 durante l'audit): le evidenze su percorsi non-text-humanizer possono essere superate dalla sessione concorrente.
5. Versioni host e disponibilità dei provider esterni non provate.

## Interventi proposti (non applicati)

1. Shinatama: sostituire `/text-humanizer:humanize-text` con `/daodan:humanize-text` in `llm-seo-audit.md:98`, `llm-seo-optimize.md:231` e rigenerare gli export. Criterio: nessuna occorrenza residua di `text-humanizer:humanize-text` nei sorgenti Shinatama.
2. Shinatama: correggere il link in `docs\plugins\digital-marketing.md:60` e la frase in `docs\plugins\business.md:7` (ruolo e località delle dipendenze). Criterio: link risolto, dipendenza descritta come `text-humanizer@daodan`.
3. Daodan: precisare in `plugin.toml:4` e `docs\plugins\text-humanizer.md` che project-lifecycle consuma via project-knowledge (o aggiungere un riferimento esplicito in project-lifecycle), e allineare `shinatama\AGENTS.md:412`. Criterio: le due AGENTS.md e la closure generata dicono la stessa cosa.
4. Daodan docs: correggere la frase su `text-only`/project-knowledge o aggiungere il formato nei brief del metodo di project-knowledge. Criterio: l'affermazione è supportata da un artefatto consumatore.
5. `humanize.md`: nominare il proprietario della scrittura, richiedere la preservazione di encoding/EOL/newline e una verifica post-scrittura; valutare un artifact di run per la mutazione autorizzata. Criterio: il flusso "Overwrite" ha un esito verificabile e non altera la formattazione del file oltre il testo.
6. Test: rendere il guard dei conteggi tollerante alle varianti ("24 local patterns") e fissare "25" nei file sorgente; aggiungere un check di completezza degli specimen. Criterio: un revert a "24 local patterns" o la perdita di uno specimen fallisce la suita.
7. (Facoltativo) Rivedere l'esempio italiano righe 82-85 e l'attribuzione del pattern 11 in `pattern-catalog.md:163` e nel consumer Shinatama. Criterio: l'esempio non potenzia claim e il pattern 11 resta non diagnostico a valle.
