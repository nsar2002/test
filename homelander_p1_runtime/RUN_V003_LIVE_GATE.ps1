param(
    [string]$PrototypeRoot = "",
    [int]$ReadyTimeoutSeconds = 90,
    [switch]$RollbackOnFail
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedV003 = "1845AFF900E77F7C98E1EF0B37A2EA83C1C293AD74D01DC8FB136A198C9027C2"
$ExpectedLoader = "BC48BAB2CF07EAF616E23BA9EEF1922EA5E8590F722B6657A8F2ED986FE6F20E"
$ExpectedOriginalBink = "DBA257F26517D57ECF3C62ACA7CCCFABBAD868DDF97160F71C9AB81D37A8627"
$BuildReady = "READY build=P1_RuntimeProbe_003_FREEAIM_STAGED_20260918"

function Get-Sha256([string]$Path) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing file: $Path" }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Assert-Hash([string]$Path, [string]$Expected, [string]$Label) {
    $actual = Get-Sha256 $Path
    if ($actual -ne $Expected.ToUpperInvariant()) {
        throw "$Label hash mismatch. Expected $Expected, got $actual ($Path)"
    }
}

function Resolve-PrototypeRoot([string]$ExplicitRoot) {
    if ($ExplicitRoot) {
        $full = [System.IO.Path]::GetFullPath($ExplicitRoot)
        if (!(Test-Path -LiteralPath (Join-Path $full "prototypef.exe") -PathType Leaf)) {
            throw "PrototypeRoot does not contain prototypef.exe: $full"
        }
        return $full
    }
    $cursor = [System.IO.Path]::GetFullPath($PSScriptRoot)
    for ($i=0; $i -lt 7; $i++) {
        if (Test-Path -LiteralPath (Join-Path $cursor "prototypef.exe") -PathType Leaf) { return $cursor }
        $parent = Split-Path -Parent $cursor
        if (!$parent -or $parent -eq $cursor) { break }
        $sibling = Join-Path $parent "Prototype"
        if (Test-Path -LiteralPath (Join-Path $sibling "prototypef.exe") -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($sibling)
        }
        $cursor = $parent
    }
    throw "Could not locate Prototype root. Re-run with -PrototypeRoot <path>."
}

function Assert-SourceTransferManifest {
    $manifest = Join-Path $PSScriptRoot "SHA256SUMS.txt"
    if (!(Test-Path -LiteralPath $manifest -PathType Leaf)) { throw "Missing source transfer manifest: $manifest" }
    $count = 0
    foreach ($line in Get-Content -LiteralPath $manifest) {
        if ($line -match '^([0-9a-fA-F]{64})\s+(.+)$') {
            $expected = $Matches[1]
            $rel = $Matches[2].Trim()
            $path = Join-Path $PSScriptRoot ($rel -replace '/', [System.IO.Path]::DirectorySeparatorChar)
            Assert-Hash $path $expected ("source transfer " + $rel)
            $count++
        }
    }
    if ($count -lt 11) { throw "Source transfer manifest parsed only $count entries; refusing session." }
}

function Invoke-ChildScript([string]$ScriptPath, [string]$Root) {
    $hostExe = (Get-Process -Id $PID).Path
    $args = @("-NoProfile")
    if ([System.IO.Path]::GetFileName($hostExe) -match '^powershell(\.exe)?$') {
        $args += @("-ExecutionPolicy", "Bypass")
    }
    $args += @("-File", $ScriptPath, "-PrototypeRoot", $Root)
    $p = Start-Process -FilePath $hostExe -ArgumentList $args -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "Child script failed with exit code $($p.ExitCode): $ScriptPath" }
}

$Root = Resolve-PrototypeRoot $PrototypeRoot
$Installer = Join-Path $PSScriptRoot "INSTALL_V003_FREEAIM_GATE.ps1"
$Rollback = Join-Path $PSScriptRoot "ROLLBACK_V003_TO_V001.ps1"
$Parser = Join-Path $PSScriptRoot "P1_V003_GATE_PARSER.psm1"

if (!(Test-Path -LiteralPath $Installer)) { throw "Missing installer: $Installer" }
if (!(Test-Path -LiteralPath $Rollback)) { throw "Missing rollback script: $Rollback" }
if (!(Test-Path -LiteralPath $Parser)) { throw "Missing parser module: $Parser" }

if (Get-Process -Name "prototypef" -ErrorAction SilentlyContinue) {
    throw "Prototype is already running. Close it before starting a clean v003 gate session."
}

Write-Host "=== Homelander P1 v003 clean runtime gate ==="
Write-Host "Prototype root: $Root"
Write-Host "1/6 Verifying immutable source transfer..."
Assert-SourceTransferManifest

Write-Host "2/6 Installing/verifying exact v003 payload..."
Invoke-ChildScript $Installer $Root
Assert-Hash (Join-Path $Root "homelander_p1.asi") $ExpectedV003 "active v003 ASI"
Assert-Hash (Join-Path $Root "binkw32.dll") $ExpectedLoader "active Ultimate ASI Loader"
Assert-Hash (Join-Path $Root "binkw32Hooked.dll") $ExpectedOriginalBink "preserved original binkw32"

