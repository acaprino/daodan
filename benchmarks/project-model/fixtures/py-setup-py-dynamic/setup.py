import os
import platform

from setuptools import setup


def requirements():
    reqs = ["requests"]
    if platform.system() == "Windows":
        reqs.append("pywin32>=300")
    reqs += [r for r in os.environ.get("DYN_EXTRAS", "").split(",") if r]
    return reqs


setup(
    name="dyn-pkg",
    version="0.4.0",
    packages=["dyn_pkg"],
    install_requires=requirements(),
)
