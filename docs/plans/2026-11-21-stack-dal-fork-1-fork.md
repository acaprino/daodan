# Stack dal fork, piano 1 di 3: il fork

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Portare `acaprino/stack-analyser` a un rilascio che Daodan può lanciare in entrambe le scansioni come unico riconoscitore: test verdi, una prova con la sua fonte per ogni tecnologia, le dichiarazioni di altri strumenti in ingresso, il perimetro deciso da chi lancia, un avvio sotto il secondo, le regole che oggi ha solo il registro di Daodan, un pacchetto che gira senza installare nulla.

**Architecture:** Il fork resta uno strumento generico. Ogni punto che oggi aggiunge una tecnologia con una frase (`reason`) aggiunge anche una prova `{tech, kind, value, path, line?, source}`; il `Payload` la trasporta attraverso fusioni e `flatten`, e `toJson` la scrive. Un elenco di dichiarazioni in ingresso passa per le stesse regole e conserva la fonte di ognuna. Il CLI e le regole si distribuiscono in un solo file. Le regole mancanti nascono da uno script che legge il registro di Daodan.

**Tech Stack:** TypeScript 5.8, Node 24, Vitest. Repository: `C:\Users\alfio\Documents\ChatGPT\Daodan\stack-analyser`, ramo `feature/stack-detection`, remoto `fork`.

**Spec:** `daodan/docs/specs/2026-11-21-stack-dal-fork.md`, quarta stesura, sezione «Disegno», punto 1 (1.1 Task 1; 1.2 Task 2–4; 1.3 Task 5; 1.4 Task 6; 1.5 Task 7; 1.6 Task 8; 1.7 Task 9). I piani 2 (Daodan dietro il benchmark) e 3 (passaggio definitivo) seguono questo e usano i nomi che fissa.

## Global Constraints

- Nessun concetto di Daodan nel codice del fork: il fork resta usabile da solo.
- `reason` resta com'è, in ogni punto: le prove si aggiungono, le frasi non cambiano.
- `dependencies.detect` (`matchDependencies`) e `tech.detectInFileList` (`matchAllFiles`) sono pubbliche: firma e uscita non cambiano.
- Una regola portata dal registro conserva l'ID che ha nel registro. Di un doppione resta un solo ID: quello di stack-analyser 1.27.6 quando la regola c'era già, altrimenti quello del registro.
- I test si eseguono con `npx vitest run --coverage.enabled=false`: il pacchetto della copertura non è installato in locale.
- Nessun progetto analizzato viene eseguito: il fork legge file.
- La fonte di ciò che il fork legge da solo è la stringa `stack-analyser`.
- Messaggi di commit nello stile del repository (`fix(rules): …`, `feat: …`), in inglese.

## Review Focus

