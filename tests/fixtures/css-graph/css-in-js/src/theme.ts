import { EditorView } from '@codemirror/view';
export const editorTheme = EditorView.theme({
  '&': { color: 'var(--ink)' },
  '.cm-content': { padding: '4px' },
  '&.cm-focused .cm-cursor': { borderLeftColor: 'red' },
});
export const base = EditorView.baseTheme({
  '&dark .cm-md-link': { color: 'blue' },
});
const fake = { theme: (x: object) => x };
export const notCm = fake.theme({ '.cm-ghost': { color: 'red' } });
