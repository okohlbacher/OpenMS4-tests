# Run ON the Windows box. One self-hosted GitHub runner per package repository. Every
# runner joins the flashbox-windows-x64 pool that the generated workflows ask for and is
# additionally labelled with its hostname.
#
# Each runner is driven by a scheduled task that starts at boot and runs as SYSTEM, rather
# than by the runner's own Windows service: installing that service succeeds but starting it
# fails with 1068 on this box, and a service account other than NETWORK SERVICE would need a
# password. A task also detaches from the SSH session, which a plain Start-Process does not.
# Registration lines "<repo> <token>" arrive on stdin from register_runners.sh.
$ErrorActionPreference = 'Stop'
$root = 'C:\actions-runners'
$version = '2.337.0'
$archive = Join-Path $root "actions-runner-win-x64-$version.zip"
New-Item -ItemType Directory -Force -Path $root | Out-Null
if (-not (Test-Path $archive)) {
  Invoke-WebRequest -UseBasicParsing -OutFile $archive `
    "https://github.com/actions/runner/releases/download/v$version/actions-runner-win-x64-$version.zip"
}
while ($line = [Console]::In.ReadLine()) {
  $line = $line.Trim()
  if (-not $line) { continue }
  $repo, $token = $line.Split(' ', 2)
  $dir = Join-Path $root $repo
  if (-not (Test-Path (Join-Path $dir 'config.cmd'))) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Expand-Archive -Path $archive -DestinationPath $dir -Force
  }
  # Every runner runs as SYSTEM and would otherwise share one profile, so each gets its own
  # HOME; setup-micromamba refuses to overwrite its own root, so the previous job's is wiped
  # before the next one starts. Git's usr/bin carries the cygpath that action needs.
  New-Item -ItemType Directory -Force -Path (Join-Path $dir 'home') | Out-Null
  Set-Content -Path (Join-Path $dir 'pre-job.ps1') -Encoding ASCII -Value @"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$dir\home\micromamba-bin", "$dir\home\micromamba"
"@
  Set-Content -Path (Join-Path $dir 'start.cmd') -Encoding ASCII -Value @"
@echo off
set "HOME=$dir\home"
set "USERPROFILE=$dir\home"
set "PATH=C:\Program Files\Git\usr\bin;%PATH%"
set "ACTIONS_RUNNER_HOOK_JOB_STARTED=$dir\pre-job.ps1"
cd /d "$dir"
call run.cmd >> "$dir\runner.log" 2>&1
"@
  Push-Location $dir
  # An existing .runner is a registration from an earlier run: config.cmd refuses to touch it
  # (--replace only covers the name on GitHub's side), and removing it needs its own token.
  if (-not (Test-Path (Join-Path $dir '.runner'))) {
    & .\config.cmd --unattended --url "https://github.com/okohlbacher/$repo" `
      --token $token --name "$env:COMPUTERNAME-$repo" `
      --labels "flashbox-windows-x64,$env:COMPUTERNAME" --work _work --disableupdate
  }
  Pop-Location
  $task = "github-runner-$repo"
  & schtasks.exe /create /f /tn $task /ru SYSTEM /sc onstart /rl HIGHEST /tr "$dir\start.cmd" | Out-Null
  & schtasks.exe /end /tn $task 2>&1 | Out-Null
  & schtasks.exe /run /tn $task | Out-Null
  Write-Output "started $env:COMPUTERNAME-$repo"
}
