<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Posizionamento e differenziazione

## Unique Value Proposition (UVP)

La UVP racconta una storia in tre atti:
- **Setup** -- persona -> tipo di azienda -> caso d'uso
- **Conflitto** -- modo attuale di fare le cose -> problema specifico/frizione
- **Risoluzione** -- capacita' uniche -> valore differenziato -> prova

### 3 domande chiave (framework Kalungi)

Il messaging deve rispondere a:
1. **Perche' cambiare?** -- abbandono dello status quo
2. **Perche' noi?** -- differenziazione
3. **Perche' adesso?** -- urgenza

## Framework "Obviously Awesome" di April Dunford

Il processo di posizionamento piu' influente nel SaaS contemporaneo. 5 componenti in ordine deliberato:

1. **Alternative competitive** -- Cosa farebbero i clienti se non esistessi? (Spesso sono Excel o un intern, non il competitor che immagini)
2. **Attributi unici** -- Quali feature/capacita' hai SOLO tu?
3. **Valore differenziato** -- Quale valore producono quegli attributi unici?
4. **Clienti best-fit** -- Chi tiene DI PIU' a quel valore?
5. **Categoria di mercato** -- Quale contesto rende ovvio il tuo valore?

**Insight cruciale**: parti dai tuoi migliori clienti, non dal mercato. Fai una lista corta di chi ha capito subito, comprato subito e diventato un fan. Non creare una nuova categoria se non hai $200M+ di revenue -- non avrai le risorse per educare il mercato.

## Crossing the Chasm (Geoffrey Moore)

Il "baratro" tra early adopter (visionari) ed early majority (pragmatici) e' dove muoiono la maggior parte delle startup. Per attraversarlo:
- Scegli una **singola nicchia** (beachhead market)
- Offri un **prodotto completo** (non solo feature)
- Costruisci credibilita' con **success story**
- Sposta il messaging da "rivoluzionario" a "provato e affidabile"

## Blue Ocean Strategy -- Framework ERRC

| Azione | Esempio SaaS |
|--------|-------------|
| **Elimina** | Setup wizard complessi, feature enterprise per prodotto SMB |
| **Riduci** | Numero di feature, complessita' del pricing |
| **Aumenta** | Facilita' d'uso, velocita' di time-to-value, qualita' del supporto |
| **Crea** | Insight AI-powered, onboarding self-serve, feature community |

## Trovare la propria nicchia in un mercato affollato

Tre domande quando un mercato sembra saturo:
1. Il pain point principale e' **davvero** quello che tutti pensano?
2. E' affrontato nel **modo giusto**?
3. E' affrontato in modo **completo**?

Se la risposta a una qualsiasi e' "no", hai trovato uno spazio.

- Loomly: il **66% degli utenti** li sceglieva per la facilita' d'uso, non per le feature
- Jason Lemkin: *"quando le aziende SaaS superano i $100M ARR, smettono di focalizzarsi su SMB, freemium o segmenti ad alto churn -- potresti fare bene li'."*
- Veeva: partita come "CRM per il pharma" (nicchia ultra-specifica), cresciuta fino a $30B+

## Product-Market Fit (PMF)

### Sean Ellis Test (gold standard)

Chiedi: *"Come ti sentiresti se non potessi piu' usare [prodotto]?"*
Opzioni: molto deluso, un po' deluso, non deluso.

Se il **40%+ risponde "molto deluso"**, hai raggiunto il PMF.
- Minimo 30 risposte per insight direzionali, 100+ per alta confidenza
- Testa **trimestralmente** nel 2025-2026

### Superhuman PMF Engine (Rahul Vohra)

Processo sistematico per raggiungere il PMF. Superhuman partiva dal **22%** (sotto soglia del 40%). Attraverso 4 survey question e un processo iterativo hanno superato il **58%**.

Il segreto: roadmap bilanciata **50/50**:
- 50% raddoppiare su cio' che amano gli utenti top
- 50% rimuovere i blocchi per gli utenti allineati ma non ancora entusiasti

**Ignora** il feedback degli utenti "non delusi" -- non sono il tuo target.

### Metriche complementari di PMF

- Retention curve che si appiattiscono al 20-50% (non vanno a zero)
- Quick Ratio >4
- NPS >50
- Logo retention >85% annuale (SMB) o >95% (enterprise)
