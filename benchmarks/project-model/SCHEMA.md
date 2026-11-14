# Forma della pre-mappa e regole del punteggio

Una sola forma per tre cose: `fixtures/<famiglia>-<nome>/expected.json` (la verità scritta a mano), l'uscita di ogni adattatore `tools/<tool>.py` (`run(fixture_dir, work_dir) -> dict`) e il campo `output` di `results/<tool>.json`. Il punteggio lo calcola `score.py`, solo libreria standard.

## Forma

```json
{
  "languages": [{"path": "src/a.ts", "language": "TypeScript"}],
  "excluded": [{"path": "vendor/", "why": "vendored"}],
  "units": [{"name": "@acme/web", "kind": "npm-package", "root": "packages/web", "manifest": "packages/web/package.json",
             "source_roots": ["packages/web/src"], "depends_on": ["@acme/core"], "config": {}}],
  "workspace": {"tool": "pnpm", "root": ".", "members": ["packages/web", "packages/core"]},
  "toolchains": [{"tool": "node", "version": "20.11.0", "declared_in": ".nvmrc"}],
  "dependencies": [{"unit": "@acme/web", "name": "react", "declared": "^18.2.0", "resolved": "18.2.0",
                    "scope": "runtime", "declared_in": "packages/web/package.json"}],
  "frameworks": [{"name": "Next.js", "unit": "@acme/web", "evidence": "packages/web/next.config.js"}],
  "services": [{"name": "PostgreSQL", "kind": "database", "evidence": "docker-compose.yml"}],
  "needs": {"container": false, "reason": ""},
  "traps": ["la radice è un pacchetto privato che non è membro del workspace"]
}
```

