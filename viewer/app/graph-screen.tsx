import { Empty } from '@acaprino/sigrid';
import { ScreenPanel } from './frame.tsx';

// shortcut: nothing is drawn (it was on Imago, in `viewer/app/app.js` at 99665814e), until ticket 22 of the port draws it on Sigrid
export function GraphScreen() {
  return <ScreenPanel title="Grafo del codice" subtitle="Esplora le relazioni."><Empty fill title="Grafo" description="Questa schermata è in preparazione." /></ScreenPanel>;
}
