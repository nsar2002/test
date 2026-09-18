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
}

function Get-Sha256([string]$Path) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing file: $Path" }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}
function Assert-Hash([string]$Path, [string]$Expected, [string]$Label) {
    $actual = Get-Sha256 $Path
    if ($actual -ne $Expected) { throw "$Label hash mismatch. Expected $Expected, got $actual ($Path)" }
}
function Resolve-PrototypeRoot([string]$ExplicitRoot) {
    if ($ExplicitRoot) {
        $full=[System.IO.Path]::GetFullPath($ExplicitRoot)
        if (!(Test-Path -LiteralPath (Join-Path $full "prototypef.exe") -PathType Leaf)) { throw "Invalid PrototypeRoot: $full" }
        return $full
    }
    $cursor=[System.IO.Path]::GetFullPath($PSScriptRoot)
    for($i=0;$i -lt 6;$i++) {
        if(Test-Path -LiteralPath (Join-Path $cursor "prototypef.exe") -PathType Leaf) { return $cursor }
        $parent=Split-Path -Parent $cursor
        if(!$parent -or $parent -eq $cursor) { break }
        $sibling=Join-Path $parent "Prototype"
        if(Test-Path -LiteralPath (Join-Path $sibling "prototypef.exe") -PathType Leaf) { return [System.IO.Path]::GetFullPath($sibling) }
        $cursor=$parent
    }
    throw "Could not locate Prototype root. Re-run with -PrototypeRoot <path>."
}

$Root=Resolve-PrototypeRoot $PrototypeRoot
$ActiveASI=Join-Path $Root "homelander_p1.asi"
$RootLua=Join-Path $Root "lua_p1"
$BackupDir=Join-Path $Root "Homelander_P1_Backup_Before_V003_FreeAimGate"
$BackupASI=Join-Path $BackupDir "homelander_p1_v001_before_v003.asi"
$BackupLua=Join-Path $BackupDir "lua_p1"

if(Get-Process -Name "prototypef" -ErrorAction SilentlyContinue) { throw "Prototype is running. Close it before rollback." }
Assert-Hash (Join-Path $Root "binkw32.dll") $ExpectedLoader "active loader"
Assert-Hash (Join-Path $Root "binkw32Hooked.dll") $ExpectedOriginalBink "preserved original binkw32"
Assert-Hash $BackupASI $ExpectedV001 "v001 backup ASI"
foreach($entry in $LuaHashes.GetEnumerator()) {
    Assert-Hash (Join-Path $BackupLua $entry.Key) $entry.Value ("backup " + $entry.Key)
}

$activeHash=Get-Sha256 $ActiveASI
if($activeHash -ne $ExpectedV003 -and $activeHash -ne $ExpectedV001) {
    throw "Unexpected active Homelander ASI; refusing rollback. SHA256: $activeHash"
}

Copy-Item -LiteralPath $BackupASI -Destination $ActiveASI -Force
foreach($entry in $LuaHashes.GetEnumerator()) {
    Copy-Item -LiteralPath (Join-Path $BackupLua $entry.Key) -Destination (Join-Path $RootLua $entry.Key) -Force
}
$freeaim=Join-Path $RootLua "freeaim_probe_v004_STAGED.lua"
if(Test-Path -LiteralPath $freeaim) { Remove-Item -LiteralPath $freeaim -Force }

Assert-Hash $ActiveASI $ExpectedV001 "restored v001 ASI"
foreach($entry in $LuaHashes.GetEnumerator()) {
    Assert-Hash (Join-Path $RootLua $entry.Key) $entry.Value ("restored " + $entry.Key)
}
if(Test-Path -LiteralPath $freeaim) { throw "Rollback failed to remove staged free-aim Lua." }

Write-Host "SUCCESS: v001 restored. Loader chain was not modified."
Write-Host "v001 SHA256: $ExpectedV001"