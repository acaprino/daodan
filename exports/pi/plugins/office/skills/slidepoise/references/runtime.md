# External SlidePoise runtime

This is a locally authored integration, not a vendored SlidePoise distribution.
Upstream source: https://github.com/henryhyw/slidepoise. License: MIT. The inspected
integration reference is version `0.8.2`, revision
`4250ba14d5d673a3215e7707b5d52f67cdf1154e`. A future upstream revision needs its
interfaces and reconstruction behavior inspected before changing this pin.

## Prerequisites and installation

Use Python 3.10+, Node.js 18+ and npm 9+. Editable reconstruction needs the upstream
Python packages (including OpenCV) and its Node/PptxGenJS runtime. Visual review
needs a compatible PPTX renderer; upstream setup supports LibreOffice and Poppler.
Image generation, image inspection and required fonts come from the current host.

When runtime installation is within the user's authorized task, run:

```text
npx --yes github:henryhyw/slidepoise#4250ba14d5d673a3215e7707b5d52f67cdf1154e setup --skip-skill
```

`--skip-skill` installs the framework without adding another registered skill
beside Daodan's integration. The framework includes its own skill resources; the
bridge discovers them through `framework.paths.SKILL_ROOT`. The pin fixes the
upstream source, while upstream's dependency ranges still govern its Python and
Node packages. Record the installed versions for reproducibility.

Setup writes under `SLIDEPOISE_HOME` when set, otherwise `~/.slidepoise`, and can
install missing preview applications through the system package manager. Read the
installer's output and respect the host's permissions for system installation.
Use `--skip-preview` only when a compatible renderer already exists or the
user accepts an explicitly unreviewed output. Check `doctor` after setup; skipped
preview setup is not evidence of visual verification.

The bridge never downloads, installs, registers skills or changes host settings.
It selects `<home>/python/Scripts/python.exe` on Windows and
`<home>/python/bin/python` on other systems. A `--home` override also sets the
child runtime's `SLIDEPOISE_HOME`. It validates the discovered external skill and
reconstruction entry point before forwarding commands.

## Host portability

Daodan ships this integration on Claude, Codex, Copilot, Pi and OpenCode. All five
must be able to execute the external local runtime, read its resources and inspect
images. The upstream installer registers skills only for Codex, Claude and Qoder;
the Daodan bridge avoids relying on that host-specific registration.

Codex is upstream's primary tested presentation environment. The availability of
Daodan packages on other hosts is compiled support, not evidence of a completed
presentation on those hosts. Discover capabilities in the active session and
report a missing runtime, generator, font or renderer precisely.

Use the upstream Console or session panel only when useful and supported by the
current host. Use the host's normal browser/file opening interface. Do not rely
on a Codex-only notification connection to resume work on other hosts. Apply the
upstream runtime's durable session-change checkpoints between operations.

## Runtime commands

Use bridge `cli` for `doctor`, `profile list`, `profile show`, profile selection
and other supported framework commands. Use bridge `script` for upstream skill
scripts, including `slidepoise_runtime.py`. Read the installed method and the
specific command's help before constructing its input contracts. Preserve
external exit codes and report objective command failures with their evidence.

Keep all generated slide evidence within the presentation's work directory. Keep
user-owned Profiles and Library Sets in the external framework home. Changes to
one presentation must not silently change the shared Profile for future work.
