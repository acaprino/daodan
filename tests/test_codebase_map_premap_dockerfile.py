"""BuildKit's reading of each Dockerfile, the declaration of a build that only its Dockerfile writes.

The answers under fixtures/premap/dockerfile are the helper's (`premap/dockerfile_stages.go`, built with BuildKit
v0.34.2 and Go 1.27.3) on two real Dockerfiles kept beside them: robot-shop's dispatch (instana/robot-shop
55292e21, Apache-2.0) and OpenTelemetry Demo's currency (open-telemetry/opentelemetry-demo b825c7c2, Apache-2.0),
the latter with Compose's OPENTELEMETRY_CPP_VERSION (1.28.0, its `.env`) and without it.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import premap  # noqa: E402
import container_runner  # noqa: E402
from premap import dockerfile  # noqa: E402

FIXTURES = ROOT / "tests/fixtures/premap/dockerfile"


def context(*files):
    return SimpleNamespace(inventory=SimpleNamespace(files=sorted(files)), stated={})


def command(rel, args="{}"):
    return {"tool": "daodan-dockerfile", "argv": ["daodan-dockerfile", rel, args], "cwd": ".", "env": {},
            "network": "none"}


def test_each_dockerfile_is_read_with_its_folder_as_the_build_context():
    """`docker build <folder>` reads `<folder>/Dockerfile` and sends that folder as the context."""
    assert dockerfile.commands(context("dispatch/Dockerfile", "dispatch/main.go", "Dockerfile", "web/x.Dockerfile")
                               ) == [command("Dockerfile"), command("dispatch/Dockerfile")]
    assert dockerfile.commands(context("main.go")) is None


def test_a_compose_file_s_builds_are_read_with_the_context_and_arguments_compose_gives():
    """OpenTelemetry Demo's compose.yaml builds currency from ./ with src/currency/Dockerfile and
    OPENTELEMETRY_CPP_VERSION from `.env`: Compose itself resolves that (`config --format json`), then BuildKit
    reads the Dockerfile with that argument. A Dockerfile Compose builds is not read again with its own folder as
    the context; one Compose cannot read is a gap naming the service."""
    files = ("compose.yaml", ".env", "src/currency/Dockerfile", "src/ad/Dockerfile", "dispatch/Dockerfile")
    commands = dockerfile.commands(context(*files))
    assert commands[0]["argv"][:3] == ["sh", "-c", "cd . && exec daodan-dockerfile --compose compose.yaml"]
    assert [c["argv"][1] for c in commands[1:]] == ["dispatch/Dockerfile", "src/ad/Dockerfile",
                                                    "src/currency/Dockerfile"]
    answers = [{"returncode": 0, "stdout": (FIXTURES / "otel-demo-compose.json").read_text(encoding="utf-8"),
                "stderr": ""},
               *({"returncode": 0, "stdout": (FIXTURES / "robot-shop-dispatch.json").read_text(encoding="utf-8"),
                  "stderr": ""} for _ in commands[1:])]
    out = dockerfile.read(context(*files), commands, answers)
    builds = {(b["dockerfile"], b["context"]): b for b in out["facts"]["docker_builds"]}
    assert sorted(builds) == [("dispatch/Dockerfile", "dispatch"), ("src/currency/Dockerfile", ".")]
    currency = builds[("src/currency/Dockerfile", ".")]
    assert currency["args"] == {"OPENTELEMETRY_CPP_VERSION": "1.28.0"}
    assert currency["declared_in"] == "compose.yaml#services.currency.build"
    assert [s["name"] for s in currency["stages"]] == ["base", "builder", "release"]
    # Its root .dockerignore, as BuildKit reads it: `.github`, `internal`, `src/*/README.md`, `src/*/Dockerfile`,
    # `src/*/*/Dockerfile` (recorded on Modal, 16 November 2026, with the folders and files they name).
    assert currency["dockerignore"] == ".dockerignore" and currency["excluded"] == [
        ".github/", "internal/", "src/currency/Dockerfile", "src/currency/README.md", "src/currency/genproto/Dockerfile"]
    missing = [g for g in out["gaps"] if g["path"] == "src/ad/Dockerfile"]
    assert missing and missing[0]["kind"] == "model_failed" and "compose.yaml#services.ad" in missing[0]["detail"]


def test_what_a_build_s_dockerignore_leaves_out_is_read_by_buildkit_s_own_matcher():
    """BuildKit's own rules (its dockerui frontend; patternmatcher v0.6.1, as BuildKit v0.34.2 pins it): the
    Dockerfile's own ignore file, `<Dockerfile>.dockerignore`, before the context's .dockerignore (here `*`, which
    would leave out everything); a folder that matches is left out whole unless an exception lies inside it
    (`docs`, with `!docs/keep.md`); `*.log` matches at the context's root only. Recorded on Modal, 16 November
    2026, from tools/: Dockerfile, .dockerignore, Dockerfile.dockerignore, docs/{a,keep}.md, x.log, sub/y.log,
    build/out.bin, src/main.c."""
    files = ("tools/Dockerfile", "tools/.dockerignore", "tools/Dockerfile.dockerignore")
    commands = dockerfile.commands(context(*files))
    answers = [{"returncode": 0, "stdout": (FIXTURES / "dockerignore-exceptions.json").read_text(encoding="utf-8"),
                "stderr": ""}]
    [build] = dockerfile.read(context(*files), commands, answers)["facts"]["docker_builds"]
    assert (build["dockerfile"], build["context"]) == ("tools/Dockerfile", "tools")
    assert build["dockerignore"] == "tools/Dockerfile.dockerignore"
    assert build["excluded"] == ["build/", "docs/a.md", "x.log"]
    # A Dockerfile without an ignore file has neither field.
    answers = [{"returncode": 0, "stdout": (FIXTURES / "robot-shop-dispatch.json").read_text(encoding="utf-8"),
                "stderr": ""}]
    [build] = dockerfile.read(context("dispatch/Dockerfile"), dockerfile.commands(context("dispatch/Dockerfile")),
                              answers)["facts"]["docker_builds"]
    assert "dockerignore" not in build and "excluded" not in build


def test_a_compose_file_compose_does_not_read_says_its_error_and_the_variables_it_found_unset():
    """OpenTelemetry Demo's compose.yaml without the `.env` Daodan never reads (Compose 5.6.1 on Modal, 16 November
    2026): Compose stops on a volume its blank HOST_FILESYSTEM leaves `:/hostfs:ro`, after warning of each
    variable it interpolates blank; the warnings come after the error."""
    files = ("compose.yaml", "src/currency/Dockerfile")
    commands = dockerfile.commands(context(*files))
    warning = 'time="2026-11-16T17:19:59Z" level=warning msg="The \\"{}\\" variable is not set. Defaulting to a ' \
              'blank string."'
    stderr = "\n".join(["invalid spec: :/hostfs:ro: empty section between colons",
                        *(warning.format(name) for name in ("CURRENCY_DOCKERFILE", "OPENTELEMETRY_CPP_VERSION",
                                                            "ENVOY_ADMIN_PORT", "ENVOY_ADMIN_PORT"))])
    answers = [{"returncode": 1, "stdout": "", "stderr": stderr},
               {"returncode": 0, "stdout": (FIXTURES / "otel-demo-currency-no-args.json").read_text(encoding="utf-8"),
                "stderr": ""}]
    out = dockerfile.read(context(*files), commands, answers)
    [gap] = [g for g in out["gaps"] if g["path"] == "compose.yaml"]
    assert gap == {"kind": "model_failed", "path": "compose.yaml", "detail": (
        "buildkit: docker compose config: invalid spec: :/hostfs:ro: empty section between colons; not set, so "
        "blank: CURRENCY_DOCKERFILE, ENVOY_ADMIN_PORT, OPENTELEMETRY_CPP_VERSION (Daodan reads no .env: it may "
        "hold secrets)")}
    # The Dockerfile is then read as `docker build` of its folder reads it.
    assert [(b["dockerfile"], b["context"]) for b in out["facts"]["docker_builds"]] == [
        ("src/currency/Dockerfile", "src/currency")]


def placeholder(file, name):
    """`container.named`'s placeholder of a tracked .env file's variable, as Compose interpolates it."""
    return f"./daodan-dotenv-{file.encode().hex()}-{name.encode().hex()}"


def test_a_build_s_values_from_a_tracked_env_file_are_named_never_given():
    """OpenTelemetry Demo's currency: the helper runs Compose with the tracked .env's values the pre-map's container
    keeps (`container.named`), and once without interpolating, which says what names a variable. It reads the
    Dockerfile CURRENCY_DOCKERFILE gives, a tracked path, and says the variable; an argument, and the words BuildKit
    expanded with it, keep `${NAME}`: no value reaches the fact. A value that names no file of the checkout is a gap
    naming the variable, as is a placeholder in Compose's own error (`compose._named`)."""
    files = ("compose.yaml", "src/currency/Dockerfile")
    commands = dockerfile.commands(context(*files))
    answer = {"builds": [{"service": "currency", "dockerfile": "src/currency/Dockerfile", "context": ".",
                          "args": {"OPENTELEMETRY_CPP_VERSION": "${OPENTELEMETRY_CPP_VERSION}"}, "target": "",
                          "dotenv": {"CURRENCY_DOCKERFILE": ".env", "OPENTELEMETRY_CPP_VERSION": ".env"},
                          "stages": [{"name": "builder", "base": "alpine:3.24.3", "base_stage": None, "line": 1,
                                      "commands": [{"kind": "RUN", "line": 2, "original": "RUN git clone v${V}",
                                                    "cmd": ["git clone --branch v${OPENTELEMETRY_CPP_VERSION} x"],
                                                    "shell": True}]}]}],
              "errors": [{"service": "ad", "dockerfile": "${AD_DOCKERFILE}",
                          "error": "AD_DOCKERFILE of .env gives no file or folder of the checkout"}]}
    out = dockerfile.read(context(*files), commands, [{"returncode": 0, "stdout": json.dumps(answer), "stderr": ""}])
    [build] = out["facts"]["docker_builds"]
    assert build["args"] == {"OPENTELEMETRY_CPP_VERSION": "${OPENTELEMETRY_CPP_VERSION}"}
    assert build["dotenv"] == {"CURRENCY_DOCKERFILE": ".env", "OPENTELEMETRY_CPP_VERSION": ".env"}
    assert out["gaps"] == [{"kind": "model_failed", "path": "${AD_DOCKERFILE}", "detail": (
        "buildkit: compose.yaml#services.ad.build: AD_DOCKERFILE of .env gives no file or folder of the checkout")}]
    port = placeholder(".env", "VALKEY_PORT")
    failed = dockerfile.read(context(*files), commands, [{"returncode": 1, "stdout": "",
                                                          "stderr": f"invalid proto: {port}"}])
    assert failed["gaps"][0]["detail"] == "buildkit: docker compose config: invalid proto: ${VALKEY_PORT}"


