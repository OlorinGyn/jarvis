param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('install', 'update', 'status', 'start', 'stop', 'check', 'register')]
    [string]$Action,
    [string]$Tag = '',
    [string]$ProdDir = 'C:\JARVIS',
    [string]$Repo = '',
    [switch]$SkipTask
)

$ErrorActionPreference = 'Stop'
$TaskName = 'JARVIS'
$DevDir = Split-Path -Parent $PSScriptRoot
$HealthSeconds = 90
$FreshSeconds = 5
$RetryMinutes = 5

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    $env:Path += ';C:\Program Files\Git\cmd'
}
if (-not $Repo) {
    $Repo = (git -C $DevDir remote get-url jarvis)
}

function Say([string]$Text) { Write-Host "[production] $Text" }

function Invoke-ProdGit { git -C $ProdDir @args; if ($LASTEXITCODE) { throw "git $args failed" } }

function Python { & (Join-Path $ProdDir '.venv\Scripts\python.exe') @args }

function HoldFile { Join-Path $ProdDir 'HOLD' }

function Hold([string]$Why) { Set-Content -Path (HoldFile) -Value $Why -Encoding ASCII }

function Release { Remove-Item (HoldFile) -ErrorAction SilentlyContinue }

function Port {
    $envFile = Join-Path $ProdDir '.env'
    if (Test-Path $envFile) {
        $line = Select-String -Path $envFile -Pattern '^\s*WEB_PORT\s*=\s*(\d+)' | Select-Object -First 1
        if ($line) { return [int]$line.Matches[0].Groups[1].Value }
    }
    return 8765
}

function CurrentVersion {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $exact = git -C $ProdDir describe --tags --exact-match 2>$null
    $found = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $previous
    if ($found) { return $exact }
    return (git -C $ProdDir rev-parse --short HEAD)
}

function LatestTag {
    Invoke-ProdGit fetch --tags --quiet
    $latest = git -C $ProdDir tag --list 'v*' --sort=-v:refname | Select-Object -First 1
    if (-not $latest) { throw 'No release tag yet. The architect tags a release after a review.' }
    return $latest
}

function Status {
    try {
        return Invoke-RestMethod "http://127.0.0.1:$(Port)/api/status" -TimeoutSec 3
    } catch {
        return $null
    }
}

function Healthy {
    $deadline = (Get-Date).AddSeconds($HealthSeconds)
    while ((Get-Date) -lt $deadline) {
        $state = Status
        if ($state -and @($state.cameras).Count -gt 0) {
            $ages = $state.frame_age.PSObject.Properties.Value
            $fresh = @($ages | Where-Object { $_ -ne $null -and $_ -lt $FreshSeconds })
            if ($fresh.Count -eq @($state.cameras).Count) { return $true }
        }
        Start-Sleep 3
    }
    return $false
}

function StopService {
    if (Status) {
        Say 'Stopping the service cleanly...'
        Push-Location $ProdDir
        try { Python -m jarvis --stop | Out-Host } finally { Pop-Location }
    }
    WaitForExit 180
}

function ProdProcesses {
    $root = (Resolve-Path $ProdDir).Path
    Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.StartsWith($root, [StringComparison]::OrdinalIgnoreCase) }
}

function WaitForExit([int]$Seconds) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((ProdProcesses) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 1 }
    $left = @(ProdProcesses)
    if ($left.Count) { throw "The old version is still running after $Seconds s ($($left.Count) process(es)); not starting another next to it." }
}

