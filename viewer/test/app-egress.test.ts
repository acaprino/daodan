import { test } from 'node:test';
import assert from 'node:assert/strict';
import { groupKey, hostsOf, pendingGroup, putAside, reachesNetwork, REPLIES, repliedWords, replyBody, requestFacts, titleOf } from '../app/egress.ts';
import type { HostGroup, HostRequest } from '../app/server.ts';

const request = (host: string, more: Partial<HostRequest> = {}): HostRequest =>
  ({ host, port: 443, address: '93.184.216.34', network: false, declared_in: [], ...more });
const gradle: HostGroup = { tool: 'gradle', project: '/p', requests: [request('repo.example.com', { declared_in: ['build.gradle'] }), request('repo.example.com', { port: 8443 })] };
const npm: HostGroup = { tool: 'npm', project: '/p', requests: [request('npm.local', { address: '10.0.0.4', network: true })] };

test('the window asks about the first group not put aside; a group that changes is asked about again', () => {
  assert.equal(pendingGroup(undefined, []), null);
  assert.equal(pendingGroup([{ ...gradle, requests: [] }], []), null);
  assert.equal(pendingGroup([gradle, npm], []), gradle);
  assert.equal(pendingGroup([gradle, npm], [groupKey(gradle)]), npm);
  assert.equal(pendingGroup([gradle, npm], [groupKey(gradle), groupKey(npm)]), null);
  assert.deepEqual([putAside([gradle, npm], []), putAside([gradle, npm], [groupKey(npm)]), putAside(undefined, [groupKey(npm)])], [false, true, false]);
  const grown = { ...npm, requests: [...npm.requests, request('other.example.com')] };
  assert.equal(pendingGroup([grown], [groupKey(npm)]), grown);
});

test('an answer is for every host of the group, each once, and says what was answered', () => {
  assert.deepEqual(hostsOf(gradle), ['repo.example.com']);
  assert.deepEqual(replyBody(npm, 'block'), { hosts: ['npm.local'], reply: 'block' });
  assert.deepEqual(REPLIES.map(item => item.reply).sort(), ['always', 'block', 'no', 'once']);
  assert.equal(repliedWords('always', ['a.example', 'b.example']), 'Host approvati per questo progetto: a.example, b.example.');
  assert.equal(repliedWords('once', ['a.example']), 'Host approvati per questa analisi: a.example.');
});

test('a request says its port, its address and the files that declare it; the user network is marked', () => {
  assert.deepEqual(requestFacts(gradle.requests[0]), { port: '443', address: '93.184.216.34', declared: 'build.gradle' });
  assert.deepEqual(requestFacts(request('x.example', { address: null, port: 80 })), { port: '80', address: 'non risolto', declared: 'nessun file del progetto' });
  assert.deepEqual([reachesNetwork(gradle), reachesNetwork(npm)], [false, true]);
  assert.equal(titleOf(npm), 'Rete per npm');
});
