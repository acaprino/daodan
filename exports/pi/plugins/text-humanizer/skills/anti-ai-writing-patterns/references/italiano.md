<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

# Italian profile

Read this file whenever the text is Italian. It adds to `SKILL.md` and replaces nothing: the ground rules, the registers, the dash rule and the structural patterns hold unchanged. The English word lists (patterns 7 and 8) do not apply; the Italian lists below do.

## Un italiano credibile, non una traduzione

Valuta il passaggio per come suona in italiano, non per quante espressioni inglesi riesci a riconoscere. Le liste aiutano a trovare punti da rileggere: non sono parole vietate né istruzioni di sostituzione automatica.

- Mantieni la voce di chi scrive: grado di confidenza, cortesia, eventuale ironia e lessico abituale. Non aggiungere «beh», «diciamo», errori o confidenze per simulare spontaneità. Un testo formale può essere naturale senza diventare colloquiale.
- Alterna frasi brevi e periodi più distesi quando il ragionamento lo richiede. Non spezzare ogni subordinata, non eliminare tutti i connettivi e non rendere ogni frase soggetto-verbo-complemento. Gli elenchi restano utili nelle istruzioni e nei confronti.
- Conserva i termini del mestiere quando sono precisi e comprensibili per il destinatario: *ticket*, *deploy*, *backup*, *API*. Non tradurli per principio e non introdurre inglesismi dove basta una parola italiana. *Valido* in «token valido» e *robusto* in statistica non sono riempitivi.
- Rileggi il risultato come un testo intero. Se una sostituzione suona rigida, riscrivi la frase o il paragrafo attorno al punto da comunicare. Verifica poi che fatti, riserve, numeri e impegni siano rimasti gli stessi.

## Sintassi e coesione: un riferimento italiano

