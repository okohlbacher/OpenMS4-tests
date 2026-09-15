#!/usr/bin/env python3
"""Write this package's Homebrew cask from the assets of a published release.

Checksums come from the release itself, so the cask can only be generated once
the tested payloads exist. Run it after the release workflow succeeds, then
commit the result. The package identifies itself through its git remote and
tools.json, so this script is identical in every console product package.
"""

import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).parent))
from run import package_name, package_tools

ARCHES = {"arm": "arm64", "intel": "x64"}


def repository(source: Path) -> str:
    url = subprocess.check_output(
        ["git", "-C", str(source), "remote", "get-url", "origin"], text=True).strip()
    owner, name = url.rstrip("/").removesuffix(".git").rsplit("/", 2)[-2:]
    return f"{owner}/{name}"


def shipped(tools: list[str], members: list[str]) -> list[str]:
    """The declared tools a payload actually installs; a Homebrew build can leave optional ones out."""
    binaries = {Path(m).parts[2] for m in members if Path(m).parts[1:2] == ("bin",) and len(Path(m).parts) == 3}
    return [tool for tool in tools if tool in binaries]


def render(cask: str, repo: str, package: str, tag_prefix: str, title: str, description: str,
           version: str, build: str, digests: dict[str, str], tools: list[str],
           core_revision: str) -> str:
    binaries = "".join(f'  binary "#{{payload}}/bin/{tool}"\n' for tool in tools)
    return f'''cask "{cask}" do
  arch arm: "arm64", intel: "x64"

  version "{version},{build}"
  sha256 arm:   "{digests['arm']}",
         intel: "{digests['intel']}"

  url "https://github.com/{repo}/releases/download/" \\
      "{tag_prefix}#{{version.csv.first}}/{package}-macos-#{{arch}}-Homebrew-#{{version.csv.second}}.tar.gz"
  name "{title}"
  desc "{description}"
  homepage "https://github.com/{repo}"

  depends_on formula: "okohlbacher/openms4-core/openms4-core"
  depends_on macos: :sequoia

  payload = "{package}-macos-#{{arch}}-Homebrew-#{{version.csv.second}}"
{binaries}
  # libOpenMS has no versioned name, so a payload only runs with the Core it was built against.
  preflight do
    config = "#{{HOMEBREW_PREFIX}}/opt/openms4-core/lib/cmake/OpenMS/OpenMSConfig.cmake"
    core = File.exist?(config) ? File.read(config)[/set\\(OpenMS_SOURCE_REVISION "([0-9a-f]{{40}})"\\)/, 1] : nil
    next if core == "{core_revision}"

    raise Cask::CaskError, "{cask} #{{version.csv.first}} was built against openms4-core {core_revision[:12]}, " \\
                           "but the installed openms4-core is #{{core&.slice(0, 12) || "unknown"}}. " \\
                           "Install the {cask} release built for the installed Core."
  end

  postflight_steps do
    run "/usr/bin/xattr",
        args:           ["-dr", "com.apple.quarantine", "."],
        chdir:          ".",
        writable_paths: ["."]
  end
end
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="published release tag, e.g. topp-v1.0.0-ci.1")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[2],
                        help="package checkout (default: the package this script belongs to)")
    parser.add_argument("--title", help="cask name (default: OpenMS 4 <package> tools)")
    parser.add_argument("--desc",
                        default="Command-line mass-spectrometry tools built against the OpenMS Core SDK")
    parser.add_argument("--output", type=Path, help="default: <source>/Casks/<cask>.rb")
    args = parser.parse_args()
    source = args.source.resolve()
    package = package_name(source)
    suffix = package.removeprefix("OpenMS4-")
    cask = f"openms4-{suffix}"
    if "-v" not in args.tag:
        parser.error("--tag must look like <package>-v<version>")
    head, version = args.tag.rsplit("-v", 1)
    tag_prefix = f"{head}-v"
    repo = repository(source)
    tools = package_tools(source)
    lock = json.loads(subprocess.check_output(
        ["git", "-C", str(source), "show", f"{args.tag}:dependencies.lock.json"], text=True))
    core_revision = lock["dependencies"]["OpenMS"]["source_revision"]
    assets = json.loads(subprocess.check_output(
        ["gh", "release", "view", args.tag, "--repo", repo, "--json", "assets"],
        text=True))["assets"]
    digests, builds = {}, set()
    for key, arch in ARCHES.items():
        prefix = f"{package}-macos-{arch}-Homebrew-"
        matches = [a for a in assets
                   if a["name"].startswith(prefix) and a["name"].endswith(".tar.gz")]
        if len(matches) != 1:
            raise SystemExit(f"{args.tag}: expected one {arch} Homebrew payload, found {len(matches)}")
        digest = matches[0].get("digest", "")
        if not digest.startswith("sha256:"):
            raise SystemExit(f"{matches[0]['name']}: release reports no sha256 digest")
        digests[key] = digest.removeprefix("sha256:")
        builds.add(matches[0]["name"].removeprefix(prefix).removesuffix(".tar.gz"))
    if len(builds) != 1:
        raise SystemExit(f"payloads disagree about the source revision: {sorted(builds)}")
    arm = f"{package}-macos-arm64-Homebrew-{next(iter(builds))}.tar.gz"
    payload = subprocess.check_output(
        ["gh", "release", "download", args.tag, "--repo", repo, "--pattern", arm, "--output", "-"])
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        installed = shipped(tools, archive.getnames())
    if not installed:
        raise SystemExit(f"{arm} installs none of the tools in tools.json")
    for tool in sorted(set(tools) - set(installed)):
        print(f"{args.tag}: {tool} is not in the Homebrew payload, so the cask does not link it")
    tools = installed
    output = args.output or source / f"Casks/{cask}.rb"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render(cask, repo, package, tag_prefix, args.title or f"OpenMS 4 {suffix} tools", args.desc,
               version, builds.pop(), digests, tools, core_revision), encoding="utf-8")
    print(f"wrote {output} for {args.tag} (Core {core_revision[:12]})")


if __name__ == "__main__":
    main()