1. **Una tecnologia senza prova.** Un punto di aggiunta dimenticato lascia una tecnologia che Daodan non può assegnare a un modulo. Ci si aspetta almeno una prova per ogni tecnologia di ogni componente. Test: Task 4, `every technology carries evidence`.
2. **Percorso della prova non portabile.** Su Windows un percorso con `\` o con la lettera del disco arriverebbe in uscita. Ci si aspetta lo stesso formato di `path`: relativo alla radice, con `/`. Test: Task 2, `toJson makes evidence paths relative and portable`.
3. **Fusione che perde o raddoppia prove.** La stessa tecnologia in due manifest, poi `flatten({merge: true})`. Ci si aspetta l'unione senza doppioni e il grafo di partenza intatto. Test: Task 2, `flatten keeps the union of evidence`.
4. **Regola portata che esiste già sotto un altro ID.** `jinja`/`jinja2`, `react-email`/`reactemail`: portarla com'è crea due tecnologie per lo stesso pacchetto. Ci si aspetta un solo ID per pacchetto. Test: Task 8, `no package identifies two technologies`.
5. **Pacchetto che non gira senza rete.** Una dipendenza non inclusa, o il WebAssembly di `@cdktf/hcl2json`. Ci si aspetta che il pacchetto scompattato in una cartella vuota analizzi un progetto con Terraform. Test: Task 9, `benchmarks/verify-package.mjs`.
6. **Una dichiarazione malformata o fuori dal progetto.** Un `path` con `..`, un tipo sconosciuto, la fonte mancante. Ci si aspetta un errore che nomina la voce, non un risultato parziale. Test: Task 5, `rejects a declaration outside the project or of an unknown type`.
7. **Il file unico che riconosce diversamente.** Una regola o un lettore lasciato fuori dal file. Ci si aspetta la stessa uscita di `dist/cli.js`. Test: Task 7, il confronto in `src/cli.test.ts`.

---

### Task 1: Test verdi

**Files:**
- Modify: `src/rules/ci.test.ts`
- Modify: gli snapshot in `src/**/__snapshots__/*.snap` dei dodici file falliti

**Interfaces:**
- Consumes: niente.
- Produces: una base con 0 test falliti, su cui i task seguenti misurano le proprie differenze.

- [ ] **Step 1: Fotografare lo stato**

Run: `npx vitest run --coverage.enabled=false 2>&1 | grep -E "Tests |Snapshots|obsolete"`
Expected: `Tests  15 failed | 2311 passed (2326)`, `Snapshots  14 failed`, `9 obsolete`.

- [ ] **Step 2: Dare ai due test di `ci.test.ts` un workflow vero**

Il lettore dei workflow riconosce `github.actions` solo da un file con `on` e almeno un job; i due test gli danno un file vuoto. In `src/rules/ci.test.ts` i due contenuti `''` di `/.github/workflows/ci.yml` e `/.github/workflows/main.yml` diventano:

```ts
const workflow = 'on: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps: []\n';
```

Run: `npx vitest run --coverage.enabled=false src/rules/ci.test.ts`
Expected: 2 passed, senza toccare lo snapshot.

- [ ] **Step 3: Leggere le differenze degli snapshot contro l'elenco ammesso**

Run: `npx vitest run --coverage.enabled=false 2>&1 > /tmp/before.txt`

Sono ammesse solo queste differenze; ogni altra riga rimossa è un difetto da correggere nel codice, non nello snapshot.

| File di test | Differenza ammessa |
| --- | --- |
| `rules/all`, `spec/golang/lockfile`, `spec/docker/component`, `spec/nodejs/component`, `spec/php/component`, `spec/python/lockfile` (due), `spec/terraform/resource`, `spec/githubActions/component` | solo ID aggiunti, nessuno rimosso |
| `rules/hosting` | rimosso `github.pages`: `_config.yml` è di Jekyll, non di Pages |
| `spec/ruby/lockfile` | rimosso `azure.staticwebapps` (i segni sono passati ad `azure.appservice`), aggiunto `github.pages` (gem `github-pages`) |
| `analyser/index` (due) | `docker` viene dal lettore Compose (`Compose services in docker-compose.yml`) sul componente virtuale e non più da `matched file`; `JSON` e `YAML` contati una volta; l'espressione di Deno per `postgresql`; `puma` con versione `6.3.0`; `/golang/go.mod` al posto di `/golang`; `invalid.yml` non è più un workflow; ordine delle frasi in `composer.json` |

- [ ] **Step 4: Rigenerare gli snapshot**

Run: `npx vitest run --coverage.enabled=false -u`
Poi: `git diff --stat -- '*.snap'` e `git diff -- '*.snap' | grep -E '^-\s+"' | sort | uniq -c`
Expected: fra le righe rimosse compaiono solo le voci dell'elenco ammesso.

- [ ] **Step 5: Verificare e committare**

Run: `npx vitest run --coverage.enabled=false 2>&1 | grep -E "Tests |obsolete"`
Expected: `Tests  2326 passed (2326)`, nessuna riga `obsolete`.

```bash
git add src/rules/ci.test.ts 'src/**/__snapshots__/*.snap'
git commit -m "test: align fixtures and snapshots with evidence-based detection"
```

---

### Task 2: La prova e il suo trasporto nel `Payload`

**Files:**
- Modify: `src/types/index.ts`, `src/payload/index.ts`, `src/payload/helpers.ts`, `src/index.ts`
- Test: `src/payload/evidence.test.ts` (aggiunte in coda)

**Interfaces:**
- Consumes: `cleanPath(paths, root)` di `src/common/helpers.ts`.
- Produces:

```ts
// src/types/index.ts, esportati anche da src/index.ts
export type EvidenceKind = 'package' | 'image' | 'action' | 'terraform' | 'file' | 'extension' | 'env' | 'source';
export interface Evidence {
  tech: AllowedKeys;
  kind: EvidenceKind;
  /** Il pacchetto, l'immagine, l'azione, la risorsa, il file, l'estensione, la variabile o il simbolo trovato. */
  value: string;
  /** Assoluto durante l'analisi; `toJson(root)` lo rende come `path`. */
  path: string;
  line?: number;
  /** Chi ha letto: `stack-analyser`, o la fonte di una dichiarazione in ingresso (Task 5). */
  source: string;
}
export type EvidenceItem = Omit<Evidence, 'tech' | 'source'> & { source?: string };   // senza `source` vale `stack-analyser`

// Analyser e AnalyserJson
evidence: Evidence[];

// src/payload/index.ts
new Payload({ ..., evidence?: EvidenceItem[] })   // vale per `tech`, quando c'è
addTech(tech: AllowedKeys, reason: string[], evidence?: EvidenceItem[]): void
addEvidence(tech: AllowedKeys, items: EvidenceItem[]): void   // senza doppioni

// src/payload/helpers.ts
findImplicitComponent({ pl, tech, reason, evidence? })   // il componente dedotto riceve la stessa prova
```

`toJson` scrive `evidence` con `path` passato da `cleanPath` (la radice analizzata si scrive `/`) e ordinato per `tech`, `kind`, `path`, `line`, `value`. `copy`, `combine`, il ramo di fusione di `addChild` e `flatten` portano le prove come portano `reason`. Il componente dell'host che `addChild` crea per un ID con il punto (`aws` per `aws.s3`, frase `implicit: aws.s3`) riceve le prove del figlio, con il proprio `tech`.

- [ ] **Step 1: Scrivere i test che falliscono**

```ts
it('toJson makes evidence paths relative and portable', () => {
  const base = path.resolve('repo'); // un percorso della piattaforma: con il separatore di Windows su Windows
  const root = new Payload({ name: 'main', folderPath: base });
  root.addTech('react', ['react matched: /^react$/'], [{ kind: 'package', value: 'react', path: path.join(base, 'web', 'package.json') }]);
  root.addEvidence('react', [{ kind: 'extension', value: '.tsx', path: base }]);
  expect(root.toJson(base).evidence).toEqual([
    { tech: 'react', kind: 'extension', value: '.tsx', path: '/', source: 'stack-analyser' },
    { tech: 'react', kind: 'package', value: 'react', path: '/web/package.json', source: 'stack-analyser' },
  ]);
});

