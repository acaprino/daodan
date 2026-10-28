<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# Further Reading

Curated reading list on the abstraction-vs-duplication question. Grouped by category; URLs marked `(snippet-only)` were found via search but not opened end-to-end during research and should be verified before citing.

## The single must-read first

- **Sandi Metz, "The Wrong Abstraction" (2016)** — https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction. Four paragraphs. The load-bearing essay of the whole modern debate. *"Duplication is far cheaper than the wrong abstraction."*

- **Sandi Metz, "All the Little Things" (RailsConf 2014)** — https://www.youtube.com/watch?v=8bZh5LMaSmE. Where the line above was first spoken. The blog post is the executive summary; the talk is the long form.

## Canonical principles

- **Kent C. Dodds, "AHA Programming"** — https://kentcdodds.com/blog/aha-programming. *Avoid Hasty Abstractions* — the operational rule of thumb for the Rule of Three in modern frontend.

- **Carson Gross, "Locality of Behaviour" (2020)** — https://htmx.org/essays/locality-of-behaviour/. The cognitive counter-force to DRY.

- **Dan North, "CUPID for joyful coding" (2022)** — https://dannorth.net/blog/cupid-for-joyful-coding/. The SOLID critique and the properties-vs-principles framing.

- **Martin Fowler, "Bounded Context"** — https://www.martinfowler.com/bliki/BoundedContext.html. The seam for *what NOT to unify*.

- **Refactoring.guru, "Speculative Generality"** — https://refactoring.guru/smells/speculative-generality. Short canonical reference to the code smell.

- **Eoin Noble, "Origins of the Rule of Three"** — https://eoinnoble.com/posts/origins-of-the-rule-of-three/. Traces the lineage to Roberts & Johnson, "Evolving Frameworks" (1996).

- **Kent Beck on preparatory refactoring** — https://martinfowler.com/articles/preparatory-refactoring-example.html (Fowler) and the original tweet https://twitter.com/KentBeck/status/250733358307500032 ("first make the change easy, then make the easy change").

## Practitioner war stories

- **Dan Abramov, "Goodbye, Clean Code"** — https://overreacted.io/goodbye-clean-code/. The most-shared personal anecdote of a clean abstraction that was reverted the next day.

- **Hacker News, 2016 thread on Metz** — https://news.ycombinator.com/item?id=12061453. The HN consensus comment: *"I'm willing to duplicate code if it makes the code less complex."* Also the 2020 revisit: https://news.ycombinator.com/item?id=23739596.

- **Jason Swett, "Why I don't buy 'duplication is cheaper than the wrong abstraction'"** — https://www.codewithjason.com/duplication-cheaper-wrong-abstraction/. The most-cited respectful dissent. Read after Metz to test your position.

- **Matt Rickard, "DRY Considered Harmful"** — https://mattrickard.com/dry-considered-harmful. Microservices-flavored take.

- **DEV, "A Case Against Abstraction"** — https://dev.to/puritanic/a-case-against-abstraction-118o. Practitioner overview with code examples.

- **DEV, "The 'Shared' Library is a Lie: Fixing Your Nx Monorepo Architecture"** — https://dev.to/abdelaaziz_ouakala/the-shared-library-is-a-lie-fixing-your-nx-monorepo-architecture-3mie. Modern monorepo war story.

## Recent (2023-2026) framings

- **Kent Beck, *Tidy First?* substack** — https://tidyfirst.substack.com/. The financial-options framing of abstraction cost. Companion to the book.

- **Henrik Warne, *Tidy First?* review** — https://henrikwarne.com/2024/01/10/tidy-first/.

- **Dan Lebrero, *Tidy First?* book notes** — https://danlebrero.com/2024/08/07/tidy-first-summary/.

- **Frontend at Scale, "Too General Too Soon" (2024)** — https://frontendatscale.com/issues/15/. Frontend-flavored speculative-generality cases.

- **Code With Seb, "WET vs AHA: Avoiding Premature Abstraction in Frontend Development" (April 2025)** — https://www.codewithseb.com/blog/wet-vs-aha-avoiding-premature-abstraction-in-frontend-development.

