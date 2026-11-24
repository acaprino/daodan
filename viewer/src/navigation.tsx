// The sidebar of the map: the flows are its places (the whole map, or what one flow goes through), the elements in view its things.
import { useState } from 'react';
import { Badge, Button, Count, Icon, Text } from '@acaprino/sigrid/primitives';
import { ItemRow } from '@acaprino/sigrid/components';
import { NavItem, Sidebar, SidebarGroup, useAppShell } from '@acaprino/sigrid/layout';
import type { Model, Phase, Shown } from './model.ts';
import { Mark } from './mark.tsx';
import { FLOW_ICON, iconFor } from './icons.ts';
import { entryName, flowTitle, nodeMeta } from './names.ts';

const NO_MAP: Record<Exclude<Phase, 'ready'>, string> = {
  none: 'Nessuna mappa: non ci sono run.', failed: "Nessuna mappa: l'export non si legge.", loading: "In attesa dell'export.",
};

type NavigationProps = { model: Model; phase: Phase; show: (asked: Shown) => void; open: boolean; onOpenChange: (open: boolean) => void };

export function Navigation({ model, phase, show, open, onOpenChange }: NavigationProps) {
  const { state, dispatch, projection, selectedIds } = model;
  const shell = useAppShell();
  const [collapsed, setCollapsed] = useState(false);
  // The rail shows its places' icons and no text: what is only text, and the things, leave it.
  const rail = shell.sidebar === 'rail' || (shell.sidebar === 'full' && collapsed);
  const { envelope } = state;
  // A flow pressed here is shown: an element's details would cover its steps.
  const toFlow = (ref: string) => { dispatch({ type: 'select', ref: null }); dispatch({ type: 'flow', ref }); show({ flow: ref }); };
  // Where the sidebar is a drawer it closes itself on a place; on a thing it is closed here.
  const enter = (ref: string) => { dispatch({ type: 'open', ref }); onOpenChange(false); };
  const choose = (ref: string) => { dispatch({ type: 'select', ref }); show({ ref }); onOpenChange(false); };
  // What is in a group opened in place says which: its frame is on the canvas, not here.
  const labels = new Map(projection.nodes.map(node => [node.id, node.label]));
  return <Sidebar aria-label="Mappa" open={open} onOpenChange={onOpenChange} collapsed={collapsed} onCollapsedChange={setCollapsed}>
    {phase === 'ready' ? <>
      <SidebarGroup label="Flussi" icon={<Icon name={FLOW_ICON} />}>
        <NavItem icon={<Icon name="all" />} current={state.flow === null} onClick={() => dispatch({ type: 'flow', ref: null })}>Tutta la mappa</NavItem>
        {envelope.flows.map(flow =>
          <NavItem key={flow.ref} icon={<Icon name={FLOW_ICON} />} current={flow.ref === state.flow} description={entryName(flow)} onClick={() => toFlow(flow.ref)}
            end={<>{!flow.complete && <Badge variant="secondary">incompleto</Badge>}<Count value={flow.steps.length} label={flow.steps.length === 1 ? 'passo' : 'passi'} reserve /></>}>
            {flowTitle(envelope, flow)}</NavItem>)}
      </SidebarGroup>
      {!envelope.flows.length && !rail && <Text as="p" variant="muted">Nessun flusso: questo run non ha regole di collegamento (codebase_map_flows).</Text>}
      {/* The group draws the list (a `ul`): its rows go in it as they are, and an ItemList would be a list in a list. */}
      {!rail && projection.nodes.length > 0 && <SidebarGroup label="Elementi visibili" icon={<Icon name="bulletList" />}>{projection.nodes.map(node =>
        <ItemRow key={node.id} title={node.label} description={[nodeMeta(node), node.parent !== null && `in ${labels.get(node.parent)}`].filter(Boolean).join(' · ')}
          leading={<Mark mark={node.mark} icon={iconFor(node)} />} current={selectedIds.has(node.id)}
          // The second press of a double press enters: a row takes no double press of its own.
          onClick={event => { if (node.open !== undefined && event.detail === 2) enter(node.ref); else choose(node.ref); }}
          controlSide="end" control={node.open !== undefined && <Button variant="ghost" size="xs" aria-label={`Entra in ${node.label}`} onClick={() => enter(node.ref)}>Entra</Button>} />)}
      </SidebarGroup>}
    </> : !rail && <Text as="p" variant="muted">{NO_MAP[phase]}</Text>}
  </Sidebar>;
}
