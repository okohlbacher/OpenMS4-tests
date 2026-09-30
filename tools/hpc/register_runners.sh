#!/bin/bash
# Usage: register_runners.sh dax|studio
# Run where `gh` is logged in as the repository owner. Fetches a one-hour runner
# registration token per package repository and streams "<repo> <token>" lines
# over ssh to the target, whose install script configures and starts one runner
# per repository. Tokens are secrets: they travel only over ssh, never to disk.
set -euo pipefail
target=${1:?dax, ibminode05, studio or windows}
only=${2:-}          # optional: one repository name instead of the whole graph
case "$target" in
  dax)    host=dax;          script=install_dax_runners.sh;    remote=/scratch/kohlbach ;;
  ibminode05) host=ibminode05; script=install_dax_runners.sh;    remote=/scratch/kohlbach ;;
  studio) host=${STUDIO_HOST:-oliver@100.94.67.26}; script=install_studio_runners.sh; remote='~' ;;   # Tailscale address of the Mac Studio
  # The Windows box answers cmd.exe and is reached through the university gateway; its
  # connection details live in the mzPeak box.env that already drives that machine.
  windows) : "${BOX_SSH:?set BOX_SSH/BOX_JUMP/BOX_SSH_KEY, e.g. from mzPeakConverter/tools/box.env}"
           host="$BOX_SSH"; script=install_windows_runners.ps1; remote='C:/Users/user' ;;
  *) echo "unknown target $target"; exit 1 ;;
esac
cd "$(dirname "$0")/../.."
repos=$(python3 -c '
import json
for name, e in json.load(open("packages.lock.json"))["packages"].items():
    if name not in ("test-data", "flashapp"):   # test-data has no CI; FLASHApp has no five-platform matrix
        print(e["repository"].removesuffix(".git").rsplit("/", 1)[-1])')
[ -n "$only" ] && repos="$only"
if [ "$target" = windows ]; then
  ssh_opts=(-i "$BOX_SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new
            -o "ProxyCommand=ssh -i $BOX_SSH_KEY -o IdentitiesOnly=yes -W %h:%p $BOX_JUMP")
  scp "${ssh_opts[@]}" -q "tools/hpc/$script" "$host:$remote/$script"
  for repo in $repos; do
    token=$(gh api -X POST "repos/okohlbacher/$repo/actions/runners/registration-token" -q .token)
    echo "$repo $token"
  done | ssh "${ssh_opts[@]}" "$host" "powershell -NoProfile -ExecutionPolicy Bypass -File $remote/$script"
  exit
fi
scp -q "tools/hpc/$script" "$host:$remote/"
for repo in $repos; do
  token=$(gh api -X POST "repos/okohlbacher/$repo/actions/runners/registration-token" -q .token)
  echo "$repo $token"
done | ssh "$host" "chmod +x $remote/$script && $remote/$script"
