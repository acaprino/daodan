# Worktrunk runtime and upstream updates

Canonical provider: [max-sixty/worktrunk](https://github.com/max-sixty/worktrunk).
Worktrunk is dual licensed **MIT OR Apache-2.0**, at the recipient's choice.
Daodan's adapter is original code and delegates to the external executable.
No upstream Rust source, plugin bodies or binary is shipped in this kernel.
The machine-readable compatibility record is `upstream.json` beside this file.

## Availability

Run the bundled boundary first:

```text
python "${CLAUDE_PLUGIN_ROOT}/skills/worktree-method/scripts/worktrunk_runtime.py" probe --project ROOT
python "${CLAUDE_PLUGIN_ROOT}/skills/worktree-method/scripts/worktrunk_runtime.py" upstream-check
```

The main checkout's `.daodan/tools/worktrunk/<version>/` is checked before PATH.
Automatic discovery requires an ignored, untracked executable in the owned
`.daodan` home without links. Repository-tracked executables are refused before
they can run. PATH fallback inspects only absolute directory entries and rejects
executables in the invoking checkout, the target checkout or any of their
registered linked worktrees, including paths that resolve into those trees.
Empty and relative PATH entries and implicit current-directory lookup are
excluded without changing the process environment. Outside Git, an executable
directly in the invoking directory is excluded; a user installation in one of
its child directories remains eligible through an absolute PATH entry.
On Windows, fallback accepts
only `git-wt.exe`, never batch files or `wt.exe`.
The installation step verifies the official archive checksum;
later probes check availability/version, not a universal binary security audit.
An explicitly supplied executable may be used for another authorized install.
The boundary checks the actual binary identity and supported version. On Windows,
`wt.exe` can be Windows Terminal; use Worktrunk's `git-wt.exe` or an explicit
verified path. Do not launch the unrelated program as a probe.

If absent, report the required release from the compatibility record and use
the provider's [installation documentation](https://worktrunk.dev/install/).
Prefer its released binary for the current OS/architecture, verify its published
checksum before execution, and keep a portable install in the project's
`.daodan/tools/worktrunk/<version>/` when no existing authorized installation
fits. System-wide/package-manager changes need their applicable authorization.
Do not run a downloaded installer script blindly. Do not install upstream agent
plugins or shell profile hooks as a prerequisite of Daodan's adapter.

Core commands support Windows; upstream shell hooks require Git Bash. Daodan
creation disables Worktrunk hooks and uses an invocation-only `core.hooksPath`
override pointing at the bundled empty hook directory. Native checkout hooks
therefore cannot run setup implicitly; persistent Git configuration is unchanged.
Run explicitly authorized setup separately.
Supply a working directory and argument array through the actual host execution
mechanism. Registration or generated instructions do not prove that a host can
execute or bind a workspace.

## Update procedure

1. On a requested upstream update, run `upstream-check`. Keep its checked and
   supported versions distinct. Network/rate-limit failure is unavailable
   evidence, not proof of being current. This command changes no installation,
   pin, project configuration or catalog.
2. Read the candidate release notes, license and relevant CLI/schema changes at
   its exact tag/commit. Assess hook execution, path handling, staging, merge,
   cleanup, supported OS and security changes. The absence of an advisory is
   not a security audit. Preserve the previous known-compatible installation.
3. Test the candidate in an isolated temporary repository with a separate
   candidate copy of the adapter's compatibility record. Verify executable
   identity, structured output, creation/resume under the main `.daodan`, dirty
   and ignored file preservation, candidate review boundaries, interrupted
   cleanup and the active host's execution binding. Keep broader host checks
   explicitly unverified until exercised.
4. Advance `upstream.json` only with the source commit, version, asset provenance
   and successful compatibility evidence. Update the original adapter only for
   demonstrated contract changes. Bump its plugin version, regenerate all host
   packages and run the repository checks. Failed probes keep the old pin and
   describe the incompatible behavior.
5. Activate the tested binary under the user's update authorization. Verify its
   version from the actual invocation path and retain the previous version for
   recovery. Report separately release discovery, adapter support, installation
   and host execution. Do not mark a downloaded release as an adopted update.

This is versioned external dependency maintenance, not vendored source syncing.
It adds no copied-source sync target and schedules no background polling.
