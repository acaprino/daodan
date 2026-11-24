import { Empty } from '@acaprino/sigrid';
import { ScreenPanel } from './frame.tsx';

// shortcut: nothing is drawn (it was on Imago, in `viewer/app/app.js` at 99665814e), until ticket 20 of the port draws it on Sigrid
export function PremapScreen() {
  return <ScreenPanel title="Pre-mappa" subtitle="Conosci il punto di partenza."><Empty fill title="Pre-mappa" description="Questa schermata è in preparazione." /></ScreenPanel>;
}