def test_buildkit_s_stages_of_a_dockerfile_are_its_build_fact():
    answer = (FIXTURES / "robot-shop-dispatch.json").read_text(encoding="utf-8")
    out = dockerfile.read(context("dispatch/Dockerfile"), [command("dispatch/Dockerfile")],
                          [{"returncode": 0, "stdout": answer, "stderr": ""}])
    [build] = out["facts"]["docker_builds"]
    assert build == {"dockerfile": "dispatch/Dockerfile", "context": "dispatch", "args": {},
                     "stages": json.loads(answer)["stages"]}
    [stage] = build["stages"]
    assert stage["base"] == "golang:1.17" and [(c["kind"], c["line"]) for c in stage["commands"]] == [
        ("WORKDIR", 3), ("COPY", 5), ("RUN", 7), ("RUN", 8), ("CMD", 10)]
    assert not out.get("gaps")


def test_a_build_argument_without_a_value_stays_unset_and_a_given_one_is_expanded():
    """currency's `ARG OPENTELEMETRY_CPP_VERSION` has no default: Compose gives 1.28.0; without it BuildKit leaves
    it unset. A stage FROM an earlier one names it; the base before the first FROM keeps its digest."""
    given, unset = (json.loads((FIXTURES / name).read_text(encoding="utf-8"))["stages"]
                    for name in ("otel-demo-currency.json", "otel-demo-currency-no-args.json"))
    assert [(s["name"], s["base_stage"]) for s in given] == [("base", None), ("builder", 0), ("release", 0)]
    assert given[0]["base"].endswith("@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a")
    [arg] = [c for c in given[1]["commands"] if c["kind"] == "ARG"]
    assert arg["args"] == [{"OPENTELEMETRY_CPP_VERSION": "1.28.0"}]
    [arg] = [c for c in unset[1]["commands"] if c["kind"] == "ARG"]
    assert arg["args"] == [{"OPENTELEMETRY_CPP_VERSION": None}] and arg["line"] == 26


def test_a_dockerfile_buildkit_does_not_read_is_a_gap_naming_it():
    out = dockerfile.read(context("dispatch/Dockerfile"), [command("dispatch/Dockerfile")],
                          [{"returncode": 1, "stdout": "", "stderr": "dockerfile parse error on line 3: unknown "
                                                                     "instruction: FORM\n"}])
    assert out == {"facts": {}, "gaps": [{"kind": "model_failed", "path": "dispatch/Dockerfile",
                                          "detail": "buildkit: dockerfile parse error on line 3: unknown "
                                                    "instruction: FORM"}]}


def test_the_helper_is_built_in_the_container_with_buildkit_at_its_pin():
    spec = container_runner.TOOLS["daodan-dockerfile"]
    assert spec["registries"] and (None, None, "dockerfile_stages.go") in spec["files"]
    assert (*premap.compose.DOWNLOAD, "docker-compose") in spec["files"]  # Compose's own reading of its files
    assert f"github.com/moby/buildkit@{dockerfile.VERSION}" in " ".join(spec["setup"])
    assert dockerfile in premap.SOURCES and "docker_builds" in premap.IDENTITY
