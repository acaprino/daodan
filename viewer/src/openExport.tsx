// «Apri altro export»: a map kept in a file takes the place of the one shown. A file that holds none says why, and the map stays.
import { useState } from 'react';
import { Dialog, FileDrop } from '@acaprino/sigrid';
import type { FileDropReason } from '@acaprino/sigrid';

const REFUSED: Record<FileDropReason, string> = {
  type: 'Serve un file JSON.', size: 'Il file è troppo grande.', count: 'Scegli un solo file.',
};
// The dialog opens on the zone: before it, in the page, is only the picker's own input, which the keyboard does not reach.
const takeFocus = (button: HTMLButtonElement | null) => button?.focus();

function ExportDrop({ onFile }: { onFile: (file: File) => Promise<void> }) {
  const [reading, setReading] = useState('');
  const [error, setError] = useState('');
  const read = async (file: File) => {
    setReading(file.name);
    setError('');
    try { await onFile(file); }
    catch (reason) { setError(`${file.name} non è un export leggibile: ${String((reason as Error)?.message ?? reason)}`); }
    finally { setReading(''); }
  };
  return <FileDrop ref={takeFocus} label="Trascina qui un export, o scegli il file" hint="JSON" dropLabel="Lascialo qui"
    accept={{ 'application/json': ['.json'] }} busy={reading ? `Leggo ${reading}…` : null} error={error}
    onFiles={([file]) => { read(file); }} onRefuse={([refused]) => setError(REFUSED[refused.reason])} />;
}

type OpenExportProps = {
  open: boolean; onOpenChange: (open: boolean) => void;
  onFile: (file: File) => Promise<void>;  // it fails with the reason, where the file holds no export
};

export function OpenExport({ open, onOpenChange, onFile }: OpenExportProps) {
  return <Dialog open={open} onOpenChange={onOpenChange} title="Apri altro export" description="La mappa del file prende il posto di quella mostrata.">
    <ExportDrop onFile={onFile} />
  </Dialog>;
}
