// The map of the run, on its own page: the one link to it, in the window's action bar. A browser opens it in a tab; in a window of its
// own there are no tabs, and the map has the way back.
import { useWindow } from '@acaprino/imago';
import { Button, Icon } from '@acaprino/sigrid/primitives';
import { model } from './use-model.ts';

export function ExplorerLink() {
  const { own } = useWindow();
  return <Button variant="outline" asChild>{own
    ? <a href={model.explorerUrl()}><Icon name="graph" />Apri l’esploratore</a>
    : <a href={model.explorerUrl()} target="_blank" rel="noopener"><Icon name="external" />Apri l’esploratore</a>}</Button>;
}
