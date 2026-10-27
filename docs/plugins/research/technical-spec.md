# Architettura e contratti

Il kernel `research` possiede la skill, i tre workflow scientifici, il template
e il runtime Python standard library. `work-controller` fornisce disciplina
del run e contratto della home; `project-delivery` e `project-knowledge`
compongono il controllo scientifico nei propri metodi. I ricercatori web
esistenti conservano il proprio perimetro.

## Stato e archivio

La preferenza vive nella home comune del progetto, in
`.daodan/science-mode.json`. Assenza significa ON senza creare file.
Scritture con revisione attesa impediscono sovrascritture concorrenti.
Il runtime condivide la semantica della home Git di Work Controller;
fuori Git usa il progetto esplicito. Non cerca preferenze globali.

La preferenza, i checkpoint e il lock sono condivisi. I documenti di ricerca
restano nella checkout del chiamante, entro i suoi permessi: una ricerca svolta
su un branch di lavoro non pubblica automaticamente documenti nella main.

Una ricerca ha identità stabile, directory canonica, puntatore `science.json`,
revisioni Markdown immutabili con metadati e digest, ricevute dei controlli
e un file corrente stabile contenente l'intera ricerca. La directory è sotto `docs/research/`, oppure sotto
`docs/plugins/<owner>/research/` nel dossier proprietario.
L'indice globale collega gli originali, senza duplicarne il contenuto.

I Markdown preesistenti mantengono il proprio percorso quando aggiornati.
L'archivio conserva il contenuto originale e le revisioni, senza una seconda
pagina corrente parallela. La ricerca semantica preventiva è responsabilità del
metodo: l'unicità di un identificatore non dimostra che un tema sia nuovo.

La pubblicazione controlla revisione, percorsi e concorrenza. Le viste derivate
si possono ricostruire con `reindex`; i documenti preesistenti sono conservati
fuori dai blocchi gestiti. `last_checked_at`, controllo completo e
`last_updated_at` restano distinti. Vedi il
[contratto del runtime](../../../plugins/research/skills/science-based-approach/references/runtime.md)
per payload, errori e recupero.

## Hook e host

Il kernel dichiara `[[hooks]]` con nome, evento neutrale, script distribuito
sotto una skill, argomenti letterali e timeout. Il compilatore valida i percorsi
e genera `hooks/hooks.json`. Il comando risolve la root dalle variabili del
plugin; gli argomenti non diventano codice shell.

| Host | Registrazione prodotta | Percorso comune |
|---|---|---|
| Claude | SessionStart e UserPromptSubmit | Controlli nei metodi |
| Codex | SessionStart e UserPromptSubmit | Controlli nei metodi |
| Copilot | Nessun hook nativo generato | Controlli nei metodi |
| Pi | Nessun hook nativo generato | Controlli nei metodi |
| OpenCode | Nessun hook nativo generato | Controlli nei metodi |

Un plugin abilitato rende gli hook individuabili; l'host conserva i propri
controlli di fiducia prima dell'esecuzione. Il callback legge lo stato e fornisce
contesto al coordinatore: nessuna rete, pubblicazione o nuova esecuzione nel callback.
Python deve essere disponibile. Gli hook sono capacità opzionale, così gli altri
host mantengono i workflow. Registrazione e test del sottoprocesso non provano
la consegna dell'evento in un host installato: vedi [validazione](validation.md).

Riferimenti: [Codex hooks](https://learn.chatgpt.com/docs/hooks),
[Claude hooks](https://code.claude.com/docs/en/hooks).
