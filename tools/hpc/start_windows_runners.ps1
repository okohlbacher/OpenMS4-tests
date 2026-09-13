# Run ON the Windows box to bring every registered runner back up (the scheduled tasks
# install_windows_runners.ps1 creates already start at boot, so this is only for a manual
# restart). Registration itself is done once by install_windows_runners.ps1.
$ErrorActionPreference = 'Stop'
Get-ChildItem C:\actions-runners -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName '.runner') } |
  ForEach-Object { & schtasks.exe /run /tn "github-runner-$($_.Name)" }
