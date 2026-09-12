#!/bin/bash
# Usage: register_runners.sh dax|studio
# Run where `gh` is logged in as the repository owner. Fetches a one-hour runner
# registration token per package repository and streams "<repo> <token>" lines
# over ssh to the target, whose install script configures and starts one runner
# per repository. Tokens are secrets: they travel only over ssh, never to disk.
set -euo pipefail
target=${1:?dax or studio}
case "$target" in
  dax)    host=dax;       script=install_dax_runners.sh;    remote=/scratch/kohlbach ;;
  studio) host=${STUDIO_HOST:-oliver@100.94.67.26}; script=install_studio_runners.sh; remote='~' ;;   # Tailscale address of the Mac Studio
  *) echo "unknown target $target"; exit 1 ;;
esac
cd "$(dirname "$0")/../.."
repos=$(python3 -c '
import json
for name, e in json.load(open("packages.lock.json"))["packages"].items():
    if name not in ("core", "test-data", "flashapp"):   # Core is not rebuilt this cycle; the others have no CI
        print(e["repository"].removesuffix(".git").rsplit("/", 1)[-1])')
scp -q "tools/hpc/$script" "$host:$remote/"
for repo in $repos; do
  token=$(gh api -X POST "repos/okohlbacher/$repo/actions/runners/registration-token" -q .token)
  echo "$repo $token"
done | ssh "$host" "chmod +x $remote/$script && $remote/$script"
