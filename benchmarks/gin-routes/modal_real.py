"""The Gin applications of `benchmarks/noir-binding/apps.py` (gin-vue-admin, go-admin, go-gin-example, at the same commits), on Modal: what
Gin itself says of their routes, against Noir. Section «Applicazioni vere» of the README.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 GIN_ROUTES_EVIDENCE=<a folder outside the repository> DAODAN_CODE=<a copy of daodan/ made at the start> \
      uv run --no-project --with modal modal run benchmarks/gin-routes/modal_real.py --stage noir|go [--only go-admin] [--probes false]
    python -I benchmarks/gin-routes/real_summary.py <the same folder>

The image of each application is built with the network open (the only moment it is): Python 3.12 and the pins of the snapshot's readers, the
Noir that `entry_points/noir.py` pins (sha256 checked), the copy of Daodan's code, the grammars (`noir-binding/warm.py`), the Go that
`preparation.GO` pins (sha256 checked, `prepare.py go`), the finder (`finder/main.go`, built against golang.org/x/tools at its latest
version, recorded), the checkout at its commit at `/work`, and Daodan's restore of its Go modules (`prepare.py restore`); MariaDB only for the
variant marked «by hand». Everything else runs with the network blocked (`real.py`). The answer of each application goes to
`$GIN_ROUTES_EVIDENCE/<name>.<stage>.json` (outside the repository: it holds Noir's endpoints and the applications' output);
`real_summary.py` writes the counts to `results/real/`.
"""
import concurrent.futures
import json
import os
import pathlib
import shlex
import sys
import tempfile
import zlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()
BINDING = HERE.parent / "noir-binding"
sys.path.insert(0, str(BINDING) if LOCAL else "/root")
import apps  # noqa: E402  (in the container: /root/apps.py)

REPO = HERE.parents[1] if LOCAL else HERE
CODE = pathlib.Path(os.environ.get("DAODAN_CODE") or REPO / "daodan")
EVIDENCE = pathlib.Path(os.environ.get("GIN_ROUTES_EVIDENCE") or pathlib.Path(tempfile.gettempdir()) / "gin-routes-evidence")
NAMES = tuple(name for name, spec in apps.APPS.items() if spec[0] == "gin")

# the user, password and database of go-gin-example's `conf/app.ini`, read from the copy when the variant runs (`configparser`)
APP_INI = ("python -c \"import configparser; c = configparser.ConfigParser(); c.read('/copy/conf/app.ini'); d = c['database'];"
           " q = lambda v: chr(39) + v + chr(39); print('CREATE DATABASE IF NOT EXISTS %s; CREATE USER IF NOT EXISTS %s@%s IDENTIFIED BY %s;"
           " GRANT ALL ON *.* TO %s@%s; ALTER USER %s@%s IDENTIFIED BY %s; FLUSH PRIVILEGES;' % (d['Name'], q(d['User']), q('127.0.0.1'),"
           " q(d['Password']), q(d['User']), q('127.0.0.1'), q(d['User']), q('localhost'), q(d['Password'])))\"")
MARIADB_UP = ("mkdir -p /run/mysqld && chown mysql:mysql /run/mysqld && (mysql_install_db --user=mysql --datadir=/var/lib/mysql > /dev/null 2>&1; true)"
              " && (mysqld_safe --user=mysql --bind-address=127.0.0.1 > /tmp/mysqld.log 2>&1 &)"
              " && for i in $(seq 120); do mysqladmin ping > /dev/null 2>&1 && break; sleep 0.5; done"
              f" && {APP_INI} | mysql -uroot")
MARIADB_DOWN = "mysqladmin -uroot --skip-password shutdown 2>/dev/null; pkill -f mysqld; sleep 2; rm -rf /var/lib/mysql/*; true"  # the next variant starts afresh
GVA_SQLITE = ("mkdir -p /tmp/gva-db && python -c \"import yaml; c = yaml.safe_load(open('/copy/server/config.yaml', encoding='utf-8'));"
              " c['system']['db-type'] = 'sqlite'; c['sqlite'].update({'path': '/tmp/gva-db', 'db-name': 'gva'});"
              " open('/tmp/gva-by-hand.yaml', 'w', encoding='utf-8').write(yaml.safe_dump(c, allow_unicode=True))\"")