Angela Ferrari, in [*La semplicità sintattica in prospettiva testuale*](https://accademiadellacrusca.it/it/contenuti/la-semplicit-sintattica-in-prospettiva-testuale-riflessioni-a-partire-dalla-guida-alla-redazione-deg/9234) (Accademia della Crusca, 19 marzo 2021), mostra che normalizzare sempre l'ordine delle parole o mettere ogni subordinata dopo la principale può rendere un testo meno coerente. Anche il passivo e il soggetto sottinteso possono essere scelte appropriate: conta come si collegano informazioni note e nuove, non una forma sintattica obbligatoria.

Perciò non aggiungere un soggetto a ogni frase e non trasformare ogni passivo in attivo. «Abbiamo ricevuto la segnalazione. La verifichiamo domani» non richiede un secondo «noi». «Se il controllo fallisce, interrompere il deploy» mantiene la condizione davanti all'azione: spostarla non è di per sé una semplificazione. Sono esempi originali per l'uso operativo, non citazioni della fonte né indizi di testo generato.

## Typography to preserve

These are correct Italian. Never "fix" them.

- **Quotation marks.** Both “…” (virgolette alte) and «…» (caporali) are correct, and straight quotes are common in digital text. The Accademia della Crusca's editorial norms put short quotations in “…”, nest them as « “…” », and use ‘…’ for meanings. Keep the document's convention. Nesting is not mixing: make marks consistent only when one document switches convention for the same use.
- **Punctuation and quotes.** The full stop goes after the closing mark; a question or exclamation mark that belongs to the quotation stays inside it (Crusca).
- **Accents.** *È*, never *E'*; the acute accent on *perché*, *poiché*, *affinché*, *né*; the grave on *è*, *cioè*, *caffè*.
- **Spacing.** No space before : ; ! ? (the French rule does not apply).
- **Dialogue** in fiction may open with a dash or with caporali. Leave it as it is.

## Lexical tells

Density is the signal, as in English: one occurrence means nothing, a cluster in a short passage means a lot.

- **Emphasis verbs:** *sottolineare*, *evidenziare*, overused by models in Italian as their equivalents are in most of the 34 languages studied (Juzek, 2026).
- **Importance and innovation:** *importanza*, *innovativo*, *mirato* (Juzek, 2026).
- **A raised register for plain predicates:** *riveste un ruolo fondamentale* where *è fondamentale* or a plain verb would do; *è cruciale che* (Antonelli, 2025).
- **Fashionable verbs and professional jargon:** *impattare* when a more precise *influire su*, *incidere su* or *riguardare* fits; *valido* meaning "correct" when *corretto* is more precise (Antonelli, 2025). These are contextual choices, not blanket bans; keep established technical meanings.
- **Antilingua:** *vi* in place of *ci* (*vi sono* for *ci sono*), *coloro che* for *chi*, abstractions such as *entità dinamiche in continua evoluzione* (Antonelli, 2025). Simplify needless distance, not legitimate formal or legal usage.
- **Closers:** a final paragraph opening with *In conclusione* that repeats what came before (Antonelli, 2025).

## The catalog in Italian

The structural patterns take these Italian forms. Their evidence is the English catalog's; these are the Italian surface forms.

- **Pattern 1:** *rappresenta un punto di svolta*, *testimonianza di*, *nel panorama di*, *in un mondo in cui*
- **Pattern 3:** a gerund tacked onto the sentence: *…, sottolineando l'importanza di…*, *…, contribuendo a…*, *…, evidenziando…*. Cut the rider, or give it a sentence of its own when it carries a fact.
- **Pattern 9:** symmetric *non X, ma Y* and *non solo X, ma anche Y*, repeated. Model-written Italian fiction is full of them (Antonelli, 2025). Keep a real correction: «Non è un errore di password: l'account è bloccato» carries two useful facts.
- **Pattern 14:** key terms in bold in running prose (Antonelli, 2025).
- **Pattern 16:** Title Case in headings (*Strategie Di Crescita Per Il Mercato*). Italian headings capitalize only the first word and proper nouns, so this one is strong in Italian.
- **Pattern 17:** in social posts, about one emoji per line and a closing block of five or more hashtags, at least one in English (Antonelli, 2025).
- **Pattern 19:** *Certamente, ecco…*, *Ecco una riformulazione…*, *Spero che ti sia utile!*, *Fammi sapere se…*; and an opening that restates the question before answering it (Antonelli, 2025). Remove empty chatbot wrappers, not a real greeting, thanks, sign-off or request for a decision in an email.
- **Pattern 20:** *sulla base delle informazioni disponibili*, *al momento non sono disponibili dati precisi*
- **Pattern 22:** *è importante sottolineare che*, *vale la pena notare che*, *in questo articolo esploreremo*
- **Pattern 24:** «Ed è questo che fa la differenza», «Una distinzione fondamentale», «Il messaggio è chiaro» after a point the reader already understood. Keep a new consequence or a useful requested recap.
- **Pattern 25:** una risposta riparte da ciò che l'interlocutore ha appena scritto o approvato e arriva alla proposta solo in fondo. Con il contesto visibile, porta avanti la risposta e accorpa le ripetizioni. Non togliere motivazioni nuove, prove, comandi o dettagli richiesti; senza contesto non supporre che siano già noti.
- **Keyword loops:** a few key words recombined and repeated from the opening to the close (Antonelli, 2025). Vary or cut the repetitions that carry nothing.

## Calques from English

Fix these as poor Italian. They are weak evidence of a model: by mid-2025 interference from English had largely disappeared from model-written Italian (Antonelli, 2025), so they point to translation as often as to generation.

- A serial comma before *e*: *rosso, bianco, e verde* becomes *rosso, bianco e verde*.
- Prefer *avere senso* to *fare senso*, *svolgere un ruolo* to *giocare un ruolo*, and *rendersi conto* to *realizzare* in the sense of "to realize".

Queste indicazioni riguardano il significato nella frase: «mi fa senso» per esprimere disgusto e «realizzare un progetto» sono usi italiani corretti. Le regole inglesi sui composti prima o dopo il sostantivo non si trasferiscono all'italiano; conserva i trattini di termini tecnici, nomi e composti quando fanno parte della loro grafia.

## Not tells in Italian

- **Synonym variation** (pattern 11). Italian schools teach writers to avoid repeating a word, and the Wikipedia page cites exactly this. Leave it unless it confuses who is who.
- **Long periods** with subordinate clauses, in formal or academic register.
- **A single connective** such as *Inoltre*, *Tuttavia* or *Pertanto*. Only a run of them opening sentence after sentence is a tell.
- **Either quotation style**, as above.
- **Una formula di cortesia o una scelta espressiva appropriata:** «Buongiorno», «Grazie per la segnalazione», «Resto in attesa della conferma». Anche «dalla progettazione alla consegna» può indicare un ambito reale, senza pretendere una scala numerica. Non correggere questi usi solo per il pattern 12 o 19.

## Register

Keep the form of address the text uses: *tu*, *Lei* or *voi*. If it switches without reason, align to the dominant form and report it under Open points. In `docs`, keep the instruction style the text uses: imperative (*Esegui il comando*), infinitive (*Eseguire il comando*) or impersonal (*Si esegue il comando*). In `business`, keep the brand's *noi* and its form of address.

## Example

**Before:**
> In un mondo in cui la digitalizzazione riveste un ruolo fondamentale, la nostra piattaforma non è solo uno strumento, ma un vero e proprio partner strategico, sottolineando l'importanza dell'innovazione per le aziende. Inoltre, è cruciale che le imprese sappiano impattare positivamente sul mercato. In conclusione, il futuro è luminoso.

**After (business register):**
> La nostra piattaforma affianca le aziende nell'innovazione.

**Open points:**
- Che cosa fa la piattaforma, in concreto: il testo la chiama "partner strategico" senza dirlo.
- "Impattare positivamente sul mercato": quale effetto, e misurato come?

## Esempi nel contesto

Gli esempi illustrano scelte possibili, non formule da applicare a ogni testo.

### Risposta in un ticket (pattern 25)

**Contesto già visibile:** «Teniamo separata la correzione generale: questo ticket riguarda solo il cliente A».

**Prima:** «Come hai osservato, questo ticket riguarda solo il cliente A ed è opportuno tenere separata la correzione generale. Dalle verifiche in QA risultano sei record da correggere. Il servizio è condiviso. Propongo quindi di aprire un ticket separato per la correzione del servizio e dei sei record, mantenendo qui la soluzione temporanea per il cliente A».

**Dopo:** «Propongo di mantenere qui la soluzione temporanea per il cliente A e aprire un ticket separato per correggere il servizio condiviso e i sei record individuati in QA».

La proposta arriva subito; il servizio condiviso, QA e i sei record restano. In una nota autonoma, senza il messaggio precedente, il contesto sul perimetro può servire e va conservato.

### Email al cliente (registro business)

**Prima:** «Buongiorno, in riferimento alla Sua segnalazione, desideriamo informarLa che abbiamo provveduto a ripristinare l'accesso al portale. Le chiediamo cortesemente di effettuare una nuova prova e di comunicarci l'esito. Cordiali saluti».

**Dopo:** «Buongiorno, abbiamo ripristinato l'accesso al portale. Può riprovare e comunicarci l'esito? Cordiali saluti».

Restano il Lei, il saluto e la richiesta di verifica. Non aggiungere «il problema è risolto definitivamente»: il testo non lo garantisce.

### Istruzioni operative (registro docs)

**Prima:** «Al fine di procedere con il ripristino, è necessario effettuare un backup prima di riavviare il servizio. Successivamente, verificare i log».

**Dopo:** «Per il ripristino, eseguire un backup prima di riavviare il servizio. Poi verificare i log».

L'infinito resta coerente; il backup rimane obbligatorio e precede il riavvio. Un comando, un percorso o una citazione presenti nel testo resterebbero identici.

### Voce personale e falsi positivi

«Mi piace l'idea, però non sono ancora convinta. Vorrei provarla con il gruppo prima di decidere» può restare così. Non trasformare l'esitazione in entusiasmo o in un generico «procediamo».

Anche «Il token è valido, ma l'account non ha i permessi necessari» va bene così: *valido* è preciso e il contrasto distingue due condizioni reali.
