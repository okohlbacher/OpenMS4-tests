#!/usr/bin/env python3
"""Build and test this package against installed, pinned Core, CLI and TestData packages.

The package names itself through tools.json and its git remote, and it declares
the tools it owns there, so this driver is identical in every console product.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time


def package_name(source: Path) -> str:
    """Archive name prefix: the repository this package is published from."""
    url = subprocess.check_output(
        ["git", "-C", str(source), "remote", "get-url", "origin"], text=True).strip()
    return url.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]


def package_tools(source: Path) -> list[str]:
    """The tool names this package owns, in tools.json order."""
    names = [tool["name"] for tool in json.loads((source / "tools.json").read_text())["tools"]]
    if not names:
        raise ValueError("tools.json lists no tools")
    return names


def check_install(prefix: Path, tools: list[str], windows: bool) -> None:
    """Fail unless every owned tool and exactly one registering manifest are installed."""
    for tool in tools:
        executable = prefix / "bin" / (f"{tool}.exe" if windows else tool)
        if not executable.is_file():
            raise ValueError(f"{executable} was not installed")
    manifests = sorted((prefix / "share/openms4/tools").glob("*.tools.tsv"))
    if len(manifests) != 1:
        raise ValueError(f"Expected one installed tool manifest, found {len(manifests)}")
    registered = {line.split("\t")[0] for line in manifests[0].read_text().splitlines()
                  if line and not line.startswith("#")}
    missing = sorted(set(tools) - registered)
    if missing:
        raise ValueError(f"{manifests[0].name} does not register {missing}")



def archive_install(prefix: Path, output: Path, name: str) -> Path:
    """Create a checksummed archive while preserving library symlinks."""
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{name}.tar.gz"
    with tarfile.open(archive, "w:gz") as stream:
        stream.add(prefix, arcname=name)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".gz.sha256").write_text(
        f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive


def core_prefix(extracted: Path) -> Path:
    """Find the single Core SDK root extracted by the workflow."""
    candidates = [path for path in extracted.iterdir()
                  if path.is_dir() and (path / "source-revision.txt").is_file()]
    if len(candidates) != 1:
        raise ValueError(f"Expected one extracted Core SDK, found {len(candidates)}")
    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--core-dir", required=True, type=Path)
    parser.add_argument("--cli-source", required=True, type=Path)
    parser.add_argument("--test-data-source", type=Path,
                        help="installed for the scientific fixture tests; omit to skip them")
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    # The first launches of freshly built binaries stall in syspolicyd on the Mac Studio runner;
    # serial tests confine that stall to the first test, so its workflow asks for them. Builds stay parallel.
    test_jobs = "1" if os.environ.get("OPENMS4_SERIAL_TESTS") == "1" else str(args.jobs)
    source = Path(__file__).resolve().parents[2]
    work = args.work_dir.resolve()
    if args.jobs < 1 or (work.exists() and any(work.iterdir())):
        parser.error("--jobs must be positive and --work-dir must be empty")
    results = work / "results"
    results.mkdir(parents=True)
    tools = package_tools(source)
    core = core_prefix(args.core_dir.resolve())
    cli_build, cli_install = work / "cli-build", work / "cli"
    data_build, data_install = work / "test-data-build", work / "test-data"
    build, install = work / "package-build", work / "package"
    dependencies = Path(os.environ["CONDA_PREFIX"]).resolve()
    windows = sys.platform == "win32"
    dependency_prefix = dependencies / "Library" if windows else dependencies
    generator = "Visual Studio 17 2022" if windows else "Ninja"
    configuration = "Release"
    env = os.environ.copy()
    runtime_dirs = [dependency_prefix / "bin", core / "bin", cli_install / "bin"]
    env["PATH"] = os.pathsep.join(str(path) for path in runtime_dirs) + os.pathsep + env["PATH"]
    library_dirs = os.pathsep.join(
        [str(dependency_prefix / "lib"), str(core / "lib"), str(cli_install / "lib")])
    if sys.platform == "linux":
        env["LD_LIBRARY_PATH"] = library_dirs
    elif sys.platform == "darwin":
        env["DYLD_FALLBACK_LIBRARY_PATH"] = library_dirs
    commands = []

    def run(name: str, command: list[str], cwd: Path = source) -> None:
        started = time.monotonic()
        print(f"\n--- {name} ---", flush=True)
        log = results / f"{name}.log"
        with log.open("w", encoding="utf-8") as stream:
            process = subprocess.Popen(command, cwd=cwd, env=env, text=True,
                                       encoding="utf-8", errors="replace",
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in process.stdout:
                stream.write(line)
                print(line, end="", flush=True)
            code = process.wait()
        commands.append({"name": name, "command": command, "returncode": code,
                         "elapsed_seconds": round(time.monotonic() - started, 3)})
        (results / "commands.json").write_text(
            json.dumps(commands, indent=2) + "\n", encoding="utf-8")
        if code:
            raise subprocess.CalledProcessError(code, command)

    common = ["-G", generator, f"-DCMAKE_BUILD_TYPE={configuration}",
              "-DOPENMS4_REQUIRE_CLEAN_SOURCE=ON"]
    if windows:
        common += ["-A", "x64", "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL"]
    elif sys.platform == "darwin":
        common += [f"-DOpenMP_ROOT={dependency_prefix.as_posix()}",
                   f"-DCURL_ROOT={dependency_prefix.as_posix()}",
                   "-DCMAKE_FIND_FRAMEWORK=LAST"]
    run("driver-tests", [sys.executable, "-m", "unittest", "discover", "-s", "tools/ci", "-v"])
    run("configure-cli", ["cmake", "-S", str(args.cli_source.resolve()), "-B", str(cli_build),
                          f"-DCMAKE_INSTALL_PREFIX={cli_install.as_posix()}",
                          f"-DCMAKE_PREFIX_PATH={core.as_posix()};{dependency_prefix.as_posix()}",
                          *common])
    run("build-cli", ["cmake", "--build", str(cli_build), "--config", configuration,
                      "--parallel", str(args.jobs)])
    run("install-cli", ["cmake", "--install", str(cli_build), "--config", configuration])
    prefixes = [core.as_posix(), cli_install.as_posix()]
    options = []
    if args.test_data_source:
        run("configure-test-data",
            ["cmake", "-S", str(args.test_data_source.resolve()), "-B", str(data_build),
             f"-DCMAKE_INSTALL_PREFIX={data_install.as_posix()}",
             f"-DCMAKE_PREFIX_PATH={core.as_posix()};{dependency_prefix.as_posix()}", *common])
        run("install-test-data", ["cmake", "--install", str(data_build), "--config", configuration])
        prefixes.append(data_install.as_posix())
        options.append("-DOPENMS4_REGRESSION_TESTS=ON")
    prefixes.append(dependency_prefix.as_posix())
    run("configure-package", ["cmake", "-S", str(source), "-B", str(build),
                           f"-DCMAKE_INSTALL_PREFIX={install.as_posix()}",
                           f"-DCMAKE_PREFIX_PATH={';'.join(prefixes)}",
                           "-DOPENMS4_WARNINGS_AS_ERRORS=ON", *options, *common])
    run("build-package", ["cmake", "--build", str(build), "--config", configuration,
                       "--parallel", str(args.jobs)])
    if windows:
        # A package that builds its own shared library leaves the DLL in the build
        # tree, and Windows resolves it from PATH rather than from an rpath, so the
        # tests cannot start without it.
        dll_dirs = sorted({str(path.parent) for path in build.rglob("*.dll")})
        env["PATH"] = os.pathsep.join([*dll_dirs, env["PATH"]])
    run("test-package", ["ctest", "--test-dir", str(build), "-C", configuration,
                      "--output-on-failure", "--no-tests=error", "--parallel", test_jobs])
    run("install-package", ["cmake", "--install", str(build), "--config", configuration])
    check_install(install, tools, windows)
    env["OPENMS_TOOL_PREFIX_PATH"] = str(install)
    first = install / "bin" / (f"{tools[0]}.exe" if windows else tools[0])
    run("installed-write-ini", [str(first), "-write_ini", str(work / "installed.ini")])
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    shutil.copyfile(source / "dependencies.lock.json", install / "dependencies.lock.json")
    (install / "source-revision.txt").write_text(revision + "\n", encoding="utf-8")
    archive_install(install, work / "dist",
                    f"{package_name(source)}-{args.platform}-Release-{revision[:12]}")


if __name__ == "__main__":
    main()
