// Run in the analyzer container: node specfy_rules.mjs SPECFY_PACKAGE PROJECT OUTPUT [CATALOGUE]
// SPECFY_PACKAGE is the trusted installation of @specfy/stack-analyser, separate from PROJECT.
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const ecosystemTypes = new Map(Object.entries({
  npm: 'npm', pypi: 'python', crates: 'rust', go: 'golang', composer: 'php', rubygems: 'ruby',
  docker: 'docker', 'github-actions': 'githubAction', terraform: 'terraform',
  'terraform-resource': 'terraform.resource', deno: 'deno',
}));
const serviceTypes = new Map(Object.entries({
  database: 'db', filesystem: 'storage', coda: 'queue', autenticazione: 'auth', gateway: 'network',
}));

const literal = value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

function dockerRepository(reference) {
  let [name] = reference.toLowerCase().split('@');
  if (name.lastIndexOf(':') > name.lastIndexOf('/')) name = name.slice(0, name.lastIndexOf(':'));
  return name.replace(/^(?:docker\.io|index\.docker\.io|registry-1\.docker\.io)\//, '').replace(/^library\//, '');
}

// Specfy's dependency API accepts RegExp and calls test() on the raw image identifier.
class DockerRepositoryMatcher extends RegExp {
  test(reference) { return super.test(dockerRepository(reference)); }
}

function dockerPattern(pattern, flags) {
  const name = pattern.replaceAll('\\/', '/');
  if (/^[a-z0-9_/-]+$/i.test(name)) {
    // A bare publisher may have several images. A scoped name identifies one repository.
    return new DockerRepositoryMatcher('^' + literal(name) + (name.includes('/') ? '$' : '(?:/|$)'), flags);
  }
  return new DockerRepositoryMatcher(pattern, flags);
}

function exactPackage(name, ecosystem) {
  // Specfy compiles string package names as regular expressions. Escape the literal identifier first.
  if (ecosystem === 'docker') return new DockerRepositoryMatcher('^' + literal(dockerRepository(name)) + '$', 'i');
  const pattern = ecosystem === 'pypi' ? name.split(/[-_.]+/).map(literal).join('[-_.]+') : literal(name);
  return new RegExp('^' + pattern + (ecosystem === 'go' ? '(?:/|$)' : '$'), 'i');
}

function dependencies(signs, native, ecosystems = ecosystemTypes) {
  const deps = [];
  for (const [ecosystem, type] of ecosystems) {
    for (const name of signs.packages?.[ecosystem] ?? []) {
      deps.push({ type, name: exactPackage(name, ecosystem), example: name });
    }
    for (const pattern of signs.patterns?.[ecosystem] ?? []) {
      const original = native?.dependencies?.find(dep => dep.type === type && dep.name.source === pattern);
      if (ecosystem === 'docker') {
        deps.push({ ...original, type, name: dockerPattern(pattern, original?.name.flags ?? 'i') });
      } else {
        deps.push(original ?? { type, name: new RegExp(pattern, 'i') });
      }
    }
  }
  return deps;
}

/**
 * Apply the shipped registry to Specfy's registered definitions, before its one rules.loadAll().
 * Keep component detectors and other native behaviour. Only package and basename evidence is projected.
 * For ecosystems Specfy does not read, Daodan consumes the manifest evidence in its own stack step.
 */
export function applyDaodanRules(rules, registry) {
  const upstream = new Map(rules.list.map(rule => [rule.tech, rule]));
  for (const entry of registry.entries) {
    const native = upstream.get(entry.id);
    const signs = entry.signs ?? {};
    if (!entry.from.includes('additions')) {
      if (native?.dependencies?.some(dep => dep.type === 'docker')) {
        native.dependencies = [...native.dependencies.filter(dep => dep.type !== 'docker'),
          ...dependencies(signs, native, [['docker', 'docker']])];
      }
      continue;
    }
    const deps = dependencies(signs, native);
    const files = signs.files ?? [];
    if (!native && !deps.length && !files.length) continue;

    // New library IDs use Specfy's tool type because its vocabulary has no library type.
    const category = entry.category ?? entry.kind;
    const type = category === 'service' ? (serviceTypes.get(entry.type) ?? 'saas')
      : category === 'framework' ? 'framework' : 'tool';
    const rule = native ?? { tech: entry.id, type };
    rule.name = entry.name;
    rule.dependencies = deps;
    if (!native) rules.register(rule);
    if (rule.files instanceof RegExp || rule.matchFullPath) {
      // Preserve the upstream path matcher; a curated basename is an independent signal.
      const added = files.filter(file => !Array.isArray(rule.files) || !rule.files.includes(file));
      if (added.length) rules.loadOne({ tech: rule.tech, name: rule.name, type: rule.type, files: added });
    } else if (files.length || rule.files) {
      rule.files = files;
    }
  }
}

async function run(packageDir, project, output, catalogue) {
  const registry = JSON.parse(await readFile(new URL('../data/service-registry.json', import.meta.url), 'utf8'));
  const pkg = JSON.parse(await readFile(resolve(packageDir, 'package.json'), 'utf8'));
  if (pkg.name !== '@specfy/stack-analyser' || pkg.version !== registry.versions['stack-analyser']) {
    throw new Error('Use the @specfy/stack-analyser version recorded in the Daodan registry.');
  }
  const moduleUrl = file => pathToFileURL(resolve(packageDir, 'dist', file));
  const { analyser, FSProvider, rules } = await import(moduleUrl('index.js'));
  await import(moduleUrl('rules/index.js'));
  applyDaodanRules(rules, registry);
  rules.loadAll();
  const root = resolve(project);
  const result = await analyser({ provider: new FSProvider({ path: root, ignorePaths: [] }) });
  await writeFile(output, JSON.stringify(result.toJson(root)));
  if (catalogue) {
    await writeFile(catalogue, JSON.stringify(Object.fromEntries(rules.list.map(r => [r.tech, [r.name, r.type]]))));
  }
}

if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  const [, , packageDir, project, output, catalogue] = process.argv;
  if (!output) throw new Error('Expected SPECFY_PACKAGE PROJECT OUTPUT [CATALOGUE]');
  await run(packageDir, project, output, catalogue);
}
