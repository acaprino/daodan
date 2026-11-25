// Functions the rule's name `file::name` also reaches: the same name, another declaration.

export function post(url: string, body: unknown) {
  return fetch(url, { method: 'POST', body: JSON.stringify(body) });
}

export const queue = {
  post(topic: string, payload: string) {
    return topic + payload;
  },
};

export function useQueue() {
  queue.post('/api/orders', 'x');
}

export function send(url: string) {
  return fetch(url);
}

if (Math.random() > 0.5) {
  function send(token: string, url: string) {
    return fetch(url);
  }
  send('/api/y', '/api/x');
}

export function relay(a: string, url: string) {
  return fetch(url);
}

export namespace Admin {
  export function relay(url: string) {
    return fetch(url);
  }
}
