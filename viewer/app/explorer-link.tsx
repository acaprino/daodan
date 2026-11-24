// The map of the run, on its own page: the one link to it, in the window's action bar.
import { Button, Icon } from '@acaprino/sigrid/primitives';
import { model } from './use-model.ts';

export function ExplorerLink() {
  return <Button variant="outline" asChild><a href={model.explorerUrl()} target="_blank" rel="noopener"><Icon name="external" />Apri l’esploratore</a></Button>;
}
