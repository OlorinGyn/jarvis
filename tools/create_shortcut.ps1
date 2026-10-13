$root = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'J.A.R.V.I.S.lnk'))
$shortcut.TargetPath = Join-Path $root 'jarvis.bat'
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = (Join-Path $root 'assets\jarvis.ico') + ',0'
$shortcut.Description = 'J.A.R.V.I.S. home surveillance'
$shortcut.Save()
Write-Host "      shortcut created on $desktop"
