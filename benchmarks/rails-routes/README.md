# Rails: `bin/rails routes` ha un'uscita per le macchine e dà il gestore?

**Stato:** Aperta: da approfondire. Il comando è ufficiale ma stampa solo testo per persone, e Daodan non legge Ruby: la domanda è se un lettore Ruby venga prima di ogni prova del comando. Strumento letto, mai eseguito: nessuna fixture, nessuna sorgente della pre-mappa. Nel prodotto le rotte di Rails sono quelle di Noir, scartate perché nessun `.rb` è nello snapshot.

## Domanda

`bin/rails routes` (o un'interfaccia pubblica di Rails) elenca le rotte con metodo, percorso e funzione del gestore (file e riga, o un simbolo che lo snapshot sa trovare), da usare nel container? Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 14e del piano).

## Strumento letto

Sola lettura, 23 novembre 2026: nessuna applicazione Rails avviata, nessun `bin/rails routes` lanciato.

| Pacchetto | `.gem` del registro | sha256 del `.gem` |
| --- | --- | --- |
| `railties` 8.1.4.1 | `https://rubygems.org/downloads/railties-8.1.4.1.gem` | `ff2ef4b5a62cbc89811f88be11c776e2ed71b14dd012eae6a494d37994aa9782` |
| `actionpack` 8.1.4.1 | `https://rubygems.org/downloads/actionpack-8.1.4.1.gem` | `8c6f2e7cbd2653ef0539bde1ff20eb3e2e264e366affe56f0ba7f06d3670cb4b` |

Versione presa da `https://rubygems.org/api/v1/versions/<gem>/latest.json`. Per ripetere la lettura (da una cartella vuota; i `.gem` sono dati, non si installano né si eseguono): `curl -fsSLO <url>`, `sha256sum`, `tar xf <gem> data.tar.gz`, `tar xzf data.tar.gz`, poi i `grep` sotto. I percorsi sono relativi al contenuto di `data.tar.gz`.

## Risultato

Nessuna uscita per le macchine (nessun JSON). L'API di Ruby che alimenta il comando (`Rails.application.routes.routes`, `RouteWrapper#to_h`) è marcata `:nodoc:`. Il gestore è `controller#action` come simbolo; il file e la riga che Rails registra sono quelli della riga di `config/routes.rb` che dichiara la rotta, non del gestore, e per default solo in `development`.

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

Una riga di `bin/rails routes -E` (in `development`) porterebbe prefisso, verbo, URI, `Controller#Action` e, quando c'è, «Source Location» (`config/routes.rb:riga`); `RouteWrapper#to_h` in uno script gli stessi dati.

- Metodo e percorso: sì.
- Gestore: solo il simbolo `users#index` (controller `UsersController`, metodo `index`); per lambda, redirect e app Rack montate nessun gestore con posizione.
- Rischi di lettura: `-E` va a capo con `IO.console_size` (senza TTY il valore di ripiego è da misurare); `reqs` fonde `controller#action` e vincoli in una stringa; i parametri `:controller` e `:action` nel percorso danno rotte senza gestore unico.

## Che cosa lo ferma oggi

Daodan non ha un adattatore né un indicizzatore Ruby (verificato: nessun `ruby.py` in `daodan/core/languages/`, nessun indicizzatore in `daodan/core/indexers/`; `support_table.py` mappa `rubygems` a `ruby` solo come ecosistema) e nessuna grammatica tree-sitter Ruby è dichiarata. `UsersController#index` non si lega a nessuna dichiarazione.

Misurato su due applicazioni vere in [noir-binding](../noir-binding/README.md), «Laravel e Rails»: Noir dà già `controller#azione` con file e riga del controller per la gran parte degli endpoint, e `bin/rails routes` non aggiungerebbe dati. I numeri sono lì. Se il passo dinamico osserva i gestori: non misurato (nessun osservatore Ruby in `daodan/core/dynamic/`).

## Aperto

- **Prima un lettore Ruby:** un adattatore con grammatica tree-sitter Ruby che dichiari classi e metodi, e un modo ufficiale di legare `Classe#metodo` al simbolo (Rails risolve `users#index` in `UsersController` per convenzione, non per un dato dell'albero).
- **Poi una prova su Modal**, su un'applicazione Rails vera, senza rete:
  1. se `bin/rails routes -E` parte senza database e servizi (carica `config/environment`: inizializzatori, gem del Gemfile), con `DATABASE_URL` assente e `SECRET_KEY_BASE_DUMMY=1`, in `development` e in `production`;
  2. se «Source Location» chiede `RAILS_ENV=development`, o se basta `Mapper.route_source_locations = true` imposto da fuori (da valutare contro la regola d'oro);
  3. se uno script con `Rails.application.routes.routes` (`:nodoc:`) dà gli stessi dati in forma strutturata e quanto è fragile fra versioni;
  4. come escono engine montati, redirect, lambda, `mount`, `scope`, `namespace`, `resources` e le rotte `:controller/:action`; tempo e memoria.
- **Non verificato:** letta solo la 8.1.4.1; `source_location` in 7.1-8.0 e la data di introduzione di `route_source_locations` non sono letti; la documentazione ufficiale (guides.rubyonrails.org) non è stata riletta: «nessun JSON» viene dal sorgente (nessun formatter), non da una pagina.
