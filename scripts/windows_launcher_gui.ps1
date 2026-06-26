param(
  [Parameter(Mandatory=$false)][string]$KitDir
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($KitDir)) {
  $KitDir = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
}
$KitDir = (Resolve-Path -LiteralPath $KitDir).Path
$Bootstrap = Join-Path $KitDir "scripts\windows_bootstrap.ps1"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

function Open-Url($Url) {
  try {
    Start-Process $Url
    Set-Status "Opened $Url"
  } catch {
    Set-Status "Could not open $Url`r`n$($_.Exception.Message)"
  }
}

function Set-Status($Text) {
  $script:StatusBox.Text = $Text
}

function Start-Bootstrap {
  if (-not (Test-Path -LiteralPath $Bootstrap)) {
    Set-Status "Missing bootstrap: $Bootstrap"
    return
  }

  $launchArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-NoExit",
    "-File", "`"$Bootstrap`"",
    "-KitDir", "`"$KitDir`"",
    "-OpenDashboard"
  )
  try {
    Start-Process -FilePath "powershell.exe" -ArgumentList $launchArgs -WorkingDirectory $KitDir
    Set-Status "Started setup/repair in a PowerShell window. The dashboard opens when setup finishes."
  } catch {
    Set-Status "Could not start setup/repair.`r`n$($_.Exception.Message)"
  }
}

function Check-Health {
  try {
    $r = Invoke-RestMethod -Uri "http://localhost:8090/health" -TimeoutSec 4
    Set-Status "Dashboard health:`r`n$($r.summary)"
  } catch {
    Set-Status "Dashboard is not responding yet. Click Start / Repair Kit, then try again.`r`n$($_.Exception.Message)"
  }
}

$Form = New-Object System.Windows.Forms.Form
$Form.Text = "Offgrid Kit Launcher"
$Form.StartPosition = "CenterScreen"
$Form.Size = New-Object System.Drawing.Size(620, 520)
$Form.MinimumSize = New-Object System.Drawing.Size(560, 460)
$Form.BackColor = [System.Drawing.Color]::FromArgb(246, 248, 252)

$Title = New-Object System.Windows.Forms.Label
$Title.Text = "Offgrid Kit"
$Title.Font = New-Object System.Drawing.Font("Segoe UI", 24, [System.Drawing.FontStyle]::Bold)
$Title.ForeColor = [System.Drawing.Color]::FromArgb(23, 32, 51)
$Title.AutoSize = $true
$Title.Location = New-Object System.Drawing.Point(24, 20)
$Form.Controls.Add($Title)

$Subtitle = New-Object System.Windows.Forms.Label
$Subtitle.Text = "Start the kit, open the dashboard, and verify the local offline services."
$Subtitle.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$Subtitle.ForeColor = [System.Drawing.Color]::FromArgb(92, 104, 125)
$Subtitle.AutoSize = $true
$Subtitle.Location = New-Object System.Drawing.Point(28, 68)
$Form.Controls.Add($Subtitle)

$Primary = New-Object System.Windows.Forms.Button
$Primary.Text = "Start / Repair Kit"
$Primary.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$Primary.BackColor = [System.Drawing.Color]::FromArgb(10, 132, 255)
$Primary.ForeColor = [System.Drawing.Color]::White
$Primary.FlatStyle = "Flat"
$Primary.Size = New-Object System.Drawing.Size(250, 48)
$Primary.Location = New-Object System.Drawing.Point(28, 110)
$Primary.Add_Click({ Start-Bootstrap })
$Form.Controls.Add($Primary)

$OpenDashboard = New-Object System.Windows.Forms.Button
$OpenDashboard.Text = "Open Dashboard"
$OpenDashboard.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$OpenDashboard.BackColor = [System.Drawing.Color]::FromArgb(11, 127, 95)
$OpenDashboard.ForeColor = [System.Drawing.Color]::White
$OpenDashboard.FlatStyle = "Flat"
$OpenDashboard.Size = New-Object System.Drawing.Size(250, 48)
$OpenDashboard.Location = New-Object System.Drawing.Point(304, 110)
$OpenDashboard.Add_Click({ Open-Url "http://localhost:8090" })
$Form.Controls.Add($OpenDashboard)

