# Sessioni con il modello

Un subagente per caso, contesto isolato, solo `mapcli.py` sui tool reali. Le chiamate vengono dalla traccia del tool:
le query contano search, modules, outline, graph e impact; i file letti contano ogni file una volta.

| Giro | Testo | Fixture | Modelli | Conta? |
|---|---|---|---|---|
| m1, m2, m3 | versioni lunghe, poi 4 blocchi | con suggerimenti | modello ereditato, nome non registrato | no: testo superato |
| m4 | testo corto | con suggerimenti | Haiku, Opus | no: i commenti suggerivano le risposte |
| m5 | testo corto | pulita | Haiku, Opus, 9 casi | sì, per C3, C4, C5, C7 |
| m6 | testo corto + 2 correzioni | pulita | Haiku, Opus, 5 casi | sì, per C1, C2, C3b, C6, C8 |

Attesa, esito e chiamate per caso, sull'ultimo giro valido:

| Caso | Atteso | Haiku | query/file letti | Opus | query/file letti |
|---|---|---|---|---|---|
| C1 | resolved: pricing, service | ok | 6/2 | ok | 13/8 |
| C2 | resolved: api, gateway | **partial**, file giusti | 7/1 | ok | 9/2 |
| C3 | resolved: rates | ok | 4/1 | ok, più `__init__` vuoto | 8/3 |
| C3b | resolved: refunds | **partial**, 5 file | 6/5 | ok | 9/7 |
| C4 | clarify: pricing, rates | ok | 7/3 | ok | 4/2 |
| C5 | resolved: 4 file, reporting fuori | ok | 6/4 | ok | 9/8 |
| C6 | partial: service, notifications | ok | 7/2 | ok | 12/5 |
| C7 | resolved: big_module | ok | 3/1 | ok | 5/1 |
| C8 | resolved o partial: pricing, refunds | ok, partial, 6 file | 5/1 | ok, partial, 3 file | 7/11 |

Totali: esito Haiku 7/9, Opus 9/9; file indispensabili 9/9 per entrambi; file vietati inclusi 0; precision media Haiku
0.82, Opus 0.90; query medie Haiku 5.7, Opus 8.4 (massimo 13).

C1, prova della frase sui chiamanti: Opus senza frase ha escluso `service.py` in m4 e m5, con la frase lo include in m6.
Haiku lo include sempre. `partial`: la riformulazione non ha cambiato gli esiti di Haiku su C2 e C3b.
