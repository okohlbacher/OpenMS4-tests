#!/usr/bin/env python3
"""Give every package the same picture of the graph.

Each package repository is standalone: it is cloned, built and released without the
parent, so it carries its own copy of the architecture figure and a generated section
that names its direct dependencies and its direct consumers. Both are derived from
``packages.lock.json`` and the packages' ``dependencies.lock.json`` files, so the
section cannot drift from the locks the build actually uses.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BEGIN, END = "<!-- package-graph:begin -->", "<!-- package-graph:end -->"

# The dependency names the packages use in their own locks, mapped to parent slugs.
DEPENDENCY_SLUGS = {
    "OpenMS": "core", "OpenMSCLI": "cli", "OpenMSTestData": "test-data",
    "OpenMSTOPP": "topp", "OpenMSFLASH": "flash", "OpenMSProSE": "prose",
    "pyopenms": "pyopenms", "FLASHTnT": "flashtnt",
}
ROLES = {
    "core": "scientific library, OpenSwathAlgo, readers and writers, runtime data, optional TestSupport",
    "cli": "TOPPBase, tool registration and discovery",
    "test-data": "versioned fixtures and the installed numerical suite",
    "topp": "123 console tools",
    "openswath": "19 executables and OpenSwathBase",
    "flash": "FLASHDeconv and the OpenMS::FLASH backend",
    "prose": "ProSE and the OpenMS::ProSE backend",
    "nuxl": "OpenNuXL",
    "nase": "NucleicAcidSearchEngine",
    "comet": "CometAdapter",
    "mascot": "MascotAdapterOnline",
    "database-suitability": "DatabaseSuitability",
    "proteomics-lfq": "ProteomicsLFQ",
    "parquet-diff": "ParquetDiff",
    "desktop": "GUI SDK, TOPPView, ImageCreator, INIFileEditor, TOPPAS, ExecutePipeline",
    "pyopenms": "nanobind bindings, installed module tree and repaired wheels",
    "flashtnt": "FLASHTnT tagging executable",
    "flashapp": "Streamlit application and Vue component",
}
PARENT = "https://github.com/okohlbacher/OpenMS4-tests"


def load_graph() -> tuple[dict, dict, dict]:
    lock = json.loads((ROOT / "packages.lock.json").read_text())["packages"]
    dependencies: dict[str, list[str]] = {}
    for slug, entry in lock.items():
        path = ROOT / entry["path"] / "dependencies.lock.json"
        if not path.exists():
            dependencies[slug] = []
            continue
        names = json.loads(path.read_text()).get("dependencies", {})
        dependencies[slug] = [DEPENDENCY_SLUGS[n] for n in names if n in DEPENDENCY_SLUGS]
    consumers = {slug: [s for s, deps in dependencies.items() if slug in deps] for slug in lock}
    return lock, dependencies, consumers


def link(slug: str, lock: dict) -> str:
    return f"[{lock[slug]['repository'].rsplit('/', 1)[-1]}]({lock[slug]['repository']})"


def section(slug: str, lock: dict, dependencies: dict, consumers: dict) -> str:
    deps, uses = dependencies[slug], consumers[slug]
    rows = "\n".join(f"| {link(other, lock)} | {'dependency' if other in deps else 'consumer'} "
                     f"| {ROLES[other]} |" for other in deps + uses)
    if deps:
        built = ("builds against the installed "
                 + ", ".join(f"**{o}**" for o in deps)
                 + " package" + ("s" if len(deps) > 1 else "")
                 + " at the revisions recorded in [`dependencies.lock.json`](dependencies.lock.json)")
    else:
        built = "has no OpenMS 4 dependency: it is the root of the graph"
    consumed = (", ".join(f"**{o}**" for o in uses) + " build" + ("s" if len(uses) == 1 else "")
                + " against it" if uses else "No other package builds against it")
    table = (f"\n| Repository | Relation | Contents |\n| --- | --- | --- |\n{rows}\n" if rows else "\n")
    return f"""{BEGIN}
## Where this package sits

![OpenMS 4 package architecture](docs/package-architecture.svg)

`{slug}` {built}. {consumed}.
{table}
The eighteen repositories are assembled by the parent repository
[OpenMS4-tests]({PARENT}), which holds the submodule pins (`packages.lock.json`), the
dependency-order build runner and the contract tests that keep the graph consistent.
[`docs/project-state.md`]({PARENT}/blob/main/docs/project-state.md) is the current state
of the whole project; [`docs/build-split-packages.md`]({PARENT}/blob/main/docs/build-split-packages.md)
reproduces the installed-SDK build.
{END}"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail instead of writing")
    args = parser.parse_args()

    lock, dependencies, consumers = load_graph()
    figure = ROOT / "docs" / "package-architecture.svg"
    stale = []
    for slug, entry in lock.items():
        package = ROOT / entry["path"]
        if not package.exists():
            continue
        target = package / "docs" / "package-architecture.svg"
        readme = package / "README.md"
        text = readme.read_text()
        block = section(slug, lock, dependencies, consumers)
        if BEGIN in text:
            head, rest = text.split(BEGIN, 1)
            text = head + block + rest.split(END, 1)[1]
        else:
            text = text.rstrip("\n") + "\n\n" + block + "\n"
        figure_stale = not target.exists() or target.read_bytes() != figure.read_bytes()
        if text != readme.read_text() or figure_stale:
            stale.append(slug)
            if not args.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(figure, target)
                readme.write_text(text)
    if args.check and stale:
        print("out of date: " + ", ".join(stale))
        return 1
    print(("would update " if args.check else "updated ") + ", ".join(stale) if stale
          else "every package README and figure is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