function StartService {
    Release
    Start-Process -FilePath (Join-Path $ProdDir '.venv\Scripts\pythonw.exe') `
        -ArgumentList '-m', 'jarvis', '--headless' -WorkingDirectory $ProdDir
}

function CheckData([string]$When) {
    Say "Checking that every existing file is still readable ($When)..."
    Push-Location $ProdDir
    try {
        Python tools\check_data.py | Out-Host
        $ok = ($LASTEXITCODE -eq 0)
    } finally { Pop-Location }
    return $ok
}

function Sync {
    Push-Location $ProdDir
    try {
        uv sync --frozen --no-dev
        if ($LASTEXITCODE) { throw 'uv sync failed' }
    } finally { Pop-Location }
    $signature = Get-AuthenticodeSignature (Join-Path $ProdDir '.venv\Scripts\pythonw.exe')
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
        throw 'The production Python is not the signed python.org build; Smart App Control may block it. See INSTALACAO 1.2.'
    }
}

function Notify([string]$Text) {
    Push-Location $ProdDir
    try { Python -c "from jarvis import notify; notify.send('$Text')" | Out-Null } catch { } finally { Pop-Location }
}

function CopyData {
    foreach ($name in '.env', 'config.json') {
        $source = Join-Path $DevDir $name
        $target = Join-Path $ProdDir $name
        if ((Test-Path $source) -and -not (Test-Path $target)) {
            Copy-Item $source $target
            Say "Copied $name"
        }
    }
    foreach ($folder in 'models', 'clips', 'faces') {
        $source = Join-Path $DevDir $folder
        if (Test-Path $source) {
            robocopy $source (Join-Path $ProdDir $folder) /E /XD _buffer _diag /NFL /NDL /NJH /NJS /NP | Out-Null
            if ($LASTEXITCODE -ge 8) { throw "copying $folder failed (robocopy $LASTEXITCODE)" }
            Say "Copied $folder\ (the originals stay where they were)"
        }
    }
}

function RegisterTask {
    $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $admin) { throw 'Registering the startup task needs an administrator PowerShell.' }
    $action = New-ScheduledTaskAction -Execute (Join-Path $ProdDir '.venv\Scripts\pythonw.exe') `
        -Argument '-m jarvis --headless' -WorkingDirectory $ProdDir
    $atStartup = New-ScheduledTaskTrigger -AtStartup
    $retry = New-ScheduledTaskTrigger -Once -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes $RetryMinutes) -RepetitionDuration (New-TimeSpan -Days 3650)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $atStartup, $retry `
        -Principal $principal -Settings $settings -Force | Out-Null
    Say "Task '$TaskName': starts with Windows, and every $RetryMinutes min starts it again if it is not running."
}

function RegisterTaskElevated {
    Say 'Registering the startup task needs administrator rights: Windows will ask for permission now.'
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Action register -ProdDir `"$ProdDir`""
    try {
        $child = Start-Process powershell -Verb RunAs -ArgumentList $arguments -Wait -PassThru
    } catch {
        Say 'Permission refused. Production is running now but will not come back after a reboot.'
        Say "Later, from an administrator PowerShell: tools\production.ps1 -Action register"
        return
    }
    if ($child.ExitCode -eq 0 -and (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)) {
        Say 'Startup task registered.'
    } else {
        Say "The task was not registered (exit code $($child.ExitCode)). Run -Action register as administrator."
    }
}

function Install {
    if (Test-Path (Join-Path $ProdDir '.git')) { throw "$ProdDir already has an installation. Use -Action update." }
    Say "Cloning $Repo into $ProdDir..."
    git clone --quiet $Repo $ProdDir
    if ($LASTEXITCODE) { throw 'git clone failed' }
    $target = if ($Tag) { $Tag } else { LatestTag }
    Invoke-ProdGit checkout --quiet --force $target
    Say "Version: $target"
    StopDevCopy
    CopyData
    Sync
    if (-not (CheckData 'copied data, new installation')) { throw 'Existing data is not readable by this version. Nothing was started.' }
    StartService
    if (-not (Healthy)) {
        throw 'Installed, but the cameras did not deliver frames in time. Read logs\jarvis.log in the production folder.'
    }
    Say "Production is running $target, every camera delivering frames."
    if ($SkipTask) { return }
    Notify "J.A.R.V.I.S. production installed: $target"
    ConfigureTestCopy
    DesktopShortcut
    RegisterTaskElevated
}

function StopDevCopy {
    $devPython = Join-Path $DevDir '.venv\Scripts\python.exe'
    if (Test-Path $devPython) {
        Push-Location $DevDir
        try { & $devPython -m jarvis --stop | Out-Null } catch { } finally { Pop-Location }
    }
}

function SetEnvValue([string]$File, [string]$Key, [string]$Value) {
    $lines = @([IO.File]::ReadAllLines($File))
    if ($lines -match "^\s*$Key\s*=") {
        $lines = $lines -replace "^\s*$Key\s*=.*", "$Key=$Value"
    } else {
        $lines += "$Key=$Value"
    }
    [IO.File]::WriteAllLines($File, [string[]]$lines, (New-Object Text.UTF8Encoding $false))
}

