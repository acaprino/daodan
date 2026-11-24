import { Empty } from '@acaprino/sigrid';
import { ScreenPanel } from './frame.tsx';

// shortcut: nothing is drawn (it was on Imago, in `viewer/app/app.js` at 99665814e), until ticket 23 of the port draws it on Sigrid
export function EngineScreen() {
  return <ScreenPanel title="Motore e domande" subtitle="Chiedi al codice."><Empty fill title="Motore e domande" description="Questa schermata è in preparazione." /></ScreenPanel>;
}