it('gives the deduced component the evidence of the technology that implied it', () => {
  const root = new Payload({ name: 'api', folderPath: '/api' });
  root.addTech('postgresql', ['postgresql matched: /^pg$/'], [{ kind: 'package', value: 'pg', path: '/api/package.json' }]);
  expect(root.childs[0].tech).toBe('postgresql');
  expect(root.childs[0].evidence).toEqual([{ tech: 'postgresql', kind: 'package', value: 'pg', path: '/api/package.json', source: 'stack-analyser' }]);
});

it('flatten keeps the union of evidence', () => {
  const root = new Payload({ name: 'main', folderPath: '/' });
  for (const folder of ['/a', '/b', '/a']) {
    const child = root.addChild(new Payload({ name: folder, folderPath: folder }));
    child.addTech('redis', ['redis client'], [{ kind: 'package', value: 'redis', path: `${folder}/package.json` }]);
  }
  const before = structuredClone(root.toJson());
  const redis = flatten(root, { merge: true }).childs.find((c) => c.tech === 'redis')!;
  expect(redis.evidence.map((e) => e.path).sort()).toEqual(['/a/package.json', '/b/package.json']);
  expect(root.toJson()).toEqual(before);
});
```

- [ ] **Step 2: Vederli fallire**

Run: `npx vitest run --coverage.enabled=false src/payload/evidence.test.ts`
Expected: i tre test nuovi falliscono su `evidence`.

- [ ] **Step 3: Implementare le firme del blocco Interfaces**

Le prove si confrontano per `tech`, `kind`, `value`, `path`, `line`, `source`.

- [ ] **Step 4: Vederli passare e rigenerare gli snapshot che ora hanno `evidence: []`**

Run: `npx vitest run --coverage.enabled=false -u`
Expected: 0 falliti; in `git diff -- '*.snap'` le sole righe aggiunte sono `"evidence": [],`.

- [ ] **Step 5: Commit**

```bash
git add src/types/index.ts src/payload src/index.ts 'src/**/__snapshots__/*.snap'
git commit -m "feat: carry structured evidence through payloads"
```

---

### Task 3: La prova dai pacchetti

**Files:**
- Modify: `src/matchDependencies.ts`, `src/payload/index.ts`, `src/rules/spec/packageManifest.ts`
- Modify (punti di aggiunta): `spec/deno/lockfile.ts`, `spec/docker/dockerfile.ts`, `spec/docker/component.ts`, `spec/githubActions/component.ts`, `spec/jvm/index.ts`, `spec/nodejs/component.ts`, `spec/nuget/component.ts`, `spec/python/lockfile.ts`, `spec/rust/component.ts`, `spec/swiftpm/component.ts`, `spec/terraform/lockfile.ts`, `spec/terraform/resource.ts`
- Test: `src/rules/spec/readerEvidence.test.ts` (aggiunte in coda)

**Interfaces:**
- Consumes: Task 2.
- Produces:

```ts
// src/matchDependencies.ts
/** Per ogni tecnologia, i nomi che l'hanno fatta riconoscere, nell'ordine d'ingresso. */
export function matchedPackages(pkgs: string[], type: SupportedDeps): Map<AllowedKeys, string[]>
/** docker → image, githubAction → action, terraform e terraform.resource → terraform, il resto → package. */
export function evidenceKind(type: SupportedDeps): EvidenceKind

// src/payload/index.ts
/** `addTechs(matchDependencies(names, type))` più una prova per nome riconosciuto, in `file`. */
addDependencyTechs(names: string[], type: SupportedDeps, file: string): void

