param(
    [string]$PrototypeRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedV001 = "577BE0AD57823B8CF562BEE014D2656819FF5C4159EF74B3C195E842D747B104"
$ExpectedV003 = "1845AFF900E77F7C98E1EF0B37A2EA83C1C293AD74D01DC8FB136A198C9027C2"
$ExpectedLoader = "BC48BAB2CF07EAF616E23BA9EEF1922EA5E8590F722B6657A8F2ED986FE6F20E"
$ExpectedOriginalBink = "DBA257F26517D57ECF3C62ACA7CCCFABBAD868DDF97160F71C9AB81D37A8627"
$LuaHashes = @{
    "runtime_probe.lua" = "BD7A6EC2006466B0F7B46F966F384103D35D5D98020BCDCE1112E9B4F363A650"
    "setter_echo_probe.lua" = "EF6857400CCEEA36278514C5808EE8290FB15DAF5827BE3DF35EB05BA5AA7B81"
    "flight_math_probe.lua" = "033BAFEC3A64F6E5C9466481D896EED35A67206703BF09BE4054369E35150FA9"
    "flight_controller_v1.lua" = "4D84D44F39B2BBC0CEF7AE4513BF73F17EAC717C80C80EB3263616207485F577B"
    "heatvision_probe.lua" = "914A6631F9E1E5C90FFF8FAF335443211B990000B985134F32B7B2D1633A2F51"
    "freeaim_probe_v004_STAGED.lua" = "89885EECDF1DCD1F324C6CD3C3580013674639167E0849688ED7036C75678CD1"
}

function Get-Sha256([string]$Path) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing file: $Path"
    }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Assert-Hash([string]$Path, [string]$Expected, [string]$Label) {
    $actual = Get-Sha256 $Path
    if ($actual -ne $Expected) {
        throw "$Label hash mismatch.`nExpected: $Expected`nActual:   $actual`nFile: $Path"
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
    for ($i = 0; $i -lt 6; $i++) {
        if (Test-Path -LiteralPath (Join-Path $cursor "prototypef.exe") -PathType Leaf) {
            return $cursor
        }
        $parent = Split-Path -Parent $cursor
        if (!$parent -or $parent -eq $cursor) { break }
        $sibling = Join-Path $parent "Prototype"
        if (Test-Path -LiteralPath (Join-Path $sibling "prototypef.exe") -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($sibling)
        }
        $cursor = $parent
    }
    throw "Could not locate the Prototype root automatically. Re-run with -PrototypeRoot <path>."
}

$Root = Resolve-PrototypeRoot $PrototypeRoot
$Payload = Join-Path $PSScriptRoot "payload"
$PayloadASI = Join-Path $Payload "homelander_p1.asi"
$PayloadLua = Join-Path $Payload "lua_p1"
$ActiveASI = Join-Path $Root "homelander_p1.asi"
$RootLua = Join-Path $Root "lua_p1"
$BackupDir = Join-Path $Root "Homelander_P1_Backup_Before_V003_FreeAimGate"
$BackupLua = Join-Path $BackupDir "lua_p1"

Write-Host "Homelander P1 v003 FreeAimGate installer"
Write-Host "Prototype root: $Root"

if (Get-Process -Name "prototypef" -ErrorAction SilentlyContinue) {
    throw "Prototype is running. Close the game before installing."
}

# Payload is immutable for this gate.
Assert-Hash $PayloadASI $ExpectedV003 "v003 payload ASI"
foreach ($entry in $LuaHashes.GetEnumerator()) {
    Assert-Hash (Join-Path $PayloadLua $entry.Key) $entry.Value ("payload " + $entry.Key)
}

# Existing loader chain must already be the verified chain; installer never modifies it.
Assert-Hash (Join-Path $Root "binkw32.dll") $ExpectedLoader "active Ultimate ASI Loader"
Assert-Hash (Join-Path $Root "binkw32Hooked.dll") $ExpectedOriginalBink "preserved original binkw32"

$activeHash = Get-Sha256 $ActiveASI
if ($activeHash -eq $ExpectedV003) {
    Write-Host "v003 ASI is already active. Verifying all six Lua files..."
    foreach ($entry in $LuaHashes.GetEnumerator()) {
        Assert-Hash (Join-Path $RootLua $entry.Key) $entry.Value ("active " + $entry.Key)
    }
    Write-Host "PASS: v003 FreeAimGate is already installed and hash-correct."
    exit 0
}
if ($activeHash -ne $ExpectedV001) {
    throw "Unexpected active Homelander ASI. This gate only promotes the confirmed v001 state.`nActive SHA256: $activeHash"
}

# Verify current v001 Lua baseline before backup/write. freeaim must not pre-exist.
foreach ($name in @("runtime_probe.lua","setter_echo_probe.lua","flight_math_probe.lua","flight_controller_v1.lua","heatvision_probe.lua")) {
    Assert-Hash (Join-Path $RootLua $name) $LuaHashes[$name] ("active v001 " + $name)
}
$existingFreeAim = Join-Path $RootLua "freeaim_probe_v004_STAGED.lua"
if (Test-Path -LiteralPath $existingFreeAim) {
    throw "Unexpected pre-existing freeaim_probe_v004_STAGED.lua. Refusing to overwrite."
}

# Stable, verifiable rollback snapshot.
New-Item -ItemType Directory -Force -Path $BackupLua | Out-Null
$BackupASI = Join-Path $BackupDir "homelander_p1_v001_before_v003.asi"
if (Test-Path -LiteralPath $BackupASI) {
    Assert-Hash $BackupASI $ExpectedV001 "existing v001 backup ASI"
} else {
    Copy-Item -LiteralPath $ActiveASI -Destination $BackupASI
    Assert-Hash $BackupASI $ExpectedV001 "new v001 backup ASI"
}
foreach ($name in @("runtime_probe.lua","setter_echo_probe.lua","flight_math_probe.lua","flight_controller_v1.lua","heatvision_probe.lua")) {
    $src = Join-Path $RootLua $name
    $dst = Join-Path $BackupLua $name
    if (Test-Path -LiteralPath $dst) {
        Assert-Hash $dst $LuaHashes[$name] ("existing backup " + $name)
    } else {
        Copy-Item -LiteralPath $src -Destination $dst
        Assert-Hash $dst $LuaHashes[$name] ("new backup " + $name)
    }
}

# Promote only after every precondition and backup check passed.
Copy-Item -LiteralPath $PayloadASI -Destination $ActiveASI -Force
New-Item -ItemType Directory -Force -Path $RootLua | Out-Null
foreach ($entry in $LuaHashes.GetEnumerator()) {
    Copy-Item -LiteralPath (Join-Path $PayloadLua $entry.Key) -Destination (Join-Path $RootLua $entry.Key) -Force
}

# Post-write verification.
Assert-Hash $ActiveASI $ExpectedV003 "installed v003 ASI"
foreach ($entry in $LuaHashes.GetEnumerator()) {
    Assert-Hash (Join-Path $RootLua $entry.Key) $entry.Value ("installed " + $entry.Key)
}

$Receipt = Join-Path $Root "HOMELANDER_P1_V003_FREEAIM_GATE_RECEIPT.txt"
@"
Homelander P1 RuntimeProbe v003 FreeAimGate
Installed: $(Get-Date -Format o)
Previous ASI: v001
Previous ASI SHA256: $ExpectedV001
Installed ASI SHA256: $ExpectedV003
Backup directory: $BackupDir
Package directory: $PSScriptRoot
Safety gate: F9 is read-only; no damage/VFX/physics mutation.
"@ | Set-Content -LiteralPath $Receipt -Encoding ASCII

Write-Host ""
Write-Host "SUCCESS: v003 FreeAimGate installed."
Write-Host "ASI SHA256: $ExpectedV003"
Write-Host "Backup: $BackupDir"
Write-Host "Next runtime gate: launch Prototype, verify READY in homelander_p1_runtime.log, run F4, then aim at a clear object and press F9."