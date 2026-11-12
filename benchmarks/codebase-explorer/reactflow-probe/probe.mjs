// Proiezione della fixture per React Flow + ELK: un'occorrenza del file per ogni gruppo che lo contiene.
import { readFileSync } from 'node:fs'
import ELK from 'elkjs/lib/elk.bundled.js'

const env = JSON.parse(readFileSync(new URL('../fixture/visual.json', import.meta.url), 'utf8'))
const byRef = Object.fromEntries(env.entities.map(e => [e.ref, e]))
const fileOf = Object.fromEntries(env.relations.filter(r => r.kind === 'defines').map(r => [r.target, r.source]))
const groups = {}
for (const m of env.memberships.filter(m => m.view === 'logical')) (groups[m.group] ??= []).push(m.member)
// React Flow ha un solo parentId per nodo: il file condiviso diventa due occorrenze, una per gruppo.
const occurrence = (group, ref) => `${group}|${ref}`
const occurrencesOf = ref => Object.entries(groups).filter(([, members]) => members.includes(ref)).map(([g]) => occurrence(g, ref))
const children = Object.entries(groups).map(([group, members]) => ({
  id: group, layoutOptions: { 'elk.padding': '[top=36,left=12,bottom=12,right=12]' },
  children: members.map(ref => ({ id: occurrence(group, ref), width: 180, height: 48 })),
}))
const outside = env.entities.filter(e => ['external', 'store'].includes(e.type)).map(e => ({ id: e.ref, width: 180, height: 48 }))
const nodeOf = ref => byRef[ref]?.type === 'symbol' ? fileOf[ref] : ref
const edges = []
for (const flow of env.flows) for (const [i, step] of flow.steps.entries()) {
  const [source, target] = [nodeOf(step.source), nodeOf(step.target)]
  for (const s of (occurrencesOf(source).length ? occurrencesOf(source) : [source]))
    for (const t of (occurrencesOf(target).length ? occurrencesOf(target) : [target]))
      if (s !== t) edges.push({ id: `${flow.ref}#${i}|${s}|${t}`, sources: [s], targets: [t] })
}
const graph = { id: 'root', layoutOptions: { 'elk.algorithm': 'layered', 'elk.direction': 'RIGHT', 'elk.hierarchyHandling': 'INCLUDE_CHILDREN', 'elk.edgeRouting': 'ORTHOGONAL' },
  children: [...children, ...outside], edges }
const t0 = performance.now()
const laid = await new ELK().layout(graph)
const ms = performance.now() - t0
const placed = laid.children.flatMap(c => [c, ...(c.children || [])]).filter(n => n.x !== undefined)
const shared = 'file:shared/money.ts'
const flowNodes = env.flows.map(f => ({ flow: f.ref, nodes: new Set(f.nodes.map(nodeOf).flatMap(r => occurrencesOf(r).length ? occurrencesOf(r) : [r])).size }))
console.log(JSON.stringify({
  groups: Object.keys(groups).length,
  nodes_placed: placed.length,
  shared_file_occurrences: occurrencesOf(shared).length,
  shared_file_groups: occurrencesOf(shared).map(o => o.split('|')[0]),
  edges: edges.length,
  states_kept: [...new Set(env.entities.flatMap(e => [e.status, e.freshness].filter(Boolean)))].sort(),
  node_types: [...new Set(env.entities.map(e => e.node_type).filter(Boolean))].sort(),
  flow_highlight_nodes: flowNodes,
  layout_ms: Math.round(ms),
}, null, 1))
