# CI runtime recovery for Code Context

The push through P5 (`2dce83a3`) reached GitHub, but both Linux workflows failed
their test step. They selected Python 3.11 while the Codebase Map's parser and
entry points require Python 3.12. The consistency run reported 110 failures and
68 errors; 171 cases directly cited the interpreter floor and other failures
followed from missing outputs after entry-point refusal.

Both workflow files already contained a local correction to Python 3.12.
The recovery adopts only those three runner pins after inspecting their complete
diff. Other uncommitted source and generated changes remain outside the commit.
The guard is retained: lowering the parser requirement would hide unsupported
grammar rather than exercise the intended implementation.

The workflow regression now passes every configured Python version to the real
`require_minimum_interpreter` boundary. The old three 3.11 pins produce three
failures; the corrected pins pass all 17 publication contract tests. It does
not assert one chosen version string or weaken the requirement.

Actual Linux suite and publication outcomes are recorded against their exact
commit in `.tritech/daodan/runs/code-context-ci-20261023/`. The initial failing
run and full logs remain in the parent code-context run. Local compatibility,
remote execution and publication are separate evidence facts. No model download
or runtime dependency is added, and the compiler's standard-library contract
is unchanged.
