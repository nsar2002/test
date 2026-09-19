param(
    [string]$PrototypeRoot = ''
)

$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$Manager = Join-Path $PSScriptRoot 'P1_PROMOTION_MANAGER.ps1'
$Observer = Join-Path $PSScriptRoot 'P1_LIVE_GATE_ASSISTANT.ps1'
$ManifestPath = Join-Path $PSScriptRoot 'promotion_manifest.json'

foreach($p in @($Manager,$Observer,$ManifestPath)) {
    if(!(Test-Path -LiteralPath $p -PathType Leaf)) { throw "Missing required runtime-promotion file: $p" }
}
$Manifest=Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json

function Resolve-PrototypeRoot([string]$ExplicitRoot) {
    if($ExplicitRoot) {
        $full=[System.IO.Path]::GetFullPath($ExplicitRoot)
        if(!(Test-Path -LiteralPath (Join-Path $full 'prototypef.exe') -PathType Leaf)) {
            throw "PrototypeRoot does not contain prototypef.exe: $full"
        }
        return $full
    }
    $cursor=[System.IO.Path]::GetFullPath($PSScriptRoot)
    for($i=0;$i -lt 8;$i++) {
        if(Test-Path -LiteralPath (Join-Path $cursor 'prototypef.exe') -PathType Leaf) { return $cursor }
        $parent=Split-Path -Parent $cursor
        if(!$parent -or $parent -eq $cursor){break}
        $sibling=Join-Path $parent 'Prototype'
        if(Test-Path -LiteralPath (Join-Path $sibling 'prototypef.exe') -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($sibling)
        }
        $cursor=$parent
    }
    throw 'Could not locate Prototype root automatically. Re-run with -PrototypeRoot <path>.'
}
function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Get-ActiveStage([string]$Root) {
    $asi=Join-Path $Root 'homelander_p1.asi'
    if(!(Test-Path -LiteralPath $asi -PathType Leaf)){return 'none'}
    $h=Get-Sha256 $asi
    if($h -eq ([string]$Manifest.baseline.asiSha256).ToLowerInvariant()){return 'v001'}
    foreach($s in @($Manifest.stages)) {
        if($h -eq ([string]$s.asiSha256).ToLowerInvariant()){return [string]$s.stage}
    }
    return 'unknown:'+$h
}

$Root=Resolve-PrototypeRoot $PrototypeRoot
if(Get-Process -Name 'prototypef' -ErrorAction SilentlyContinue) {
    throw 'Prototype is already running. Close it before starting the first controlled v003 live test.'
}

$active=Get-ActiveStage $Root
Write-Host "Prototype root: $Root"
Write-Host "Active Homelander stage: $active"

if($active -eq 'v001') {
    Write-Host 'Installing the ONLY permitted first promotion: v003.' -ForegroundColor Cyan
    & $Manager -Action Install -Stage v003 -PrototypeRoot $Root
    if($LASTEXITCODE -ne 0){throw "v003 install failed with exit code $LASTEXITCODE"}
    $active=Get-ActiveStage $Root
    if($active -ne 'v003'){throw "Post-install verification expected v003, got $active"}
}
elseif($active -ne 'v003') {
    throw "This first-live-test launcher only permits v001 -> v003 or an already-installed v003. Active stage is $active. Refusing any skip or later-stage action."
}

$log=Join-Path $Root 'homelander_p1_runtime.log'
if(Test-Path -LiteralPath $log -PathType Leaf) {
    if((Get-Item -LiteralPath $log).Length -gt 0) {
        throw 'A non-empty runtime log exists. Refusing stale evidence. Use P1_PROMOTION_MANAGER.ps1 -Action ResetLog explicitly before retrying.'
    }
}

Write-Host ''
Write-Host 'Starting v003 live observer.' -ForegroundColor Cyan
Write-Host 'In game: F4 -> aim at nearby NPC/vehicle -> F9.' -ForegroundColor Yellow
Write-Host 'This launcher will NOT record PASS and will NOT unlock v004.'
& $Observer -Action Observe -Stage v003 -PrototypeRoot $Root
exit $LASTEXITCODE
