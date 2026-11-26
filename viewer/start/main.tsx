// The page inside Daodan's window: what is there until the server answers, and when it has died. The program takes the window to the
// server's page as soon as there is one.
import { useEffect, useState } from 'react';
import type { ComponentProps } from 'react';
import { AppWindow, startApp, useNotify, useWindow } from '@acaprino/imago';
import type { AppView } from '@acaprino/imago';
import { Badge, Column, Text } from '@acaprino/sigrid/primitives';
import { Note } from '@acaprino/sigrid/components';
import { Panel } from '@acaprino/sigrid/layout';
import '@acaprino/sigrid/styles.css';
import { DAODAN } from '../src/page.ts';
import { Failed, Loading } from '../src/states.tsx';
import { follow, startAgain } from './program.ts';
import type { State, Told } from './program.ts';

const VIEWS: AppView[] = [{ id: 'start', label: 'Avvio', icon: 'play' }];
const WORD: Record<State, [word: string, tone: ComponentProps<typeof Badge>['tone']]> = {
  starting: ['In avvio', 'info'], restarting: ['Server fermato', 'warning'], failed: ['Non si avvia', 'danger'], stopped: ['Server fermato', 'danger'],
};

function Start() {
  const notify = useNotify(), window_ = useWindow();
  const [[state, cause], tell] = useState<Told>(['starting', '']);
  useEffect(() => {
    window_.setTitle(DAODAN.name);
    follow(tell).catch(unanswered);
  }, [notify, window_]);
  const unanswered = (error: unknown) => notify(String(error), { kind: 'error' });
  const retry = () => { startAgain().catch(unanswered); };
  const [word, tone] = WORD[state];
  return <AppWindow views={VIEWS} view="start" onView={() => {}} status={<Badge tone={tone}>{word}</Badge>}>
    <Panel title="Avvio">
      <Column pad="lg" gap="lg" width="page">
        {state === 'starting' && <>
          <Text as="p" variant="soft">Daodan si sta avviando.</Text>
          <Loading label="Avvio di Daodan" />
        </>}
        {state === 'restarting' && <>
          <Note tone="warning" title="Il server si è fermato: lo riavvio."><Text pre data-selectable="">{cause}</Text></Note>
          <Loading label="Riavvio del server" />
        </>}
        {state === 'failed' && <Failed title="Daodan non si avvia." cause={cause} retry={retry} />}
        {state === 'stopped' && <Failed title="Il server si è fermato quattro volte in un minuto." cause={cause} retry={retry} />}
      </Column>
    </Panel>
  </AppWindow>;
}

startApp(DAODAN, document.getElementById('app')!, <Start />);
