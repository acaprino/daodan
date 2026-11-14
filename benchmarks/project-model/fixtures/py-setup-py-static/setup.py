from setuptools import find_packages, setup

setup(
    name="legacy-tool",
    version="1.0.2",
    packages=find_packages(where="lib"),
    package_dir={"": "lib"},
    install_requires=["requests>=2.20", "six"],
    extras_require={"yaml": ["PyYAML>=5.1"]},
    tests_require=["nose"],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["legacy=legacy_tool.cli:main"]},
)
