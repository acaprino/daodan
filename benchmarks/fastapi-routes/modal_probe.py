"""FastAPI's own loader and route objects on Modal, in the runner's container image, with the network blocked.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/fastapi-routes/modal_probe.py
    ... --only environment,cli-source        some variants, nothing recorded
    ... --label before-review                the answers go to `results/before-review/`, nothing recorded

The image is Daodan's (`container_runner.IMAGE`, with Modal's Python added beside it), and what Daodan's runner does before a command is
done by the same lines: `plan.py` (run with the Python that has Daodan's own dependencies, `DAODAN_PYTHON` names it, default `python`)
prints, for a project folder, the commands `fastapi_app.commands` gives, the setup command `container_runner.plan` gives, the restore
lines `container_runner._python` makes and the files the setup unpacks. There is one image for the `fixture` (the restore of its
`pyproject.toml`, which has no `requirements.txt`: the `pip` line reads the `pyproject.toml`) and one for each of `OTHER_IMAGES`, the
same files with another way to depend on FastAPI (see there): the image build, the one moment the network is open, unpacks those files
at `preparation.IN`, copies the folder to `/work` (`container.WORKDIR`) and runs the setup command there, with the runner's environment
(`preparation.ENV`); its standard error, exit code and seconds are kept in the image (`environment` returns them). Each variant of
`VARIANTS` then runs in a copy of its folder at `/work`, with the network blocked and the same environment, in the `cwd` the source's
command names, and its answer (`argv`, `returncode`, `stdout`, `stderr`, seconds, peak memory, the files it left in the project) goes to
`results/<variant>.json`. The project's code runs only in the container. What differs from Daodan's own container: Modal's runtime, and
the Python Modal installs in `/usr/local/bin` (3.12.1), which comes before `/usr/bin` in `preparation.PATH` and so is the `python3` the
restore's `uv venv --python python3` picks.

The variants named in `RECORDED` are the answers the tests read: the run writes them to `tests/fixtures/premap/fastapi/<variant>.json`
(`returncode`, `stdout`, `stderr`, as the container runner returns them) with the sha256 of the two script files that produced them and
the `VERSION` of the source (`script.json`). If a script changes, record again and raise the `VERSION`.
"""
import hashlib
import json
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import tempfile

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
if LOCAL:
    sys.path.insert(0, str(HERE))
    import apps  # noqa: E402  (the pinned Noir)
REPO = HERE.parents[1] if LOCAL else HERE
OUT = HERE / "results"
RECORDED_DIR = REPO / "tests/fixtures/premap/fastapi"
SCRIPTS = ("fastapi_routes.py", "python_script.py")
# image -> how the fixture's way to depend on FastAPI changes: `plain` has `fastapi` (no `fastapi-cli`, which `fastapi[standard]`
# brings) in a `requirements.txt` and none in the `pyproject.toml`; `old` is the same fixture on the FastAPI and Starlette of a year before, `mid` on 0.137.1, where `include_router` keeps the routers
# and `iter_route_contexts` is not yet there
OTHER_IMAGES = {
    "plain": {"requirements.txt": "fastapi==0.165.0\n"},
    "old": {"pyproject.toml": ("fastapi[standard]==0.165.0", "fastapi[standard]==0.115.14")},
    "mid": {"pyproject.toml": ("fastapi[standard]==0.165.0", "fastapi[standard]==0.137.1")},
}
WORK = "/work"  # `container.WORKDIR`


def _folders() -> dict[str, pathlib.Path]:
    """The folder of each image: the fixture, and a copy of it with the edit of `OTHER_IMAGES` (host files only, nothing runs)."""
    out = {"fixture": HERE / "fixture"}
    base = pathlib.Path(os.environ.get("DAODAN_PROBE_TMP") or tempfile.gettempdir()) / "fastapi-images"
    for name, edits in OTHER_IMAGES.items():
        folder = base / name
        shutil.rmtree(folder, ignore_errors=True)
        shutil.copytree(HERE / "fixture", folder, ignore=shutil.ignore_patterns("__pycache__"))
        for rel, edit in edits.items():
            target = folder / rel
            if isinstance(edit, str):
                target.write_text(edit, encoding="utf-8", newline="\n")
            else:
                target.write_text(target.read_text(encoding="utf-8").replace(*edit), encoding="utf-8", newline="\n")
        if name == "plain":  # `fastapi` only in `requirements.txt`
            text = (folder / "pyproject.toml").read_text(encoding="utf-8")
            (folder / "pyproject.toml").write_text(text.replace('dependencies = ["fastapi[standard]==0.165.0"]', "dependencies = []"),
                                                   encoding="utf-8", newline="\n")
        out[name] = folder
    return out


