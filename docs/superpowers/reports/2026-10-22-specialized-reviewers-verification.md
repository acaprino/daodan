> Chiarimento del 23 ottobre 2026: questo resoconto verifica un candidato
> intermedio con reviewer ancora ampi. Non certifica il completamento della
> specializzazione concordata. Il modello approvato usa specialisti canonici e
> reviewer ampi generati dalla loro unione; vedi la
> [specifica aggiornata](../specs/2026-10-22-specialized-reviewers-design.md).

# Verifica della prima fase dei reviewer specializzati

Implementazione: [specifica e mapping](../specs/2026-10-22-specialized-reviewers-design.md).
Decisione: reviewer autonomi per responsabilità coerente, con priorità alla
copertura e riuso di registro, selettore, contratti e consegne esistenti.

## Risultato implementato

- Tre nuovi ruoli senior-review: accessibility, performance e operability.
- Dieci corpi senior-review riscritti con controlli, controevidenza e confini
  espliciti. Cleanup riusa le convenzioni comuni; testing, React e platform sono
  stati riallineati ai rispettivi mandati. Gli altri owner restano autonomi.
- Tutti i 50 temi e i tre supplementi dell'inventario hanno un owner nella
  specifica. È copertura del mandato, non una misura dei difetti individuati.
- Registro esistente: 21 ruoli e due binding a metodi. I sette consumer di branch
  review dichiarano i nuovi ruoli. La review light mantiene il reviewer unico.
- Selezione su aggiunte, rimozioni, file eliminati e percorsi pertinenti, compresi
  CSS/markup, SQL, deploy e piattaforme client. I diff concatenati conservano
  ogni percorso; le righe di contenuto simili alle intestazioni restano contenuto.
- I flag di contesto/costo preservano roster, provenienza e controlli obbligatori.
  La consegna mantiene evidenza e lacune senza punteggi o quote arbitrari.
- Il mantra di economia resta nel canonico `CLAUDE.md` e nel generato `AGENTS.md`.
  Nessun composer, registro aggiuntivo o nuovo schema è stato introdotto.

## Verifiche concluse

| Verifica | Esito e significato |
|---|---|
| Test mirati sul candidato finale | 65 superati, zero errori/fallimenti/skip: roster, catalogo, ownership, binding operativi, pipeline e budget di istruzioni |
| Regressioni del parser | Tre casi fallivano prima della correzione e passano dopo; modulo roster completo: 18 test |
| Build universale | Completato; rigenerati Claude, Codex, Copilot, Pi e OpenCode |
| `daodan_build.py --check --support` | Exit 0, nessuna deriva degli export |
| Lint dipendenze | 22 plugin, 549 riferimenti runtime; tutti i controlli superati |
| Lint percorsi distribuiti | 396 corpi, 157 riferimenti alla root risolti; superato |
| Lint registrazione | 22 plugin, 116 percorsi dichiarati; superato per i cinque host |
| Lint vocabolario host | 396 corpi, zero occorrenze non ammesse |
| Lint fact anchor | 3.346 file; tutti i dieci anchor verificati |
| Parità documentazione e istruzioni | `sync_plugin_docs.py --check` e `sync_codex_instructions.py --check` superati |
| Policy Copilot | 36/36 test superati, exit 0 |
| Revisione indipendente | Corretti il parser dei diff e le contraddizioni sui flag; nessun ulteriore difetto concreto segnalato nel perimetro esaminato |

Le tre [smoke review isolate](../../../evals/senior-review/specialist-smoke/README.md)
hanno individuato i tre difetti attesi e lasciato senza finding le tre alternative
corrette. Le consegne hanno richiesto una riparazione del formato, documentata nel
resoconto. Fixture, risultati e fingerprint sono conservati insieme.

La [misura del testo](../../../evals/senior-review/specialist-smoke/instruction-size.json)
confronta 38 file Markdown operativi modificati, includendo i nuovi corpi e i
riferimenti comuni, con il commit `849797acbf8aaae74f23b55ce30710dc599c89bb`:
50.706 parole prima, 34.960 dopo, riduzione del 31,1%. Sono parole separate da
spazi nel sorgente; il conteggio non misura token, contesto effettivamente caricato
o costo dell'intero run.

La suite completa ha eseguito 1.596 test in 1.115 secondi. Il primo passaggio ha
registrato 26 fallimenti e tre errori (incluse le varianti per host), poi analizzati:

- Otto test erano impediti dalla creazione di hardlink/junction nel sandbox;
  tutti passano invariati con accesso consentito alle fixture temporanee.
- Cinque metodi del Codebase Map, incluse le varianti dei cinque host, richiedevano
  una directory temporanea ereditata dai processi figli. Il test sui percorsi
  esclusi richiedeva inoltre una fixture senza `.daodan` negli antenati. Tutti
  passano con queste sole correzioni dell'ambiente, senza modifiche al prodotto.
- Le asserzioni della pipeline imponevano il testo della vecchia selezione e
  dodici copie della stessa policy. Sono state sostituite con controlli sul roster
  autorevole e sul riferimento comune, mantenendo isolamento, barriera e
  provenienza nei cinque host. Il modulo aggiornato passa tutti i dieci test.
- Quattro unità avevano superato il limite di parole, insieme al totale della
  fase di consolidamento. Sono state compresse; tutti i quattro test di budget
  passano senza aumentare alcun limite. Il critic riceve i report della copertura
  esaminata: zero finding o assenza di citazioni non dimostrano una lacuna.

Il primo passaggio integrale non è presentato come verde. Le casistiche fallite
sono state rieseguite dopo la correzione pertinente; il perimetro dei reviewer è
verificato nuovamente sul candidato finale. Restano 69 skip nella suite estesa:
54 per grammatiche/parser opzionali assenti, nove per runtime MCP non disponibili,
cinque per link non consentiti dal sandbox e uno per semantica POSIX non
disponibile su Windows. Gli skip non sono successi e non provano quei percorsi.

## Limiti e ambiente

Le verifiche strutturali dei cinque host non dimostrano esecuzione nei cinque host
installati. Le smoke review sono controlli statici piccoli e mirati; non provano
equivalenza del recall rispetto ai reviewer precedenti o efficacia generale.
Nessuna esecuzione di browser, database, applicazione o deploy è stata usata per
trasformare una deduzione in evidenza runtime.

Su Windows, la directory temporanea predefinita del sandbox impediva la pulizia
di alcuni test. I controlli sono stati eseguiti con `tempfile.tempdir` nella
directory del run sotto `.daodan/runs/reviewer-specialists-20261022/checks/tmp`.
Per i processi figli sono stati impostati anche `TMP`, `TEMP` e `TMPDIR`.
Il build ha richiesto l'accesso approvato al catalogo generato dentro `.agents`.
Le modifiche preesistenti del workspace sono state preservate; non sono stati
eseguiti commit o push.

La composizione dinamica, la semplificazione delle modalità pubbliche e una
valutazione comparativa su casi reali restano fasi successive esplicite.
