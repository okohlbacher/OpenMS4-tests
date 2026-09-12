#!/bin/bash
# Run where `gh` is logged in as the repository owner. Fetches a one-hour runner
# registration token per package repository and streams "<repo> <token>" lines to
# dax, where install_dax_runners.sh configures and starts one runner per repository.
# Tokens are secrets: they travel only over ssh and are never written to disk here.
set -euo pipefail
cd "$(dirname "$0")/../.."
repos=$(python3 -c '
import json
for name, e in json.load(open("packages.lock.json"))["packages"].items():
    if name not in ("core", "flashapp"):   # Core is not rebuilt this cycle; FLASHApp has no CI
        print(e["repository"].removesuffix(".git").rsplit("/", 1)[-1])')
scp -q tools/hpc/install_dax_runners.sh dax:/scratch/kohlbach/
for repo in $repos; do
  token=$(gh api -X POST "repos/okohlbacher/$repo/actions/runners/registration-token" -q .token)
  echo "$repo $token"
done | ssh dax 'chmod +x /scratch/kohlbach/install_dax_runners.sh && /scratch/kohlbach/install_dax_runners.sh'