FOLDERS = _folders() if LOCAL else {"fixture": None, **{name: None for name in OTHER_IMAGES}}


def _plan(folder: pathlib.Path) -> dict:
    return json.loads(subprocess.run([os.environ.get("DAODAN_PYTHON", "python"), str(HERE / "plan.py"), str(folder)], capture_output=True,
                                     text=True, check=True, encoding="utf-8", env={**os.environ, "DAODAN_CONTAINER": "off"}).stdout)


PLANS = {name: _plan(folder) for name, folder in FOLDERS.items()} if LOCAL else None
STATE = PLANS["fixture"]["state"] if LOCAL else "/daodan/state"
PY = f"{PLANS['fixture']['venvs']}/./bin/python" if LOCAL else ""  # the root folder's environment, `container_runner._python`


def _image(name: str) -> modal.Image:
    if not LOCAL:
        return modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
    plan = PLANS[name]
    state, inputs = plan["state"], plan["inputs"]
    image = modal.Image.from_registry(plan["image"], add_python="3.12").run_commands(f"mkdir -p {inputs}")
    # the Noir `entry_points/noir.py` pins, to compare it with the framework's routes (`noir` variant, `real_summary.py`)
    image = image.run_commands(f"curl -fsSL -o /usr/local/bin/noir {apps.NOIR[0]} && echo '{apps.NOIR[1]}  /usr/local/bin/noir' | sha256sum -c - && chmod +x /usr/local/bin/noir")
    for url, sha, file in plan["files"]:
        if url:  # a download of the runner (`uv`), checked by its sha256 as the runner does
            image = image.run_commands(f"curl -fsSL {shlex.quote(url)} -o {inputs}/{file} && echo '{sha}  {inputs}/{file}' | sha256sum -c -")
        else:  # Daodan's own file, beside the premap modules
            image = image.add_local_file(REPO / "daodan/core/premap" / file, f"{inputs}/{file}", copy=True)
    env = " ".join(f"{k}={shlex.quote(v)}" for k, v in plan["env"].items())
    setup = shlex.quote(plan["setup"]["argv"][2])
    return (image.add_local_dir(FOLDERS[name], "/fix", copy=True, ignore=["**/__pycache__/**", "**/.venv/**"])
            # the runner's setup, run as the runner runs it (`sh -c`, its environment, the project's folder, which is `/work`); a failed
            # restore does not fail the build (the restore line ends in `true`): its standard error, exit code and seconds are kept
            .run_commands(f"mkdir -p {state} {WORK} && cp -a /fix/. {WORK}/ && cd {WORK} && s=$(date +%s) && "
                          f"env -i {env} sh -c {setup} 2> {state}/setup.stderr; echo $? > {state}/setup.exit; "
                          f"echo $(( $(date +%s) - s )) > {state}/setup.seconds"))


IMAGES = {name: _image(name) for name in FOLDERS}
app = modal.App("fastapi-routes")

RSS = ("import resource, subprocess, sys\n"
       "code = subprocess.run(sys.argv[2:]).returncode\n"
       "open(sys.argv[1], 'w').write(str(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss))\n"
       "sys.exit(code)\n")
ENVIRONMENT = (
    "import importlib.metadata as m, os, sys, sysconfig\n"
    "paths = sysconfig.get_paths()\n"
    "def version(name):\n"
    "    try:\n"
    "        return m.version(name)\n"
    "    except m.PackageNotFoundError:\n"
    "        return None\n"
    "print(repr({'version': sys.version, 'executable': sys.executable, 'prefix': sys.prefix, 'base_prefix': sys.base_prefix,\n"
    "            'purelib': paths['purelib'], 'platlib': paths['platlib'], 'stdlib': paths['stdlib'],\n"
    "            'fastapi': version('fastapi'), 'fastapi-cli': version('fastapi-cli'), 'starlette': version('starlette'),\n"
    "            'uvicorn': version('uvicorn'), 'pydantic': version('pydantic'),\n"
    "            'fastapi-cli requires': m.requires('fastapi-cli') if version('fastapi-cli') else None,\n"
    "            'fastapi requires': m.requires('fastapi'),\n"
    "            'packages': sorted(f\"{d.metadata['Name']} {d.version}\" for d in m.distributions())}))\n")
