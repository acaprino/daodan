# README layout techniques

Choose only sections that serve the planned readers and project. Preserve the
author's intentional voice. Structure is a reader decision, not a line quota or
adoption-funnel requirement.

## Entry and purpose

Name the project, explain the concrete problem and who uses it. A plain text
introduction is sufficient. Use an existing logo or screenshot only if it helps
show verified behavior; do not create placeholder visuals. Dark/light `<picture>`
variants are useful when existing assets need them.

Link to relevant project documentation rather than duplicate a long reference.
Clarify scope and limitations before making unsupported claims of maturity,
speed, compatibility or popularity.

## Getting started

Use the project's actual installation and distribution mechanism. A CLI, library,
private application and source-only tool need different instructions. Preserve
prerequisites, environment setup, expected outcomes and safety-relevant steps.
Do not shorten a real setup to satisfy an invented time limit.

Provide complete commands that follow the configured scripts and package manager.
Say when the commands have not been exercised. Code blocks contain usable input,
without shell prompt prefixes or ellipses that hide required steps.

## Features and reference

Explain user-visible capabilities with examples, and use tables for command/API
mappings or comparisons. Put advanced configuration in linked documents or
collapsible sections when the project's renderer and readers support them.
Preserve useful detail rather than impose a fixed README length.

Architecture diagrams are optional. When useful, use actual modules and flows,
with source evidence and the repository's supported diagram format. A diagram
does not imply runtime coverage.

## Metadata and community

License, author, package name and repository links come from verified project
metadata. Badges are optional; their URLs must name the real repository/package
and their metric must mean what the prose claims. Do not invent download counts,
test coverage, stars, endorsements or user quotations.

Link existing CONTRIBUTING, issue tracker, community or sponsor pages only when
relevant and supported by the supplied project information. Optional missing
assets or links can be omitted without another questionnaire.

## Delivery

For an existing README, apply accepted findings to the authorized scope. Full
restructure is a distinct scope from fact maintenance. Preserve content and
intentional voice, validate relative links and report unexercised examples or
external URLs. Operational status belongs in the owned run, not in README.
