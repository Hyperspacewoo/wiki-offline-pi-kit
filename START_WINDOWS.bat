@echo off
setlocal enabledelayedexpansion

for %%I in ("%~dp0") do set "KIT_DIR=%%~fI"
if "%KIT_DIR:~-1%"=="\" set "KIT_DIR=%KIT_DIR:~0,-1%"
set "PS1=%KIT_DIR%\scripts\windows_bootstrap.ps1"

echo [Offgrid Wiki] Windows launcher
if exist "%PS1%" (
  where powershell.exe >nul 2>nul
  if not errorlevel 1 (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -KitDir "%KIT_DIR%"
  ) else (
    where pwsh.exe >nul 2>nul
    if errorlevel 1 (
      echo Neither powershell.exe nor pwsh.exe was found.
      pause
      exit /b 1
    )
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -KitDir "%KIT_DIR%"
  )
  if errorlevel 1 (
    echo Windows bootstrap failed.
    pause
    exit /b 1
  )
  goto :eof
)

echo PowerShell bootstrap not found: %PS1%
echo Falling back to WSL Ubuntu installer...
where wsl >nul 2>nul
if errorlevel 1 (
  echo WSL is not installed. Install WSL and Ubuntu first, then run:
  echo   bash ./INSTALL_OFFLINE_KNOWLEDGE.sh
  pause
  exit /b 1
)

for /f "delims=" %%P in ('wsl wslpath -a "%KIT_DIR%"') do set "WSL_PATH=%%P"
if not defined WSL_PATH (
  echo Could not translate Windows path into WSL path.
  pause
  exit /b 1
)

wsl -e bash -lc "cd \"%WSL_PATH%\" && ./INSTALL_OFFLINE_KNOWLEDGE.sh"
if errorlevel 1 (
  echo Installer failed in WSL.
  pause
  exit /b 1
)

echo Done.
pause
