# Rails: `bin/rails routes` ha un'uscita per le macchine e dà il gestore?

Domanda: `bin/rails routes` (o un'interfaccia pubblica di Rails) elenca le rotte con metodo, percorso e funzione del gestore (file e riga, o un simbolo che lo snapshot sa trovare), da usare nel container come il task 14 chiede? Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14 e 14e; forma e metodo come in [express-routes](../express-routes/README.md).

**Stato:** verifica in sola lettura del 23 novembre 2026; nulla eseguito (nessuna applicazione Rails avviata, nessun `bin/rails routes` lanciato).

**Risultato in una riga:** il comando esiste ed è ufficiale, ma stampa solo testo per persone (tabella, vista verticale, HTML): **nessuna uscita per macchine** (nessun JSON). L'API di Ruby che la alimenta (`Rails.application.routes.routes`, `RouteWrapper#to_h`) esiste ma è marcata `:nodoc:` («People should not use this class»). Il gestore è `controller#action` come simbolo, non file e riga; il file e la riga che Rails 7.1+ registra sono quelli della riga di `config/routes.rb` che dichiara la rotta, non quelli del gestore, e per default solo in `development`. **Nessun codice nuovo, nessuna sorgente della pre-mappa finché una prova su Modal non misura quanto sotto.**

## Fonti lette (23 novembre 2026)

| Pacchetto | `.gem` del registro | sha256 del `.gem` |
| --- | --- | --- |
| `railties` 8.1.4.1 | `https://rubygems.org/downloads/railties-8.1.4.1.gem` | `ff2ef4b5a62cbc89811f88be11c776e2ed71b14dd012eae6a494d37994aa9782` |
| `actionpack` 8.1.4.1 | `https://rubygems.org/downloads/actionpack-8.1.4.1.gem` | `8c6f2e7cbd2653ef0539bde1ff20eb3e2e264e366affe56f0ba7f06d3670cb4b` |

Versione presa da `https://rubygems.org/api/v1/versions/<gem>/latest.json`. Per ripetere la lettura (da una cartella vuota; i `.gem` sono dati, non si installano né si eseguono): `curl -fsSLO <url>`, `sha256sum`, `tar xf <gem> data.tar.gz`, `tar xzf data.tar.gz`, poi i `grep` sotto. I percorsi sono relativi al contenuto di `data.tar.gz`.

## Che cosa dicono

| Affermazione | Dove | Estratto |
| --- | --- | --- |
| Il comando è `rails/commands/routes/routes_command.rb` (`RoutesCommand`, marcata `:nodoc:`); opzioni `-c/--controller`, `-g/--grep`, `-E/--expanded`, `-u/--unused`; nessuna opzione di formato | railties `lib/rails/commands/routes/routes_command.rb` righe 6-12 | `class_option :expanded, type: :boolean, aliases: "-E"` |
| Il comando avvia l'applicazione e stampa il testo del formatter | stesso file righe 23-27, 33-39 | `boot_application!` ... `say inspector.format(formatter, routes_filter)`; solo `Expanded` o `Sheet` |
| Il formatter è `RoutesInspector` con `Sheet`, `Expanded`, `Unused` (sottoclasse di `Sheet`) e `HtmlTableFormatter` (pagina d'errore di sviluppo); nessun formatter JSON | actionpack `lib/action_dispatch/routing/inspector.rb` righe 160-280; `grep -n json` sul file: nessuna occorrenza | `class Sheet < Base`, `class Expanded < Base`, `class HtmlTableFormatter` |
| `RoutesInspector` e `RouteWrapper` non sono API pubblica | stesso file, righe 9 e 83-86 | `class RouteWrapper < SimpleDelegator # :nodoc:`; «This class is just used for displaying route information ... People should not use this class.» |
| `RouteWrapper#to_h` dà `name, verb, path, reqs, source_location`; `reqs` è l'`endpoint` più i vincoli | stesso file righe 14-23, 40-46, 69-74 | `{ name: name, verb: verb, path: path, reqs: reqs, source_location: source_location }` |
| Azione di controller: `reqs` = `"#{controller}##{action}"` (es. `users#index`; `:controller`/`:action` se il percorso li ha come parametri) | stesso file righe 14-17, 48-54 | `when app.dispatcher? "#{controller}##{action}"` |
| Lambda o Proc: testo fisso, senza posizione | stesso file righe 18-19 | `"Inline handler (Proc/Lambda)"` |
| Altra app Rack (o redirect): `rack_app.inspect` | stesso file riga 21; `routing/redirection.rb` righe 69-71, 106-108, 145-147 | `redirect(301)`, `redirect(301, <blocco>)`, `redirect(301, k: v)` |
| Engine montato: `endpoint` è `rack_app.inspect` (il nome della classe); `engine?` = classe che discende da `Rails::Engine`; le rotte dell'engine escono in una sezione propria «Routes for <engine>» | `routing/endpoint.rb` righe 14-16; `inspector.rb` righe 98-107, 112-123 | `rack_app.is_a?(Class) && rack_app < Rails::Engine` |
| Le rotte `internal` (di Rails stesso) sono scartate | `inspector.rb` riga 108 | `.reject(&:internal?)` |
| `Journey::Route` ha l'attributo `source_location`; il Mapper lo riempie se `Mapper.route_source_locations` è vero, con il primo frame fuori da `action_dispatch` ripulito dal backtrace cleaner: `"percorso:riga"` | actionpack `journey/route.rb` righe 10, 79, 95; `routing/mapper.rb` righe 26, 187, 373-385 | `return "#{cleaned_path}:#{location.lineno}"` |
| Per default la posizione c'è solo in `development` | actionpack `railtie.rb` riga 90 | `ActionDispatch::Routing::Mapper.route_source_locations = Rails.env.development?` |
| `Expanded` stampa «Source Location»; `Sheet` (l'uscita predefinita) no | `inspector.rb` righe 270-273 (Expanded); righe 222-228 (Sheet: solo name, verb, path, reqs) | `Source Location   | #{r[:source_location]}` |
| Il comando avvia l'applicazione: `require_application!` poi `Rails.application.require_environment!` (carica `config/environment`, quindi inizializzatori e configurazione dell'ambiente) | railties `lib/rails/command/actions.rb` righe 13-21 | `Rails.application.require_environment! if defined?(APP_PATH)` |

## Che cosa porterebbe una riga

Da `bin/rails routes -E` (nell'ambiente `development`): prefisso (`name`), verbo, URI, `Controller#Action` (`reqs`) e, quando c'è, «Source Location» (`config/routes.rb:riga`). Da `RouteWrapper#to_h` in uno script: gli stessi quattro più `source_location`.

- Metodo e percorso: sì, testo stabile in entrambe le forme.
- Gestore: solo come simbolo `users#index` (controller `UsersController`, metodo `index`); mai file e riga del metodo. Per lambda, redirect e app Rack montate: nessun gestore con posizione (testo fisso o `inspect`).
- File e riga: quelli della dichiarazione della rotta in `config/routes.rb`, non della funzione. Non soddisfano «la funzione del gestore»; servono solo come evidenza della rotta.
- Esito della regola del task 14 («metodo, percorso, funzione del gestore con file e riga o un simbolo che lo snapshot sa trovare»): **soddisfatta solo se lo snapshot sa trovare `UsersController#index`**, e oggi non lo sa (sotto).
- Rischi di lettura: `-E` va a capo con larghezza `IO.console_size` (nessun TTY: valore di ripiego da misurare); `reqs` fonde `controller#action` e vincoli in una stringa (`{:id=>/\d+/}`), da separare con cura; i parametri `:controller`/`:action` nel percorso danno rotte senza gestore unico.

## Lacuna di linguaggio

Daodan non ha un adattatore Ruby né un indicizzatore Ruby: in `daodan/core/languages/` non c'è `ruby.py` (Python, Go, Rust, Java, Kotlin, C#, JS/TS, C-family, SQL, PL/SQL, markup, stili), in `daodan/core/indexers/` nessun indicizzatore Ruby (`jvm.py` nomina RubyGems solo come registro di pacchetti; `support_table.py` riga 58 mappa `rubygems` a `ruby` come ecosistema), e nessuna grammatica tree-sitter Ruby è dichiarata. Lo snapshot non ha simboli Ruby: `UsersController#index` non si lega oggi a nessuna dichiarazione del grafo, quindi nemmeno una rotta Rails con il gestore giusto potrebbe diventare una sorgente. Servirebbero (senza deciderlo qui): un adattatore con grammatica tree-sitter Ruby che dichiari classi e metodi, e un modo ufficiale di legare `Classe#metodo` al simbolo (Rails risolve `users#index` in `UsersController` per convenzione, non per un dato dell'albero).

## Che cosa deve misurare una prova su Modal prima che si scriva una sorgente

Da fare solo nel container (regola invalicabile), su un'applicazione Rails reale, senza rete:

1. Se `bin/rails routes -E` parte senza database e senza servizi: il comando carica `config/environment` (inizializzatori, `config.after_initialize`, gem del Gemfile), che possono connettersi o fallire; misurare che cosa si rompe con `DATABASE_URL` assente e con `SECRET_KEY_BASE_DUMMY=1`, in `development` e in `production` (dove `source_location` è spento).
2. Se serve `RAILS_ENV=development` per avere «Source Location» e se in quell'ambiente l'avvio chiede ciò che non c'è (database, chiavi, `bundle install` senza rete); in alternativa se `Mapper.route_source_locations = true` imposto da fuori basta (è una modifica di configurazione, non una regola sulla forma di un caso: va valutata contro la regola d'oro).
3. Se uno script con `Rails.application.routes.routes` (API `:nodoc:`) dà gli stessi dati in forma strutturata e quanto è fragile tra versioni (`RouteWrapper` e i suoi campi cambiano senza avviso).
4. Come escono engine montati, redirect, lambda, `mount SomeRackApp`, rotte con `scope`, `namespace` e `resources` (controller con prefisso `admin/users#index`), e rotte `:controller/:action` dinamiche; con quante rotte il tempo e la memoria restano accettabili.
5. Che cosa fa il comando se un inizializzatore esegue codice del progetto: tutto resta nel container.

## Non verificato

- Nulla è stato eseguito: nessun output reale di `bin/rails routes`, nessun avvio senza database, nessuna misura.
- Letta solo la versione 8.1.4.1 (ultima del registro il 23 novembre 2026); il comportamento di `source_location` in 7.1-8.0 e di `-E`/`-u` nelle versioni più vecchie non è letto. La data di introduzione di `route_source_locations` non è verificata (il CHANGELOG non è stato cercato in modo esaustivo).
- Che cosa fallisca senza database non è letto nei sorgenti del comando (`routes_command.rb` non tocca il database): dipende dagli inizializzatori dell'applicazione, quindi solo la prova lo dice.
- La documentazione ufficiale (guides.rubyonrails.org) non è stata riletta: l'affermazione «nessun JSON» viene dal sorgente (nessuna occorrenza e nessun formatter), non da una pagina.