| Campo | Significato |
| --- | --- |
| `languages` | linguaggio di un file. In `expected.json`: solo i file il cui linguaggio non si capisce dall'estensione o che uno strumento sbaglia facilmente, più una voce per ogni linguaggio presente. `path` può mancare in un'uscita che dà solo i totali per linguaggio |
| `excluded` | file o cartella (con `/` finale) che non è codice del progetto; `why` fra `vendored`, `generated`, `documentation`, `binary`, `submodule` (il percorso di un sottomodulo Git, che può mancare dall'archivio; URL, ramo e commit fissato stanno in `dependencies`). In `expected.json` l'elenco è completo |
| `units` | un'unità che il sistema di build dichiara. `root` cartella dell'unità, `manifest` file che la dichiara (`null` per un'unità senza manifest, come una cartella di script), `source_roots` cartelle dei sorgenti, `depends_on` nomi di altre unità dello stesso progetto (le esterne vanno in `dependencies`), `config` ciò che serve a un indicizzatore |
| `units[].kind` | `npm-package` (anche la radice privata di un workspace: non esiste un tipo "radice"), `deno-project`, `angular-project` e `nx-project` (progetti dichiarati in `angular.json` o `project.json`), `python-project`, `cargo-crate`, `go-module`, `maven-module`, `gradle-project`, `sbt-project`, `dotnet-project`, `cmake-target`, `make-target`, `meson-target`, `bazel-target` (per C e C++ l'unità è il bersaglio di build: `add_library`, `add_executable`, una regola di Make, `library()`/`executable()` di Meson, una regola Bazel; `root` è la cartella del file che lo dichiara, `name` il nome del bersaglio), `composer-package`, `gem`, `pub-package`, `swift-package`, `mix-project`, `cabal-package`, `stack-project`, `dune-project`, `zig-package`, `julia-package`, `terraform-module`, `helm-chart`, `bundler-project` (Gemfile senza gemspec, come un'app Rails; `gem` è chi ha un `.gemspec`), `buf-module` (modulo dichiarato in `buf.yaml`), `msbuild-project` (progetto MSBuild che non è .NET, come un `.vcxproj`), `kobalt-project`, `xcode-target` (un target di un `.xcodeproj`: `root` la cartella che contiene il `.xcodeproj`, `manifest` il suo `project.pbxproj`, `name` il nome del target), `source-tree` (codice senza alcun file di build: una sola unità alla radice di quel codice, `name` e `manifest` null), `bazel-module` (il `module()` di `MODULE.bazel`, a cui appartengono i `bazel_dep`; i bersagli Bazel sono `bazel-target` con il label come nome, `//lib:core`); un tipo nuovo si chiede a chi tiene questo file |
| `units[].name` | `null` se nessun file dà un nome all'unità (allora non si confronta). Altrove (`depends_on`, `unit`, `connections`, `known`) un'unità si nomina con il suo nome, o con la sua `root` quando il nome è null o è lo stesso di un'altra unità (tre build Gradle separati si chiamano tutti `:`); altrimenti come lo scrive l'ecosistema: npm con lo scope (`@acme/web`), Python il nome del progetto, Cargo il nome del pacchetto, Go il percorso del modulo, Maven `groupId:artifactId`, Gradle il percorso del progetto (`:app`, `:` per la radice), .NET il nome del file di progetto senza estensione |
| `units[].config` | ciò che serve a un indicizzatore, come mappa aperta. Vocabolario documentato, da usare quando il fatto ci rientra: `tsconfig` (lista dei tsconfig che valgono per l'unità), `paths` (alias verso la lista dei percorsi: `paths` di tsconfig, alias del bundler, import map, `imports` di package.json), `entry_files` (lista dei file dove parte l'esecuzione: `main`, `module`, `exports`, `bin`, l'HTML di ingresso, il `main` di Angular, il modulo di uno script di console Python, il file Go con `func main`), `packages` (lista dei nomi importabili che l'unità fornisce: pacchetti Python di primo livello, namespace compresi, percorsi di import Go), `build_tags` (lista di ciò che sceglie quali file si compilano: tag di build Go, feature Cargo, define C e C++), `include_dirs` (lista delle cartelle di include C e C++), `source_sets` (nome verso la lista delle cartelle), `compile_tasks` (lista), `nested_modules` (lista dei percorsi). Una chiave fuori dal vocabolario è ammessa (`--check` la segnala come avviso) quando serve a dire un fatto vero che nessuna di queste dice: per esempio `entry_points`, `namespace_packages`, `settings_module`, `main_packages`, `replace`. Percorsi relativi alla radice della fixture; l'ordine delle liste non conta |
| `workspace` | la struttura che lega le unità: `tool` (npm, pnpm, yarn, cargo, go, uv, gradle, maven, dotnet, …), `root`, `members` come cartelle delle unità membro già risolte, non i glob. Un oggetto, o una lista se il progetto ha più workspace; `null` se non ce n'è |
| `toolchains` | versione chiesta dal progetto di ciò che deve esserci sulla macchina (la versione che un controllore di tipi o un linter prende come bersaglio, come `pythonVersion` di Pyright o `target-version` di Ruff, è una dichiarazione della versione del linguaggio: `tool` è il linguaggio, `declared_in` nomina l'impostazione) prima che il gestore dei pacchetti installi qualcosa: linguaggio, runtime, gestore dei pacchetti, strumento di build (`tool` fra go, node, python, java, rust, gradle, maven, npm, pnpm, yarn, bun, deno, …), scritta com'è nel file (una matrice di CI dà una voce per versione), con `declared_in` il file seguito, se nello stesso file ci sono più dichiarazioni, da `#` e dal campo (`package.json#engines`, `package.json#volta`, `pyproject.toml#tool.pyright.pythonVersion`). Fonti tipiche: `engines`, `packageManager`, `volta`, `.nvmrc`, `go.mod`, `rust-toolchain.toml`, wrapper, `.tool-versions`, `mise.toml`, …). Ciò che il gestore installa da una dipendenza dichiarata nello stesso file (typescript, nx, lerna, turbo in `package.json`) sta solo in `dependencies`; lo stesso strumento chiesto da due file diversi (`cmake_minimum_required` in `CMakeLists.txt`, `tool_requires` di Conan) è una voce in ciascuna faccetta |
| `dependencies` | dipendenza esterna **diretta**, dichiarata in un manifest. `unit` nome dell'unità, `name` nome del pacchetto, `declared` intervallo com'è scritto (`null` se non c'è), `resolved` la versione fissata da un lockfile o, per una dipendenza dichiarata senza versione, dal BOM, dal parent o dalla piattaforma che la gestisce (anche un BOM preso da Maven Central alla sua versione fissata, detto in `traps`); `null` altrimenti. Una versione scritta in un catalogo (`libs.versions.toml`, catalogo pnpm) o in una proprietà (`${picocli.version}` in un pom, `${jacksonVersion}` in `gradle.properties`) è `declared` con il valore della proprietà, e `declared_in` è il file che la scrive, con il frammento (`pom.xml#properties.picocli.version`); il segnaposto va in `traps`. Un sottomodulo Git è una dipendenza: `name` l'URL come lo scrive `.gitmodules`, `declared` il ramo o null, `resolved` il commit del gitlink, `declared_in` `.gitmodules#submodule.<percorso>`. I plugin di build con versione (Gradle, Maven, sbt) sono dipendenze `build`, con nome l'id del plugin per Gradle, `scope` fra `runtime`, `dev`, `build`, `test`, `optional`, `peer`, `provided` (serve alla compilazione e non si impacchetta: `provided` di Maven, `compileOnly` di Gradle), `declared_in` il file, con `#` e il campo quando serve a distinguere (`pyproject.toml#project.optional-dependencies.color`). I pacchetti solo transitivi del lockfile non si elencano; una dipendenza verso un'altra unità del progetto (`workspace:*`, percorso, membro del workspace) sta solo in `depends_on` |
| `frameworks` | framework usato da un'unità, `evidence` un file che lo mostra |
| `services` | servizio esterno di cui il progetto ha bisogno (database, coda, cache, storage, autenticazione, pagamenti, …), `kind` una parola, `evidence` un file |
| `needs` | `container: true` se leggere il progetto richiede un container (build che esegue codice, toolchain non scaricabile), con `reason` |
| `traps` | cosa sbaglia un lettore ingenuo in questa fixture. Non entra nel punteggio |
| `unknown` | faccette che l'autore non ha potuto stabilire per intero (tipico di un progetto vero descritto senza copiarne i file): non entrano nel punteggio di quella fixture. Una faccetta elencata per nome resta vuota. Per `dependencies` e `frameworks` una voce `{"facet": "dependencies", "known": ["web", "api"]}` dice che la faccetta è completa solo per quelle unità: si contano solo le loro voci; dell'uscita di uno strumento restano le voci di quelle unità e, se lo strumento non dà l'unità, quelle con un nome atteso |
| `connections` | punti di contatto fra unità, per il grafo unico che verrà dopo; non entrano nel punteggio. Ogni voce: `kind` (`http-route`, `rpc`, `queue`, `event`, `table`, `ipc-command`, …), `key` (la rotta, il nome della coda o della tabella), `provided_by` e `used_by` liste di nomi di unità, `evidence` lista di file |

Regole per chi scrive `expected.json`: ogni fatto si legge dai file della fixture, mai dall'uscita di uno strumento; ogni percorso esiste nella fixture; `needs` e `traps` ci sono sempre. Una fixture che descrive un progetto vero senza copiarne i file (famiglia `real`, cartelle `real-svc-*` e `real-app-*`) ha accanto `source.json` (`{"repo": url, "commit": sha di 40 caratteri}`); i runner la clonano a quel commit nel container e i percorsi non si controllano; i suoi fatti vengono dai file del repository a quel commit, non dal README, e una faccetta che non si stabilisce per intero va in `unknown`, perché una faccetta parziale conterebbe come "in più" le voci giuste che mancano. Gradle: un build incluso e `buildSrc` sono `gradle-project` con il percorso di build come nome (`:buildSrc`, `:money`); sbt: il nome è l'id del progetto. Due sistemi di build nella stessa cartella danno due unità con la stessa `root` e due workspace.

Regole per chi scrive un adattatore: una faccetta che lo strumento non dà **manca** dall'uscita; una faccetta che lo strumento dà ma vuota è `[]`. Lo stesso per i campi: un campo che lo strumento non conosce manca; `null` vuol dire che lo strumento dice "nessuno". Le dipendenze transitive si tolgono quando lo strumento le distingue; se non le distingue restano e contano come in più. Nomi Maven in `groupId:artifactId`, non come purl.

## Normalizzazione

`score.py` la applica a entrambe le parti prima del confronto.

- **Percorsi:** POSIX e relativi alla radice della fixture; `\` diventa `/`, si tolgono `./` iniziale e `/` finale; la radice è `.`. Con l'argomento `root` di `score()` si toglie anche quel prefisso dai percorsi assoluti. In `excluded` una cartella con `/` finale copre i file sotto di sé, in entrambe le direzioni.
- **Nomi di pacchetto**, secondo l'ecosistema dedotto dal file in `declared_in`, o dal `kind` dell'unità: Python PEP 503 (minuscole, `-_.` ripetuti diventano `-`); npm, NuGet, Composer, pub in minuscolo, scope tenuto; Cargo in minuscolo con `_` come `-`; Maven `/` come `:`; Go e gli altri come scritti. Se l'ecosistema non si deduce, un ultimo abbinamento usa la forma PEP 503 per tutti.
- **Linguaggi:** come li scrive Linguist (`TypeScript`, `C++`, `Shell`); il confronto non distingue maiuscole.
- **Framework e servizi:** solo lettere e cifre in minuscolo (`Next.js` e `nextjs` coincidono), più pochi alias in `FRAMEWORK_ALIASES` di `score.py`.
- **Versioni** (`version`, `declared`, `resolved`): confrontate come scritte. Se differiscono solo per spazi, maiuscole, `v`, `go`, `=` o `==` iniziali, o segmenti `.0` finali, la voce resta sbagliata ma con `same_after_normalisation: true`.

## Punteggio

`score(expected, got) -> {faccetta: risultato}`. Faccette: `languages` (insieme dei nomi), `languages.files` (linguaggio dei file elencati in `expected.json`; nessun "in più"), `excluded`, `units`, `units.depends_on`, `units.source_roots`, `units.config`, `workspace`, `workspace.members`, `toolchains`, `dependencies`, `frameworks`, `services`, `needs`.

Una faccetta assente da `got` è **non data**: `{"given": false, "expected": n}`, non zero. Una faccetta data:

```json
{"given": true, "expected": 3, "found": 1, "found_normalised": 2, "missed": ["…"], "extra": ["…"], "wrong": [{"item": "…", "fields": {"version": {"expected": "20.11.0", "got": "v20.11.0"}}, "same_after_normalisation": true}]}
```

con `expected = found + len(wrong) + len(missed)`. Una voce è trovata se è abbinata e ogni campo che lo strumento dà coincide; sbagliata se è abbinata ma un campo dato differisce; i campi che lo strumento non dà non si confrontano.

| Faccetta | Abbinamento, dal più stretto al più largo | Campi confrontati |
| --- | --- | --- |
| `units` | `root` + `kind` + `name` + `manifest` (lo stesso bersaglio in più makefile della stessa cartella), poi `root` + `kind` + `name` (più bersagli nella stessa cartella), poi `root` + `kind`, poi solo `root` | `kind`, `name`, `manifest` |
| `units.depends_on`, `units.source_roots`, `workspace.members` | coppie (unità, valore) su tutte le unità attese; un'unità non trovata perde tutti i suoi valori | — |
| `units.config` | coppie (unità, chiave) | valore della chiave |
| `workspace` | `root` + `tool`, poi `root` | `tool` |
| `toolchains` | `tool` + `declared_in` con il frammento + `version` (più versioni nella stessa impostazione, come una matrice di CI), poi `tool` + `declared_in`, poi `tool` + file + `version`, poi `tool` + file, poi `tool` | `version`, `declared_in`: il frammento dopo `#` si confronta solo se entrambe le parti ne nominano uno |
| `dependencies` | `unit` + `name` + `scope` + `declared_in` (la stessa dipendenza dichiarata in due file sono due voci), poi `unit` + `name` + `scope`, poi `unit` + `name`, poi `name`, poi nome PEP 503 | `unit`, `declared`, `resolved`, `scope`, `declared_in` |
| `frameworks` | `name` + `unit`, poi `name` | `unit` |
| `services` | `name` | nessuno: `kind` è una parola libera, descrive e non si confronta |
| `needs` | una voce | `container` |

## Risultati di uno strumento

`results/<tool>.json`, scritto dal runner:

```json
{
  "tool": "syft", "version": "1.33.0", "group": "sbom", "command": "syft dir:. -o json",
  "fixtures": {
    "js-pnpm-workspace": {
      "output": {"…": "la forma sopra"},
      "raw": "riassunto breve o percorso dell'uscita grezza",
      "seconds": 1.2, "peak_mb": 40,
      "network_attempts": 0, "offline_second_run": true,
      "executed_project_code": "no",
      "error": null,
      "score": {"…": "score(expected, output)"}
    }
  }
}
```

`executed_project_code` vale `yes`, `no` o `unknown`; `offline_second_run` dice se la seconda esecuzione senza rete dà lo stesso `output`; una fixture fallita ha `error` e nessun `output`.

## Comandi

```
python score.py all all                  tabelle per strumento e faccetta su tutto il corpus
python score.py syft,trivy js            due strumenti, una famiglia
python score.py all all --json out.json  anche ogni punteggio per fixture
python score.py --check [js|nome,…]      controlla gli expected.json
python -m unittest test_score.py
```