function ConfigureTestCopy {
    $envFile = Join-Path $DevDir '.env'
    if (Test-Path $envFile) {
        SetEnvValue $envFile 'CAM_STREAM' 'stream2'
        SetEnvValue $envFile 'WEB_PORT' '8766'
        Say 'Development copy is now the test copy: stream2 (640x360), port 8766.'
    }
    $devPython = Join-Path $DevDir '.venv\Scripts\python.exe'
    Push-Location $DevDir
    try {
        & $devPython -c "from jarvis import settings; settings.update(notify_token='', notify_prefix='[TEST]', archive_path='')"
        Say 'Test copy: Telegram off and no external drive (production keeps both), prefix [TEST].'
    } finally { Pop-Location }
}

function DesktopShortcut {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $old = Join-Path $desktop 'J.A.R.V.I.S.lnk'
    if (Test-Path $old) {
        Move-Item $old (Join-Path $desktop 'J.A.R.V.I.S. (test).lnk') -Force
    }
    $icon = Join-Path $ProdDir 'assets\jarvis.ico'
    $content = "[InternetShortcut]`r`nURL=http://127.0.0.1:$(Port)/`r`nIconFile=$icon`r`nIconIndex=0`r`n"
    Set-Content -Path (Join-Path $desktop 'J.A.R.V.I.S.url') -Value $content -Encoding ASCII
    Say "Desktop: 'J.A.R.V.I.S.' opens production; 'J.A.R.V.I.S. (test)' starts the test copy."
}

function SwitchTo([string]$Version) {
    Invoke-ProdGit checkout --quiet --force $Version
    Sync
}

function Update {
    if (-not (Test-Path (Join-Path $ProdDir '.git'))) { throw "Nothing installed in $ProdDir. Use -Action install." }
    $previous = CurrentVersion
    $target = if ($Tag) { Invoke-ProdGit fetch --tags --quiet; $Tag } else { LatestTag }
    if ($target -eq $previous) { Say "Already on $target."; return }
    Say "Updating $previous -> $target"

    if (-not (CheckData 'before, current version')) { throw 'Data already unreadable before updating; nothing changed. Investigate first.' }
    Hold "update $previous -> $target"
    StopService
    $good = $false
    try {
        SwitchTo $target
        $good = CheckData 'after, new version'
        if ($good) {
            StartService
            $good = Healthy
        }
    } catch {
        Say "Error during the update: $_"
    }
    if ($good) {
        Say "Production is running $target."
        Notify "J.A.R.V.I.S. production updated: $previous -> $target"
        return
    }

    Say "The new version failed. Rolling back to $previous..."
    $back = $false
    try {
        Hold "rollback to $previous"
        StopService
        SwitchTo $previous
        StartService
        $back = Healthy
    } catch {
        Say "Error during the rollback: $_"
    }
    Notify "J.A.R.V.I.S. update to $target FAILED; rolled back to $previous (running: $back)"
    throw "Update to $target failed and was rolled back to $previous. Running again: $back."
}

function ShowStatus {
    if (-not (Test-Path (Join-Path $ProdDir '.git'))) { Say "Not installed in $ProdDir."; return }
    Say "Version: $(CurrentVersion)"
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Say "Startup task: $(if ($task) { $task.State } else { 'not registered' })"
    if (Test-Path (HoldFile)) { Say "HELD: $(Get-Content (HoldFile)) - the task will not start it. Use -Action start." }
    $state = Status
    if ($state) {
        $ages = ($state.frame_age.PSObject.Properties | ForEach-Object { "$($_.Name) $($_.Value) s" }) -join ', '
        Say "Running on port $(Port). Last frame: $ages"
    } else {
        Say "Not answering on port $(Port)."
    }
}

switch ($Action) {
    'install' { Install }
    'update' { Update }
    'status' { ShowStatus }
    'start' { StartService; if (Healthy) { Say 'Running.' } else { throw 'Started, but no frames in time.' } }
    'stop' { Hold 'stopped on request'; StopService; Say 'Stopped, and held until -Action start.' }
    'check' { if (CheckData 'on request') { Say 'Data OK.' } else { throw 'Some files are not readable by this version.' } }
    'register' { RegisterTask }
}
