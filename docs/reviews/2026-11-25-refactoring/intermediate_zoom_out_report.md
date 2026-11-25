# Fase 4 di 5 (stage 8 del protocollo): seconda visione d'insieme

Seconda visione d'insieme (zoom out), parte 1 di 1: 6 Major e 5 Nit nuovi, nessun errore di fatto nelle note controllate, B1 e B2 ancora aperti.

Base: confronto con `78e070129`. Piano da 1.703 a 4.538 parole, architettura da 1.951 a 2.710. Sola lettura, nulla eseguito.

## Che cosa è migliorato
- «Termini» definisce Kiri, Noir, fork, SCIP, store, tessera: chiude la metà «termini non definiti» di B2.
- Le note «[accertato nel repository]» controllate reggono: `container.py` senza `--cap-drop` e `--user`, con `no-new-privileges` e rete `--internal`; i due test citati esistono; `FRAMEWORK_SOURCES` ha 4 voci senza Django/FastAPI/Flask; `EXECUTES` corrisponde; `NODE_TYPES`, estensione in `system_map.py:38`, 410 voci `by: model`, `service_registry.py:160`, `visual.py:260`.
- Riferimenti sbagliati di M8 corretti (`docs/pipeline/`, `feat/link-key-shape`, `go-enry`); errore su Syft in M2 corretto; `0/19` spiegato; I4 adottato come regola 5.

## Rilievi nuovi

**Z1. I rilievi sono diventati «fatto + scelta aperta», ma il testo dice ancora `[deciso]`.**
1. Severity: Major
2. Scope: piano punti 6, 7, 8, 12, 16, T2.1, Cancelli T1 e T2 (righe 103-121, 137, 150, 160); `architettura.md` righe 33, 43, 45, 48-50; `backlog.md` riga 58.
3. Rationale: sotto «[deciso] Integrare Django, FastAPI e Flask» c'è la nota con tre verdetti «no», e il Cancello T1 le richiede comunque. Il contratto non porta nessun segno: per chi legge solo `architettura.md` la sorgente dedicata è primaria, il menu OpenTelemetry/`strace`/eBPF è il disegno (la nota di T3.3 dice che il codice li ha già scartati e che `strace` non c'è), l'evidence model è nuovo. La legenda dice che `[deciso]` è approvato: due marcatori che si contraddicono. Basta un segno «contestato, vedi scelta X» sulle voci, o togliere `[deciso]` finché T0.A.3 non chiude.

**Z2. Il piano è quasi triplicato per processo, non per contenuto.**
1. Severity: Major
2. Scope: «Mappa di avanzamento», «Regole di esecuzione», «Struttura in tranche» di T1, T2, T3 (righe 11-35, 87-91, 145-148, 168-171).
3. Rationale: ogni traguardo è descritto tre volte (riga di mappa, elenco delle tranche, punti numerati), più i passi di T0. La regola 1 dice che le tranche bloccate non si dettagliano, ma la mappa ne fissa già verifiche, comandi Modal e scelte per 12 righe che dipendono da decisioni non prese. La regola 4 (commit `C`, commit `D`, colonna SHA) è cerimonia per una mappa con una sola riga viva. Tenere la tranche aperta e una riga per traguardo.

**Z3. La baseline su Modal aspetta tre passi di carta.**
1. Severity: Major
2. Scope: T0.A.1-3, riga `T0.B` della mappa, regola 2.
3. Rationale: T0.B.1-3 (doppia run, verifica del fork, difetti) non dipendono da B2, M1/I1, I2: solo T0.B.4 ne dipende. Eppure tutta T0.B è «bloccata da T0.A». La risposta a B2 è un «dossier» nel piano, con l'uscita «o registrare dove il beneficio è solo strutturale»: il problema di fondo resta non scritto, e `architettura.md` si aggiorna solo «eventualmente». Bastano tre frasi nell'introduzione del contratto; la misura può partire subito.

**Z4. T1.A non può essere «a comportamento invariato» con il punto 9.**
1. Severity: Major
2. Scope: riga `T1.A` della mappa, riga 88, punti 7, 8, 9.
3. Rationale: il punto 9 («nessuna sorgente decide più da sé se applicarsi») richiede che il fork riconosca CMake, Bazel, Meson e gli altri (punto 7) e `build-tools.json` (punto 8), che stanno in T1.C, due tranche dopo. O il punto 9 esce da T1.A, o T1.A cambia comportamento.