# the official material, printed whole: the installed source of fastapi-cli's loader, and what the `fastapi` command says of itself
CLI_SOURCE = (
    "import importlib, inspect, pathlib\n"
    "import fastapi_cli\n"
    "root = pathlib.Path(fastapi_cli.__file__).parent\n"
    "print('FILES', sorted(p.relative_to(root).as_posix() for p in root.rglob('*.py')))\n"
    "for rel in ('discover.py', 'config.py', 'cli.py', 'exceptions.py'):\n"
    "    print('=====', rel)\n"
    "    print((root / rel).read_text(encoding='utf-8'))\n"
    "import fastapi\n"
    "print('=====', 'fastapi/cli.py')\n"
    "print((pathlib.Path(fastapi.__file__).parent / 'cli.py').read_text(encoding='utf-8'))\n")
# the route classes of Starlette and FastAPI: the parts of their source that set the attributes the script reads
API_SOURCE = (
    "import inspect\n"
    "import fastapi, starlette\n"
    "from fastapi import applications, routing as froute\n"
    "from starlette import routing as sroute\n"
    "print('versions', fastapi.__version__, starlette.__version__)\n"
    "def show(label, obj):\n"
    "    print('=====', label)\n"
    "    print(inspect.getsource(obj))\n"
    "for label, obj in (('starlette.routing.compile_path', sroute.compile_path), ('starlette.routing.replace_params', sroute.replace_params),\n"
    "                   ('starlette.routing.Route.__init__', sroute.Route.__init__), ('starlette.routing.WebSocketRoute.__init__', sroute.WebSocketRoute.__init__),\n"
    "                   ('starlette.routing.Mount.__init__', sroute.Mount.__init__), ('starlette.routing.Mount.routes', sroute.Mount.routes),\n"
    "                   ('starlette.routing.Host.__init__', sroute.Host.__init__), ('starlette.routing.Host.routes', sroute.Host.routes),\n"
    "                   ('fastapi.routing.APIRoute.__init__', froute.APIRoute.__init__),\n"
    "                   ('fastapi.routing.APIWebSocketRoute.__init__', froute.APIWebSocketRoute.__init__),\n"
    "                   ('fastapi.routing.APIRouter.add_api_route', froute.APIRouter.add_api_route),\n"
    "                   ('fastapi.routing.APIRouter.include_router', froute.APIRouter.include_router),\n"
    "                   ('fastapi.applications.FastAPI.setup', applications.FastAPI.setup)):\n"
    "    try:\n"
    "        show(label, obj)\n"
    "    except (OSError, TypeError) as error:\n"
    "        print('=====', label, 'NO SOURCE', type(error).__name__, error)\n"
    "print('=====', 'FastAPI.__init__ signature')\n"
    "print(inspect.signature(applications.FastAPI.__init__))\n")

# how FastAPI 0.165 keeps an included router: `include_router` appends an object, it no longer copies the routes
ROUTING_SOURCE = (
    "import inspect\n"
    "import fastapi.routing as r\n"
    "import fastapi.openapi.utils as u\n"
    "names = [n for n in dir(r) if any(w in n for w in ('Include', 'Context', 'iter_routes', 'flatten', 'mark_routes', 'Route'))]\n"
    "print('NAMES', names)\n"
    "print('APIRouter members', [n for n in dir(r.APIRouter) if not n.startswith('__')])\n"
    "for n in names:\n"
    "    obj = getattr(r, n)\n"
    "    if getattr(obj, '__module__', None) != 'fastapi.routing':\n"
    "        continue\n"
    "    print('=====', n)\n"
    "    try:\n"
    "        print(inspect.getsource(obj))\n"
    "    except (OSError, TypeError) as error:\n"
    "        print('NO SOURCE', error)\n"
    "for n in ('get_openapi',):\n"
    "    print('=====', n)\n"
    "    print(inspect.getsource(getattr(u, n)))\n"
    "print('=====', 'APIRouter.routes', inspect.getattr_static(r.APIRouter, 'routes', None))\n")
