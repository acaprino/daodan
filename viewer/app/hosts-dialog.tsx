// The question about the hosts a tool of the project asked to reach outside the registries: one window for each tool's group, its
// hosts with their port, address and declaring files, and the four answers. Closed without one, it waits in the palette.
import { Badge, Button, Cluster, Column, Icon, Section, Text } from '@acaprino/sigrid/primitives';
import { DescriptionList, Dialog, Note } from '@acaprino/sigrid/components';
import { useCommand } from '@acaprino/sigrid/assemblies';
import { pendingGroup, putAside, reachesNetwork, REPLIES, requestFacts, titleOf } from './egress.ts';
import { model, useModel } from './use-model.ts';

export function HostsDialog() {
  const s = useModel();
  const groups = s.server?.egress, group = pendingGroup(groups, s.hostsHidden), replying = s.hostsReplying;
  useCommand({ id: 'daodan.hosts.answer', label: 'Rispondi alle richieste di rete', group: 'Viste', icon: <Icon name="globe" />,
    when: group === null && putAside(groups, s.hostsHidden), run: model.showHosts });
  return <Dialog open={group !== null} onOpenChange={open => { if (!open) model.hideHosts(); }} width="lg"
    title={group ? titleOf(group) : ''}
    description="Lo strumento chiede di raggiungere questi host, fuori dai registri. La risposta vale per tutti gli host del gruppo."
    footer={REPLIES.map(({ reply, label }) =>
      <Button key={reply} variant={reply === 'once' ? 'default' : reply === 'no' ? 'ghost' : 'outline'} autoFocus={reply === 'no'}
        loading={replying === reply} disabled={replying !== '' && replying !== reply} onClick={() => { model.replyHosts(reply); }}>{label}</Button>)}>
    {group && <Column gap="lg" data-selectable="">
      {reachesNetwork(group) && <Note tone="warning" title="Un host è nella rete dell’utente.">
        Il suo indirizzo è privato, di loopback o link-local: approvarlo apre al container la rete locale.
      </Note>}
      {group.requests.map(request => {
        const facts = requestFacts(request);
        return <Section key={`${request.host}:${request.port}`} title={<Text mono>{request.host}</Text>} level={3}>
          <DescriptionList aria-label={request.host} items={[
            { name: 'Porta', value: facts.port },
            { name: 'Indirizzo risolto', value: <Cluster>
              <Text mono>{facts.address}</Text>
              {request.network && <Badge variant="secondary" tone="warning">Rete dell’utente</Badge>}
            </Cluster> },
            { name: 'Dichiarato in', value: facts.declared, code: request.declared_in.length > 0 },
          ]} />
        </Section>;
      })}
    </Column>}
  </Dialog>;
}
