@AGENTS.md

La regola d'oro di `AGENTS.md` vale prima di ogni scelta di metodo: per ogni framework, libreria o strumento del progetto analizzato si usa il suo materiale ufficiale (parser, compilatore, controllore dei tipi, comando), mai una regola scritta a mano sulla forma di un caso.

Per il lavoro sull'interfaccia applica il design file di Imago (`viewer/node_modules/@acaprino/imago/docs/design-file.md`) e l'`AGENTS.md` di Sigrid (`viewer/node_modules/@acaprino/sigrid/AGENTS.md`), con i file che richiamano; `sigrid-check` (`npx --no sigrid-check src`, poi `app`) e `imago-check` sono puliti nel workflow Viewer prima di dire che è finito.

Ogni app della suite ha l'unico aspetto di Sigrid nella shell di Imago: solo componenti del design system, mai una cornice, un componente, una classe o un foglio di stile propri; ciò che manca si aggiunge a Imago (la cornice) o a Sigrid (un componente). Vedi «Un solo aspetto per tutta la suite» in AGENTS.md.

Never compile, build or lint on this machine (`cargo`, `tauri`, `tsc`, `vite build`, bundlers, `npm run build`, `npm run verify`,
`npm install` of a git dependency that runs `prepare`): GitHub Actions does it. Only an explicit request of the owner, in that
request, to build or test locally overrides this. See "Nothing is compiled on this machine" in AGENTS.md.