# The argument lists each main package is run with, and where each comes from; the label's first word is the tier `real_summary.py` counts:
# «none» (as `go run .`: what Daodan can do with nothing read), «Dockerfile» (the project's Dockerfile says it: argv, and the config file a
# COPY puts where the CMD looks), «CI» (also the build tags of the project's CI workflow), «by hand» (written for this measurement: never
# part of what Daodan would do). A main package that depends on Gin and is not listed runs once with no argument.
VARIANTS = {
    "gin-vue-admin": [
        {"dir": "server", "argv": [], "label": "none"},
        {"dir": "server", "argv": ["-c", "config.docker.yaml"], "label": "Dockerfile: server/Dockerfile, ENTRYPOINT ./server -c config.docker.yaml"},
        {"dir": "server", "argv": [], "plain": True, "label": "none, built without the hook: Gin's own debug text (way b)"},
        {"dir": "server", "argv": ["-c", "/tmp/gva-by-hand.yaml"], "before": [GVA_SQLITE],
         "label": "by hand: config.yaml with system.db-type sqlite and a database file in /tmp (the plugins register their routes once a database is there)"},
    ],
    "go-admin": [
        {"dir": ".", "argv": [], "label": "none"},
        {"dir": ".", "argv": ["server"], "label": "by hand: the command `server` of cmd/api/server.go, its flag -c defaults to config/settings.yml"},
        {"dir": ".", "argv": ["server", "-c", "config/settings.demo.yml"],
         "label": "Dockerfile: CMD /main server -c /config/settings.yml after COPY ./config/settings.demo.yml /config/settings.yml"},
        {"dir": ".", "argv": ["server", "-c", "config/settings.demo.yml"], "tags": "sqlite3,json1",
         "label": "CI: the same, built with -tags sqlite3,json1 as .github/workflows/build.yml builds the main the Dockerfile copies (Makefile build-sqlite: -tags sqlite3)"},
        {"dir": ".", "argv": ["server", "-c", "config/settings.demo.yml"], "tags": "sqlite3,json1", "plain": True,
         "label": "CI: the same, built without the hook: Gin's own debug text (way b)"},
    ],
    "go-gin-example": [
        {"dir": ".", "argv": [], "label": "none (and Dockerfile: ENTRYPOINT ./go-gin-example, no argument)"},
        {"dir": ".", "argv": [], "label": "by hand: MariaDB on 127.0.0.1:3306 with the user, password and database of conf/app.ini",
         "before": [MARIADB_UP], "after": [MARIADB_DOWN]},
        {"dir": ".", "argv": [], "plain": True, "label": "by hand: the same, built without the hook: Gin's own debug text (way b)",
         "before": [MARIADB_UP], "after": [MARIADB_DOWN]},
    ],
}


def _image(name: str) -> modal.Image:
    base = modal.Image.from_registry("buildpack-deps:bookworm", add_python="3.12")
    if not LOCAL:
        return base
    _framework, repository, commit, _licence, _file, _note = apps.APPS[name]
    ignore = ["**/__pycache__/**", "**/tests/**", "**/*.pyc"]
    image = (base.pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
             .run_commands(f"curl -fsSL -o /usr/local/bin/noir {shlex.quote(apps.NOIR[0])} && echo '{apps.NOIR[1]}  /usr/local/bin/noir' | sha256sum -c - && chmod +x /usr/local/bin/noir")
             .env({"DAODAN_SHARED_DIR": "/daodan-shared", "PYTHONDONTWRITEBYTECODE": "1"})
             .add_local_dir(CODE / "core", "/daodan/core", copy=True, ignore=ignore)
             .add_local_dir(CODE / "data", "/daodan/data", copy=True)
             .add_local_file(BINDING / "warm.py", "/daodan/measure/warm.py", copy=True)
             .run_commands("python /daodan/measure/warm.py")
             .add_local_file(HERE / "prepare.py", "/daodan/measure/prepare.py", copy=True)
             .run_commands("python /daodan/measure/prepare.py go && /usr/local/go/bin/go version")
             .add_local_file(HERE / "finder" / "main.go", "/opt/finder/main.go", copy=True)
             .run_commands("cd /opt/finder && export PATH=/usr/local/go/bin:$PATH GOMODCACHE=/opt/finder-mod GOCACHE=/tmp/finder-cache GOTOOLCHAIN=local"
                           " && go mod init daodan-gin-finder && go get golang.org/x/tools/go/packages@latest && go mod tidy && go build -o finder ."
                           " && go list -m golang.org/x/tools > /opt/finder/x-tools-version && cat /opt/finder/x-tools-version && rm -rf /tmp/finder-cache"))
    if name == "go-gin-example":  # the service of the variant «by hand»
        image = image.run_commands("apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends mariadb-server > /dev/null"
                                   " && rm -rf /var/lib/apt/lists/*")
    return (image.run_commands(f"mkdir -p /work && curl -fsSL https://codeload.github.com/{repository}/tar.gz/{commit} | tar xz -C /work --strip-components=1")
            .run_commands("python /daodan/measure/prepare.py restore")
            .add_local_file(BINDING / "measure.py", "/daodan/measure/measure.py")
            .add_local_file(BINDING / "after.py", "/daodan/measure/after.py")
            .add_local_file(HERE / "real.py", "/daodan/measure/real.py")
            .add_local_file(HERE / "hooks" / "route_hook.go", "/daodan/measure/route_hook.go")
            .add_local_file(HERE / "hooks" / "engine_probe.go.tmpl", "/daodan/measure/engine_probe.go.tmpl")
            .add_local_file(BINDING / "apps.py", "/root/apps.py"))  # last: files added at run time cannot be followed by a command


