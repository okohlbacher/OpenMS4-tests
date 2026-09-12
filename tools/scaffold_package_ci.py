#!/usr/bin/env python3
"""Generate a package's CI, release and Homebrew workflows from the package graph.

Every generated workflow pins its dependencies to the revisions in
packages.lock.json, so re-running this after a re-pin rewrites the refs, the Core
release it downloads and the TOPP release the desktop tests run. The console
product drivers under tools/ci-templates are package-agnostic and are copied
verbatim; packages with their own drivers keep them.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "tools/ci-templates"
CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6"
UPLOAD = "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f # v6"
MAMBA = "mamba-org/setup-micromamba@f457c30a868e4760d3a6fcea5f25dc655b8edf39 # v3"

# Packages that build their own tools but keep hand-maintained drivers.
KEEP_DRIVERS = {"nuxl"}
# Kinds that are not console products and have bespoke drivers.
SPECIAL = {"cli", "desktop", "pyopenms"}

PLATFORMS = [
    ("linux-x64", "ubuntu-24.04", "gcc_linux-64=14 gxx_linux-64=14 coin-or-cbc=2.10.*", 4),
    ("linux-arm64", "ubuntu-24.04-arm", "gcc_linux-aarch64=14 gxx_linux-aarch64=14 coin-or-cbc=2.10.*", 4),
    ("macos-arm64", "macos-15", "llvm-openmp coin-or-cbc=2.10.*", 2),
    ("macos-x64", "macos-15-intel", "llvm-openmp coin-or-cbc=2.10.*", 4),
    ("windows-x64", "windows-2022", "glpk=5.*", 4),
]
# Qt's CMake package requires an OpenGL provider, which the Linux runners lack.
DESKTOP_EXTRA = {"linux-x64": " qt6-main>=6.7 libgl-devel libegl-devel libglx-devel",
                 "linux-arm64": " qt6-main>=6.7 libgl-devel libegl-devel libglx-devel",
                 "macos-arm64": " qt6-main>=6.7", "macos-x64": " qt6-main>=6.7",
                 "windows-x64": " qt6-main>=6.7"}


def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def release_tag(package_path: Path, revision: str, prefix: str) -> str:
    """The one release tag at a pinned revision; a pin without a release cannot be consumed."""
    tags = [t for t in git(package_path, "tag", "--points-at", revision).split() if t.startswith(prefix)]
    if len(tags) != 1:
        raise SystemExit(f"{package_path.name}: expected one {prefix}* tag at {revision[:12]}, found {tags}")
    return tags[0]


def checkout_step(repo: str, ref: str, path: str) -> str:
    return f"""      - uses: {CHECKOUT}
        with:
          repository: okohlbacher/{repo}
          ref: {ref}
          path: dependencies/{path}
          persist-credentials: false
"""


def core_download_step(core_tag: str, core_short: str) -> str:
    return f"""      - name: Download and verify the pinned Core SDK
        shell: bash
        run: |
          mkdir -p "${{{{ runner.temp }}}}/core"
          gh release download {core_tag} --repo okohlbacher/OpenMS4-core \\
            --pattern "OpenMS4-core-${{{{ matrix.platform }}}}-Release-{core_short}.tar.gz*" \\
            --dir "${{{{ runner.temp }}}}/core"
          cd "${{{{ runner.temp }}}}/core"
          if command -v shasum >/dev/null; then
            tr -d '\\r' < *.sha256 | shasum -a 256 -c -
          else
            tr -d '\\r' < *.sha256 | sha256sum -c -
          fi
          tar -xzf *.tar.gz
"""


def native_job(slug: str, title: str, refs: dict, kind: str, env_name: str, topp_tag: str = "", topp_short: str = "") -> str:
    core_tag, core_short = refs["core_tag"], refs["core"][:12]
    matrix = "".join(
        f"          - platform: {p}\n            runner: {r}\n"
        f"            packages: {pk}{DESKTOP_EXTRA[p] if kind == 'desktop' else ''}\n            jobs: {j}\n"
        for p, r, pk, j in PLATFORMS)
    checkouts = ""
    if kind != "cli":
        checkouts += checkout_step("OpenMS4-cli", refs["cli"], "cli")
        checkouts += checkout_step("OpenMS4-test-data", refs["test-data"], "test-data")
    if kind == "pyopenms":
        checkouts += checkout_step("OpenMS4-prose", refs["prose"], "prose")
        checkouts += checkout_step("OpenMS4-flash", refs["flash"], "flash")
    env_extra = "      QT_QPA_PLATFORM: 'minimal'\n" if kind == "desktop" else ""
    before_build = ""
    if kind == "pyopenms":
        before_build += f"""      - name: Install the exact nanobind the bindings require
        shell: bash
        run: |
          # The bindings ask for nanobind 2.10.0 EXACT. conda-forge went from
          # 2.9.2 to 2.10.2 without packaging 2.10.0, so it comes from PyPI.
          micromamba run -n {env_name} python -m pip install --no-input nanobind==2.10.0
          micromamba run -n {env_name} python -c "import nanobind, sys; assert nanobind.__version__ == '2.10.0', nanobind.__version__; print('nanobind', nanobind.__version__)"
