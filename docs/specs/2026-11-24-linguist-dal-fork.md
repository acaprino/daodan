# Linguaggio dei file dal fork di Linguist

**Stato:** bozza, da approvare. Il fork è creato (24 novembre 2026, `acaprino/linguist-daodan`, pubblico), senza modifiche nostre. Nel prodotto non c'è nulla: oggi decide `languages.detect_language`. Modello: [stack dal fork](2026-11-21-stack-dal-fork.md).

## Perché

Il proprietario chiede meno codice nostro e dati da una sorgente aggiornata, «con tutte le improvements, fix e miglioramenti». Un primo lettore dei soli dati di Linguist 9.7.0 è stato provato e bocciato dalla review (24 novembre). Le misure, con il lettore di oggi come riferimento:

| Prova | Esito |
| --- | --- |
| 51.729 file di 180 progetti | 11 differenze, tutte a favore di Linguist. Il corpus ha solo 66 `.h`: non basta a decidere |
| 6.857 `.h` (per lo più Windows SDK, MSVC, CPython) | 130 differenze: 95 C++ letti C, 33 C letti C++, 2 senza linguaggio |
| 47.999 `.ts` | 8 TypeScript con `<TS` letti come XML: nessun linguaggio |
| Estensioni nuove | `binding.gyp` diventa Python: aggiunge un analyzer e fonde le corse di due servizi |
| Costo | 8–48 s per un file da 50 KB costruito male, su sei estensioni |

## Come si somiglia a stack-analyser e dove no

| | stack-analyser | Linguist |
| --- | --- | --- |
| Fork pubblico, tag `vX.Y.Z-daodan.N`, rilascio fissato con sha256 | Sì | Sì |
| Daodan lo esegue | Sì, con il suo Node | **No:** è Ruby con estensioni native, e il linguaggio serve per ogni file prima di leggere |
| Che cosa contiene il rilascio | Un programma | **Dati:** estensioni, regole e correzioni, in un JSON |
| Se manca | Una lacuna | **Daodan non può leggere nulla:** i dati stanno nel repository di Daodan, non si scaricano al primo uso |
| Chi legge i dati | Il programma | Un lettore Python piccolo in Daodan |

## Nel fork

1. **Correzioni nei dati** (`heuristics.yml`, `languages.yml`), ognuna con un campione scritto a mano che la prova, mai un header copiato.
   - `.ts`: XML solo se il file inizia come XML.
   - `.h`: le regole C++ che il lettore di oggi ha e Linguist no (`namespace`, `enum class`, modificatori di accesso, `template`, `std::`), quelle che sopravvivono senza togliere commenti e stringhe.
   - Pacchetti Oracle in `.sql`.
2. **L'elenco delle estensioni accettate** (le 63 di oggi) è un dato del rilascio, non codice di Daodan. Un'estensione nuova di Linguist entra solo quando la si aggiunge lì, con la prova che non cambia il piano dell'analisi.
3. **Un lettore Python nel fork**, con i suoi test e un confronto con Linguist vero (Ruby) sugli stessi campioni, in GitHub Actions: qui non si installa Ruby.
4. **Tempo massimo per ogni regola**, come Linguist (`Regexp.timeout`). Da provare con il pacchetto `regex`.
5. **Il rilascio:** tag e JSON come asset, con la licenza MIT. Il pin si sposta con un commit in Daodan, come per stack-analyser: niente workflow che apre da solo una modifica.
6. **L'aggiornamento da GitHub:** una corsa settimanale nel fork unisce l'ultima versione di Linguist, lancia i test e apre una modifica **nel fork**. Se le nostre correzioni non si uniscono da sole, il job è rosso.

## In Daodan

1. Il JSON del rilascio sta nel repository, con il suo sha256 e la versione.
2. Il lettore (`languages/linguist.py`) sostituisce la tabella e le regole di `languages/__init__.py`. I dati entrano nell'impronta del parser.
3. Le sei liste di suffissi sparse (`import_resolution`, `clang`, `typescript`, `edge_grading`, `usage_finder`, `store_consumers`) si leggono dalla stessa tabella, o restano solo dove il motivo è scritto.

## Ciò che non promette

- Il codice di Daodan può non calare: lettore, limite di tempo e impronta restano suoi. Il guadagno è che le **regole** stanno in un posto che si aggiorna da solo, e le correzioni si vedono e si provano.
- La parità piena su `.h` con il lettore di oggi: quello toglie commenti e stringhe prima di cercare, e `heuristics.yml` ha solo modelli di testo. O si estende il formato nel fork, o si accettano alcune decine di header su migliaia. Si misura prima di scegliere.

## Come si prova

1. I 5 casi della review e i 130 `.h` / 8 `.ts` / 1 `.rs` diventano campioni, con l'esito giusto.
2. Il gate: i 180 progetti e gli insiemi della review (6.857 `.h`, 47.999 `.ts`, 26.896 `.rs`), contro il lettore di oggi preso con `git show`, senza cloni. Ogni differenza è spiegata.
3. Il costo: nessun file da 50 KB costruito male tiene fermo il lettore più di un secondo.
4. Il piano dell'analisi: i 122 progetti della pre-mappa danno lo stesso piano di prima.
5. Suite e phazly su Modal: niente scende.

## Scelte aperte

| Scelta | Proposta |
| --- | --- |
| `.h` senza togliere commenti e stringhe | Misurare quanto si perde, poi decidere |
| `regex` come dipendenza di Daodan | Sì, se il tempo massimo funziona sui casi della review |
| Il lettore vive nel fork o in Daodan | Nel fork i dati, i test e la prova con Ruby; in Daodan una copia piccola del lettore, controllata da un test contro quella del fork |
