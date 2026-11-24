import { Empty } from '@acaprino/sigrid';
import { ScreenPanel } from './frame.tsx';

// shortcut: nothing is drawn (it was on Imago, in `viewer/app/app.js` at 99665814e), until ticket 21 of the port draws it on Sigrid
export function SynthesisScreen() {
  return <ScreenPanel title="Sintesi" subtitle="Dalla mappa alla comprensione."><Empty fill title="Sintesi" description="Questa schermata è in preparazione." /></ScreenPanel>;
}
