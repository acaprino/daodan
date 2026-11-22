@AGENTS.md

La regola d'oro di `AGENTS.md` vale prima di ogni scelta di metodo: per ogni framework, libreria o strumento del progetto analizzato si usa il suo materiale ufficiale (parser, compilatore, controllore dei tipi, comando), mai una regola scritta a mano sulla forma di un caso.

Per il lavoro sull'interfaccia applica il design file `viewer/node_modules/@acaprino/imago/docs/design-file.md` (da `viewer/`: `node_modules/@acaprino/imago/docs/design-file.md`) e i file che richiama; esegui `npx imago-check` in `viewer/` prima di dire che è finito.
