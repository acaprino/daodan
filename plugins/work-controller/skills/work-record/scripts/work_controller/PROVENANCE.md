# Work Controller provenance

This runtime is owned by `work-controller@daodan`. It transfers the original
local implementation from the former standalone `process-controller` project
into Daodan without embedding third-party implementation code. The retained MIT
notice is in [LICENSE](LICENSE). The historical inspiration record follows;
it identifies examined projects, not required providers.

## Original inspiration

Process Controller uses original code and contracts. The following projects supplied architectural ideas, not copied source or text.

| Project | Examined revision | License | Ideas adopted |
|---|---|---|---|
| [Hatchet](https://github.com/hatchet-dev/hatchet) | `a4bd80db3231bff9411c292a92dd154f8cbc8e29` | MIT | Durable DAG progress, parent-to-child outputs, persistent attempts, explicit waits and bounded execution policy |
| [Foreman](https://github.com/thruwire/foreman) | `c3142ef636617f32f772140125aa310d81ceece9` | MIT | Bounded observations, attempt supervision, explicit intervention vocabulary and non-authoritative recommendations |
| [Wayfinder](https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder) | `8295b8e10d4cdb6cce772a56dda7b7c37075074d` | MIT | Destination-led maps, typed tickets, acyclic blockers, a small frontier and exclusive claims |

The architectural differences are deliberate: Process Controller uses a local SQLite journal, content-addressed artifacts and host-neutral packets. It does not copy Hatchet's distributed runtime, Foreman's single-worker implementation or Wayfinder's tracker and text.

PyYAML is a runtime dependency, not vendored source. It is MIT licensed and is used only through a restricted safe loader with additional schema and resource checks.