// src/rules/spec/packageManifest.ts
packageComponent(name, folderPath, ecosystem, requirements, file: string): Payload   // `file`: dove stanno i requisiti
```

Ogni `x.addTechs(matchDependencies(names, type))` dei file elencati diventa `x.addDependencyTechs(names, type, file)` con il percorso del manifest letto. Nei tre punti che creano un `Payload` figlio con `tech` (`docker/component.ts`, `terraform/lockfile.ts`, `terraform/resource.ts`) il costruttore riceve `evidence` con il nome riconosciuto e il file.

- [ ] **Step 1: Scrivere i test che falliscono**

Usano `scan(files)` già definita in `readerEvidence.test.ts`.

```ts
it('records where each package, image, action and resource was declared', async () => {
  const result = await scan({
    'package.json': JSON.stringify({ name: 'api', dependencies: { react: '18', pg: '8' } }),
    'docker-compose.yml': 'services:\n  cache:\n    image: redis:7\n',
    '.github/workflows/ci.yml': 'on: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/setup-node@v4\n',
    'main.tf': 'resource "aws_s3_bucket" "b" {}\n',
  });
  const all = [result, ...result.childs].flatMap((c) => c.toJson('').evidence);
  expect(all).toEqual(expect.arrayContaining([
    { tech: 'react', kind: 'package', value: 'react', path: '/package.json', source: 'stack-analyser' },
    { tech: 'postgresql', kind: 'package', value: 'pg', path: '/package.json', source: 'stack-analyser' },
    { tech: 'redis', kind: 'image', value: 'redis', path: '/docker-compose.yml', source: 'stack-analyser' },
    { tech: 'nodejs', kind: 'action', value: 'actions/setup-node', path: '/.github/workflows/ci.yml', source: 'stack-analyser' },
    { tech: 'aws.s3', kind: 'terraform', value: 'aws_s3_bucket', path: '/main.tf', source: 'stack-analyser' },
  ]));
});
```

In `src/matchDependencies.test.ts` (nuovo, o in coda a quello esistente se c'è):

```ts
expect(matchedPackages(['left-pad', 'pg', 'postgres'], 'npm').get('postgresql')).toEqual(['pg', 'postgres']);
expect(matchDependencies(['pg'], 'npm')).toEqual(new Map([['postgresql', ['postgresql matched: /^pg$/']]]));
```

- [ ] **Step 2: Vederli fallire**

Run: `npx vitest run --coverage.enabled=false src/rules/spec/readerEvidence.test.ts src/matchDependencies.test.ts`
Expected: FAIL su `matchedPackages` non definita e sulle prove mancanti.

- [ ] **Step 3: Implementare `matchedPackages`, `evidenceKind`, `addDependencyTechs` e convertire i punti elencati**

`matchDependencies` e `matchedPackages` condividono lo stesso ciclo sulle regole; l'uscita di `matchDependencies` non cambia di un carattere.

- [ ] **Step 4: Vederli passare**

Run: `npx vitest run --coverage.enabled=false -u`
Expected: 0 falliti; negli snapshot cambiano solo righe dentro `evidence`.

- [ ] **Step 5: Commit**

```bash
git add src
git commit -m "feat: record the manifest behind every package match"
```

---

### Task 4: La prova da file, estensioni, variabili e lettori diretti

**Files:**
- Modify: `src/types/rule.ts`, `src/common/rules/matchFiles.ts`, `src/loader.ts`, `src/matchAllFiles.ts`, `src/payload/index.ts`, `src/rules/spec/dotenv/index.ts`
- Modify (frasi scritte a mano): `spec/docker/component.ts:39`, `spec/docker/dockerfile.ts:30`, `spec/githubActions/component.ts:57`, `spec/hex/component.ts:85,101`, `spec/jvm/index.ts:15`, `spec/maestro/component.ts:37`, `spec/nuget/component.ts:182,184`, `spec/php/component.ts:41`, `spec/pub/component.ts:68`, `spec/ruby/lockfile.ts:116-128`, `spec/rust/component.ts:122`, `spec/swiftpm/component.ts:108,124`, `rules/ui/shadcn.ts:37`
- Modify: `README.md` (sezione «Output»: il campo `evidence`)
- Test: `src/analyser/evidence.test.ts` (nuovo)

**Interfaces:**
- Consumes: Task 2 e 3.
- Produces:

```ts
// src/types/rule.ts
export type TechMatcher = (files: ProviderFile[], basePath?: string) => [Rule, string, string] | false;  // regola, nome mostrato, percorso assoluto

// src/matchAllFiles.ts
export type TechMatch = { reason: string[]; evidence: EvidenceItem[] };
/** Come matchAllFiles, con la prova: `file` nel file trovato, `extension` nella cartella `folder`. */
export function matchAllFilesWithEvidence(files: ProviderFile[], basePath: string, folder: string): Map<AllowedKeys, TechMatch>

// src/payload/index.ts
addTechs(tech: Map<AllowedKeys, string[] | TechMatch>): void
```

Valori della prova, per origine:

| Origine | `kind` | `value` | `path` | `line` |
| --- | --- | --- | --- | --- |
| regola `files` | `file` | il nome che la frase già riporta | il file o la cartella trovata | — |
| regola `extensions` | `extension` | l'estensione, es. `.ts` | la cartella analizzata | — |
| variabile `.env` | `env` | il nome scritto nella regola, es. `STRIPE_` | il file `.env` | — |
| import Swift, `ExUnit` in Hex | `source` | il modulo o il simbolo | il sorgente | la riga che la frase già riporta |
| ogni altra frase scritta a mano dell'elenco | `file` | il nome del file | quel file | — |

`recurse` chiama `matchAllFilesWithEvidence`; `matchAllFiles` resta e dà la stessa uscita di oggi.

- [ ] **Step 1: Scrivere il test che fallisce**

```ts
import path from 'node:path';
import { expect, it } from 'vitest';
import { analyser } from './index.js';
import { FSProvider } from '../provider/fs.js';
import '../autoload.js';

import type { AnalyserJson } from '../types/index.js';

const root = path.join(import.meta.dirname, '../../tests/__fixtures__');