# the application as the CLI's own functions load it, and what its routes are
DUMP = (
    "import sys\n"
    "from fastapi_cli.config import FastAPIConfig\n"
    "from fastapi_cli.discover import get_import_data, get_import_data_from_import_string\n"
    "config = FastAPIConfig.resolve()\n"
    "data = get_import_data_from_import_string(config.entrypoint, config.from_pyproject) if config.entrypoint else get_import_data()\n"
    "print('CONFIG', config)\n"
    "print('IMPORT', data)\n"
    "from uvicorn.importer import import_from_string\n"
    "app = import_from_string(data.import_string)\n"
    "print('APP', type(app), 'root_path', repr(app.root_path), 'urls', app.openapi_url, app.docs_url, app.redoc_url, app.swagger_ui_oauth2_redirect_url)\n"
    "def public(o):\n"
    "    return [n for n in dir(o) if not n.startswith('_')]\n"
    "def show(route, indent=''):\n"
    "    kind = type(route).__module__ + '.' + type(route).__qualname__\n"
    "    print(indent + kind, [c.__name__ for c in type(route).__mro__][:5], 'path=', getattr(route, 'path', None))\n"
    "    print(indent + '  attrs', public(route))\n"
    "print('same list', app.routes is app.router.routes, len(app.routes))\n"
    "for i, route in enumerate(app.routes):\n"
    "    show(route)\n")
OPENAPI = (
    "import json\n"
    "from fastapi_cli.config import FastAPIConfig\n"
    "from fastapi_cli.discover import get_import_data, get_import_data_from_import_string\n"
    "from uvicorn.importer import import_from_string\n"
    "config = FastAPIConfig.resolve()\n"
    "data = get_import_data_from_import_string(config.entrypoint, config.from_pyproject) if config.entrypoint else get_import_data()\n"
    "app = import_from_string(data.import_string)\n"
    "try:\n"
    "    schema = app.openapi()\n"
    "    print(json.dumps({path: {m: o.get('operationId') for m, o in item.items()} for path, item in schema['paths'].items()}, indent=1))\n"
    "except BaseException as error:\n"
    "    print('OPENAPI FAILED', type(error).__name__, str(error)[:300])\n")
# the route contexts FastAPI 0.137.2 gives to read the routes of an application whose routers are included (`routing.iter_route_contexts`)
CONTEXTS = (
    "import inspect\n"
    "from fastapi import routing\n"
    "from fastapi_cli.config import FastAPIConfig\n"
    "from fastapi_cli.discover import get_import_data, get_import_data_from_import_string\n"
    "from uvicorn.importer import import_from_string\n"
    "config = FastAPIConfig.resolve()\n"
    "data = get_import_data_from_import_string(config.entrypoint, config.from_pyproject) if config.entrypoint else get_import_data()\n"
    "app = import_from_string(data.import_string)\n"
    "print('ALL', getattr(routing, '__all__', None))\n"
    "print(inspect.getsource(routing.iter_route_contexts))\n"
    "def line(prefix, ctx):\n"
    "    convertors = {k: type(v).__name__ for k, v in (getattr(ctx, 'param_convertors', None) or {}).items()}\n"
    "    endpoint = getattr(ctx, 'endpoint', None)\n"
    "    print(prefix, type(ctx).__name__, type(ctx.route).__name__, type(ctx.original_route).__name__, repr(ctx.path), repr(ctx.path_format), sorted(ctx.methods or []) if ctx.methods is not None else None, getattr(endpoint, '__qualname__', type(endpoint).__name__), convertors)\n"
    "def walk(routes, prefix=''):\n"
    "    for ctx in routing.iter_route_contexts(routes):\n"
    "        line(prefix, ctx)\n"
    "        inner = getattr(ctx.route, 'routes', None)\n"
    "        if type(ctx.route).__name__ in ('Mount', 'Host'):\n"
    "            print(prefix + '   app', type(ctx.route.app).__module__ + '.' + type(ctx.route.app).__qualname__, 'routes of it:', None if inner is None else len(inner))\n"
    "            if inner:\n"
    "                walk(inner, prefix + '      ')\n"
    "walk(app.routes)\n")
