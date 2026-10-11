---
name: multi-stage-dockerfile
description: >
  Ship a runtime layer that carries only what it executes, for any language or framework.
  TRIGGER WHEN: creating Dockerfiles, optimizing container images, multi-stage builds, Docker best practices.
---

<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

Source: github/awesome-copilot - `skills/multi-stage-dockerfile/SKILL.md`


Your goal is to help me create efficient multi-stage Dockerfiles that follow best practices, resulting in smaller, more secure container images.

## Multi-Stage Structure

- Use a builder stage for compilation, dependency installation, and other build-time operations
- Use a separate runtime stage that only includes what's needed to run the application
- Copy only the necessary artifacts from the builder stage to the runtime stage
- Use meaningful stage names with the `AS` keyword (e.g., `FROM node:18 AS builder`)
- Place stages in logical order: dependencies -> build -> test -> runtime

## Base Images

- Start with official, minimal base images when possible
- Specify exact version tags to ensure reproducible builds (e.g., `python:3.11-slim` not just `python`)
- Consider distroless images for runtime stages where appropriate
- Use Alpine-based images for smaller footprints when compatible with your application
- Ensure the runtime image has the minimal necessary dependencies

## Layer Optimization

- Organize commands to maximize layer caching
- Place commands that change frequently (like code changes) after commands that change less frequently (like dependency installation)
- Use `.dockerignore` to prevent unnecessary files from being included in the build context
- Combine related RUN commands with `&&` to reduce layer count
- Consider using COPY --chown to set permissions in one step

## Security Practices

- Avoid running containers as root - use `USER` instruction to specify a non-root user
- Remove build tools and unnecessary packages from the final image
- Scan the final image for vulnerabilities
- Set restrictive file permissions
- Use multi-stage builds to avoid including build secrets in the final image

## Performance Considerations

- Use build arguments for configuration that might change between environments
- Leverage build cache efficiently by ordering layers from least to most frequently changing
- Consider parallelization in build steps when possible
- Set appropriate environment variables like NODE_ENV=production to optimize runtime behavior
- Use appropriate healthchecks for the application type with the HEALTHCHECK instruction

## Common Anti-Patterns

### Wrong: Installing dev dependencies in runtime

```dockerfile
FROM node:20
WORKDIR /app
COPY . .
RUN npm install
CMD ["node", "server.js"]
```

### Correct: Multi-stage with production-only deps

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-slim
WORKDIR /app
COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/dist ./dist
USER node
CMD ["node", "dist/server.js"]
```

### Wrong: Breaking layer cache

```dockerfile
COPY . .
RUN pip install -r requirements.txt
```

### Correct: Dependencies first, code second

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

### Wrong: Running as root with no healthcheck

```dockerfile
FROM python:3.12
COPY app.py .
CMD ["python", "app.py"]
```

### Correct: Non-root user + healthcheck

```dockerfile
FROM python:3.12-slim
RUN useradd --create-home appuser
WORKDIR /home/appuser
COPY --chown=appuser:appuser app.py .
USER appuser
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "app.py"]
```

## Language Templates

### Node.js (TypeScript)

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json tsconfig.json ./
RUN npm ci
COPY src/ src/
RUN npm run build && npm prune --omit=dev

FROM gcr.io/distroless/nodejs22-debian12
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
USER nonroot
EXPOSE 3000
CMD ["dist/server.js"]
```

### Python (FastAPI/Flask)

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM python:3.12-slim
WORKDIR /app
RUN useradd --create-home appuser
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app .
ENV PATH="/opt/venv/bin:$PATH"
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Go

```dockerfile
FROM golang:1.24-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /server ./cmd/server

FROM gcr.io/distroless/static-debian12
COPY --from=builder /server /server
USER nonroot
EXPOSE 8080
ENTRYPOINT ["/server"]
```

### Rust

```dockerfile
FROM rust:1.82-slim AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs && cargo build --release && rm -rf src
COPY src/ src/
RUN touch src/main.rs && cargo build --release

FROM debian:bookworm-slim
RUN useradd --create-home appuser
COPY --from=builder /app/target/release/myapp /usr/local/bin/
USER appuser
EXPOSE 8080
CMD ["myapp"]
```

### Java (Spring Boot / Gradle)

```dockerfile
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app
COPY gradle/ gradle/
COPY gradlew build.gradle.kts settings.gradle.kts ./
RUN ./gradlew dependencies --no-daemon
COPY src/ src/
RUN ./gradlew bootJar --no-daemon

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /app/build/libs/*.jar app.jar
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### Bun (Server or API)

```dockerfile
FROM oven/bun:1-alpine AS builder
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun build ./src/index.ts --target=bun --outdir=./dist --minify

FROM oven/bun:1-alpine
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=builder --chown=app:app /app/dist ./dist
COPY --from=builder --chown=app:app /app/node_modules ./node_modules
USER app
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["bun", "run", "./dist/index.js"]
```

Notes: Bun 1.2+ uses text-based `bun.lock` (replaces legacy `bun.lockb`). Pin the Bun major version; do not use `:latest`.

### Deno (API or CLI)

```dockerfile
FROM denoland/deno:2-alpine AS builder
WORKDIR /app
COPY deno.json deno.lock ./
RUN deno cache --lock=deno.lock main.ts
COPY . .
RUN deno compile --allow-net --allow-env --output=/app/server main.ts

FROM alpine:3.20
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=builder --chown=app:app /app/server /app/server
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8000/health || exit 1
ENTRYPOINT ["/app/server"]
```

Notes: Deno 2 ships `deno compile` producing a self-contained binary; the runtime image can be plain alpine with no Deno installed. Declare required permissions explicitly -- Deno refuses unknown ones.

## .dockerignore Template

Always create a `.dockerignore` alongside the Dockerfile:

```
.git
.gitignore
.env*
*.md
LICENSE
docker-compose*.yml
Dockerfile*
node_modules
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.venv
target/
build/
dist/
.idea
.vscode
*.log
coverage/
.next
```

Adapt to the specific language -- remove entries that don't apply, add framework-specific build artifacts.

## Validation Checklist

Before finalizing the Dockerfile, verify:

- [ ] Multi-stage build separates build-time from runtime dependencies
- [ ] Base images use exact version tags (no `latest`)
- [ ] Runtime image is minimal (slim, alpine, or distroless)
- [ ] Dependencies copied before source code (layer cache)
- [ ] `USER` instruction sets non-root user in final stage
- [ ] `HEALTHCHECK` instruction present for service containers
- [ ] `.dockerignore` exists and excludes build artifacts, `.git`, `.env`
- [ ] No secrets or credentials baked into the image
- [ ] `EXPOSE` documents the listening port
- [ ] Build arguments used for environment-specific configuration
