import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { applyDaodanRules } from '../daodan/core/specfy_rules.mjs';

test('extends the pinned Specfy definitions using the shipped catalog', async () => {
  const registry = JSON.parse(await readFile(new URL('../daodan/data/service-registry.json', import.meta.url), 'utf8'));
  const detect = () => false;
  const rules = {
    list: [{ tech: 'gcp', type: 'cloud', detect, dependencies: [{ type: 'npm', name: 'passport-google-oauth20' }] }],
    register(rule) { this.list.push(rule); },
    loadOne() { assert.fail('no native path matcher in this case'); },
  };
  applyDaodanRules(rules, registry);
  assert.equal(rules.list.filter(r => r.tech === 'gcp').length, 1);
  assert.equal(rules.list[0].detect, detect);
  assert.ok(!rules.list[0].dependencies.some(d => d.type === 'npm' && d.name.test('passport-google-oauth20')));
  const fastapi = rules.list.find(r => r.tech === 'fastapi');
  assert.equal(fastapi.type, 'framework');
  assert.ok(fastapi.dependencies.some(d => d.type === 'python' && d.name.test('FastAPI')));
  assert.ok(!fastapi.dependencies.some(d => d.type === 'python' && d.name.test('my-fastapi')));
  assert.ok(!rules.list.some(r => r.dependencies?.some(d => ['maven', 'nuget'].includes(d.type))));
});

test('preserves native matchers and scopes normalized Python, Go and literal package keys', () => {
  const files = /^config\.custom$/;
  const nativePattern = /^widget-v[0-9]+$/i;
  const native = { tech: 'widget', name: 'Widget CI', files, dependencies: [{ type: 'npm', name: nativePattern }] };
  const added = [];
  const rules = { list: [native], register() { assert.fail('duplicate registration'); }, loadOne(rule) { added.push(rule); } };
  applyDaodanRules(rules, { entries: [{ id: 'widget', name: 'Widget', kind: 'project', category: 'library', from: ['additions'],
    signs: { packages: { npm: ['example.js'], pypi: ['widget-core'], go: ['acme.org/widget'] },
      patterns: { npm: [nativePattern.source] }, files: ['widget.config.json'] } }] });
  const matches = (type, name) => native.dependencies.some(d => d.type === type && d.name.test(name));
  assert.ok(matches('npm', 'example.js') && !matches('npm', 'exampleXjs'));
  assert.ok(matches('python', 'Widget_.Core') && !matches('python', 'widgetcore'));
  assert.ok(matches('golang', 'acme.org/widget/client') && !matches('golang', 'acme.org/widget2'));
  assert.equal(native.files, files);
  assert.equal(native.name, 'Widget');
  assert.ok(native.dependencies.some(d => d.name === nativePattern));
  assert.deepEqual(added.map(r => r.files), [['widget.config.json']]);
});

test('requires Docker registry and publisher identity, including for unchanged upstream rules', () => {
  const native = { tech: 'redis', dependencies: [{ type: 'docker', name: /redis/ }, { type: 'npm', name: 'redis' }] };
  const rules = { list: [native], register(rule) { this.list.push(rule); } };
  applyDaodanRules(rules, { entries: [
    { id: 'redis', from: ['stack-analyser'], signs: { patterns: { docker: ['redis'] } } },
    { id: 'store', name: 'Store', from: ['additions'], category: 'service', type: 'filesystem', signs: {
      packages: { docker: ['quay.io/acme/store', 'registry.acme:5000/store'] }, patterns: { docker: ['vendor\\/store', '^airbyte\\/'] } } },
    { id: 'router', name: 'Router', from: ['additions'], category: 'service', type: 'gateway',
      signs: { packages: { npm: ['router-sdk'] } } },
  ] });
  const matches = (rule, name) => rule.dependencies.some(dep => dep.type === 'docker' && dep.name.test(name));
  for (const name of ['redis:7', 'library/redis', 'docker.io/redis', 'index.docker.io/library/redis@sha256:a',
    'registry-1.docker.io/redis', 'redis/redis-stack']) assert.ok(matches(native, name), name);
  for (const name of ['redis-private', 'myorg/redis', 'quay.io/redis', 'registry:5000/library/redis']) {
    assert.ok(!matches(native, name), name);
  }
  const [, store, router] = rules.list;
  for (const name of ['quay.io/acme/store:v1', 'registry.acme:5000/store@sha256:b', 'docker.io/vendor/store',
    'airbyte/worker']) assert.ok(matches(store, name), name);
  for (const name of ['acme/store', 'other/store', 'registry.acme:5001/store', 'vendor/store/fork',
    'vendor/airbyte/worker']) assert.ok(!matches(store, name), name);
  assert.equal(store.type, 'storage');
  assert.equal(router.type, 'network');
});
