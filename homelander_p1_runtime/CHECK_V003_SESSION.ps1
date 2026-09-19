param(
    [string]$PrototypeRoot = "",
    [string]$SessionDir = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedV003 = "1845AFF900E77F7C98E1EF0B37A2EA83C1C293AD74D01DC8FB136A198C9027C2"

function Resolve-PrototypeRoot([string]$ExplicitRoot) {
    if ($ExplicitRoot) { return [System.IO.Path]::GetFullPath($ExplicitRoot) }
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
    throw "Could not locate Prototype root."
}

$Root = Resolve-PrototypeRoot $PrototypeRoot
$active = (Get-FileHash -LiteralPath (Join-Path $Root "homelander_p1.asi") -Algorithm SHA256).Hash.ToUpperInvariant()
if ($active -ne $ExpectedV003) { throw "v003 is not active. Active SHA256: $active" }

if (!$SessionDir) {
    $sessionRoot = Join-Path $Root "Homelander_P1_RuntimeSessions\v003"
    $latestFile = Join-Path $sessionRoot "LATEST.txt"
    if (!(Test-Path -LiteralPath $latestFile)) { throw "No v003 session pointer found." }
    $id = (Get-Content -LiteralPath $latestFile -Raw).Trim()
    $SessionDir = Join-Path $sessionRoot $id
}
$SessionDir = [System.IO.Path]::GetFullPath($SessionDir)
$log = Join-Path $SessionDir "runtime.log"
if (!(Test-Path -LiteralPath $log -PathType Leaf)) {
    $activeLog = Join-Path $Root "homelander_p1_runtime.log"
    if (Test-Path -LiteralPath $activeLog -PathType Leaf) { $log = $activeLog }
    else { throw "No runtime.log in session and no active runtime log." }
}

Import-Module (Join-Path $PSScriptRoot "P1_V003_GATE_PARSER.psm1") -Force
$result = Test-V003GateLog -LogText (Get-Content -LiteralPath $log -Raw)
$result | ConvertTo-Json -Depth 8
if ($result.pass) { exit 0 }
exit 30