"""
    if kind == "desktop":
        before_build += f"""      - name: Download and verify the released TOPP tools
        shell: bash
        run: |
          mkdir -p "${{{{ runner.temp }}}}/topp"
          gh release download {topp_tag} --repo okohlbacher/OpenMS4-topp \\
            --pattern "OpenMS4-topp-${{{{ matrix.platform }}}}-Release-{topp_short}.tar.gz*" \\
            --dir "${{{{ runner.temp }}}}/topp"
          cd "${{{{ runner.temp }}}}/topp"
          if command -v shasum >/dev/null; then
            tr -d '\\r' < *.sha256 | shasum -a 256 -c -
          else
            tr -d '\\r' < *.sha256 | sha256sum -c -
          fi
          tar -xzf *.tar.gz
"""
    driver_args = {
        "product": "          --cli-source dependencies/cli\n          --test-data-source dependencies/test-data\n",
        "cli": "",
        "desktop": ("          --cli-source dependencies/cli\n"
                    "          --topp-dir \"${{ runner.temp }}/topp\"\n"
                    "          --test-data-source dependencies/test-data\n"),
        "pyopenms": ("          --cli-source dependencies/cli\n          --prose-source dependencies/prose\n"
                     "          --flash-source dependencies/flash\n          --test-data-source dependencies/test-data\n"),
    }[kind]
    return f"""name: {title}

