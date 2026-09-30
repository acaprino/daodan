# Docker Plugin

> Docker best practices: optimized multi-stage Dockerfiles, layer caching, security hardening, and minimal base image selection for any language or framework.

## Skills

### `multi-stage-dockerfile`

Creates efficient multi-stage Dockerfiles that follow best practices, resulting in smaller, more secure container images.

| | |
|---|---|
| **Trigger** | Creating Dockerfiles, optimizing container images, multi-stage builds, Docker best practices |
| **Upstream** | `github/awesome-copilot` |

**What it covers:**
- Multi-stage structure (builder vs runtime stages)
- Base image selection (exact version tags, slim, alpine or distroless)
- Layer caching optimization
- Security hardening (non-root users, no build secrets in the final image, `HEALTHCHECK`)
- Anti-pattern pairs, each wrong Dockerfile shown next to the corrected one (dev dependencies in the runtime image, a broken layer cache, running as root with no healthcheck)
- Per-language templates: Node.js/TypeScript, Python (FastAPI/Flask), Go, Rust, Java (Spring Boot/Gradle), Bun and Deno
- A `.dockerignore` template, to adapt per language
- A validation checklist to run before finalizing the Dockerfile

---

**Related:** [platform-engineering](platform-engineering.md) (infrastructure and deployment patterns)