HANGS = "import time\ntime.sleep(120)\n"
SMALL = "from fastapi import FastAPI\n\napp = FastAPI()\n\n\n@app.get('/x')\ndef x():\n    return 'x'\n"
THREAD = "import threading\nimport time\n" + SMALL + "\n\nthreading.Thread(target=time.sleep, args=(100000,)).start()\n"
ATEXIT = "import atexit\n" + SMALL + "\n\natexit.register(lambda: print('goodbye'))\n"
REPLACED = "import io\nimport sys\n" + SMALL + "\n\nsys.stdout = io.StringIO()\n"
API_NAME = "from fastapi import FastAPI\n\napi = FastAPI()\n\n\n@api.get('/by-api')\ndef by_api():\n    return 'api'\n"
OTHER_NAME = "from fastapi import FastAPI\n\nserver = FastAPI()\n\n\n@server.get('/by-server')\ndef by_server():\n    return 'server'\n"
TWO_APPS = ("from fastapi import FastAPI\n\nfirst = FastAPI()\nsecond = FastAPI()\n\n\n@first.get('/one')\ndef one():\n    return 1\n\n\n"
            "@second.get('/two')\ndef two():\n    return 2\n")
WRAPPED = ("from fastapi import FastAPI\nfrom starlette.middleware.cors import CORSMiddleware\n\ninner = FastAPI()\n\n\n@inner.get('/inner')\n"
           "def served():\n    return 'inner'\n\n\napp = CORSMiddleware(inner, allow_origins=['*'])\n")
NO_APP = "def not_an_app():\n    return 1\n"
OTHER = ("from fastapi import FastAPI\n\nservice = FastAPI()\nplain = 'text'\n\n\n@service.get('/other')\ndef other():\n    return 'other'\n")
DOCS_OFF = ("from fastapi import FastAPI\n\napp = FastAPI(docs_url=None, redoc_url=None)\n\n\n@app.get('/docs')\ndef my_docs():\n    return 'mine'\n")
ROOT_PATH = "from fastapi import FastAPI\n\napp = FastAPI(root_path='/proxy')\n\n\n@app.get('/x')\ndef x():\n    return 'x'\n"
LIFESPAN = ("import contextlib\nimport pathlib\n\nfrom fastapi import FastAPI\n\n\n@contextlib.asynccontextmanager\nasync def lifespan(app):\n"
            "    pathlib.Path('lifespan-ran').write_text('x')\n    yield\n\n\napp = FastAPI(lifespan=lifespan)\n\n\n@app.get('/x')\ndef x():\n    return 'x'\n")
EMPTY = "from fastapi import FastAPI\n\napp = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)\n"
HOST = ("\n\nhost_app = FastAPI()\n\n\n@host_app.get('/hosted')\ndef hosted():\n    return 'hosted'\n\n\napp.router.host('api.example.com', host_app)\n")
FRONTEND = "\n\napp.frontend('/ui', directory='static')\n"
STRANGE = ("\n\nfrom pydantic import BaseModel, ConfigDict\n\n\nclass Opaque:\n    pass\n\n\nclass Strange(BaseModel):\n"
           "    model_config = ConfigDict(arbitrary_types_allowed=True)\n    thing: Opaque\n\n\n@app.post('/strange')\ndef strange(body: Strange):\n    return {}\n")
MANY = ("from fastapi import APIRouter, FastAPI\n\napp = FastAPI()\nrouter = APIRouter(prefix='/included')\n\n\ndef make(n):\n    def view(id: int):\n"
        "        return n\n\n    return view\n\n\nfor n in range(3000):\n    app.add_api_route(f'/r{n}/{{id}}', make(n), methods=['GET', 'POST'])\n"
        "for n in range(1000):\n    router.add_api_route(f'/s{n}/{{id}}', make(n), methods=['GET'])\napp.include_router(router)\n")
