---
name: python-packaging
description: >
  Build wheels and sdists from a pyproject.toml, then publish them.
  TRIGGER WHEN: packaging Python libraries, choosing a src or flat layout, setting up dynamic versioning, creating CLI entry points, or uploading to TestPyPI and PyPI.
---

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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

# Python Packaging

Create, structure, and distribute Python packages using modern packaging tools, pyproject.toml, and publishing to PyPI.

## When to Invoke

- Creating Python libraries for distribution
- Building CLI tools with entry points
- Publishing packages to PyPI or private repositories
- Setting up Python project structure (src layout vs flat)
- Configuring pyproject.toml, setup.py, or setup.cfg
- Building wheels and source distributions
- Versioning and releasing Python packages
- Creating namespace packages or multi-package projects

## Core Concepts

### Package Structure
- **Source layout**: `src/package_name/` (recommended)
- **Flat layout**: `package_name/` (simpler but less flexible)
- **Package metadata**: pyproject.toml, setup.py, or setup.cfg
- **Distribution formats**: wheel (.whl) and source distribution (.tar.gz)

### Modern Packaging Standards
- **PEP 517/518**: Build system requirements
- **PEP 621**: Metadata in pyproject.toml
- **PEP 660**: Editable installs
- **pyproject.toml**: Single source of configuration

### Build Backends
- **setuptools**: Traditional, widely used
- **hatchling**: Modern, opinionated
- **flit**: Lightweight, for pure Python
- **poetry**: Dependency management + packaging

### Distribution
- **PyPI**: Python Package Index (public)
- **TestPyPI**: Testing before production
- **Private repositories**: JFrog, AWS CodeArtifact, etc.

## Quick Start

### Minimal Package Structure

```
my-package/
  pyproject.toml
  README.md
  LICENSE
  src/
    my_package/
      __init__.py
      module.py
  tests/
    test_module.py
```

### Minimal pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-package"
version = "0.1.0"
description = "A short description"
authors = [{name = "Your Name", email = "you@example.com"}]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=22.0",
]
```

### Source Layout Configuration

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

## Package Structure Patterns

### Source Layout (Recommended)

```
my-package/
  pyproject.toml
  README.md
  LICENSE
  .gitignore
  src/
    my_package/
      __init__.py
      core.py
      utils.py
      py.typed
  tests/
    __init__.py
    test_core.py
    test_utils.py
  docs/
    index.md
```

Advantages: prevents accidental imports from source, cleaner test imports, better isolation.

### Flat Layout

```
my-package/
  pyproject.toml
  README.md
  my_package/
    __init__.py
    module.py
  tests/
    test_module.py
```

Simpler, but can import package without installing.

### Multi-Package Project

```
project/
  pyproject.toml
  packages/
    package-a/
      src/
        package_a/
    package-b/
      src/
        package_b/
  tests/
```

## Dynamic Versioning

```toml
[build-system]
requires = ["setuptools>=61.0", "setuptools-scm>=8.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-package"
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "my_package.__version__"}
```

**In __init__.py:**
```python
__version__ = "1.0.0"

# Or with setuptools-scm
from importlib.metadata import version
__version__ = version("my-package")
```

## Building and Publishing

### Build Package Locally

```bash
pip install build twine

# Build distribution
python -m build

# Check the distribution
twine check dist/*
```

### Publishing to PyPI

```bash
# Test on TestPyPI first
twine upload --repository testpypi dist/*

# Install from TestPyPI to verify
pip install --index-url https://test.pypi.org/simple/ my-package

# Publish to PyPI
twine upload dist/*
```

**Using API tokens (recommended):**
```bash
# Create ~/.pypirc
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-...your-token...

[testpypi]
username = __token__
password = pypi-...your-test-token...
```

## Testing Installation

### Editable Install

```bash
pip install -e .
pip install -e ".[dev]"
pip install -e ".[dev,docs]"
```

### Testing in Isolated Environment

```bash
python -m venv test-env
source test-env/bin/activate

pip install dist/my_package-1.0.0-py3-none-any.whl
python -c "import my_package; print(my_package.__version__)"
my-tool --help

deactivate
rm -rf test-env
```

## Version Constraints

```toml
dependencies = [
    "requests>=2.28.0,<3.0.0",  # Compatible range
    "click~=8.1.0",              # Compatible release (>=8.1.0,<8.2.0)
    "pydantic>=2.0",             # Minimum version
    "numpy==1.24.3",             # Exact version (avoid if possible)
]
```

## Best Practices

1. **Use src/ layout** for cleaner package structure
2. **Use pyproject.toml** for modern packaging
3. **Pin build dependencies** in build-system.requires
4. **Version appropriately** with semantic versioning
5. **Include all metadata** (classifiers, URLs, etc.)
6. **Test installation** in clean environments
7. **Use TestPyPI** before publishing to PyPI
8. **Document thoroughly** with README and docstrings
9. **Include LICENSE** file
10. **Automate publishing** with CI/CD

## Checklist for Publishing

- [ ] Code is tested (pytest passing)
- [ ] Documentation is complete (README, docstrings)
- [ ] Version number updated
- [ ] CHANGELOG.md updated
- [ ] License file included
- [ ] pyproject.toml is complete
- [ ] Package builds without errors
- [ ] Installation tested in clean environment
- [ ] CLI tools work (if applicable)
- [ ] PyPI metadata is correct (classifiers, keywords)
- [ ] GitHub repository linked
- [ ] Tested on TestPyPI first
- [ ] Git tag created for release

## References

- `references/packaging-guide.md` - full-featured pyproject.toml example with all tool configs, CLI patterns (Click and argparse), CI/CD publishing with GitHub Actions, multi-architecture wheels, data files, namespace packages, C extensions, git-based versioning, private package index, file templates (.gitignore, MANIFEST.in, README.md)

## Resources

- **Python Packaging Guide**: https://packaging.python.org/
- **PyPI**: https://pypi.org/
- **TestPyPI**: https://test.pypi.org/
- **setuptools documentation**: https://setuptools.pypa.io/
- **build**: https://pypa-build.readthedocs.io/
- **twine**: https://twine.readthedocs.io/
