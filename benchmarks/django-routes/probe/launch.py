"""Exploratory: which way of running the project's own `manage.py` gives the settings Django loaded, measured on Modal
(`benchmarks/django-routes/modal_probe.py`, kinds `launch-a`, `launch-b`, `launch-c`). The collector is one function; only how `manage.py` is
reached differs.

    a   `python manage.py shell -c "<runs this file>"`, descriptor 1 moved to the standard error by the shell (`exec 3>&1 1>&2`), the answer
        written to descriptor 3
    b   `python -I launch.py b` (cwd: the folder of manage.py): the script saves descriptor 1 itself, then runs manage.py through `runpy`
        with the argv `shell -c "<calls back into this file>"`
    c   `python -I launch.py c`: the script saves descriptor 1, replaces `django.core.management.execute_from_command_line` by its own
        function, and runs manage.py through `runpy` as `__main__`: manage.py sets the environment and calls it
"""
import json
import os
import resource
import runpy
import sys
import time

ANSWER = None


def collect():
    import django
    started = time.monotonic()
    django.setup()
    from django.conf import settings
    from django.urls import get_resolver
    top = get_resolver().url_patterns
    return {"settings_module": os.environ.get("DJANGO_SETTINGS_MODULE"), "settings_wrapped": settings.SETTINGS_MODULE,
            "root_urlconf": settings.ROOT_URLCONF, "top_level": len(top), "version": django.get_version(), "argv": sys.argv,
            "path0": sys.path[0], "setup_seconds": round(time.monotonic() - started, 3),
            "max_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)}


def deliver(fd):
    try:
        document = json.dumps({"called": True, **collect()})
    except BaseException as error:
        os.write(2, f"{type(error).__name__}: {error}\n".encode("utf-8", "replace"))
        os._exit(3)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        out.write(document)
    os._exit(0)


def main(mode):
    global ANSWER
    ANSWER = os.dup(1)
    os.dup2(2, 1)
    sys.path.insert(0, os.getcwd())  # what `python manage.py` does: the script's folder first
    if mode == "b":
        sys.modules["daodan_launch"] = sys.modules[__name__]
        sys.argv = ["manage.py", "shell", "-c", "import daodan_launch; daodan_launch.deliver(daodan_launch.ANSWER)"]
    else:
        import django.core.management as management
        management.execute_from_command_line = lambda argv=None: deliver(ANSWER)
        sys.argv = ["manage.py"]
    try:
        runpy.run_path("manage.py", run_name="__main__")
    except SystemExit as error:
        os.write(2, f"manage.py exited with {error.code}\n".encode())
        os._exit(5)
    except BaseException as error:
        os.write(2, f"{type(error).__name__}: {error}\n".encode("utf-8", "replace"))
        os._exit(3)
    os.write(2, b"manage.py did not run the command\n")
    os._exit(4)


if __name__ == "__main__":
    main(sys.argv[1])
elif __name__ == "a":
    deliver(3)