$SessionRoot = Join-Path $Root "Homelander_P1_RuntimeSessions\v003"
New-Item -ItemType Directory -Force -Path $SessionRoot | Out-Null
$SessionId = (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + ([guid]::NewGuid().ToString("N").Substring(0,8))
$SessionDir = Join-Path $SessionRoot $SessionId
New-Item -ItemType Directory -Force -Path $SessionDir | Out-Null

$Log = Join-Path $Root "homelander_p1_runtime.log"
if (Test-Path -LiteralPath $Log) {
    Move-Item -LiteralPath $Log -Destination (Join-Path $SessionDir "pre_session_runtime.log")
}
$StartUtc = [DateTime]::UtcNow
$State = [ordered]@{
    schema = "homelander-p1-v003-runtime-session/1.0"
    session_id = $SessionId
    started_utc = $StartUtc.ToString("o")
    prototype_root = $Root
    expected_build = "P1_RuntimeProbe_003_FREEAIM_STAGED_20260918"
    expected_asi_sha256 = $ExpectedV003
    log_path = $Log
}
$State | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $SessionDir "session.json") -Encoding UTF8
Set-Content -LiteralPath (Join-Path $SessionRoot "LATEST.txt") -Value $SessionId -Encoding ASCII

Write-Host "3/6 Starting Prototype with a clean log boundary..."
$Game = Start-Process -FilePath (Join-Path $Root "prototypef.exe") -WorkingDirectory $Root -PassThru

$deadline = [DateTime]::UtcNow.AddSeconds([Math]::Max(10,$ReadyTimeoutSeconds))
$ready = $false
while ([DateTime]::UtcNow -lt $deadline) {
    Start-Sleep -Milliseconds 500
    if (Test-Path -LiteralPath $Log) {
        try {
            $rawNow = Get-Content -LiteralPath $Log -Raw -ErrorAction Stop
            if ($rawNow.Contains($BuildReady)) { $ready = $true; break }
        } catch {}
    }
    if ($Game.HasExited) { break }
    try { $Game.Refresh() } catch {}
}

if (!$ready) {
    Write-Host "FAIL: exact v003 READY line was not observed within the clean session timeout."
    Write-Host "The game is NOT killed automatically."
    Write-Host "Session: $SessionDir"
    exit 20
}

Write-Host ""
Write-Host "4/6 READY confirmed from this session only."
Write-Host "In free roam: press F4 once. Then aim at a clear nearby wall/vehicle/NPC and press F9 once."
Write-Host "A fresh F9 HIT is required; a MISS will not pass this gate."
Write-Host "Do NOT press F5/F6/F7 during this gate. Exit Prototype after F9 completes."
Write-Host ""

$seenF4 = $false
$seenHit = $false
while (!$Game.HasExited) {
    Start-Sleep -Milliseconds 700
    try { $Game.Refresh() } catch { break }
    if (Test-Path -LiteralPath $Log) {
        try {
            $live = Get-Content -LiteralPath $Log -Raw -ErrorAction Stop
            if (!$seenF4 -and $live.Contains("[HOMELANDER_P1_PROBE_V3] HOMELANDER_PLAYER SET TO VERIFIED HANDLE")) {
                $seenF4 = $true
                Write-Host "F4 verified-player evidence captured."
            }
            if (!$seenHit -and $live.Contains("[HOMELANDER_P1_FREEAIM_V004] HIT |")) {
                $seenHit = $true
                Write-Host "F9 fresh HIT evidence captured. You can exit Prototype."
            }
        } catch {}
    }
}
try { $Game.WaitForExit() } catch {}
Start-Sleep -Milliseconds 800

Write-Host "5/6 Evaluating only the clean-session log..."
if (!(Test-Path -LiteralPath $Log -PathType Leaf)) {
    Write-Host "FAIL: runtime log was not produced."
    exit 21
}
$LogInfo = Get-Item -LiteralPath $Log
if ($LogInfo.LastWriteTimeUtc -lt $StartUtc) {
    Write-Host "FAIL: runtime log timestamp predates the session boundary."
    exit 22
}
Copy-Item -LiteralPath $Log -Destination (Join-Path $SessionDir "runtime.log") -Force

Import-Module $Parser -Force
$raw = Get-Content -LiteralPath $Log -Raw
$result = Test-V003GateLog -LogText $raw
$report = [ordered]@{
    schema = "homelander-p1-v003-runtime-gate-report/1.0"
    session_id = $SessionId
    evaluated_utc = [DateTime]::UtcNow.ToString("o")
    active_asi_sha256 = Get-Sha256 (Join-Path $Root "homelander_p1.asi")
    parser_result = $result
}
$reportPath = Join-Path $SessionDir "v003_gate_report.json"
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Host ""
$result.checks | Format-List | Out-Host
Write-Host ("camera_axis=" + [string]$result.camera_axis + " margin=" + [string]$result.camera_margin)
Write-Host ("hit_fraction=" + [string]$result.hit_fraction + " hitGOH=" + [string]$result.hit_goh_text + " hitName=" + [string]$result.hit_name_text)
Write-Host "Report: $reportPath"

if (!$result.pass) {
    Write-Host "FAIL: v003 live gate did not pass."
    Write-Host ("Failed checks: " + ($result.failed_checks -join ", "))
    if ($result.forbidden_log_markers.Count -gt 0) {
        Write-Host ("Forbidden markers: " + ($result.forbidden_log_markers -join " | "))
    }
    if ($result.mutation_hotkeys_seen.Count -gt 0) {
        Write-Host ("Mutation hotkeys seen: " + ($result.mutation_hotkeys_seen -join ", "))
    }

    if ($RollbackOnFail) {
        Write-Host "RollbackOnFail requested: restoring the verified v001 backup..."
        Invoke-ChildScript $Rollback $Root
    } else {
        Write-Host "No automatic rollback was performed."
        Write-Host "Rollback command:"
        Write-Host ('powershell -ExecutionPolicy Bypass -File "' + $Rollback + '" -PrototypeRoot "' + $Root + '"')
    }
    exit 30
}

Write-Host ""
Write-Host "6/6 PASS: v003 F4 -> F9 clean-session runtime gate passed."
Write-Host "No automatic promotion to v004 was performed."
Write-Host "v003 remains active until the next ordered gate is explicitly staged."
exit 0
