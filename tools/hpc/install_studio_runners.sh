#!/bin/bash
# Run ON the Mac Studio (Apple Silicon). One self-hosted GitHub runner per package
# repository, all labelled studio-macos-arm64, each installed as a per-user launchd
# service so it survives logouts and reboots (no root). Registration lines
# "<repo> <token>" arrive on stdin from register_runners.sh.
set -euo pipefail
umask 077
ROOT="$HOME/gh-runners"
VERSION=2.337.0
xcode-select -p >/dev/null || { echo "install the Xcode command line tools first: xcode-select --install"; exit 1; }
mkdir -p "$ROOT/bin"
cd "$ROOT"
if [ ! -f "actions-runner-$VERSION.tar.gz" ]; then
  curl -sSL -o "actions-runner-$VERSION.tar.gz" \
    "https://github.com/actions/runner/releases/download/v$VERSION/actions-runner-osx-arm64-$VERSION.tar.gz"
fi
# The workflows download Core releases with gh; give every job a copy on PATH.
if [ ! -x bin/gh ]; then
  curl -sSL -o gh.zip "https://github.com/cli/cli/releases/download/v2.97.0/gh_2.97.0_macOS_arm64.zip"
  unzip -q -o gh.zip "gh_2.97.0_macOS_arm64/bin/gh" && mv gh_2.97.0_macOS_arm64/bin/gh bin/gh && rm -rf gh.zip gh_2.97.0_macOS_arm64
fi
while read -r repo token; do
  [ -n "$repo" ] || continue
  dir="$ROOT/$repo"
  mkdir -p "$dir"
  if [ ! -f "$dir/config.sh" ]; then tar -xzf "actions-runner-$VERSION.tar.gz" -C "$dir"; fi
  # Own HOME per runner: setup-micromamba keeps its root under ~ and concurrent
  # jobs sharing one would race ("Non-conda folder exists at prefix").
  mkdir -p "$dir/home"
  # .env is applied by the runner itself; a launchd service inherits almost no PATH.
  printf 'HOME=%s\nPATH=%s/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin\n' "$dir/home" "$ROOT" > "$dir/.env"
  ( cd "$dir" && ./config.sh --unattended --replace --url "https://github.com/okohlbacher/$repo" \
      --token "$token" --name "studio-$repo" --labels studio-macos-arm64 --work _work --disableupdate )
  # config.sh writes .path from the configuring shell's PATH; jobs need gh in front of it.
  sed -i '' "1s|^|$ROOT/bin:|" "$dir/.path"
  ( cd "$dir" && ./svc.sh install >/dev/null && ./svc.sh start >/dev/null )
  echo "started studio-$repo"
done