it('every technology carries evidence', async () => {
  const graph = (await analyser({ provider: new FSProvider({ path: root }) })).toJson(root);
  const missing: string[] = [];
  const visit = (node: AnalyserJson) => {
    for (const id of node.tech ? [node.tech, ...node.techs] : node.techs) {
      if (!node.evidence.some((item) => item.tech === id)) missing.push(`${node.name}: ${id}`);
    }
    for (const item of node.evidence) {
      expect(item.path.startsWith('/'), item.path).toBe(true);
      expect(item.path).not.toMatch(/\\|^\/[A-Za-z]:/);
    }
    node.childs.forEach(visit);
  };
  visit(graph);
  expect(missing).toEqual([]);
});
```

- [ ] **Step 2: Vederlo fallire**

Run: `npx vitest run --coverage.enabled=false src/analyser/evidence.test.ts`
Expected: FAIL con l'elenco `missing` delle tecnologie senza prova (file, estensioni, variabili, lettori diretti).

- [ ] **Step 3: Implementare le firme e convertire i punti elencati**

- [ ] **Step 4: Vederlo passare, con tutto il resto**

Run: `npx vitest run --coverage.enabled=false -u`
Expected: 0 falliti; negli snapshot cambiano solo righe dentro `evidence`, nessuna in `reason` o `techs`.

- [ ] **Step 5: Documentare e committare**

In `README.md`, sezione «Output», aggiungere `evidence` all'esempio JSON e una frase: ogni tecnologia di un componente ha almeno una prova con `kind`, `value`, `path` e, quando il lettore la conosce, `line`.

```bash
git add src README.md
git commit -m "feat: give every detected technology its evidence"
```

---

### Task 5: Le dichiarazioni in ingresso

**Files:**
- Modify: `src/types/index.ts`, `src/analyser/index.ts`, `src/cli.ts`, `src/index.ts`, `README.md`
- Test: `src/analyser/declarations.test.ts` (nuovo)

**Interfaces:**
- Consumes: `matchedPackages`, `evidenceKind` (Task 3), `addTech` con la prova (Task 2).
- Produces:

```ts
// src/types/index.ts, esportato da src/index.ts
export interface Declaration {
  type: SupportedDeps;
  name: string;
  version?: string;
  /** Relativo alla radice analizzata, con `/`. */
  path: string;
  line?: number;
  /** Chi l'ha letta: riportata tale e quale nella prova. */
  source: string;
}

// src/analyser/index.ts
analyser({ provider, declarations?: Declaration[] }): Promise<Payload>

// src/cli.ts
--declarations <FILE>   // un array JSON di Declaration
```

Le dichiarazioni si riconoscono con le stesse regole dei manifest. Le tecnologie e le prove vanno sul componente radice; la prova ha `path` dentro la radice, `line` e `source` della dichiarazione. Un nome che nessuna regola conosce non dà nulla. Sono errori, con il numero della voce nel messaggio: un `type` che non è un `SupportedDeps`; un `path` assoluto o che esce dalla radice; un campo obbligatorio mancante; con il CLI, un file che non è un array JSON (codice di uscita 1, nessun risultato scritto).

- [ ] **Step 1: Scrivere i test che falliscono**

```ts
const project = () => new FakeProvider({
  paths: { '/': ['package.json', 'setup.cfg'] },
  files: { '/package.json': JSON.stringify({ name: 'app', dependencies: { react: '18' } }), '/setup.cfg': '' },
});

it('recognises external declarations and keeps their source', async () => {
  const result = await analyser({ provider: project(), declarations: [
    { type: 'python', name: 'requests', version: '>=2', path: 'setup.cfg', line: 4, source: 'python-build' },
    { type: 'python', name: 'not-a-known-package', path: 'setup.cfg', source: 'python-build' },
  ] });
  expect(result.toJson('').evidence).toContainEqual(
    { tech: 'requests', kind: 'package', value: 'requests', path: '/setup.cfg', line: 4, source: 'python-build' });
});

it('keeps both proofs when the fork and a declaration agree', async () => {
  const result = flatten(await analyser({ provider: project(), declarations: [
    { type: 'npm', name: 'react', path: 'package.json', line: 1, source: 'renovate' },
  ] }), { merge: true });
  const sources = [result, ...result.childs].flatMap((c) => c.toJson('').evidence)
    .filter((e) => e.tech === 'react').map((e) => e.source).sort();
  expect(sources).toEqual(['renovate', 'stack-analyser']);
});

it('rejects a declaration outside the project or of an unknown type', async () => {
  const bad = (declaration: object) => analyser({ provider: project(), declarations: [declaration as never] });
  await expect(bad({ type: 'npm', name: 'react', path: '../other/package.json', source: 'x' })).rejects.toThrow(/declaration 0/);
  await expect(bad({ type: 'cobol', name: 'react', path: 'package.json', source: 'x' })).rejects.toThrow(/declaration 0/);
  await expect(bad({ type: 'npm', name: 'react', path: 'package.json' })).rejects.toThrow(/declaration 0/);
});
```

- [ ] **Step 2: Vederli fallire**

Run: `npx vitest run --coverage.enabled=false src/analyser/declarations.test.ts`
Expected: FAIL, `declarations` non è un'opzione di `analyser`.

- [ ] **Step 3: Implementare tipo, opzione e `--declarations`**

- [ ] **Step 4: Vederli passare**

Run: `npx vitest run --coverage.enabled=false`
Expected: 0 falliti, nessuno snapshot cambiato.

- [ ] **Step 5: Documentare e committare**

In `README.md`, sezione «CLI», l'opzione con un esempio di file; in «Programmatic Usage», l'opzione `declarations`.

```bash
git add src README.md
git commit -m "feat: recognise declarations read by other tools"
```

---

### Task 6: Il perimetro lo decide chi lancia

**Files:**
- Modify: `src/provider/base.ts`, `src/provider/fs.ts`, `src/provider/fake.ts`, `src/payload/index.ts`, `src/cli.ts`, `README.md`
- Test: `src/provider/fs.test.ts` e `src/payload/evidence.test.ts` (aggiunte in coda)

**Interfaces:**
- Consumes: niente dei task precedenti.
- Produces:

```ts
// src/provider/base.ts
export interface BaseProvider { /* … */ readonly skipDirs?: readonly string[] }   // sostituisce IGNORED_DIVE_PATHS quando c'è

// src/provider/fs.ts e fake.ts
new FSProvider({ path, ignorePaths?, maxFileBytes?, skipDirs?: string[] })
new FakeProvider({ paths, files, skipDirs?: string[] })

