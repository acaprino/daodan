"""SmoothUI's build on Modal: `npm ci` and `npm run build` in a Node container, nothing on this PC.

    MODAL_CONFIG_PATH="C:/Users/alfio/.modal.toml" modal run prototypes/daodan-app/smoothui/modal_build.py

This builds the historical prototype in isolation. Its outputs live beside its source.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
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
    """Rebuild the static assets used by the prototype."""
    shutil.copytree("/smoothui", WORK)
    for command in (["npm", "ci", "--no-audit", "--no-fund"], ["npm", "run", "build"]):
        print("$", " ".join(command), flush=True)
        subprocess.run(command, cwd=WORK, check=True)
    return {name: (WORK / name).read_bytes() for name in FILES}


@app.local_entrypoint()
def main():
    for name, data in build.remote().items():
        (HERE / name).write_bytes(data)
