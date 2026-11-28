# Le classi d'attacco di security-audit nei ruoli di senior-review

28 novembre 2026. Fonte: [`cloudflare/security-audit-skill`](https://github.com/cloudflare/security-audit-skill), licenza MIT, commit `c1c8a8c` del 14 settembre 2026. I ruoli sono scritti nella forma dei ruoli di Daodan; dalla skill vengono le classi, non il testo.

## Che cosa è entrato

Solo le classi d'attacco senza un ruolo che le possedesse. Il metodo della skill (fasi, registro di copertura, verificatore indipendente, `needs_validation`, validatori) non è entrato: senior-review ha già job isolati, lenti, `coverage.json` con il critico e le lacune.

| File della skill | Chi lo possiede in Daodan | Stato |
|---|---|---|
| `ATTACK-CLASSES.md` | `input-validation`, `authorization`, `untrusted-resource`, `secret-exposure`, `logic-integrity`, `transaction-integrity` | già coperto; in `authorization` un controllo in più: lettori derivati e oracoli, chiavi composte, chiavi API |
| `WEB-PROTOCOL-AND-AUTH.md`, framing e cache | `http-framing-auditor` | ruolo nuovo |
| `WEB-PROTOCOL-AND-AUTH.md`, identità federata, MFA, passkey, collegamento e recupero | `identity-transition-auditor` | ruolo nuovo |
| `WEB-PROTOCOL-AND-AUTH.md`, sessioni, JWT, mTLS, CSRF, cookie | `session-delegation`, `browser-security` | già coperto |
| `CLIENT-SIDE.md` | `client-context-auditor`; XSS del DOM, CORS e clickjacking restano a `browser-security` | ruolo nuovo |
| `AI-AND-LLM.md` | `ai-boundary` | un controllo in più: identità dei server MCP, dispatcher, deleghe, cicli |
| `SUPPLY-CHAIN-AND-RELEASE.md` | `build-release-auditor`; origine dei pacchetti resta a `dependency-provenance` | ruolo nuovo |
| `CLOUD-AND-DEPLOYMENT.md` | `deployment-boundary-auditor` | ruolo nuovo |
| `PROTOCOLS-RPC-AND-MESSAGING.md` | `message-authority-auditor`; consegna, ordine e duplicati restano a `message-delivery` e `remote-effect`, enum e default a `api-contract` | ruolo nuovo |
| `RESOURCE-EXHAUSTION-AND-AVAILABILITY.md` | `capacity-quota`, `input-validation`, `algorithmic-cost`, `service-resilience`, `resource-lifecycle` | già coperto; in `capacity-quota` un controllo in più: lavoro prima dell'autenticazione e dopo l'annullamento |
| `DATA-ISOLATION-AND-LIFECYCLE.md` | `authorization`, `cache-consistency`, `data-retention`, `recovery` | già coperto, con il controllo aggiunto in `authorization` |
| `DESKTOP-MOBILE-AND-LOCAL-IPC.md` | `local-ipc-auditor`; Tauri resta ai ruoli `tauri-*` | ruolo nuovo |
| `MEMORY-SAFETY-AND-BINARY.md` | `memory-safety-auditor`, con `defect-taxonomy/references/memory-resources.md` | ruolo nuovo |

## Scelte aperte

- **Gli otto ruoli nuovi stanno nel catalogo da soli, fuori da `security-auditor`.** Un membro di `security-auditor` entra nel corpo di ogni job di `code-auditor`: otto ruoli sono circa 4.100 parole in più a ogni review. Così li sceglie il coordinatore della review di branch leggendo i mandati; i roster automatici (leggera, `quick`, `standard`, `deep`) non li includono. Nessun segnale di `review_roster.py` li attiva.
- **Non entrati:** gli agenti «wildcard» e «cose ovvie», i gradi di severità della skill, il riporto dei finding fra una run e la successiva.

## Prova

Nessuna misura: i ruoli nuovi e i tre controlli aggiunti non hanno un benchmark con semi ed esche, come lo ha `prior-art-auditor` in [`benchmarks/prior-art`](../../benchmarks/prior-art/README.md). `tests/test_senior_review_composition.py` prova solo che il catalogo li elenca e che i file esistono.
