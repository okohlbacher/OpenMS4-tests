#!/bin/bash
# Run ON dax. One self-hosted GitHub runner per package repository, all labelled
# dax-linux-x64, each started in the background as this user (no root, no systemd).
# Registration lines "<repo> <token>" arrive on stdin from register_dax_runners.sh.
set -euo pipefail
umask 077
ROOT=/scratch/kohlbach/gh-runners
VERSION=2.337.0
mkdir -p "$ROOT/bin" "$ROOT/tmp"
cd "$ROOT"
if [ ! -f "actions-runner-$VERSION.tar.gz" ]; then
  curl -sSL -o "actions-runner-$VERSION.tar.gz" \
    "https://github.com/actions/runner/releases/download/v$VERSION/actions-runner-linux-x64-$VERSION.tar.gz"
fi
# The workflows download Core releases with gh; give every job a copy on PATH.
if [ ! -x bin/gh ]; then
  curl -sSL "https://github.com/cli/cli/releases/download/v2.97.0/gh_2.97.0_linux_amd64.tar.gz" \
    | tar -xz --strip-components=2 -C bin gh_2.97.0_linux_amd64/bin/gh
fi
while read -r repo token; do
  [ -n "$repo" ] || continue
  dir="$ROOT/$repo"
  mkdir -p "$dir"
  if [ ! -f "$dir/config.sh" ]; then tar -xzf "actions-runner-$VERSION.tar.gz" -C "$dir"; fi
  # Every runner gets its own HOME: setup-micromamba keeps its root under ~ and
  # concurrent jobs sharing one would race ("Non-conda folder exists at prefix").
  mkdir -p "$dir/home"
  printf 'HOME=%s\nTMPDIR=%s\nDOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1\n' "$dir/home" "$ROOT/tmp" > "$dir/.env"
  # setup-micromamba refuses to overwrite its binary and root from an earlier job,
  # so a job-start hook wipes them; the environment is restored from the cache.
  printf '#!/bin/bash\nrm -rf "$HOME/micromamba-bin" "$HOME/micromamba"\n' > "$dir/pre-job.sh"
  chmod +x "$dir/pre-job.sh"
  echo "ACTIONS_RUNNER_HOOK_JOB_STARTED=$dir/pre-job.sh" >> "$dir/.env"
  ( cd "$dir" && ./config.sh --unattended --replace --url "https://github.com/okohlbacher/$repo" \
      --token "$token" --name "dax-$repo" --labels dax-linux-x64 --work _work --disableupdate )
  # config.sh writes .path from the configuring shell's PATH; jobs need gh in front of it.
  sed -i "1s|^|$ROOT/bin:|" "$dir/.path"
  ln -sfn "$ROOT/bin/gh" "$HOME/.local/bin/gh"   # the PATH jobs inherit starts with ~/.local/bin
  ( cd "$dir" && nohup ./run.sh > runner.log 2>&1 & )
  echo "started dax-$repo"
done
