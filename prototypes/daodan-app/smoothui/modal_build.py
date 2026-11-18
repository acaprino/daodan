"""SmoothUI's build on Modal: `npm ci` and `npm run build` in a Node container, nothing on this PC.

    MODAL_CONFIG_PATH="C:/Users/alfio/.modal.toml" modal run prototypes/daodan-app/smoothui/modal_build.py

The container gets this folder without node_modules and builds both entries of build.mjs; the entrypoint writes the
app's files to plugins/codebase-map/assets/app when the build changed them (smoothui.bundle.js and its licence notices)
and keeps smoothui.css unless the build adds a class. The mockup's own bundle stays as committed.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
ASSETS = "plugins/codebase-map/assets/app"  # where build.mjs writes the app's bundle, from the checkout's root
WORK = Path("/build/prototypes/daodan-app/smoothui")  # the checkout's layout, so that build.mjs's paths hold
FILES = ("smoothui.bundle.js", "smoothui.bundle.js.LEGAL.txt", "smoothui.css")
# Daodan's Node (`preparation.NODE`), checked by its sha256.
NODE = ("https://nodejs.org/dist/v24.22.3/node-v24.22.3-linux-x64.tar.gz",
        "061ec3e3062115705b56b51fa9cc330ab50d34b6969387d4e4b1a50c6809acc2")
FETCH_NODE = ("python -c \"import hashlib, urllib.request; data = urllib.request.urlopen('%s').read(); "
              "assert hashlib.sha256(data).hexdigest() == '%s'; open('/tmp/node.tar.gz', 'wb').write(data)\"" % NODE)
image = (modal.Image.debian_slim(python_version="3.13")
         .run_commands(FETCH_NODE, "tar -xzf /tmp/node.tar.gz -C /opt && rm /tmp/node.tar.gz",
                       "ln -s /opt/node-v24.22.3-linux-x64/bin/node /usr/local/bin/node",
                       "ln -s /opt/node-v24.22.3-linux-x64/bin/npm /usr/local/bin/npm"))
if (HERE / "package-lock.json").is_file():  # on this PC; in the container the folder is already in the image
    image = image.add_local_dir(HERE, "/smoothui", ignore=["**/node_modules/**", "**/__pycache__/**"])
app = modal.App("daodan-smoothui-build", image=image)


@app.function(timeout=900)
def build() -> dict:
    """The app's built files by name: the bundle from build.mjs's second entry, smoothui.css from Tailwind."""
    shutil.copytree("/smoothui", WORK)
    for command in (["npm", "ci", "--no-audit", "--no-fund"], ["npm", "run", "build"]):
        print("$", " ".join(command), flush=True)
        subprocess.run(command, cwd=WORK, check=True)
    built = {name: WORK.parents[2] / ASSETS / name for name in FILES[:2]} | {"smoothui.css": WORK / "smoothui.css"}
    return {name: path.read_bytes() for name, path in built.items()}


def classes(css: bytes) -> set:
    return set(re.findall(rb"\.((?:\\.|[\w-])+)", css))


@app.local_entrypoint()
def main():
    target = HERE.parents[2] / ASSETS
    built = build.remote()
    css = built.pop("smoothui.css")
    for name, data in built.items():
        path = target / name
        same = path.is_file() and path.read_bytes() == data
        if not same:
            path.write_bytes(data)
        print(f"{name}: {len(data)} bytes, {'unchanged' if same else 'written'}")
    # Tailwind's scan finds fewer candidates in the container than where the committed stylesheet was made, whose
    # theme variables the app's styles read: the app's copy stays unless the build adds a class it lacks.
    added = classes(css) - classes((target / "smoothui.css").read_bytes())
    if added:
        raise SystemExit(f"smoothui.css not written: the build adds {sorted(added)}; merge them into the app's copy")
    print(f"smoothui.css: kept, the build ({len(css)} bytes) adds no class")
