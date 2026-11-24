// The sidebar of the map: the flows, with the steps of the one that is on, and the elements in view.
import { useState } from 'react';
import { Column, Heading, Icon, NavItem, Sidebar, SidebarGroup, Text, useAppShell } from '@acaprino/sigrid';
import type { Flow, FlowStep } from './envelope.ts';
import type { Model } from './model.ts';
import { ENTRY_LABEL, FLOW_ICON, iconFor, LINK_LABEL } from './icons.ts';
import { bindingSite, entityName, flowTitle, nodeMeta } from './names.ts';

const flowMeta = (flow: Flow) => [ENTRY_LABEL[flow.entry_kind] ?? flow.entry_kind, flow.label ? bindingSite(flow) : null,
  `${flow.steps.length} passi`, flow.complete ? null : 'incompleto'].filter(Boolean).join(' · ');

const stepMeta = (step: FlowStep) => [step.route?.slice(1).join(' '), step.site, step.origin,
  step.confidence === 'sampled' ? 'campionata dal profiler' : step.confidence === 'observed' ? 'osservata in esecuzione' : null,
  step.conflict ? 'destinazioni in conflitto' : null].filter(Boolean).join(' · ');

// What a flow goes through, in order, and where its proof stops: text to read and copy, so not rows to press.
function FlowSteps({ model, flow }: { model: Model; flow: Flow }) {
  const { envelope } = model.state;
  return <>
    <Column as="ol" gap="md" pad="sm" aria-label="Passi del flusso">{flow.steps.slice(0, 40).map((step, index) =>
      <Column as="li" key={index} gap="xs">
        <Text pre>{index + 1}. {entityName(envelope, step.source)} <Text variant="strong">{LINK_LABEL[step.type] ?? step.type}</Text> {entityName(envelope, step.target)}</Text>
        <Text variant="note" pre>{stepMeta(step)}</Text>
      </Column>)}</Column>
    {!!flow.gaps?.length && <Column gap="sm" pad="sm">
      <Heading size="label">Dove si ferma la prova</Heading>
      <Column as="ul" gap="sm">{flow.gaps.map((gap, index) =>
        <Column as="li" key={index} gap="xs"><Text variant="note" pre>{gap.site}</Text><Text pre>{gap.reason}</Text></Column>)}</Column>
    </Column>}
  </>;
}

export function Navigation({ model, ready, open, onOpenChange }: { model: Model; ready: boolean; open: boolean; onOpenChange: (open: boolean) => void }) {
  const { state, dispatch, projection, selectedIds } = model;
  const shell = useAppShell();
  const [collapsed, setCollapsed] = useState(false);
  // The rail shows its rows' icons and no text: what is only text leaves it.
  const rail = shell.sidebar === 'rail' || (shell.sidebar === 'full' && collapsed);
  const current = state.envelope.flows.find(flow => flow.ref === state.flow);
  return <Sidebar aria-label="Mappa" open={open} onOpenChange={onOpenChange} collapsed={collapsed} onCollapsedChange={setCollapsed}>
    {ready ? <>
      <SidebarGroup label="Flussi" icon={<Icon name={FLOW_ICON} />}>{state.envelope.flows.map(flow =>
        <NavItem key={flow.ref} icon={<Icon name={FLOW_ICON} />} current={flow === current} aria-pressed={flow === current} description={flowMeta(flow)}
          onClick={() => dispatch({ type: 'flow', ref: flow === current ? null : flow.ref })}>{flowTitle(state.envelope, flow)}</NavItem>)}</SidebarGroup>
      {!state.envelope.flows.length && !rail && <Text as="p" variant="muted">Nessun flusso: questo run non ha regole di collegamento (codebase_map_flows).</Text>}
      {current && !rail && <FlowSteps model={model} flow={current} />}
      <SidebarGroup label="Elementi visibili" icon={<Icon name="bulletList" />}>{projection.nodes.map(node =>
        <NavItem key={node.id} icon={<Icon name={iconFor(node)} />} current={selectedIds.has(node.id)} description={nodeMeta(node)}
          onClick={() => dispatch({ type: 'select', ref: node.ref })}
          onDoubleClick={() => { if (node.collapsed) dispatch({ type: 'open', ref: node.ref }); }}>{node.label}</NavItem>)}</SidebarGroup>
    </> : rail ? null : <Text as="p" variant="muted">In attesa dell'export.</Text>}
  </Sidebar>;
}