**Z5. «Nodi del grafo»: descrive l'oggi dentro un contratto di arrivo, senza aggancio al piano.**
1. Severity: Major
2. Scope: `architettura.md` righe 80-99.
3. Rationale: la sezione esiste per richiesta del proprietario; il rilievo è sulla collocazione.
   - Nessuno step ne è dichiarato padrone (`recognize_stack`? `assemble_graph`?).
   - I tipi di framework, librerie e strumenti sono dati senza consumatore: per le parole stesse della sezione «il grafo non li usa», sono `by: model` e non verificati a campione. È YAGNI già costruito; la «scelta aperta» sul modulo che prende il tipo del framework e il logo mancante nella mappa di sistema non sono in nessuna «Scelte aperte» del piano (stessa classe di M8).
   - Dettaglio da codice (`viewer/src/details.tsx`, `system_levels.view`, `technologies.externals`) in un documento di architettura.
   - Da ricontrollare: la riga «`tool`: né nodo né elenco del gruppo». `technologies.py:250,272` costruisce una lista `tools` per unità e `visual.py:212` la copia sul gruppo.

**Z6. Il contratto dichiara tre requisiti che «nessun traguardo porta», e uno serve a T3.**
1. Severity: Major
2. Scope: `architettura.md` righe 61, 65, 67; piano T3.3 e scelta M8 (riga 135).
3. Rationale: scrivere «non nel codice, nessun traguardo lo porta» documenta M8, non lo risolve. In più `surface` «decide con che cosa `run_and_observe` esegue», e T3.3 esegue su `web` e `webview`: quindi un traguardo ne ha bisogno. La scelta è messa fra quelle di T1. O si assegna a T3.B, o va nel backlog.

**Nit**
- **Z7.** T0.7 (riga 52) dice ancora «altrimenti collaudarlo in T3 prima del primo uso con rete»; la nota subito sotto (riga 53) dice che la rete è già usata oggi. La frase è superata.
- **Z8.** Legenda: «Proposta» è «mai approvata», ma la riga «L'utente» è «Proposta (T3)» e T3.2 la pianifica.
- **Z9.** Le note «Nel codice» nel contratto (righe 95, 99, 133, 136, 143) invecchiano al primo commit: N2 peggiora. Stanno nel piano.
- **Z10.** T0.B.4 chiama «sonda» anche `--cap-drop ALL` e `--user`, che sono modifiche a `container.py`. I1 proponeva di anticipare solo la prova.
- **Z11.** La mappa taglia già T1 come propone M7 e T2.A dice già «estensione» per M5, mentre le due scelte risultano aperte. Nota di T1.7: «Mix non ha un file in `premap/`» è vero, ma `mix-project` è in `EXECUTES`; una riga in più evita l'equivoco.

## Rilievi della prima visione: stato
- **Aperti, invariati nella sostanza:** B1, M3, M4, M5, M6, I2, I3, N1, N3, N5.
- **Parziali:** B2 (termini sì, problema no), M1/I1 (fatti scritti, decisione no), M2 (errore corretto), M7 (taglio adottato nella mappa, scelta aperta), M8 (riferimenti corretti, tre requisiti senza traguardo), N4 (contratto dice quattro step, punto 11 del piano ancora due).
- **Peggiorato:** N2.
- **Adottato:** I4 (regola 5; manca la scadenza per voce).

Prossimo passo: decidere Z1, cioè togliere `[deciso]` o marcare «contestato» sulle sei voci del piano e sulle righe 43, 48-50 di `architettura.md`.

---

**Revisore:** agente nuovo `general-purpose`, `fable`, effort `medium`, completato; contesto `zoom_out_report.md` e `docs/backlog.md`. Sola lettura per istruzione. Un primo revisore di questa fase è stato fermato prima del rapporto, perché leggeva il testo di prima delle correzioni.
**Versione letta:** il checkout prima dell'unione con `origin/develop` (`9601b9eb9`). Il piano letto contiene sezioni «a tranche» non in un commit, scritte fuori da questa sessione (Z2, Z3, Z4, Z10 riguardano quelle).