# what Starlette's own matcher answers to a request, to set beside what the convertor classes say: the status of each (the application is
# called, its lifespan is not run)
MATCHES = (
    "from fastapi_cli.config import FastAPIConfig\n"
    "from fastapi_cli.discover import get_import_data, get_import_data_from_import_string\n"
    "from uvicorn.importer import import_from_string\n"
    "from starlette.testclient import TestClient\n"
    "config = FastAPIConfig.resolve()\n"
    "data = get_import_data_from_import_string(config.entrypoint, config.from_pyproject) if config.entrypoint else get_import_data()\n"
    "client = TestClient(import_from_string(data.import_string), raise_server_exceptions=False, follow_redirects=False)\n"
    "for path in ('/typed/7', '/typed/a', '/files/a', '/files/a/b', '/slug/a-b', '/slug/a/b', '/pair/a/b', '/pair/a', '/two/1/2', '/two/1',\n"
    "             '/glued/x-y', '/strict/', '/strict', '/loose', '/loose/', '/api/users/7', '/api/users/7/8', '/api/users/embedded/leaf',\n"
    "             '/api/embedded/leaf',\n"
    "             '/t/acme/info', '/t/acme/b/info', '/sub/hello', '/static/hello.txt'):\n"
    "    response = client.get(path)\n"
    "    print(path, '->', response.status_code, response.headers.get('location', ''))\n")


def _rename(old: str, new: str):
    return lambda p: (p / old).rename(p / new)


def _write(name: str, text: str):
    return lambda p: (p / name).write_text(text, encoding="utf-8", newline="\n")


def _no_tool(p):
    """The fixture without `[tool.fastapi]`: the CLI looks for the application by its default paths."""
    text = (p / "pyproject.toml").read_text(encoding="utf-8")
    (p / "pyproject.toml").write_text(text.split("[tool.fastapi]")[0], encoding="utf-8", newline="\n")


def _entrypoint(value: str):
    def edit(p):
        text = (p / "pyproject.toml").read_text(encoding="utf-8")
        (p / "pyproject.toml").write_text(text.replace('entrypoint = "app.main:app"', f'entrypoint = "{value}"'), encoding="utf-8", newline="\n")
    return edit


def _both(*edits):
    return lambda p: [edit(p) for edit in edits]


def _main(function):
    """Edit `app/main.py` with `function(text)`."""
    return lambda p: (p / "app/main.py").write_text(function((p / "app/main.py").read_text(encoding="utf-8")), encoding="utf-8", newline="\n")


def _remove(name: str):
    return lambda p: shutil.rmtree(p / name)


