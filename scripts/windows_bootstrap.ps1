param(
  [Parameter(Mandatory=$false)][string]$KitDir
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($KitDir)) {
  $KitDir = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
}

Write-Host "[Offgrid Wiki] Kit dir: $KitDir"
$installers = Join-Path $KitDir "installers"
if (-not (Test-Path $installers)) {
  New-Item -ItemType Directory -Force -Path $installers | Out-Null
}

function Test-Cmd($name) {
  return $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

if (-not (Test-Cmd "python")) {
  $pyInstaller = Get-ChildItem $installers -Filter "python*.exe" -File -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $pyInstaller) {
    Write-Warning "Python not found and no python*.exe in $installers"
  } else {
    Write-Host "Installing Python from $($pyInstaller.Name)..."
    Start-Process -FilePath $pyInstaller.FullName -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
  }
} else {
  Write-Host "Python already available"
}

if (-not (Test-Cmd "wsl")) {
  Write-Warning "WSL not found. Install WSL Ubuntu to run Linux services."
  exit 1
}

$wslPath = (& wsl.exe wslpath -a $KitDir 2>$null | Select-Object -First 1)
if ([string]::IsNullOrWhiteSpace($wslPath)) {
  # Fallback conversion if wslpath is unavailable for some reason.
  $drive = $KitDir.Substring(0,1).ToLower()
  $rest = $KitDir.Substring(2).Replace('\','/')
  $wslPath = "/mnt/$drive$rest"
}
$wslPath = $wslPath.Trim()

Write-Host "Running Linux installer in WSL..."
wsl -e bash -lc "cd '$wslPath' && ./INSTALL_OFFLINE_KNOWLEDGE.sh"
if ($LASTEXITCODE -ne 0) {
  throw "WSL installer failed"
}

Write-Host "Done."
