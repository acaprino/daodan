// What the page of the real window says, over the debugging port of WebView2: node smoke-page.mjs <port> <expression>
// The expression is evaluated in the page (a promise is waited for) and its value is printed as JSON.
const [port, expression] = process.argv.slice(2);
const until = async (seconds, what, found) => {
  let last;
  for (const end = Date.now() + seconds * 1000; Date.now() < end; await new Promise((done) => setTimeout(done, 200))) {
    try {
      const value = await found();
      if (value) return value;
    } catch (error) {
      last = error;
    }
  }
  throw new Error(`${what}: ${last ?? 'not there'}`);
};

const target = await until(20, 'the page', async () =>
  (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(({ type, url }) => type === 'page' && url.startsWith('http://127.0.0.1')));
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((open, failed) => {
  socket.onopen = open;
  socket.onerror = () => failed(new Error('the debugging port refused the connection'));
});
let last = 0;
const call = (method, params) => new Promise((done) => {
  const id = ++last;
  const heard = ({ data }) => {
    const message = JSON.parse(data);
    if (message.id !== id) return;
    socket.removeEventListener('message', heard);
    done(message);
  };
  socket.addEventListener('message', heard);
  socket.send(JSON.stringify({ id, method, params }));
});
const evaluate = async (text) => {
  const { result, error } = await call('Runtime.evaluate', { expression: text, awaitPromise: true, returnByValue: true, userGesture: true });
  if (error || result.exceptionDetails) throw new Error(JSON.stringify(error ?? result.exceptionDetails));
  return result.result.value;
};
await until(20, 'the page has loaded', () => evaluate("document.readyState === 'complete'"));
console.log(JSON.stringify((await evaluate(expression)) ?? null));
socket.close();