# variant -> (image, what runs, environment added to the runner's, how the copy of the project is edited)
VARIANTS = {
    "environment": ("fixture", "environment", {}, None),
    "cli-source": ("fixture", "snippet:CLI_SOURCE", {}, None),
    "api-source": ("fixture", "snippet:API_SOURCE", {}, None),
    "routing-source": ("fixture", "snippet:ROUTING_SOURCE", {}, None),
    "cli-help": ("fixture", "cli:--help", {}, None),
    "cli-dev-help": ("fixture", "cli:dev --help", {}, None),
    "cli-run-help": ("fixture", "cli:run --help", {}, None),
    "dump": ("fixture", "snippet:DUMP", {}, None),
    "openapi": ("fixture", "snippet:OPENAPI", {}, None),
    "contexts": ("fixture", "snippet:CONTEXTS", {}, None),
    "matches": ("fixture", "snippet:MATCHES", {}, None),
    "plain-environment": ("plain", "environment", {}, None),
    "old-environment": ("old", "environment", {}, None),
    "mid-environment": ("mid", "environment", {}, None),
    "old-dump": ("old", "snippet:DUMP", {}, None),
    "old-openapi": ("old", "snippet:OPENAPI", {}, None),
    # the script, on the fixture: where the application is found
    "routes": ("fixture", "script", {}, None),
    "noir": ("fixture", "noir", {}, None),
    "no-entrypoint": ("fixture", "script", {}, _no_tool),
    "main-py": ("fixture", "script", {}, _both(_no_tool, _write("main.py", "from app.main import app\n"))),
    "api-name": ("fixture", "script", {}, _both(_no_tool, _write("main.py", API_NAME))),
    "other-name": ("fixture", "script", {}, _both(_no_tool, _write("main.py", OTHER_NAME))),
    "two-apps": ("fixture", "script", {}, _both(_no_tool, _write("main.py", TWO_APPS))),
    "wrapped": ("fixture", "script", {}, _both(_no_tool, _write("main.py", WRAPPED))),
    "no-app": ("fixture", "script", {}, _both(_no_tool, _write("main.py", NO_APP))),
    "no-main": ("fixture", "script", {}, _both(_no_tool, _remove("app"))),
    "entrypoint-other": ("fixture", "script", {}, _both(_entrypoint("other:service"), _write("other.py", OTHER))),
    "entrypoint-missing": ("fixture", "script", {}, _entrypoint("nothing:app")),
    "entrypoint-not-app": ("fixture", "script", {}, _both(_entrypoint("other:plain"), _write("other.py", OTHER))),
    # how it does not load
    "module-raises": ("fixture", "script", {}, _write("app/main.py", "raise RuntimeError('boom')\n")),
    "missing-package": ("fixture", "script", {}, _write("app/main.py", "import not_installed\n")),
    "module-prints": ("fixture", "script", {}, _main(lambda text: "print('main loaded')\n" + text)),
    "module-hangs": ("fixture", "hangs", {}, _write("app/main.py", HANGS)),
    # after the JSON: a thread that never ends, a print at exit, a project that replaces `sys.stdout`
    "thread": ("fixture", "hangs", {}, _write("app/main.py", THREAD)),
    "atexit-print": ("fixture", "script", {}, _write("app/main.py", ATEXIT)),
    "replaced-stdout": ("fixture", "script", {}, _write("app/main.py", REPLACED)),
    # what the application is
    "docs-off": ("fixture", "script", {}, _write("app/main.py", DOCS_OFF)),
    "root-path": ("fixture", "script", {}, _write("app/main.py", ROOT_PATH)),
    "lifespan": ("fixture", "script", {}, _write("app/main.py", LIFESPAN)),
    "empty": ("fixture", "script", {}, _write("app/main.py", EMPTY)),
    "host": ("fixture", "script", {}, _main(lambda text: text + HOST)),
    "frontend": ("fixture", "script", {}, _main(lambda text: text + FRONTEND)),  # FastAPI's own static front end: a route of a class that is not Starlette's
    "many-routes": ("fixture", "script", {}, _write("app/main.py", MANY)),  # 3000 routes with two methods and 1000 included: time and memory, not recorded
    "openapi-fails-routes": ("fixture", "script", {}, _main(lambda text: text + STRANGE)),
    "openapi-fails-openapi": ("fixture", "snippet:OPENAPI", {}, _main(lambda text: text + STRANGE)),
    # the other environments
    "plain-routes": ("plain", "script", {}, None),
    "old-routes": ("old", "script", {}, None),
    "mid-routes": ("mid", "script", {}, None),
}
RECORDED = ("routes", "no-entrypoint", "main-py", "api-name", "other-name", "two-apps", "wrapped", "no-app", "no-main", "entrypoint-other",
            "entrypoint-missing", "entrypoint-not-app", "module-raises", "missing-package", "module-prints", "module-hangs", "thread",
            "atexit-print", "replaced-stdout", "docs-off", "root-path", "lifespan", "empty", "host", "openapi-fails-routes", "plain-routes",
            "old-routes", "mid-routes", "matches", "frontend")
# the variants whose output is the point: kept whole in `results/`
FULL = ("noir", "cli-source", "api-source", "routing-source", "dump", "openapi", "contexts", "matches", "old-dump", "old-openapi", "openapi-fails-openapi")


def _listing(root: str) -> dict[str, int]:
    out = {}
    for directory, _names, files in os.walk(root):
        for f in files:
            path = os.path.join(directory, f)
            out[os.path.relpath(path, root).replace("\\", "/")] = os.path.getsize(path)
    return out


def _run(name: str, argv: list[str], env: dict[str, str], state: str, cwd: str) -> dict:
    import shutil
    import sys
    import time

    edit = VARIANTS[name][3]
    work = pathlib.Path(WORK)
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree("/fix", work)
    if edit:
        edit(work)
    os.makedirs(env["HOME"], exist_ok=True)
    before = _listing(WORK)
    mark = f"/tmp/rss-{name}"
    started = time.monotonic()
    r = subprocess.run([sys.executable, "-c", RSS, mark, *argv], cwd=work / cwd, capture_output=True, text=True, timeout=600,
                       stdin=subprocess.DEVNULL, env=env)
    seconds = round(time.monotonic() - started, 2)
    after = _listing(WORK)
    answer = {"variant": name, "argv": argv, "cwd": cwd, "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr,
              "seconds": seconds, "max_rss_mb": round(int(pathlib.Path(mark).read_text()) / 1024, 1) if os.path.exists(mark) else None,
              "left_in_the_project": sorted(set(after) - set(before)),
              "changed_in_the_project": sorted(f for f in set(after) & set(before) if after[f] != before[f])}
    if name.endswith("environment"):  # what the setup of the image did: its exit code, its seconds, what it wrote on the standard error
        answer["setup"] = {k: pathlib.Path(f"{state}/setup.{k}").read_text(encoding="utf-8").strip() for k in ("exit", "seconds", "stderr")}
    return answer


