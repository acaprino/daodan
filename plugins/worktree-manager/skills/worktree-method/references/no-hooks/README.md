# Checkout hook boundary

This shipped directory contains no Git hooks. The limited Worktrunk adapter
sets `core.hooksPath` to this path only in its subprocess environment, so
creation cannot execute a repository's native checkout hooks implicitly.
Worktrunk hooks are separately disabled with `--no-hooks`. Trusted project
setup remains an explicit task step. The adapter exposes no commit command
and grants no permission to bypass commit or review gates.