// src/cli.ts
--skip-dirs <NAMES>   // nomi di cartella separati da virgola; sostituisce l'elenco predefinito, anche vuoto
--ignore <PATHS>      // percorsi relativi separati da virgola, passati a `ignorePaths`
```

`Payload.recurse` salta una cartella quando il suo nome è in `provider.skipDirs ?? IGNORED_DIVE_PATHS`. Senza opzioni il comportamento non cambia.

- [ ] **Step 1: Scrivere il test che fallisce**

```ts
it('dives into a folder the default list skips when the caller says so', async () => {
  const paths = { '/': ['tests/'], '/tests': ['package.json'] };
  const files = { '/tests/package.json': JSON.stringify({ name: 't', dependencies: { vitest: '1' } }) };
  const found = async (skipDirs?: string[]) =>
    flatten(await analyser({ provider: new FakeProvider({ paths, files, skipDirs }) }), { merge: true }).techs.has('vitest');
  expect(await found()).toBe(false);
  expect(await found([])).toBe(true);
  expect(await found(['tests'])).toBe(false);
});
```

- [ ] **Step 2: Vederlo fallire**

Run: `npx vitest run --coverage.enabled=false src/payload/evidence.test.ts`
Expected: FAIL sulla seconda attesa.

- [ ] **Step 3: Implementare `skipDirs` e le due opzioni del CLI**

- [ ] **Step 4: Vederlo passare**

Run: `npx vitest run --coverage.enabled=false`
Expected: 0 falliti, nessuno snapshot cambiato.

- [ ] **Step 5: Documentare e committare**

In `README.md`, sezione «Filesystem provider», `skipDirs` e l'elenco predefinito; in «CLI», le due opzioni.

```bash
git add src README.md
git commit -m "feat: let the caller choose which folders are skipped"
```

---

### Task 7: L'avvio rapido

**Files:**
- Create: `benchmarks/startup.mjs`
- Modify: `package.json` (script `bundle`, `devDependencies`), `src/scripts/` se serve, `benchmarks/README.md`
- Test: `src/cli.test.ts` (aggiunta)

**Interfaces:**
- Consumes: i Task 1–6.
- Produces: `dist/cli.mjs`, un solo file con il CLI e tutte le regole, che dà la stessa uscita di `dist/cli.js` e accetta le stesse opzioni. `npm run build` lo produce dopo `tsc`. Resta esterno al file solo ciò che non si può includere, come il WebAssembly di `@cdktf/hcl2json`.

`node benchmarks/startup.mjs CLI PROJECT [--max-ms N]` lancia il CLI cinque volte sul progetto, stampa i cinque tempi e la mediana in millisecondi, ed esce con 1 se la mediana supera `N`.

- [ ] **Step 1: Misurare il punto di partenza**

Run: `npm run build && node benchmarks/startup.mjs dist/cli.js ../daodan/benchmarks/project-model/fixtures/py-fastapi-compose`
Expected: mediana di alcuni secondi (circa 4,8 il 21 novembre 2026 sulla macchina del proprietario). Il numero va nel README.

- [ ] **Step 2: Scrivere il test che fallisce**

In `src/cli.test.ts`: il test lancia `dist/cli.js` e `dist/cli.mjs` su `tests/__fixtures__` con `--flat`, toglie da entrambe le uscite i campi `id`, e i riferimenti che li contengono (`inComponent`, `edges[].target`), e attende che siano uguali. Salta, con il motivo, se `dist/` non c'è.

Run: `npx vitest run --coverage.enabled=false src/cli.test.ts`
Expected: FAIL, `dist/cli.mjs` non esiste.

- [ ] **Step 3: Produrre `dist/cli.mjs`**

Con esbuild, come `devDependency` a versione esatta: `--bundle --platform=node --format=esm`. Soluzione pronta, niente concatenazione a mano.

- [ ] **Step 4: Vedere il test passare e l'obiettivo raggiunto**

Run: `npm run build && npx vitest run --coverage.enabled=false src/cli.test.ts && node benchmarks/startup.mjs dist/cli.mjs ../daodan/benchmarks/project-model/fixtures/py-fastapi-compose --max-ms 1000`
Expected: test passato; codice di uscita 0, mediana sotto 1.000 ms.

Se la mediana resta sopra: non si abbassa la soglia. Si scrive nel README la misura con il profilo di dove va il tempo (`node --cpu-prof`), ci si ferma qui e si torna dal proprietario: è il rischio che la spec nomina.

- [ ] **Step 5: Registrare e committare**

In `benchmarks/README.md`, una sezione «Startup» con il comando e le due mediane.

```bash
git add package.json package-lock.json benchmarks src
git commit -m "perf: ship the CLI and its rules as one file"
```

---

### Task 8: Le regole che ha solo il registro di Daodan

**Files:**
- Create: `benchmarks/port-registry.mjs`, `benchmarks/registry-port.json`
- Create: un file di regola per voce nuova in `src/rules/<tipologia>/<id>.ts`
- Modify: le regole che ricevono pacchetti, `src/types/techs.ts`, gli `index.ts` delle tipologie (li scrive `npm run prebuild`), `src/rules/tool/jinja2.ts` → `src/rules/tool/jinja.ts`
- Modify: `benchmarks/README.md` (sezione «Measured results»)
- Test: `src/rules/packageIdentities.test.ts` (aggiunta), più `src/rules/quality.test.ts` e gli snapshot esistenti

**Interfaces:**
- Consumes: `daodan/daodan/data/service-registry.json` (schema `daodan/service-registry/v1`: voci con `id`, `name`, `kind`, `category?`, `type`, `signs.packages`, `signs.patterns`, `signs.env`, `signs.hosts`, `signs.files`).
- Produces: `benchmarks/registry-port.json`, che il piano 3 legge:

```json
{ "registry": "<sha256 del file letto>", "new": ["<id>"], "extended": { "<id>": ["<tipo>:<nome>"] },
  "renamed": { "react-email": "reactemail" },
  "differences": [{ "id": "<id>", "sign": "<tipo>:<valore>", "reason": "<perché il fork non lo prende>" }] }
