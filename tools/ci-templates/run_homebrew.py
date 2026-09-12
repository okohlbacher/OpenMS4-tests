#!/usr/bin/env python3
"""Build this package's cask payload against the Homebrew Core formula.

The payload carries the CLI runtime the tools link, the package's own installed
data and its tool manifest, so a cask install needs only the openms4-core formula.
"""

import argparse
import os
from pathlib import Path
import shutil
import subprocess

from run import archive_install, check_install, package_name, package_tools


def command(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli-source", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[2]
    work = args.work_dir.resolve()
    if args.jobs < 1 or (work.exists() and any(work.iterdir())):
        parser.error("--jobs must be positive and --work-dir must be empty")
    work.mkdir(parents=True)
    tools = package_tools(source)
    core = Path(command("brew", "--prefix", "openms4-core"))
    brew = Path(command("brew", "--prefix"))
    dependency_names = ["apache-arrow", "boost", "cbc", "curl", "eigen", "libomp",
                        "libsvm", "libxml2", "libzip", "nlohmann-json", "xerces-c"]
    dependency_prefixes = [command("brew", "--prefix", name) for name in dependency_names]
    cli_build, package_build, payload = work / "cli-build", work / "package-build", work / "payload"
    payload.mkdir()
    env = os.environ.copy()
    env["DYLD_FALLBACK_LIBRARY_PATH"] = os.pathsep.join(
        [str(payload / "lib"), str(core / "lib"), str(brew / "lib")])
    prefix_path = ";".join([str(core), *dependency_prefixes, str(brew)])

    def run(args_list: list[str]) -> None:
        subprocess.run(args_list, check=True, env=env)

    common = ["-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release", "-DOPENMS4_REQUIRE_CLEAN_SOURCE=ON",
              f"-DOpenMP_ROOT={command('brew', '--prefix', 'libomp')}",
              f"-DCURL_ROOT={command('brew', '--prefix', 'curl')}", "-DCMAKE_FIND_FRAMEWORK=LAST"]
    run(["cmake", "-S", str(args.cli_source.resolve()), "-B", str(cli_build),
         f"-DCMAKE_INSTALL_PREFIX={payload}", f"-DCMAKE_PREFIX_PATH={prefix_path}", *common])
    run(["cmake", "--build", str(cli_build), "--parallel", str(args.jobs)])
    run(["ctest", "--test-dir", str(cli_build), "--output-on-failure", "--no-tests=error",
         "--parallel", str(args.jobs)])
    run(["cmake", "--install", str(cli_build)])
    run(["cmake", "-S", str(source), "-B", str(package_build),
         f"-DCMAKE_INSTALL_PREFIX={payload}", f"-DCMAKE_PREFIX_PATH={payload};{prefix_path}",
         "-DOPENMS4_WARNINGS_AS_ERRORS=ON", *common])
    run(["cmake", "--build", str(package_build), "--parallel", str(args.jobs)])
    run(["ctest", "--test-dir", str(package_build), "--output-on-failure", "--no-tests=error",
         "--parallel", str(args.jobs)])
    run(["cmake", "--install", str(package_build)])
    check_install(payload, tools, False)
    env["OPENMS_TOOL_PREFIX_PATH"] = str(payload)
    # A cask exposes each tool through a symlink in the Homebrew prefix, and
    # executable-relative data must still resolve, so exercise that exact path.
    linked = work / "linked-bin"
    linked.mkdir()
    clean_env = env.copy()
    clean_env.pop("DYLD_FALLBACK_LIBRARY_PATH")
    for tool in tools:
        (linked / tool).symlink_to(payload / "bin" / tool)
        subprocess.run([str(linked / tool), "-write_ini", str(work / f"{tool}.ini")],
                       check=True, env=clean_env)
    revision = command("git", "-C", str(source), "rev-parse", "HEAD")
    shutil.copyfile(source / "dependencies.lock.json", payload / "dependencies.lock.json")
    (payload / "source-revision.txt").write_text(revision + "\n", encoding="utf-8")
    archive_install(payload, work / "dist",
                    f"{package_name(source)}-{args.platform}-Homebrew-{revision[:12]}")


if __name__ == "__main__":
    main()
