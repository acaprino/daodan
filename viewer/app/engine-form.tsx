// The engine: which one, its endpoint and key where it has them, whether it answers; and the key's removal, confirmed first.
import { useRef, useState } from 'react';
import { Badge, Button, Cluster, Column, Dialog, FormField, Icon, Input, Note, Section, Select, Text } from '@acaprino/sigrid';
import type { NoteTone } from '@acaprino/sigrid';
import { engineOptions, hasKey, keyHelp, needsEndpoint, NO_ENGINE } from './engine.ts';
import type { Snapshot } from './snapshot.ts';
import { model, useModel } from './use-model.ts';

const TONE: Record<Snapshot['engineTone'], NoteTone> = { '': 'info', good: 'success', bad: 'error' };

export function EngineForm() {
  const s = useModel();
  const key = useRef<HTMLInputElement>(null);
  const [removal, setRemoval] = useState<'' | 'asked' | 'confirmed'>('');
  const engine = s.server?.engine, draft = s.engineDraft, endpoint = needsEndpoint(draft?.engine);
  const said = s.engineSaid, tone = TONE[s.engineTone];
  return <Section title="Motore" level={3} icon={<Icon name="ai" />} gap="lg" end={<Badge variant="secondary">{engine?.engine ?? 'Non scelto'}</Badge>}>
    <form noValidate onSubmit={event => { event.preventDefault(); model.saveEngine(); }}>
      <Column gap="md">
        <FormField label="Motore">
          <Select value={draft?.engine ?? NO_ENGINE} options={engineOptions(engine?.engines)}
            onValueChange={value => model.editEngine({ engine: value === NO_ENGINE ? null : value })} />
        </FormField>
        {endpoint && <>
          <FormField label="Indirizzo dell’endpoint">
            <Input type="url" value={draft?.base_url ?? ''} onChange={event => model.editEngine({ base_url: event.target.value })} />
          </FormField>
          <FormField label="Modello">
            <Input value={draft?.model ?? ''} onChange={event => model.editEngine({ model: event.target.value })} />
          </FormField>
          <FormField label="Chiave" help={keyHelp(engine)}>
            <Input ref={key} type="password" autoComplete="off" value={draft?.api_key ?? ''}
              onChange={event => model.editEngine({ api_key: event.target.value })} />
          </FormField>
        </>}
        <Cluster>
          <Button type="submit" variant="outline" loading={s.engineBusy.includes('save')}><Icon name="check" />Salva</Button>
          <Button variant="outline" loading={s.engineBusy.includes('probe')} onClick={() => { model.probeEngine(); }}>
            <Icon name="refresh" />Prova il motore
          </Button>
          {endpoint && hasKey(engine) && <Button variant="outline" loading={s.engineBusy.includes('forget')} onClick={() => setRemoval('asked')}>
            <Icon name="delete" />Rimuovi la chiave
          </Button>}
        </Cluster>
      </Column>
    </form>
    {engine?.unkept && <Note tone="warning" announce={false} title="Non conservato per il prossimo avvio."><Text data-selectable="">{engine.unkept}</Text></Note>}
    {/* An error is announced by its note; what went well, or is in course, by the status that holds it. */}
    {said && tone === 'error' && <Note tone="error" title={said} data-selectable="" />}
    <Column role="status">{said && tone !== 'error' && <Note tone={tone} title={said} data-selectable="" />}</Column>
    {/* Once confirmed, the button that opened it goes with the key: the focus goes to the field the key is written in. */}
    <Dialog open={removal === 'asked'} onOpenChange={open => { if (!open) setRemoval(''); }} restoreFocusTo={removal === 'confirmed' ? key : undefined}
      title="Rimuovere la chiave?"
      description="La chiave dell’endpoint viene tolta dal deposito delle credenziali del sistema e non si può recuperare: per usare di nuovo il motore dovrai inserirla un’altra volta."
      footer={<>
        <Button variant="ghost" autoFocus onClick={() => setRemoval('')}>Annulla</Button>
        <Button variant="destructive" onClick={() => { setRemoval('confirmed'); model.forgetKey(); }}>Rimuovi la chiave</Button>
      </>} />
  </Section>;
}