def _runner(folder: str):
    """The Modal function that runs a variant in the image of `folder`: one each, their names are their own."""
    def run(name: str, argv: list[str], env: dict[str, str], state: str, cwd: str) -> dict:
        return _run(name, argv, env, state, cwd)
    run.__name__ = run.__qualname__ = "run_" + folder.replace("-", "_")
    globals()[run.__name__] = function = app.function(image=IMAGES[folder], timeout=900, block_network=True)(run)
    return function


RUNNERS = {folder: _runner(folder) for folder in FOLDERS}


def _with_seconds(argv: list[str], seconds: str) -> list[str]:
    """The command with another limit: the one element that is only digits (`timeout`'s)."""
    at = next(i for i, word in enumerate(argv) if word.isdigit())
    return [*argv[:at], seconds, *argv[at + 1:]]


def _argv(folder: str, kind: str) -> tuple[list[str], str]:
    py = f"{PLANS[folder]['venvs']}/./bin/python"
    if kind == "environment":
        return [py, "-c", ENVIRONMENT], "."
    if kind == "noir":
        return ["noir", "scan", WORK, "-f", "json", "--no-log"], "."
    if kind.startswith("snippet:"):
        return [py, "-I", "-c", globals()[kind.partition(":")[2]]], "."
    if kind.startswith("cli:"):
        return [os.path.dirname(py) + "/fastapi", *kind.partition(":")[2].split()], "."
    [command, *_] = PLANS[folder]["commands"] or [None]
    if command is None:
        raise SystemExit(f"{folder}: the source gives no command for this folder")
    argv, cwd = list(command["argv"]), command["cwd"]
    if kind == "script":
        return argv, cwd
    if kind == "hangs":
        return _with_seconds(argv, "5"), cwd
    raise SystemExit(f"unknown kind {kind}")


def _recorded(answers: dict) -> None:
    RECORDED_DIR.mkdir(parents=True, exist_ok=True)
    for name in RECORDED:
        a = answers[name]
        (RECORDED_DIR / f"{name}.json").write_text(
            json.dumps({k: a[k] for k in ("returncode", "stdout", "stderr")}, indent=1) + "\n", encoding="utf-8", newline="\n")
    premap = REPO / "daodan/core/premap"
    prints = {name: hashlib.sha256((premap / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in SCRIPTS}
    (RECORDED_DIR / "script.json").write_text(json.dumps({**prints, "version": PLANS["fixture"]["version"]}, indent=1) + "\n", encoding="utf-8", newline="\n")


@app.local_entrypoint()
def main(only: str = "", label: str = ""):
    OUT.mkdir(exist_ok=True)
    out = OUT / label if label else OUT
    out.mkdir(exist_ok=True)
    chosen = set(only.split(",")) if only else set(VARIANTS)  # `--only environment,cli-source`: some variants, nothing recorded
    answers = {}
    for folder, runner in RUNNERS.items():
        calls = []
        for name, (where, kind, env, _edit) in VARIANTS.items():
            if where == folder and name in chosen:
                argv, cwd = _argv(folder, kind)
                calls.append((name, argv, {**PLANS[folder]["env"], **env}, PLANS[folder]["state"], cwd))
        for answer in (runner.starmap(calls) if calls else ()):
            answers[answer["variant"]] = answer
            limit = None if answer["variant"] in FULL else 20000
            kept = {**answer, "stdout": answer["stdout"][:limit], "stdout_chars": len(answer["stdout"])}  # the answer in full is in `RECORDED`
            (out / f"{answer['variant']}.json").write_text(json.dumps(kept, indent=1), encoding="utf-8", newline="\n")
    if not only and not label and RECORDED:
        _recorded(answers)
    print(json.dumps({v: [a["returncode"], a["seconds"], a["max_rss_mb"]] for v, a in answers.items()}, indent=1))
