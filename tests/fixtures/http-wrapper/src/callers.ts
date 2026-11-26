import { Api, arrow, generic, plain, remote, second, viaWindow } from './client';

declare function computed(): string;

export async function useAll(api: Api) {
  await plain('/api/orders', { id: 1 });
  await plain(`/api/orders/${1}`, {});
  await plain('https://pay.example.com/charge', {});
  await plain(computed(), {});
  await generic('/api/users', (raw) => raw);
  await arrow('/api/ping');
  await api.remove('/api/items/1');
  await second('x', '/api/second');
  await viaWindow('/api/window');
  await remote('https://api.example.com/v1/rates');
  await remote('https://api.example.com/v1/rates?x=1');
}
