@AGENTS.md

La regola d'oro di `AGENTS.md` vale prima di ogni scelta di metodo: per ogni framework, libreria o strumento del progetto analizzato si usa il suo materiale ufficiale (parser, compilatore, controllore dei tipi, comando), mai una regola scritta a mano sulla forma di un caso.

Per il lavoro sull'interfaccia applica il design file `viewer/node_modules/@acaprino/imago/docs/design-file.md` (da `viewer/`: `node_modules/@acaprino/imago/docs/design-file.md`) e i file che richiama; esegui `npx imago-check` in `viewer/` prima di dire che è finito.

Ogni app della suite ha l'unico aspetto di Sigrid: solo componenti del design system, mai un componente, una classe o un foglio di stile propri; ciò che manca si aggiunge a Sigrid. Vedi «Un solo aspetto per tutta la suite» in AGENTS.md.

Never compile, build or lint on this machine (`cargo`, `tauri`, `tsc`, `vite build`, bundlers, `npm run build`, `npm run verify`,
`npm install` of a git dependency that runs `prepare`): GitHub Actions does it. Only an explicit request of the owner, in that
request, to build or test locally overrides this. See "Nothing is compiled on this machine" in AGENTS.md.
