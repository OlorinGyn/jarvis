$root = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'J.A.R.V.I.S.lnk'))
$shortcut.TargetPath = Join-Path $root 'jarvis.bat'
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = (Join-Path $root 'assets\jarvis.ico') + ',0'
$shortcut.Description = 'Vigilancia domestica J.A.R.V.I.S.'
$shortcut.Save()
Write-Host "      atalho criado em $desktop"