IMAGES = {name: _image(name) for name in NAMES}
app = modal.App("gin-routes-real")
CHUNK = 6000  # bytes: with the network blocked a call cannot return more than about 8 KB


def _runner(name: str):
    def run(stage: str, probes: bool):
        sys.path.insert(0, "/daodan/measure")
        import traceback
        try:
            import real
            if stage == "noir":
                answer = real.noir_stage(name)
            else:
                answer = real.go_stage(name, VARIANTS.get(name, []), probes)
                answer["prepared"] = json.loads(pathlib.Path("/prepared.json").read_text(encoding="utf-8"))
                answer["x_tools"] = pathlib.Path("/opt/finder/x-tools-version").read_text(encoding="utf-8").strip()
        except BaseException:
            answer = {"name": name, "failed": traceback.format_exc()[-3000:]}
        payload = zlib.compress(json.dumps(answer).encode("utf-8"), 9)
        for start in range(0, len(payload), CHUNK):
            yield payload[start:start + CHUNK]
    run.__name__ = run.__qualname__ = "run_" + name.replace("-", "_")
    globals()[run.__name__] = function = app.function(image=IMAGES[name], timeout=3600, block_network=True, memory=16384, cpu=4)(run)
    return function


RUNNERS = {name: _runner(name) for name in NAMES}


@app.local_entrypoint()
def main(stage: str = "noir", only: str = "", probes: bool = True):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    chosen = [n for n in NAMES if not only or n in only.split(",")]
    with concurrent.futures.ThreadPoolExecutor(len(chosen)) as pool:
        calls = {n: pool.submit(lambda n=n: json.loads(zlib.decompress(b"".join(RUNNERS[n].remote_gen(stage, probes))))) for n in chosen}
        for name, call in calls.items():
            try:
                answer = call.result()
            except Exception as error:
                answer = {"name": name, "failed": f"{type(error).__name__}: {str(error)[-600:]}"}
            (EVIDENCE / f"{name}.{stage}.json").write_text(json.dumps(answer, indent=1), encoding="utf-8", newline="\n")
            if answer.get("failed"):
                print(name, "FAILED", answer["failed"][-800:])
            elif stage == "noir":
                print(name, "noir rows", len(answer["measure"].get("rows", ())), "http", answer["measure"].get("http_rows"), "go functions", len(answer["go_functions"]))
            else:
                print(name, "modules", list(answer["modules"]), "runs", [(r.get("label", "")[:30], (r.get("run") or {}).get("ended"), (r.get("run") or {}).get("returncode"),
                                                                           sum(1 for l in r.get("lines", ()) if l.get("kind") == "route")) for r in answer["runs"]],
                      "probes", [(p["builder"]["package"] + "." + p["builder"]["name"], (p.get("run") or {}).get("returncode"), len(p.get("lines", ()))) for p in answer["probes"]])
