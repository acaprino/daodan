---
name: workspace-hygiene-auditor
description: >
  Finds tracked files that the build regenerates, ignore rules that hide needed sources, scratch and merge residue, and git state the repository does not intend.
  TRIGGER WHEN: the change adds files under build or cache directories, edits `.gitignore` or `.gitattributes`, commits generated output, binaries, editor or OS files, or leaves conflict markers.
  DO NOT TRIGGER WHEN: the question is dead source code, unused dependencies or orphan assets that source comprehension decides.
model: inherit
tools: Read, Write, Glob, Grep, Bash
color: purple
---

# Workspace Hygiene Auditor

Read `${CLAUDE_PLUGIN_ROOT}/skills/review-quality-gates/references/reviewer-common.md`
once per assignment and apply its conventions; reuse them if already supplied.

## Mandate and input

Require the tracked file list at the candidate, the effective ignore rules (`.gitignore` at every level, `.git/info/exclude` when supplied, `.gitattributes`), the build and generator configuration that names output directories, and the recorded pre-review work tree. Decide only what the filesystem and git decide: what is tracked, ignored, generated or left behind. Show the file, the rule or generator that proves its status and the consequence: a diff that will churn on every build, a source that will never be committed, a merge that cannot apply, a checkout that breaks on another platform.

## Causal checks

- Match tracked paths against the output directories of the build (`outDir`, `target-dir`, `dist`, `build`, `__pycache__`, coverage, `.cache`) and against generator outputs. A tracked file that a configured step regenerates is a finding when its tracked content and its regenerated content differ, or when the diff shows it churning.
- Read ignore rules for over-reach: a pattern that also matches sources, fixtures or documentation assets the project needs (`*.json`, `lib/`, `build` without an anchor), negations that no longer apply, and rules that ignore a lockfile the manifest relies on. Show the needed file that `git check-ignore` reports as ignored.
- Find residue: editor backups and swap files, OS metadata, `.orig`/`.rej`, conflict markers inside tracked files, empty placeholder directories, scratch output committed with the change. Show the artifact and its origin.
- Check git state: binaries committed where `.gitattributes` declares LFS, symlinks that leave the repository, executable bits on non-executables or missing on scripts, line-ending declarations that disagree with the content, case-colliding or Windows-reserved file names, submodule pointers that no remote serves.
- Compare the pre-review work tree with the candidate when supplied: files the run or the change produced outside the owned artifact set.

## Counterevidence

A tracked generated file that the project documents as committed on purpose (vendored output, checked-in lockfile, snapshot fixtures) with a check that keeps it fresh, an ignore pattern anchored to the intended path, and a binary that LFS or the declared policy admits can refute findings. Never remove, rewrite or reformat anything.

## Boundaries and output

Dead code belongs to application-reachability, unused and phantom dependencies to dependency-usage, orphan shipped assets to asset-delivery, credentials in tracked files to secret-exposure, historical intent to artifact-lifecycle.
Report the path, its status (tracked, ignored, generated, residue), the rule or configuration that proves it, the consequence and whether removal from tracking or an ignore rule closes it.
