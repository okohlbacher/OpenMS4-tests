#!/usr/bin/env python3
"""Regenerate the console-product casks from their published releases, once a pin cycle is tagged.

update_cask.py reads the checksums and the pinned Core revision out of a package's
release, so every cask it writes is the generator's default text. Two casks were
named by hand and one installs a tool under another name; those live here so a later
cycle does not silently drop them.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from scaffold_package_ci import release_tag  # noqa: E402

# Casks whose name or description is not what the generator derives from the package name.
TEXT = {
    "topp": ["--title", "OpenMS TOPP tools"],
    "nuxl": ["--title", "OpenNuXL", "--desc",
             "Search engine for protein-nucleic acid cross-links, built against the OpenMS Core SDK"],
}
# TOPP's FileInfo would shadow other tools of that name on PATH, so it installs only under another name.
RENAME = {"topp": {"FileInfo": "OpenMSFileInfo"}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", nargs="*", help="package names (default: every package with a cask)")
    args = parser.parse_args()
    lock = json.loads((ROOT / "packages.lock.json").read_text())["packages"]
    names = args.packages or [n for n in lock if (ROOT / lock[n]["path"] / "Casks").is_dir()]
    for name in names:
        source = ROOT / lock[name]["path"]
        tag = release_tag(source, lock[name]["source_revision"], f"{name}-v")
        subprocess.run([sys.executable, str(ROOT / "tools/ci-templates/update_cask.py"),
                        "--source", str(source), "--tag", tag] + TEXT.get(name, []), check=True)
        cask = source / f"Casks/openms4-{name}.rb"
        text = cask.read_text()
        for tool, target in RENAME.get(name, {}).items():
            line = f'  binary "#{{payload}}/bin/{tool}"\n'
            if line not in text:
                raise SystemExit(f"{cask}: no {tool} binary to rename")
            text = text.replace(line, f'  binary "#{{payload}}/bin/{tool}", target: "{target}"\n')
        cask.write_text(text, encoding="utf-8")
        if "disable!" in cask.read_text():
            raise SystemExit(f"{cask}: still disabled after regeneration")


if __name__ == "__main__":
    main()
