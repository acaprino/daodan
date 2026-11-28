"""The real public Flask applications `modal_real.py` runs and `real_summary.py` reads: where they are, at which commit, under which licence,
and how to fetch their sources as text on the host. Nothing of them is in the repository: the sources are fetched at the pinned commit into a
folder outside it (here, and in the image `modal_real.py` builds) and never run on this machine.
"""
import io
import pathlib
import tarfile
import urllib.request

# name -> repository, commit, licence (GitHub's SPDX id, checked against the repository's LICENSE file), the folder that is the project, why it is here
APPS = {
    "ctfd": ("CTFd/CTFd", "f9fa28b2f17b22ec6c631a5b745f47573966f7f2", "Apache-2.0", "",
             "an application factory (`create_app`), Flask-RESTX namespaces, blueprints, plugins that register blueprints, decorators around views; "
             "a uv project (`uv.lock`) that asks for CPython 3.11 only"),
    "redash": ("getredash/redash", "f561a53dc55eeb3f20615be951560dc78bb23f4c", "BSD-2-Clause", "",
               "Flask-RESTful (`api.add_org_resource(...)`), blueprints, decorators around views; a uv project (`uv.lock`) that asks for CPython 3.13 only; "
               "the application is `redash/wsgi.py`, not a file at the root"),
    "microblog-api": ("miguelgrinberg/microblog-api", "e250d7115b47010ff0e7051d5868485fff4e32fb", "MIT", "",
                      "an application factory, `app.register_blueprint(users, url_prefix='/api')` (the prefix at registration), APIFairy (routes of an extension: "
                      "the documentation), decorators that take arguments; `FLASK_APP` only in `.flaskenv`"),
    "shhh": ("smallwat3r/shhh", "448acf4bed058d27a28a939b1ff5fba1601e2273", "MIT", "",
             "a `MethodView` added with `add_url_rule` and `as_view` to a blueprint that has a `url_prefix`, decorators made with `functools.partial`; "
             "a `requirements.txt` and a `wsgi.py` at the root"),
}
NOIR = ("https://github.com/owasp-noir/noir/releases/download/v1.5.0/noir-v1.5.0-linux-x86_64",  # `entry_points/noir.py` DOWNLOAD
        "4e176c92ee16f60fafd3be7ea6f605d82d3f27c39704a3f875cbed5bd050dc70")


def fetch(name: str, root: pathlib.Path) -> pathlib.Path:
    """The project of `name` at its commit, as text, into `root/<name>-tree` (the repository's tree), and the folder that is the project:
    untrusted, only read, never run."""
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