$buttons = @(
  @("Setup Check", "http://localhost:8090/setup"),
  @("Knowledge", "http://localhost:8080"),
  @("Maps", "http://localhost:8091"),
  @("Offline AI", "http://localhost:8092"),
  @("Ebooks", "http://localhost:8090/ebooks"),
  @("Updates", "http://localhost:8090/updates"),
  @("Field Cards", "http://localhost:8090/field-cards"),
  @("Offline Proof", "http://localhost:8090/offline-proof")
)

$x0 = 28
$y0 = 178
$w = 118
$h = 38
$gapX = 20
$gapY = 12
for ($i = 0; $i -lt $buttons.Count; $i++) {
  $b = New-Object System.Windows.Forms.Button
  $b.Text = $buttons[$i][0]
  $b.Tag = $buttons[$i][1]
  $b.Font = New-Object System.Drawing.Font("Segoe UI", 9)
  $b.BackColor = [System.Drawing.Color]::White
  $b.ForeColor = [System.Drawing.Color]::FromArgb(23, 32, 51)
  $b.FlatStyle = "Flat"
  $b.Size = New-Object System.Drawing.Size($w, $h)
  $col = $i % 4
  $row = [Math]::Floor($i / 4)
  $b.Location = New-Object System.Drawing.Point(($x0 + ($col * ($w + $gapX))), ($y0 + ($row * ($h + $gapY))))
  $b.Add_Click({ Open-Url $this.Tag })
  $Form.Controls.Add($b)
}

$Health = New-Object System.Windows.Forms.Button
$Health.Text = "Health Check"
$Health.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$Health.BackColor = [System.Drawing.Color]::White
$Health.ForeColor = [System.Drawing.Color]::FromArgb(23, 32, 51)
$Health.FlatStyle = "Flat"
$Health.Size = New-Object System.Drawing.Size(156, 42)
$Health.Location = New-Object System.Drawing.Point(28, 286)
$Health.Add_Click({ Check-Health })
$Form.Controls.Add($Health)

$Folder = New-Object System.Windows.Forms.Button
$Folder.Text = "Open Kit Folder"
$Folder.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$Folder.BackColor = [System.Drawing.Color]::White
$Folder.ForeColor = [System.Drawing.Color]::FromArgb(23, 32, 51)
$Folder.FlatStyle = "Flat"
$Folder.Size = New-Object System.Drawing.Size(156, 42)
$Folder.Location = New-Object System.Drawing.Point(204, 286)
$Folder.Add_Click({ Start-Process explorer.exe -ArgumentList "`"$KitDir`""; Set-Status "Opened kit folder." })
$Form.Controls.Add($Folder)

$Exit = New-Object System.Windows.Forms.Button
$Exit.Text = "Close"
$Exit.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$Exit.BackColor = [System.Drawing.Color]::White
$Exit.ForeColor = [System.Drawing.Color]::FromArgb(23, 32, 51)
$Exit.FlatStyle = "Flat"
$Exit.Size = New-Object System.Drawing.Size(156, 42)
$Exit.Location = New-Object System.Drawing.Point(380, 286)
$Exit.Add_Click({ $Form.Close() })
$Form.Controls.Add($Exit)

$script:StatusBox = New-Object System.Windows.Forms.TextBox
$script:StatusBox.Multiline = $true
$script:StatusBox.ReadOnly = $true
$script:StatusBox.ScrollBars = "Vertical"
$script:StatusBox.Font = New-Object System.Drawing.Font("Consolas", 9)
$script:StatusBox.BackColor = [System.Drawing.Color]::White
$script:StatusBox.ForeColor = [System.Drawing.Color]::FromArgb(23, 32, 51)
$script:StatusBox.Size = New-Object System.Drawing.Size(528, 108)
$script:StatusBox.Location = New-Object System.Drawing.Point(28, 350)
$Form.Controls.Add($script:StatusBox)

Set-Status "Ready. Click Start / Repair Kit on a fresh machine, or Open Dashboard if services are already running."
[void]$Form.ShowDialog()
