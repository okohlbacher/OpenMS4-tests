#!/usr/bin/env python3
"""Write this package's Homebrew cask from the assets of a published release.

Checksums come from the release itself, so the cask can only be generated once
the tested payloads exist. Run it after the release workflow succeeds, then
commit the result. The package identifies itself through its git remote and
tools.json, so this script is identical in every console product package.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parent))
from run import package_name, package_tools

ARCHES = {"arm": "arm64", "intel": "x64"}


def repository(source: Path) -> str:
    url = subprocess.check_output(
        ["git", "-C", str(source), "remote", "get-url", "origin"], text=True).strip()
    owner, name = url.rstrip("/").removesuffix(".git").rsplit("/", 2)[-2:]
    return f"{owner}/{name}"


def render(cask: str, repo: str, package: str, tag_prefix: str, title: str, description: str,
           version: str, build: str, digests: dict[str, str], tools: list[str]) -> str:
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
  postflight_steps do
    run "/usr/bin/xattr",
        args:           ["-dr", "com.apple.quarantine", "."],
        chdir:          ".",
        writable_paths: ["."]
  end
end
'''


def main() -> None:
    source = Path(__file__).resolve().parents[2]
    package = package_name(source)
    suffix = package.removeprefix("OpenMS4-")
    cask = f"openms4-{suffix}"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help=f"published release tag, e.g. {suffix}-v1.0.0-ci.1")
    parser.add_argument("--title", default=f"OpenMS 4 {suffix} tools")
    parser.add_argument("--desc",
                        default="Command-line mass-spectrometry tools built against the OpenMS Core SDK")
    parser.add_argument("--output", type=Path, default=source / f"Casks/{cask}.rb")
    args = parser.parse_args()
    if "-v" not in args.tag:
        parser.error("--tag must look like <package>-v<version>")
    head, version = args.tag.rsplit("-v", 1)
    tag_prefix = f"{head}-v"
    repo = repository(source)
    tools = package_tools(source)
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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render(cask, repo, package, tag_prefix, args.title, args.desc,
               version, builds.pop(), digests, tools), encoding="utf-8")
    print(f"wrote {args.output} for {args.tag}")


if __name__ == "__main__":
    main()