on:
  push:
    branches: ['**']
    paths-ignore:
      - 'Casks/**'
      - 'README.md'
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  native:
    name: ${{{{ matrix.platform }}}} / Release
    # Pushes and dispatches build Linux x64 on the dax runner and macOS arm64 on the
    # Mac Studio; pull requests from forks must never run there, so they stay hosted.
    runs-on: ${{{{ (github.event_name != 'pull_request' && matrix.platform == 'linux-x64' && 'dax-linux-x64') || (github.event_name != 'pull_request' && matrix.platform == 'macos-arm64' && 'studio-macos-arm64') || matrix.runner }}}}
    timeout-minutes: 120
    strategy:
      fail-fast: false
      matrix:
        include:
{matrix}    env:
      GH_TOKEN: ${{{{ github.token }}}}
      PYTHONUTF8: '1'
      OMP_NUM_THREADS: '1'
{env_extra}    steps:
      - uses: {CHECKOUT}
        with:
          persist-credentials: false
{checkouts}      - uses: {MAMBA}
        with:
          environment-file: tools/ci/environment.yml
          micromamba-version: 2.9.0-0
          create-args: ${{{{ matrix.packages }}}}
          init-shell: none
          generate-run-shell: false
          cache-environment: true
          cache-environment-key: {slug}-${{{{ matrix.platform }}}}
{before_build}{core_download_step(core_tag, core_short)}      - name: Build, test, install, and package
        run: >-
          micromamba run -n {env_name} python tools/ci/run.py
          --platform ${{{{ matrix.platform }}}} --jobs ${{{{ (startsWith(runner.name, 'dax') && 24) || (startsWith(runner.name, 'studio') && 12) || matrix.jobs }}}}
          --core-dir "${{{{ runner.temp }}}}/core"
{driver_args}          --work-dir "${{{{ runner.temp }}}}/{slug}"
      - name: Upload tested package
        uses: {UPLOAD}
        with:
          name: {slug}-${{{{ matrix.platform }}}}
          path: ${{{{ runner.temp }}}}/{slug}/dist/*
          if-no-files-found: error
          compression-level: 0
      - name: Upload logs
        if: always()
        uses: {UPLOAD}
        with:
          name: results-${{{{ matrix.platform }}}}
          path: ${{{{ runner.temp }}}}/{slug}/results/
          if-no-files-found: warn
"""


def cask_payload_job(slug: str, cli_ref: str) -> str:
    return f"""
  homebrew-cask:
    name: Homebrew cask payload / ${{{{ matrix.platform }}}}
    runs-on: ${{{{ matrix.runner }}}}
    timeout-minutes: 120
    strategy:
      fail-fast: false
      matrix:
        include:
          - platform: macos-arm64
            runner: macos-15
            jobs: 2
          - platform: macos-x64
            runner: macos-15-intel
            jobs: 4
    env:
      HOMEBREW_NO_AUTO_UPDATE: '1'
      HOMEBREW_NO_INSTALL_CLEANUP: '1'
    steps:
      - uses: {CHECKOUT}
        with:
          persist-credentials: false
{checkout_step("OpenMS4-cli", cli_ref, "cli")}      - name: Install the pinned Core formula
        run: |
          brew trust --formula okohlbacher/openms4-core/openms4-core
          brew tap okohlbacher/openms4-core https://github.com/okohlbacher/OpenMS4-core
          brew install nlohmann-json
          brew install --formula --build-from-source okohlbacher/openms4-core/openms4-core
      - name: Build and test the cask payload
        run: >-
          python3 tools/ci/run_homebrew.py --platform ${{{{ matrix.platform }}}}
          --jobs ${{{{ matrix.jobs }}}} --cli-source dependencies/cli
          --work-dir "${{{{ runner.temp }}}}/{slug}-homebrew"
      - name: Upload tested cask payload
        uses: {UPLOAD}
        with:
          name: cask-${{{{ matrix.platform }}}}
          path: ${{{{ runner.temp }}}}/{slug}-homebrew/dist/*
          if-no-files-found: error
          compression-level: 0
"""


def release_workflow(slug: str, title: str, workflow_file: str, with_cask: bool, notes: str) -> str:
    patterns = f"--pattern '{slug}-*'" + (" --pattern 'cask-*'" if with_cask else "")
    count = 7 if with_cask else 5
    assets = f"./artifacts/{slug}-*/*" + (" ./artifacts/cask-*/*" if with_cask else "")
    return f"""name: Release {title}

on:
  push:
    tags: ['{slug}-v*']

permissions:
  actions: read
  contents: write

jobs:
  publish:
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    env:
      GH_TOKEN: ${{{{ github.token }}}}
    steps:
      - uses: {CHECKOUT}
        with:
          persist-credentials: false
      - name: Download packages from successful branch CI
        run: |
          set -euo pipefail
          revision=$(git rev-parse HEAD)
          run_id=$(gh run list --workflow {workflow_file} --commit "$revision" --event push \\
            --status success --limit 1 --json databaseId --jq '.[0].databaseId // empty')
          if [ -z "$run_id" ]; then
            echo "::error::No successful branch CI run exists for $revision"
            exit 1
          fi
          gh run download "$run_id" {patterns} --dir artifacts
          test "$(find artifacts -name '*.sha256' | wc -l)" -eq {count}
          find artifacts -name '*.sha256' -print0 | while IFS= read -r -d '' checksum; do
            sed -i 's/\\r$//' "$checksum"
            (cd "$(dirname "$checksum")" && shasum -a 256 -c "$(basename "$checksum")")
          done
      - name: Publish tested packages
        run: |
          gh release create "${{{{ github.ref_name }}}}" \\
            {assets} \\
            --verify-tag --prerelease --title "{title} ${{{{ github.ref_name }}}}" \\
            --notes "{notes}"
"""


NOTES = {
    "product": "Tested packages for Linux x64/arm64, macOS x64/arm64 and Windows x64, plus Homebrew cask payloads for both macOS architectures. Each payload carries the CLI runtime and this package's tool manifest, and requires the pinned openms4-core SDK.",
    "cli": "Each archive installs the OpenMS::CLI target that every console product links, and requires the pinned openms4-core SDK.",
    "desktop": "Each archive carries the GUI SDK, TOPPView, ImageCreator, INIFileEditor, TOPPAS and ExecutePipeline, and requires the pinned openms4-core SDK and a matching Qt 6.7. Interactive tests stay disabled in this headless build.",
    "pyopenms": "Each archive is the installed module tree built against the pinned Core SDK and the ProSE and FLASH backends, with generated stubs. These are not repaired, redistributable wheels; wheel building and repair remain a separate pipeline.",
}


def cask_workflow(cask: str, repo: str, tools: list) -> str:
    # Writing a default INI through the installed symlink exercises the tool's
    # executable-relative data lookup; --help would pass with broken data paths.
    checks = "".join(f'          {tool} -write_ini "$RUNNER_TEMP/{tool}.ini"\n'
                     f'          test -s "$RUNNER_TEMP/{tool}.ini"\n' for tool in tools[:3])
    return f"""name: Homebrew cask

on:
  push:
    branches: ['**']
    paths:
      - 'Casks/**'
  workflow_dispatch:

permissions:
  contents: read

jobs:
  install:
    name: ${{{{ matrix.platform }}}}
    runs-on: ${{{{ matrix.runner }}}}
    timeout-minutes: 90
    strategy:
      fail-fast: false
      matrix:
        include:
          - platform: macos-arm64
            runner: macos-15
          - platform: macos-x64
            runner: macos-15-intel
    env:
      HOMEBREW_NO_AUTO_UPDATE: '1'
      HOMEBREW_NO_INSTALL_CLEANUP: '1'
    steps:
      - uses: {CHECKOUT}
        with:
          persist-credentials: false
      - name: Install and run the released cask
        run: |
          brew trust --formula okohlbacher/openms4-core/openms4-core
          brew trust --cask okohlbacher/{cask}/{cask}
          brew tap okohlbacher/openms4-core https://github.com/okohlbacher/OpenMS4-core
          brew tap okohlbacher/{cask} https://github.com/okohlbacher/{repo}
          brew install --cask okohlbacher/{cask}/{cask}
{checks}          brew uninstall --cask {cask}
"""


def patch_topp(source: Path, refs: dict) -> None:
    """TOPP keeps its hand-written workflows; only the pinned refs move."""
    for name in ("topp.yml",):
        p = source / ".github/workflows" / name
        s = p.read_text()
        s = re.sub(r"(repository: okohlbacher/OpenMS4-cli\n\s+ref: )[0-9a-f]{40}", r"\g<1>" + refs["cli"], s)
        s = re.sub(r"core-v[0-9][^ ]* --repo okohlbacher/OpenMS4-core", f"{refs['core_tag']} --repo okohlbacher/OpenMS4-core", s)
        s = re.sub(r"Release-[0-9a-f]{12}\.tar\.gz", f"Release-{refs['core'][:12]}.tar.gz", s)
        p.write_text(s)


def scaffold(name: str, lock: dict, refs: dict) -> None:
    entry = lock[name]
    source = ROOT / entry["path"]
    repo = entry["repository"].removesuffix(".git").rsplit("/", 1)[-1]
    workflows = source / ".github/workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    if name == "topp":
        patch_topp(source, refs)
        print(f"patched {name}: refs updated in hand-written workflows")
        return
    kind = name if name in SPECIAL else "product"
    title = {"cli": "CLI", "desktop": "Desktop", "pyopenms": "pyOpenMS", "nuxl": "NuXL"}.get(name, repo.removeprefix("OpenMS4-"))
    env_file = source / "tools/ci/environment.yml"
    env_name = "package-ci"
    if env_file.exists():
        env_name = next((line.split(":", 1)[1].strip() for line in env_file.read_text().splitlines()
                         if line.startswith("name:")), env_name)
    topp_tag = topp_short = ""
    if kind == "desktop":
        topp_tag = release_tag(ROOT / lock["topp"]["path"], refs["topp"], "topp-v")
        topp_short = refs["topp"][:12]
    workflow = native_job(name, title, refs, kind, env_name, topp_tag, topp_short)
    if kind == "product":
        workflow += cask_payload_job(name, refs["cli"])
    (workflows / f"{name}.yml").write_text(workflow, encoding="utf-8")
    (workflows / "release.yml").write_text(
        release_workflow(name, title, f"{name}.yml", kind == "product", NOTES[kind]), encoding="utf-8")
    if kind == "product":
        tools = [t["name"] for t in json.loads((source / "tools.json").read_text())["tools"]]
        (workflows / "homebrew-cask.yml").write_text(cask_workflow(f"openms4-{name}", repo, tools), encoding="utf-8")
        if name not in KEEP_DRIVERS:
            ci = source / "tools/ci"
            ci.mkdir(parents=True, exist_ok=True)
            for template in TEMPLATES.iterdir():
                shutil.copyfile(template, ci / template.name)
    ignore = source / ".gitignore"
    lines = ignore.read_text().splitlines() if ignore.exists() else []
    for wanted in ("/dependencies/", "build/", "__pycache__/"):
        if wanted not in lines:
            lines.insert(0, wanted) if wanted == "/dependencies/" else lines.append(wanted)
    ignore.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"scaffolded {name} ({kind}): core {refs['core_tag']}, cli {refs['cli'][:7]}, test-data {refs['test-data'][:7]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", nargs="+", help="package names from packages.lock.json, or 'all'")
    args = parser.parse_args()
    lock = json.loads((ROOT / "packages.lock.json").read_text())["packages"]
    refs = {n: lock[n]["source_revision"] for n in ("core", "cli", "test-data", "prose", "flash", "topp")}
    refs["core_tag"] = release_tag(ROOT / lock["core"]["path"], refs["core"], "core-v")
    names = [n for n in lock if n not in ("core", "test-data", "flashapp")] if args.packages == ["all"] else args.packages
    for name in names:
        scaffold(name, lock, refs)


if __name__ == "__main__":
    main()
