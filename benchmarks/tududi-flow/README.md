# Benchmark: uno stato letto da un altro campo, fra interfaccia e servizio

Caso per le spec [fase 2](../../docs/specs/2026-11-09-flow-model.md) e [fase 3](../../docs/specs/2026-11-09-flows-in-review.md): un'app con frontend e backend nello stesso repository, [chrisvel/tududi](https://github.com/chrisvel/tududi), con un difetto reale già corretto. Lo stato di un'attività ha sette valori; il calendario lo mostra ricavandolo dalla sola data di completamento e chiede le attività senza indicare lo stato. Il codice di tududi non è copiato qui; le run e i loro artefatti restano fuori dal repository.

## Parametri

| Parametro | Valore |
|---|---|
| target | chrisvel/tududi al commit `71da9d7b34dfd1600657e9c5ddf40420206fd263`, il genitore della fix, copiato senza storia successiva; 531 file in `backend/` e 483 in `frontend/`, JavaScript e TypeScript, esclusi test, migrazioni e traduzioni |
| fix | [PR 2068](https://github.com/chrisvel/tududi/pull/2068), commit `fc630cd4491b309dbe82c5c9782f7a594dda78c9`, unita il 2026-11-05; issue [2067](https://github.com/chrisvel/tududi/issues/2067) |
| difetti attesi | T1 `frontend/components/Calendar.tsx:671`: il popup mostra «Completed» o «Pending» secondo `task.completed_at`; lo stato vero ha sette valori (`Task.STATUS`, `backend/models/task.js:405`), quindi un'attività annullata senza data di completamento appare «Pending». T2 `frontend/components/Calendar.tsx:199` chiede `tasks?type=calendar` senza stato e `backend/modules/tasks/queries/query-builders.js:307` in quel caso esclude solo le attività finite: annullate e archiviate restano nel calendario |
| criterio | T1 trovato se una segnalazione nel rapporto finale afferma, con `file:line`, che l'etichetta del popup è ricavata da `completed_at` e non dallo stato; T2 trovato se afferma che il calendario riceve attività annullate o archiviate. Parziale se compare solo in un incarico |
| richiesta | «la logica del calendario e del modulo delle attività» |
| perimetro | `frontend/components/Calendar.tsx`, `frontend/components/Calendar/` e `backend/modules/tasks/`: 41 file, 350.861 byte |
| contesto | `backend/models/task.js`, `frontend/constants/taskStatus.ts` |
| mappa | `backend/` e `frontend/` con i collegamenti `chiama` per JavaScript e TypeScript |
| fase 2, caso fra strati | dall'etichetta di stato del popup il flusso arriva al modello `Task` (`backend/models/task.js`) passando per `GET /tasks` (`backend/modules/tasks/routes.js:180`) |
| esecuzione | copia in una directory fuori da questo repository, senza accesso web; i revisori non vedono questo README |

## Limite del caso

Il difetto riguarda il significato di uno stato, non la granularità. Il backend è JavaScript senza tipi: i collegamenti `chiama` risolti vanno contati prima delle run.

## Risultati

Nessuna run eseguita.
