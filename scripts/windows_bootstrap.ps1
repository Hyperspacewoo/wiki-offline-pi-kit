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

function Find-Installer($patterns) {
  foreach ($pattern in $patterns) {
    $match = Get-ChildItem $installers -Filter $pattern -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -First 1
    if ($null -ne $match) {
      return $match
    }
  }
  return $null
}

function Get-WSLExe() {
  $cmd = Get-Command wsl.exe -ErrorAction SilentlyContinue
  if ($null -ne $cmd) {
    return $cmd.Source
  }
  $fallback = Join-Path $env:SystemRoot "System32\wsl.exe"
  if (Test-Path $fallback) {
    return $fallback
  }
  return $null
}

if (-not (Test-Cmd "python")) {
  $pyInstaller = Find-Installer @("python*.exe")
  if ($null -eq $pyInstaller) {
    Write-Warning "Python not found and no python*.exe in $installers"
  } else {
    Write-Host "Installing Python from $($pyInstaller.Name)..."
    Start-Process -FilePath $pyInstaller.FullName -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
  }
} else {
  Write-Host "Python already available"
}

$wslExe = Get-WSLExe
if ($null -eq $wslExe) {
  $wslInstaller = Find-Installer @("wsl.*.x64.msi", "wsl*.x64.msi", "wsl*.msi")
  if ($null -eq $wslInstaller) {
    Write-Warning "WSL not found and no wsl*.msi installer is bundled."
    exit 1
  }

  Write-Host "Installing WSL from $($wslInstaller.Name)..."
  Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$($wslInstaller.FullName)`" /passive /norestart" -Wait
  $wslExe = Get-WSLExe
}

if ($null -eq $wslExe) {
  Write-Warning "WSL still not available after installer run. Reboot Windows if needed, then rerun this launcher."
  exit 1
}

$distroList = @(& $wslExe -l -q 2>$null | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($distroList.Count -eq 0) {
  $ubuntuBundle = Find-Installer @("Ubuntu*.AppxBundle", "Ubuntu*.appxbundle", "Ubuntu*.msixbundle", "Ubuntu*.appx")
  if ($null -ne $ubuntuBundle) {
    Write-Host "Installing Ubuntu WSL bundle from $($ubuntuBundle.Name)..."
    Add-AppxPackage -Path $ubuntuBundle.FullName
    Start-Sleep -Seconds 3
    $distroList = @(& $wslExe -l -q 2>$null | ForEach-Object { $_.Trim() } | Where-Object { $_ })
  }
}

if ($distroList.Count -eq 0) {
  Write-Warning "No initialized WSL distro is available yet. If Ubuntu was just installed, launch it once to finish first-run setup, then rerun START_WINDOWS.bat."
  exit 1
}

$defaultDistro = $distroList[0]
$wslPath = (& $wslExe wslpath -a $KitDir 2>$null | Select-Object -First 1)
if ([string]::IsNullOrWhiteSpace($wslPath)) {
  $drive = $KitDir.Substring(0,1).ToLower()
  $rest = $KitDir.Substring(2).Replace('\','/')
  $wslPath = "/mnt/$drive$rest"
}
$wslPath = $wslPath.Trim()

Write-Host "Running Linux installer in WSL distro: $defaultDistro"
& $wslExe -d $defaultDistro -e bash -lc "cd '$wslPath' && ./INSTALL_OFFLINE_KNOWLEDGE.sh"
if ($LASTEXITCODE -ne 0) {
  throw "WSL installer failed"
}

Write-Host "Done."