```

`node benchmarks/port-registry.mjs REGISTRY.json` stampa quel JSON senza scrivere nulla; con `--write` crea i file di regola, aggiunge i pacchetti alle regole esistenti e scrive il report. `differences` si scrive a mano nel file e lo script la conserva: ogni segno del registro che non è una regola del fork deve stare lì con il suo motivo, altrimenti lo script esce con 1 e lo elenca.

Che cosa c'è da portare, misurato il 21 novembre 2026 sul registro distribuito e sul fork a `c8476c6`:
- 146 ID che il fork non ha, con 194 pacchetti;
- sugli ID in comune, 173 pacchetti (141 ID), 51 espressioni (48 ID) e 1 variabile che il fork non elenca: si portano, tranne quelli che il fork ha tolto apposta, che vanno in `differences` (le risorse `azurerm_app_service`, `azurerm_linux_web_app` e `azurerm_windows_web_app` di `azure.staticwebapps`, ora di `azure.appservice`; la variabile `ROOLBAR_` di `rollbar`, un refuso; un'espressione che il fork ha già in forma più stretta, come `cats-core`);
- 22 nomi di file (19 ID) e 8 segni di sorgente (6 ID) che il fork riconosce con un lettore invece che con una regola (`Dockerfile` e i file Compose per `docker`, `.github` per `github`, gli import Swift, le chiamate `ExUnit`): per ognuno un test in `readerEvidence.test.ts` prova che il fork lo riconosce da solo, e il segno va in `differences` con quel motivo; se il fork non lo riconosce, diventa una regola `files`;
- le 13 voci `wrong_signs` di `daodan/daodan/data/registry-additions.json`: un segno che le aggiunte dichiarano sbagliato si toglie dalla regola del fork, se c'è ancora.

Corrispondenze, le stesse di `daodan/daodan/core/specfy_rules.mjs`:

| Registro | Fork |
| --- | --- |
| ecosistemi `npm`, `pypi`, `crates`, `go`, `composer`, `rubygems`, `docker`, `github-actions`, `terraform`, `terraform-resource`, `deno`, `maven`, `nuget`, `pub`, `hex`, `swiftpm` | `npm`, `python`, `rust`, `golang`, `php`, `ruby`, `docker`, `githubAction`, `terraform`, `terraform.resource`, `deno`, `maven`, `nuget`, `pub`, `hex`, `swiftpm` |
| `signs.packages` | `dependencies` con `name` stringa |
| `signs.patterns` | `dependencies` con `name` espressione regolare ed `example` |
| `signs.env`, `signs.hosts`, `signs.files` | `dotenv`, `hosts`, `files` |
| categoria `service` con `type` `database`, `filesystem`, `coda`, `autenticazione`, `gateway` | tipologia `db`, `storage`, `queue`, `auth`, `network` |
| categoria `service`, altri `type` | `saas` |
| categoria `framework` | `framework` |
| categoria `library` o `tool` | `tool` |
| nessuna categoria | come `service` se `kind` è `service`, altrimenti `tool` |

Una voce del registro è un doppione di una regola del fork quando hanno lo stesso nome, senza maiuscole e segni, o un pacchetto in comune nello stesso ecosistema. Vale la regola degli ID dei Global Constraints: `react-email` confluisce in `reactemail` e finisce in `renamed`; la regola `jinja2` del fork, nata in questo ramo, prende l'ID `jinja`.

- [ ] **Step 1: Scrivere il test che fallisce**

In `src/rules/packageIdentities.test.ts`:

```ts
it('no package identifies two technologies', () => {
  const owners = new Map<string, Set<string>>();
  for (const rule of registeredRules) {
    for (const dep of rule.dependencies ?? []) {
      if (typeof dep.name !== 'string') continue;
      const key = `${dep.type}:${dep.name.toLowerCase()}`;
      owners.set(key, (owners.get(key) ?? new Set()).add(rule.tech));
    }
  }
  const shared = [...owners].filter(([, techs]) => techs.size > 1).map(([key, techs]) => `${key} → ${[...techs].sort().join(', ')}`);
  expect(shared).toMatchSnapshot();
});
```

Run: `npx vitest run --coverage.enabled=false src/rules/packageIdentities.test.ts -u`
Lo snapshot scritto ora elenca le condivisioni volute che esistono già. Dopo il porting non deve crescere.

- [ ] **Step 2: Fotografare cosa riconosce il fork prima del porting**

```bash
npm run build
node benchmarks/replay-declarations.mjs . . ../daodan/benchmarks/project-model ../coverage-before.json
```

Expected: il comando stampa i totali; `../coverage-before.json` contiene `idsAfter` per progetto.

- [ ] **Step 3: Scrivere `benchmarks/port-registry.mjs` ed eseguirlo senza `--write`**

Run: `npm run build && node benchmarks/port-registry.mjs ../daodan/daodan/data/service-registry.json`
Expected: le voci del registro con segni e senza ID nel fork sono 146, con 194 pacchetti; `new` più i doppioni trovati fa 146; sugli ID in comune lo script elenca 173 pacchetti, 51 espressioni, 22 file, 8 sorgenti e 1 variabile da portare o da motivare, ed esce con 1 finché `differences` non li copre. Fra i doppioni ci sono `react-email` (in `renamed` verso `reactemail`) e `jinja` (coincide con `jinja2`). Ogni altro doppione trovato si legge a mano prima di proseguire.

- [ ] **Step 4: Rinominare `jinja2` in `jinja`, poi eseguire con `--write`**

```bash
git mv src/rules/tool/jinja2.ts src/rules/tool/jinja.ts
```

In quel file `tech: 'jinja'`; in `src/types/techs.ts` `'jinja2'` diventa `'jinja'`.

Run: `node benchmarks/port-registry.mjs ../daodan/daodan/data/service-registry.json --write && npm run build`
Expected: la compilazione passa; `src/types/techs.ts`, che lo script aggiorna, contiene ogni ID di `new`.

- [ ] **Step 5: Verificare che nulla sia andato perso e che la soglia sia raggiunta**

```bash
node benchmarks/replay-declarations.mjs . . ../daodan/benchmarks/project-model ../coverage-after.json
node -e "const b=require('../coverage-before.json'),a=require('../coverage-after.json');let lost=0;for(const p in b.projects){const now=new Set(a.projects[p].idsAfter);for(const id of b.projects[p].idsAfter)if(!now.has(id)&&id!=='jinja2'){lost++;console.log(p,id)}}console.log('lost',lost,JSON.stringify(a.counts))"
```

Expected: `lost 0`; `counts.frameworks.after` è almeno 478 (su 569) e `counts.services.after` almeno 232 (su 518). Sotto soglia: l'elenco `noMatchingPackage` del report dice quale segno del registro lo script non ha portato; si corregge lo script e si ripete dallo Step 4.

Run: `npx vitest run --coverage.enabled=false`
Expected: falliscono solo gli snapshot che elencano ID. Si rigenerano con `-u` dopo aver controllato che `git diff -- '*.snap'` non rimuova ID tranne `jinja2`, e che lo snapshot di `no package identifies two technologies` non abbia righe nuove.

- [ ] **Step 6: Registrare la misura e committare**

In `benchmarks/README.md`, sotto «Measured results», una riga con il numero di tecnologie registrate e i due totali dello Step 5, e il comando di `port-registry.mjs`.

```bash
git add src benchmarks
git commit -m "feat(rules): add the technologies known only to the Daodan registry"
```

---

### Task 9: Il rilascio

**Files:**
- Modify: `package.json`
- Create: `benchmarks/verify-package.mjs`

**Interfaces:**
- Consumes: i Task 1–8.
- Produces, per il piano 2: l'URL dell'asset `specfy-stack-analyser-1.27.6-daodan.1.tgz` del rilascio `v1.27.6-daodan.1` di `acaprino/stack-analyser`, il suo sha256, e il fatto che il pacchetto scompattato in `package/` gira con `node package/dist/cli.mjs PROGETTO --output FILE --declarations FILE --skip-dirs NOMI --ignore PERCORSI` senza `npm install`.

In `package.json`: `"version": "1.27.6-daodan.1"`; `repository.url`, `homepage` e `bugs.url` puntano a `acaprino/stack-analyser`; `"bundledDependencies"` elenca le 14 chiavi di `dependencies`. Il nome resta `@specfy/stack-analyser`.

- [ ] **Step 1: Scrivere `benchmarks/verify-package.mjs`**

`node benchmarks/verify-package.mjs` esegue `npm pack`, scompatta il `.tgz` in una cartella temporanea fuori dal repository, lancia da lì `node package/dist/cli.mjs <repo>/tests/__fixtures__ --output out.json` con `NODE_PATH` vuoto, e termina con codice 1 se: il comando fallisce; nessun componente ha una tecnologia con prova `terraform` (il WebAssembly di `hcl2json`); nessuno ha una prova `package`. Stampa il percorso del `.tgz` e il suo sha256.

- [ ] **Step 2: Vederlo fallire**

Run: `npm run build && node benchmarks/verify-package.mjs`
Expected: FAIL con `Cannot find package`, perché le dipendenze non sono nel pacchetto.

- [ ] **Step 3: Aggiornare `package.json` come sopra**

- [ ] **Step 4: Vederlo passare**

Run: `npm run build && node benchmarks/verify-package.mjs`
Expected: codice 0, percorso e sha256 stampati.

- [ ] **Step 5: Committare e pubblicare**

```bash
git add package.json benchmarks/verify-package.mjs
git commit -m "chore(release): 1.27.6-daodan.1 with bundled dependencies"
git tag v1.27.6-daodan.1
git push fork feature/stack-detection v1.27.6-daodan.1
```

Prima del comando seguente chiedere conferma al proprietario: crea un rilascio pubblico sul suo account.

```bash
gh release create v1.27.6-daodan.1 specfy-stack-analyser-1.27.6-daodan.1.tgz --repo acaprino/stack-analyser --title "1.27.6-daodan.1" --notes "sha256: <valore stampato allo Step 4>"
```

Expected: `gh release view v1.27.6-daodan.1 --repo acaprino/stack-analyser --json assets` elenca il `.tgz`.
