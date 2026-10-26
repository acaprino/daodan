---
name: xtermjs-skill
description: >
  Build, configure, debug and extend browser and Electron terminal UIs with xterm.js (@xterm/xterm).
  TRIGGER WHEN: working with xterm.js, @xterm/xterm, FitAddon, WebglAddon, SearchAddon, AttachAddon, node-pty over WebSocket, ANSI/VT sequences, or embedding a web terminal in React/Vue/Electron.
---

# xterm.js Development Skill

xterm.js (`@xterm/xterm`) is a terminal emulator for the browser and Electron. It is not a shell: connect it to a backend process (such as `node-pty` over WebSocket) to execute commands.

## Reference router

| Task | Reference |
|---|---|
| Custom themes, key handlers, `SearchAddon`, markers/decorations, OSC/CSI parser hooks, high-throughput streaming, ConPTY quirks, WebGL sleep recovery, or coordinate translation | `references/advanced-api-and-resiliency.md` |

## 1. Installation

```bash
npm install @xterm/xterm
# Install only needed addons:
npm install @xterm/addon-fit @xterm/addon-attach @xterm/addon-web-links \
            @xterm/addon-search @xterm/addon-webgl @xterm/addon-clipboard \
            @xterm/addon-web-fonts @xterm/addon-unicode11
```

Always import the CSS (`import '@xterm/xterm/css/xterm.css';`).

## 2. Basic Setup

```ts
import { Terminal } from '@xterm/xterm';

const term = new Terminal({
  cols: 80,
  rows: 24,
  cursorBlink: true,
  scrollback: 5000,
  fontFamily: '"Cascadia Code", Menlo, monospace',
  fontSize: 14,
  theme: {
    background: '#1e1e1e',
    foreground: '#d4d4d4',
    cursor: '#d4d4d4',
  },
});

term.open(document.getElementById('terminal')!);
term.write('Hello from \x1B[1;32mxterm.js\x1B[0m\r\n$ ');
```

Call `term.open(element)` only after the element is mounted in the DOM with non-zero dimensions. Use `\r\n` for newlines when writing directly.

## 3. Official Addons

| Addon | Package | Purpose |
|---|---|---|
| FitAddon | `@xterm/addon-fit` | Resize terminal to fill its container |
| AttachAddon | `@xterm/addon-attach` | Connect to a WebSocket backend |
| SearchAddon | `@xterm/addon-search` | In-terminal text search |
| WebglAddon | `@xterm/addon-webgl` | GPU-accelerated WebGL2 renderer |
| WebLinksAddon | `@xterm/addon-web-links` | Clickable URLs |
| ClipboardAddon | `@xterm/addon-clipboard` | Browser clipboard integration |
| WebFontsAddon | `@xterm/addon-web-fonts` | Wait for web fonts before rendering |
| Unicode11Addon | `@xterm/addon-unicode11` | Unicode 11 character width support |

```ts
import { FitAddon } from '@xterm/addon-fit';
import { WebglAddon } from '@xterm/addon-webgl';
import { WebLinksAddon } from '@xterm/addon-web-links';

const fitAddon = new FitAddon();
term.loadAddon(fitAddon);
term.loadAddon(new WebLinksAddon());
term.open(document.getElementById('terminal')!);

try {
  const webgl = new WebglAddon();
  webgl.onContextLoss(() => webgl.dispose());
  term.loadAddon(webgl);
} catch {
  console.warn('WebGL2 unavailable, falling back to default renderer');
}

fitAddon.fit();
const ro = new ResizeObserver(() => fitAddon.fit());
ro.observe(document.getElementById('terminal')!);
```

## 4. Backend Integration: `node-pty` + WebSocket

### Frontend (`AttachAddon` or Manual Wiring)

```ts
import { AttachAddon } from '@xterm/addon-attach';

const socket = new WebSocket('ws://localhost:3000/ws');
term.loadAddon(new AttachAddon(socket));

term.onResize(({ cols, rows }) => {
  socket.send(JSON.stringify({ type: 'resize', cols, rows }));
});
```

For custom framing without `AttachAddon`, wire `ptyProcess.onData(d => term.write(d))`, `term.onData(d => ptyProcess.write(d))`, and `term.onBinary(d => ptyProcess.write(d))`.

### Backend (Node.js + `node-pty`)

```ts
import * as pty from 'node-pty';
import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 3000 });

wss.on('connection', (ws) => {
  const shell = process.platform === 'win32' ? 'powershell.exe' : 'bash';
  const ptyProcess = pty.spawn(shell, [], {
    name: 'xterm-color',
    cols: 80,
    rows: 24,
    env: process.env,
  });

  ptyProcess.onData((data) => ws.send(data));
  ws.on('message', (msg) => {
    const parsed = JSON.parse(msg.toString());
    if (parsed.type === 'resize') {
      ptyProcess.resize(parsed.cols, parsed.rows);
    } else {
      ptyProcess.write(msg.toString());
    }
  });
  ws.on('close', () => ptyProcess.kill());
});
```

## 5. React Integration Pattern

```tsx
import { useEffect, useRef } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';

export function XTerminal() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const term = new Terminal({ cursorBlink: true });
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(containerRef.current!);
    fitAddon.fit();

    const ro = new ResizeObserver(() => fitAddon.fit());
    ro.observe(containerRef.current!);

    return () => {
      ro.disconnect();
      term.dispose();
    };
  }, []);

  return <div ref={containerRef} style={{ width: '100%', height: '400px' }} />;
}
```

## 6. Common Pitfalls and Disposal

| Problem | Cause | Fix |
|---|---|---|
| Terminal renders blank / wrong size | `fit()` called before DOM paint or `display: none` | Call `fitAddon.fit()` after `open()`, use `ResizeObserver`, avoid `display: none` |
| Characters appear wrong width | Unicode width table | Load `Unicode11Addon`, set `term.unicode.activeVersion = '11'` |
| Backspace does not work | PTY termios mismatch | Send `\x7f` or `\x08`; check PTY settings |
| WebGL context lost after sleep/tab switch | GPU resource reclaim | Handle `onContextLoss`, DOM `webglcontextlost`, and health check (see `references/advanced-api-and-resiliency.md`) |
| `\n` without `\r` causes staircase | Missing carriage return | Use `\r\n` or set `convertEol: true` |

Always call `term.dispose()` (and `marker.dispose()` / `decoration.dispose()`) on teardown to prevent memory leaks.
