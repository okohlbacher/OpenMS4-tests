#!/usr/bin/env python3
"""Advance the package graph to a new Core revision as one coordinated cycle.

Consumers are rewritten in dependency order: each package's dependencies.lock.json
takes the new revisions of what it consumes, its generated workflows are re-created
from those pins, and the result is committed so the next consumer can pin it.
packages.lock.json is rewritten at the end. Nothing is pushed, tagged or released
here; that is driven per phase, because a consumer that downloads a release (the
desktop's TOPP tools) cannot be regenerated before that release exists.
"""
import argparse
from graphlib import TopologicalSorter
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_packages import native_graph  # noqa: E402
import scaffold_package_ci  # noqa: E402

COMMIT_MESSAGE = """[BUILD] Pin the package graph to Core {core}

Consumed packages move to the revisions the integration parent now pins, and the
generated workflows follow: the Core release they download, the CLI and fixture
checkouts they build, and for pyOpenMS the ProSE and FLASH backends.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
"""


def git(path: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True,
                          check=check).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", required=True, help="qualified Core revision to pin (40 hex)")
    parser.add_argument("--skip", nargs="*", default=[], help="packages to leave for a later phase")
    parser.add_argument("--only", nargs="*", default=[], help="restrict to these packages")
    parser.add_argument("--message", help="commit subject when the cycle is more than a pin move")
    args = parser.parse_args()
    if len(args.core) != 40:
        parser.error("--core must be a full 40-character revision")

    lock_path = ROOT / "packages.lock.json"
    lock = json.loads(lock_path.read_text())
    packages = lock["packages"]
    by_repo = {e["repository"].removesuffix(".git").lower(): n for n, e in packages.items()}
    graph = native_graph(packages)
    graph["flashapp"] = {by_repo[d["repository"].removesuffix(".git").lower()]
                         for d in json.loads((ROOT / packages["flashapp"]["path"] / "dependencies.lock.json").read_text())["dependencies"].values()} - {"core"}
    order = list(TopologicalSorter(graph).static_order())

    # Core is pinned, not rebuilt: check the submodule out at that exact revision.
    core_path = ROOT / packages["core"]["path"]
    git(core_path, "fetch", "-q", "origin")
    git(core_path, "checkout", "-q", args.core)
    revisions = {"core": args.core}
    packages["core"]["source_revision"] = args.core

    for name in order:
        if name in args.skip or (args.only and name not in args.only):
            revisions[name] = packages[name]["source_revision"]
            continue
        path = ROOT / packages[name]["path"]
        if git(path, "status", "--porcelain"):
            raise SystemExit(f"{name}: commit or resolve its working changes first")
        lock_file = path / "dependencies.lock.json"
        deps = json.loads(lock_file.read_text())
        for dep in deps["dependencies"].values():
            owner = by_repo[dep["repository"].removesuffix(".git").lower()]
            if owner not in revisions:
                raise SystemExit(f"{name}: depends on {owner}, which is not pinned yet")
            dep["source_revision"] = revisions[owner]
        lock_file.write_text(json.dumps(deps, indent=2) + "\n")
        # Regenerate workflows from the parent lock as it will read after this cycle.
        for dep_name, rev in revisions.items():
            packages[dep_name]["source_revision"] = rev
        lock_path.write_text(json.dumps(lock, indent=2) + "\n")
        if name in packages and name not in ("test-data", "flashapp"):
            refs = {n: packages[n]["source_revision"] for n in ("core", "cli", "test-data", "prose", "flash", "topp")}
            refs["core_tag"] = scaffold_package_ci.release_tag(core_path, refs["core"], "core-v")
            scaffold_package_ci.scaffold(name, packages, refs)
        git(path, "add", "-A")
        if git(path, "diff", "--cached", "--name-only"):
            subprocess.run(["git", "-C", str(path), "-c", "user.name=Oliver",
                            "-c", "user.email=oliver.kohlbacher@uni-tuebingen.de",
                            "commit", "-q", "-F", "-"],
                           input=(f"{args.message}\n\n" if args.message else "") + COMMIT_MESSAGE.format(core=args.core[:12]),
                           text=True, check=True)
        revisions[name] = git(path, "rev-parse", "HEAD")
        packages[name]["source_revision"] = revisions[name]
        print(f"{name:22} {revisions[name][:12]}", flush=True)

    lock_path.write_text(json.dumps(lock, indent=2) + "\n")
    print("packages.lock.json rewritten; push the children, then pin the parent.")


if __name__ == "__main__":
    main()
