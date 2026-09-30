# CSP Plugin

> Solve complex scheduling, routing, and assignment problems that would take days to model from scratch. Expert constraint programming with Google OR-Tools CP-SAT.

## Agents

### `or-tools-expert`

Master constraint programmer specializing in modeling and solving complex optimization problems using Google OR-Tools CP-SAT.

| | |
|---|---|
| **Invoke** | Agent reference |
| **Use for** | Constraint programming, scheduling, optimization, routing, assignment problems |

**Core capabilities:**
- **CSP Modeling**: variables, domains, linear and global constraints
- **Scheduling**: job shop, flow shop, nurse scheduling, resource allocation
- **Optimization**: minimize/maximize objectives, multi-objective problems (weighted-sum scalarization or lexicographic solving, since CP-SAT has no native multi-objective API)
- **Performance**: parallel solving, hints, domain tightening, symmetry breaking
- **Debugging**: infeasibility analysis, assumptions, solution enumeration

**Integer-only rule:** CP-SAT supports integers only, so the agent never passes a float to any CP-SAT API (variables, domains or objective coefficients). Real-world decimals are scaled by 10^N and rounded to int before they enter the model (cents for money, millimeters for length).

**Problem types:**
| Problem Type | Examples |
|--------------|----------|
| Scheduling | Job shop, nurse shifts, project scheduling (RCPSP) |
| Assignment | Task allocation, load balancing, bin packing |
| Routing | TSP and simple VRP via `add_circuit` / `add_multiple_circuit` |
| Classic CSP | N-Queens, Sudoku, graph coloring |
| Planning | Production planning, workforce optimization |
| Packing | Bin packing, cutting stock, rectangle packing |
| Sequencing | Tournament scheduling, timetabling |

Complex VRP (CVRP, VRPTW, pickup and delivery) is out of pure CP-SAT's sweet spot: the agent points you to the dedicated OR-Tools Routing Library instead.

**Dry-run validation:** before presenting generated code, the agent runs a quick syntax and import check on it through Bash.

**Prerequisites:**
```bash
pip install ortools
# or with uv
uv add ortools
```

**Resources:**
- [OR-Tools Documentation](https://developers.google.com/optimization/cp)
- [CP-SAT Primer](https://d-krupke.github.io/cpsat-primer/): comprehensive guide
- [CP-SAT Log Analyzer](https://cpsat-log-analyzer.streamlit.app/)

---

**Related:** [python-development](python-development.md) (Python implementation patterns for constraint models)
