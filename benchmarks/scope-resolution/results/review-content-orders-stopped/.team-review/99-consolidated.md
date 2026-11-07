# Consolidated findings (pre-verification)

Seven of seven jobs delivered. Deduplication keeps distinct failure modes: job-02-F3 spans F03 (before the ledger write) and F04 (after it). Severity conflicts take the higher rating; confidence takes the highest member. Each finding's full text is in `verification/findings/<id>.md`.

| ID | Severity | Conf. | Location | Finding | Sources | Lens 0 |
|---|---|---|---|---|---|---|
| F01 | High | 97 | `pricing.py:19` | Customer discount is subtracted twice | job-01-F1 (High), job-02-F1 (High) | no |
| F02 | High | 95 | `service.py:25` | Checkout ignores a failed stock reservation | job-01-F2 (High), job-02-F2 (High), job-05-F1 (High) | yes |
| F03 | High | 92 | `service.py:25` | A granted reservation is never released when a later step fails before the ledger write | job-01-F4 (Medium), job-02-F3 (High, part), job-04-F2 (Medium), job-05-F2 (High) | yes |
| F04 | High | 90 | `service.py:29` | A notification failure after the ledger write reports a failed checkout; a retry books it twice | job-01-F3 (High), job-02-F3 (High, part), job-05-F3 (High) | yes |
| F05 | High | 90 | `ledger.py:30` | The refund row has no amount and no VAT portion | job-01-F5 (Medium), job-02-F4 (High), job-06-F1 (High) | yes |
| F06 | High | 88 | `ledger.py:10` | Lockfile contention fails the writer instead of serializing it | job-03-F1 (High), job-05-F5 (Medium) | yes |
| F07 | High | 90 | `ledger.py:15` | A holder that dies leaves ledger.lock behind and every later ledger write fails | job-03-F2 (High), job-04-F1 (Medium), job-05-F6 (Medium) | yes |
| F08 | Medium | 85 | `service.py:27` | The validation pipeline runs after its subject is consumed, and its result is discarded | job-01-F6 (Medium), job-02-F5 (Medium), job-07-F5 (Medium) | yes |
| F09 | Medium | 85 | `inventory.py:21` | A non-positive or NaN quantity passes the stock guard and inverts or poisons stock | job-01-F8 (Medium), job-07-F4 (Medium) | yes |
| F10 | Medium | 85 | `ledger.py:18` | The order id is written unescaped into a tab and newline delimited row | job-06-F4 (Medium), job-07-F1 (Medium) | yes |
| F11 | Medium | 80 | `pricing.py:14` | `net * loyalty` becomes sequence repetition on mistyped input, allocating before rejection | job-07-F3 (Medium) | yes |
| F12 | Medium | 75 | `ledger.py:5` | The ledger's location depends on the process working directory | job-05-F7 (Medium) | no |
| F13 | Medium | 85 | `ledger.py:18` | A missing or null order id is stored as an ordinary id | job-05-F9 (Low), job-06-F3 (Medium) | no |
| F14 | Medium | 70 | `pricing.py:14` | Price and discount from the payload reach the ledger without type or range check | job-06-F2 (Medium), job-07-F2 (Medium) | yes |
| F15 | Medium | 62 | `ledger.py:25` | A refund is appended without checking that its sale exists or was not already reversed | job-05-F4 (Medium) | yes |
| F16 | Medium | 60 | `service.py:29` | The receipt handler receives neither the total nor the VAT | job-01-F7 (Low), job-02-F6 (Medium) | yes |
| F17 | Medium | 55 | `inventory.py:7` | Stock lives in one process while the ledger outlives it | job-05-F8 (Medium) | yes |
| F18 | Low | 80 | `pricing.py:19` | The same net can yield VAT and total one cent apart | job-06-F5 (Low) | no |
| F19 | Low | 80 | `service.py:29` | `channel` documented as configuration is read from the order, and an unknown value fails only after the ledger write | job-07-F6 (Low) | yes |
| F20 | Low | 80 | `big_module.py:16` | Audit formatters render booleans and integer identifiers as money | job-01-F9 (Low), job-06-F7 (Low) | yes |
| F21 | Low | 70 | `inventory.py:14` | `_LOCKS` keeps one entry per sku value forever, even for skus refused | job-04-F3 (Low) | yes |
| F22 | Low | 65 | `api.py:26` | Dispatcher ignores its own service; routing follows the last registration | job-01-F10 (Low), job-02-F7 (Low) | yes |
| F23 | Low | 55 | `ledger.py:18` | A sale row has no VAT breakdown and no rate | job-06-F6 (Low) | yes |

Corroborated (independent agreement): F01, F02, F03, F04, F05, F06, F07, F08, F09, F10, F13, F14, F16, F22. F20 has one independent member and one mixed, so it is not corroborated. Echoes: none declared; all members read the same `01-context.md`, which states no defect.

`[MAP-GAP]` findings, rules `01-context.md` did not anchor: job-02-F2 (F02), job-02-F3 (F03, F04), job-02-F5 (F08), job-02-F6 (F16), job-02-F7 (F22).
