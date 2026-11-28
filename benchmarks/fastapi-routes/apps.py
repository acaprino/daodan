"""The real public FastAPI applications `modal_real.py` runs and `real_summary.py` reads: where they are, at which commit, under which licence,
and how to fetch their sources as text on the host. Nothing of them is in the repository: the sources are fetched at the pinned commit into a
folder outside it (here, and in the image `modal_real.py` builds) and never run on this machine.
"""
import io
import pathlib
import tarfile
import urllib.request

# name -> repository, commit, licence (GitHub's SPDX id, checked against the repository's LICENSE file), the folder that is the project, why it is here
APPS = {
    "template": ("fastapi/full-stack-fastapi-template", "77e550a73bb49dd2967622c5ed11bf7a49603c93", "MIT", "",
                 "`app.include_router(api_router, prefix=settings.API_V1_STR)`, a router that includes routers with their own prefixes, a lifespan, "
                 "dependencies on endpoints; a uv workspace (`backend/` under a root `pyproject.toml` and `uv.lock`), Python 3.14"),
    "users": ("fastapi-users/fastapi-users", "e9c57ff7ff2fd385bb0f6f795b524e9736b64290", "MIT", "examples/sqlalchemy",
              "every router is made by a factory of a library (`fastapi_users.get_auth_router(...)`, `get_users_router(...)`) and included with a prefix; "
              "`fastapi` declared without `[standard]`"),
}
NOIR = ("https://github.com/owasp-noir/noir/releases/download/v1.5.0/noir-v1.5.0-linux-x86_64",  # `entry_points/noir.py` DOWNLOAD
        "4e176c92ee16f60fafd3be7ea6f605d82d3f27c39704a3f875cbed5bd050dc70")


def fetch(name: str, root: pathlib.Path) -> pathlib.Path:
    """The project of `name` at its commit, as text, into `root/<name>` (the repository's tree, then the folder that is the project): untrusted,
    only read, never run."""
    repository, commit, _, folder, _ = APPS[name]
    whole = root / f"{name}-tree"
    if not whole.exists():
        data = urllib.request.urlopen(f"https://codeload.github.com/{repository}/tar.gz/{commit}", timeout=300).read()
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            members = archive.getmembers()
            top = members[0].name.split("/")[0]
            for member in members:
                member.name = member.name[len(top):].lstrip("/")
            whole.mkdir(parents=True)
            archive.extractall(whole, members=[member for member in members if member.name and (member.isfile() or member.isdir())], filter="data")  # links are no text
    return whole / folder if folder else whole
