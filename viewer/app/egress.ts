// The hosts a tool of the project asked to reach outside the registries, a group for each tool, as the state has them: which group
// the page asks about, what it sends with the person's answer and what it says of it. It draws nothing.
import type { HostGroup, HostRequest } from './server.ts';

export type Reply = 'always' | 'once' | 'no' | 'block';

// The four answers, in the order the window shows them, the word of their button and what is said once the server has them.
export const REPLIES: readonly { reply: Reply; label: string; said: string }[] = [
  { reply: 'no', label: 'No', said: 'Host rifiutati per questa analisi' },
  { reply: 'block', label: 'Blocca sempre', said: 'Host bloccati per questo progetto' },
  { reply: 'always', label: 'Sempre per questo progetto', said: 'Host approvati per questo progetto' },
  { reply: 'once', label: 'Solo per questa analisi', said: 'Host approvati per questa analisi' },
];

// A group is the same while its tool, its project and its hosts are: one that grows is asked about again.
export const groupKey = (group: HostGroup) =>
  JSON.stringify([group.tool, group.project, group.requests.map(request => [request.host, request.port])]);

// The group the window asks about: the first one the person did not put aside (`hidden`, by `groupKey`), or none.
export const pendingGroup = (groups: readonly HostGroup[] | undefined, hidden: readonly string[]): HostGroup | null =>
  (groups ?? []).find(group => group.requests.length > 0 && !hidden.includes(groupKey(group))) ?? null;

// Whether a group waits that the person put aside: the palette offers to answer it.
export const putAside = (groups: readonly HostGroup[] | undefined, hidden: readonly string[]) =>
  (groups ?? []).some(group => group.requests.length > 0 && hidden.includes(groupKey(group)));

// The hosts an answer is for, each once: the server takes hosts, not ports.
export const hostsOf = (group: HostGroup) => [...new Set(group.requests.map(request => request.host))];

export const replyBody = (group: HostGroup, reply: Reply) => ({ hosts: hostsOf(group), reply });

export const repliedWords = (reply: Reply, hosts: readonly string[]) =>
  `${REPLIES.find(item => item.reply === reply)!.said}: ${hosts.join(', ')}.`;

// The facts of one request, in words. The user's network is said beside the address (the window marks it).
export const requestFacts = (request: HostRequest) => ({
  port: String(request.port),
  address: request.address ?? 'non risolto',
  declared: request.declared_in.length ? request.declared_in.join(', ') : 'nessun file del progetto',
});

// Whether a host of the group resolves inside the user's own network (private, loopback, link-local).
export const reachesNetwork = (group: HostGroup) => group.requests.some(request => request.network);

export const titleOf =(group: HostGroup) => `Rete per ${group.tool}`;
