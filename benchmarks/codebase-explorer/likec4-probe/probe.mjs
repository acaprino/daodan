// Proiezione della fixture in LikeC4 Model Builder: misura cosa entra senza adattamento.
import { readFileSync } from 'node:fs'
import { Builder } from '@likec4/core/builder'

const env = JSON.parse(readFileSync(new URL('../fixture/visual.json', import.meta.url), 'utf8'))
const kinds = ['component', 'feature', 'external', 'build', 'directory', 'file', 'symbol', 'store']
const id = ref => ref.replace(/[^A-Za-z0-9_]/g, '_')
// LikeC4 deriva il genitore dall'FQN (a.b.c): un elemento ha un solo genitore.
const parent = {}
const lost = []
for (const m of env.memberships.filter(m => m.view === 'logical')) {
  if (parent[m.member]) lost.push(`${m.member} in ${m.group}`)
  else parent[m.member] = m.group
}
for (const r of env.relations.filter(r => r.kind === 'defines')) parent[r.target] = r.source
const fqn = ref => (parent[ref] ? fqn(parent[ref]) + '.' : '') + id(ref)
const tags = ['inferred', 'confirmed', 'incomplete', 'stale_body', 'fresh', 'uncovered', 'internal', 'external']
const b = Builder.specification({
  elements: Object.fromEntries(kinds.map(k => [k, {}])),
  relationships: Object.fromEntries(['imports', 'calls', 'uses', 'declares', 'chiama', 'scrive', 'legge', 'usa'].map(k => [k, {}])),
  tags: Object.fromEntries(tags.map(t => [t, {}])),
})
const { model: m, views: v } = b.helpers()
const ordered = [...env.entities].sort((a, z) => fqn(a.ref).split('.').length - fqn(z.ref).split('.').length)
const ops = ordered.map(e => m.model(m[e.type](fqn(e.ref), {
  title: e.name,
  description: e.description,
  tags: [e.status, e.freshness, e.location].filter(Boolean),
  metadata: { ref: e.ref, node_type: e.node_type ?? '', provenance: e.provenance ?? '' },
})))
const rels = env.relations.filter(r => !['contains', 'defines'].includes(r.kind))
  .map(r => m.model(m.rel(fqn(r.source), fqn(r.target), { kind: r.kind })))
const flowSteps = env.flows.flatMap(f => f.steps).map(s => m.model(m.rel(fqn(s.source), fqn(s.target), { kind: s.type, title: s.origin })))
let built = b.with(...ops, ...rels, ...flowSteps,
  v.views(v.view('index', v.$include('*')), v.view('server', v.$include('component_server.*'))))
const t0 = performance.now()
const lc = built.toLikeC4Model()
const ms = performance.now() - t0
const elements = [...lc.elements()]
console.log(JSON.stringify({
  elements: elements.length,
  shared_file_parents_lost: lost,
  shared_file_occurrences: elements.filter(e => e.getMetadata('ref') === 'file:shared/money.ts').length,
  views: [...lc.views()].map(x => ({ id: x.id, nodes: [...x.nodes()].length, edges: [...x.edges()].length })),
  stale_body_tagged: elements.filter(e => e.tags.includes('stale_body')).map(e => e.title),
  compute_ms: Math.round(ms),
}, null, 1))