- **Java Code Geeks, "The Dark Side of Clean Code" (May 2026)** *(snippet-only)* — https://www.javacodegeeks.com/2026/05/the-dark-side-of-clean-code-when-solid-and-dry-principles-actively-hurt-you.html.

- **Piotr Sikora, "DRY, WET, AHA: Finding the Right Balance" (January 2026)** *(snippet-only)* — https://www.piotr-sikora.com/blog/2026-01-28-dry-wet-aha.

## Counter-current from game and performance communities

- **Mike Acton, "Data-Oriented Design and C++" (CppCon 2014)** — https://www.youtube.com/watch?v=rX0ItVEVjHc. The strongest non-overlapping critique of OOP-style abstraction.

- **Marcell Juhasz, "Cost of C++ Abstractions in Embedded Systems" (CppCon 2024)** — https://isocpp.org/blog/2025/06/cppcon-2024-cost-of-cpp-abstractions-in-c-embedded-systems-marcell-juhasz. Current numbers complementing Acton.

## Italian-language resources (DDD-flavored)

- **Avanscoperta, "Domain-Driven Design: una questione tecnica?" (2023)** — https://blog.avanscoperta.it/2023/01/03/domain-driven-design-una-questione-tecnica/.
- **Avanscoperta, "DDD Open Space: Bounded Context" (2021)** — https://blog.avanscoperta.it/2021/06/17/ddd-open-space-bounded-context/.
- **Avanscoperta, "Microservices e Domain-Driven Design" (2024)** — https://blog.avanscoperta.it/2024/03/19/microservices-e-domain-driven-design/.
- **MokaByte, "DDD, microservizi e architetture evolutive" (2024)** — https://mokabyte.it/2024/01/11/architettureevolutive-3/.
- **Intre.it, "DDD, microservizi: strategic patterns" (May 2025)** — https://www.intre.it/2025/05/21/ddd-microservizi-strategic-patterns/.
- **Wikipedia IT, "Regola del tre (programmazione)"** — https://it.wikipedia.org/wiki/Regola_del_tre_(programmazione).

## Books

- **Sandi Metz, Katrina Owen, TJ Stankus, *99 Bottles of OOP* (2nd ed.)** — https://sandimetz.com/99bottles. Book-length expansion with the "Shameless Green" pattern.
- **Kent Beck, *Tidy First?* (2024)** — ~100 pages. The options framing of abstraction cost.
- **Eric Evans, *Domain-Driven Design* (Blue Book, 2003)** — strategic chapters for what NOT to unify.
- **Vaughn Vernon, *Implementing Domain-Driven Design* (2013)** — operational counterpart with concrete bounded-context examples.
- **Martin Fowler, *Refactoring* (2nd ed., 2018)** — Rule of Three, *Speculative Generality*, *Inline Method*, *Inline Class*.

## Conference talks

- **Sandi Metz, "All the Little Things" — RailsConf 2014** — https://www.youtube.com/watch?v=8bZh5LMaSmE.
- **Mike Acton, "Data-Oriented Design and C++" — CppCon 2014** — https://www.youtube.com/watch?v=rX0ItVEVjHc.
- **Kent Beck, "Tidy First?" — InfoQ** — https://www.infoq.com/presentations/refactoring-cleaning-code/ and https://www.youtube.com/watch?v=XmsyvStDuqI.
- **Kent C. Dodds, "AHA Programming" — GitNation** — https://gitnation.com/contents/aha-programming.
- **Eric Evans on Bounded Contexts — DDD Europe 2019 (InfoQ)** — https://www.infoq.com/news/2019/06/bounded-context-eric-evans/.

## Minimum reading path (~3 hours)

1. Metz, "The Wrong Abstraction" (4 paragraphs)
2. Metz, "All the Little Things" — RailsConf 2014 (~30 min)
3. Abramov, "Goodbye, Clean Code" (~10 min)
4. Gross, "Locality of Behaviour" (~5 min)
5. Beck, *Tidy First?* (book or substack, ~2 hours)
6. Swett, "Why I don't buy..." (~10 min, to test the position)
