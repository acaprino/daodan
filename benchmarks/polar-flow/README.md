# Benchmark: un conteggio letto a un'altra granularità, in un servizio

Caso per le spec [fase 2](../../docs/specs/2026-11-09-flow-model.md) e [fase 3](../../docs/specs/2026-11-09-flows-in-review.md): un servizio senza interfaccia, [polarsource/polar](https://github.com/polarsource/polar), con un difetto reale già corretto. Una concessione di beneficio è registrata per membro; la revoca la conta per cliente. Il codice di polar non è copiato qui; le run e i loro artefatti restano fuori dal repository.

## Parametri

| Parametro | Valore |
|---|---|
| target | `server/` di polarsource/polar al commit `ee8e1c01492eeeb6bd773d35a51a01ed53e613dc`, il genitore della fix, copiato senza storia successiva; 1134 file Python in `server/polar/`, esclusi test e migrazioni |
| fix | [PR 16556](https://github.com/polarsource/polar/pull/16556), commit `1fdf26e65f6a1d2d683a0a99bf815e645c869024`, unita il 2026-11-10 |
| difetti attesi | P1 `server/polar/benefit/grant/service.py:292`: `revoke_benefit` conta le concessioni attive con `list_granted_by_benefit_and_customer` (`server/polar/benefit/grant/repository.py:186`), che filtra per beneficio e cliente; la concessione è per membro (`member_id`, `server/polar/models/benefit_grant.py:131`). Se altri membri dello stesso cliente hanno ancora la concessione, `len(other_grants) < 2` è falso e il beneficio reale del membro revocato resta. P2, secondario, `server/polar/benefit/grant/scope.py:122` e `server/polar/benefit/grant/service.py:360`: il membro è cercato senza `include_deleted`, quindi la revoca non trova un membro già eliminato |
| criterio | P1 trovato se una segnalazione nel rapporto finale afferma, con `file:line`, che la revoca decide su un conteggio per cliente mentre la concessione è per membro; P2 trovato se afferma che la revoca non trova un membro eliminato. Parziale se compare solo in un incarico |
| richiesta | «la logica dei benefici in `server/polar/benefit/`» |
| perimetro | `server/polar/benefit/`: 56 file Python, 224.659 byte |
| contesto | `server/polar/models/benefit_grant.py`, `server/polar/models/member.py`, `server/polar/member/repository.py` |
| mappa | `server/` con i collegamenti `chiama` per Python |
| esecuzione | copia in una directory fuori da questo repository, senza accesso web; i revisori non vedono questo README |

## Limite del caso

Chi conta e chi interroga stanno nella stessa cartella: i gruppi per percorso del file li tengono già insieme. Il caso mette alla prova il flusso dato in più (prova C) più che le unità (prova B).

## Risultati

Nessuna run eseguita.
