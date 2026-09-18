param(
    [string]$PrototypeRoot = "",
    [int]$TailLines = 180
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ExpectedV003 = "1845AFF900E77F7C98E1EF0B37A2EA83C1C293AD74D01DC8FB136A198C9027C2"

function Resolve-PrototypeRoot([string]$ExplicitRoot) {
    if($ExplicitRoot) { return [System.IO.Path]::GetFullPath($ExplicitRoot) }
    $cursor=[System.IO.Path]::GetFullPath($PSScriptRoot)
    for($i=0;$i -lt 6;$i++) {
        if(Test-Path -LiteralPath (Join-Path $cursor "prototypef.exe") -PathType Leaf) { return $cursor }
        $parent=Split-Path -Parent $cursor
        if(!$parent -or $parent -eq $cursor) { break }
        $sibling=Join-Path $parent "Prototype"
        if(Test-Path -LiteralPath (Join-Path $sibling "prototypef.exe") -PathType Leaf) { return [System.IO.Path]::GetFullPath($sibling) }
        $cursor=$parent
    }
    throw "Could not locate Prototype root."
}

$Root=Resolve-PrototypeRoot $PrototypeRoot
$asi=Join-Path $Root "homelander_p1.asi"
$hash=(Get-FileHash -LiteralPath $asi -Algorithm SHA256).Hash.ToUpperInvariant()
if($hash -ne $ExpectedV003) { throw "v003 is not active. Active SHA256: $hash" }

$log=Join-Path $Root "homelander_p1_runtime.log"
if(!(Test-Path -LiteralPath $log)) {
    Write-Host "NO LOG: launch Prototype once after installing v003."
    exit 2
}
$raw=Get-Content -LiteralPath $log -Raw
$boot=$raw.Contains("READY build=P1_RuntimeProbe_003_FREEAIM_STAGED_20260918")
$f9Dispatch=$raw.Contains("F9: read-only free-aim camera/LOS probe")
$f9End=$raw.Contains("[HOMELANDER_P1_FREEAIM_V004] END")
$f9Hit=$raw.Contains("[HOMELANDER_P1_FREEAIM_V004] HIT |")
$f9Miss=$raw.Contains("[HOMELANDER_P1_FREEAIM_V004] MISS |")
$fatal=($raw -match "FATAL|FAIL signature|FAIL consistent ref|Lua compile error|Lua runtime error")

Write-Host ("BOOT READY: " + $boot)
Write-Host ("F9 DISPATCH SEEN: " + $f9Dispatch)
Write-Host ("F9 COMPLETED READ-ONLY PROBE: " + $f9End)
Write-Host ("F9 HIT SEEN: " + $f9Hit)
Write-Host ("F9 MISS SEEN: " + $f9Miss)
Write-Host ("FATAL/RESOLUTION ERROR TEXT SEEN: " + $fatal)
Write-Host ""
Write-Host "Latest relevant log lines:"
Get-Content -LiteralPath $log -Tail $TailLines | Where-Object {
    $_ -match "READY|F4:|F9:|FREEAIM|FAIL|FATAL|Lua .*error"
}