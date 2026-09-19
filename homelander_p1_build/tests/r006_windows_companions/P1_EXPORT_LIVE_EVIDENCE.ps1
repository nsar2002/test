param(
    [ValidateSet('Export','SelfTest')]
    [string]$Action = 'Export',
    [string]$PrototypeRoot = '',
    [string]$OutputDirectory = ''
)

$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ManifestPath=Join-Path $PSScriptRoot 'promotion_manifest.json'
if(!(Test-Path -LiteralPath $ManifestPath -PathType Leaf)){throw "Missing manifest: $ManifestPath"}
$Manifest=Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$Stages=@($Manifest.stages)

function UtcNow { [DateTime]::UtcNow.ToString('o') }
function SafeStamp { [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') }
function Get-Sha256([string]$Path) {
    if(!(Test-Path -LiteralPath $Path -PathType Leaf)){throw "Missing file: $Path"}
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Resolve-PrototypeRoot([string]$ExplicitRoot) {
    if($ExplicitRoot){
        $full=[System.IO.Path]::GetFullPath($ExplicitRoot)
        if(!(Test-Path -LiteralPath (Join-Path $full 'prototypef.exe') -PathType Leaf)){throw "PrototypeRoot does not contain prototypef.exe: $full"}
        return $full
    }
    $cursor=[System.IO.Path]::GetFullPath($PSScriptRoot)
    for($i=0;$i -lt 8;$i++){
        if(Test-Path -LiteralPath (Join-Path $cursor 'prototypef.exe') -PathType Leaf){return $cursor}
        $parent=Split-Path -Parent $cursor
        if(!$parent -or $parent -eq $cursor){break}
        $sibling=Join-Path $parent 'Prototype'
        if(Test-Path -LiteralPath (Join-Path $sibling 'prototypef.exe') -PathType Leaf){return [System.IO.Path]::GetFullPath($sibling)}
        $cursor=$parent
    }
    throw 'Could not locate Prototype root automatically. Re-run with -PrototypeRoot <path>.'
}
function Get-ActiveStage([string]$Root) {
    $asi=Join-Path $Root 'homelander_p1.asi'
    if(!(Test-Path -LiteralPath $asi -PathType Leaf)){return 'none'}
    $h=Get-Sha256 $asi
    if($h -eq ([string]$Manifest.baseline.asiSha256).ToLowerInvariant()){return 'v001'}
    foreach($s in $Stages){if($h -eq ([string]$s.asiSha256.ToLowerInvariant())){return [string]$s.stage}}
    return 'unknown:'+$h
}
function Assert-Hash([string]$Path,[string]$Expected,[string]$Label){
    $actual=Get-Sha256 $Path
    if($actual -ne $Expected.ToLowerInvariant()){throw "$Label hash mismatch. Expected=$Expected Actual=$actual File=$Path"}
}
function Assert-Identity([string]$Root,[string]$ActiveStage){
    Assert-Hash (Join-Path $Root 'binkw32.dll') ([string]$Manifest.baseline.loaderSha256) 'Ultimate ASI Loader'
    Assert-Hash (Join-Path $Root 'binkw32Hooked.dll') ([string]$Manifest.baseline.originalBinkSha256) 'preserved original binkw32'
    if($ActiveStage -eq 'v001'){
        Assert-Hash (Join-Path $Root 'homelander_p1.asi') ([string]$Manifest.baseline.asiSha256) 'active v001 ASI'
        return $null
    }
    $cfg=@($Stages | Where-Object stage -eq $ActiveStage | Select-Object -First 1)
    if($cfg.Count -ne 1){throw "Active ASI is not a managed stage: $ActiveStage"}
    Assert-Hash (Join-Path $Root 'homelander_p1.asi') ([string]$cfg[0].asiSha256) "active $ActiveStage ASI"
    return $cfg[0]
}
function Copy-IfExists([string]$Source,[string]$Destination){
    if(Test-Path -LiteralPath $Source -PathType Leaf){
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
        return $true
    }
    return $false
}
function Copy-TreeIfExists([string]$Source,[string]$Destination){
    if(Test-Path -LiteralPath $Source -PathType Container){
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        $base=[System.IO.Path]::GetFullPath($Source).TrimEnd('\')
        Get-ChildItem -LiteralPath $Source -File -Recurse | ForEach-Object {
            $rel=$_.FullName.Substring($base.Length).TrimStart('\')
            $dst=Join-Path $Destination $rel
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $dst -Force
        }
        return $true
    }
    return $false
}
function Build-Archive([string]$PayloadDir,[string]$ZipPath){
    if(Test-Path -LiteralPath $ZipPath){Remove-Item -LiteralPath $ZipPath -Force}
    Compress-Archive -Path (Join-Path $PayloadDir '*') -DestinationPath $ZipPath -CompressionLevel Optimal
    if(!(Test-Path -LiteralPath $ZipPath -PathType Leaf)){throw 'Compress-Archive did not produce an output ZIP.'}
    return Get-Sha256 $ZipPath
}
function Run-SelfTest {
    $tmp=Join-Path ([System.IO.Path]::GetTempPath()) ('homelander_evidence_selftest_'+[Guid]::NewGuid().ToString('N'))
    try{
        $payload=Join-Path $tmp 'payload'
        New-Item -ItemType Directory -Force -Path (Join-Path $payload 'observer') | Out-Null
        'synthetic-log' | Set-Content -LiteralPath (Join-Path $payload 'homelander_p1_runtime.log') -Encoding UTF8
        '{"schema":"synthetic"}' | Set-Content -LiteralPath (Join-Path $payload 'observer\candidate.json') -Encoding UTF8
        $zip=Join-Path $tmp 'evidence.zip'
        $h=Build-Archive $payload $zip
        if($h.Length -ne 64){throw 'SelfTest ZIP SHA256 invalid.'}
        Expand-Archive -LiteralPath $zip -DestinationPath (Join-Path $tmp 'roundtrip') -Force
        if(!(Test-Path -LiteralPath (Join-Path $tmp 'roundtrip\homelander_p1_runtime.log'))){throw 'SelfTest round-trip log missing.'}
        if(!(Test-Path -LiteralPath (Join-Path $tmp 'roundtrip\observer\candidate.json'))){throw 'SelfTest round-trip candidate missing.'}
        Write-Host "SELFTEST PASS: evidence archive round-trip SHA256=$h"
    } finally {
        if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Recurse -Force}
    }
}
if($Action -eq 'SelfTest'){Run-SelfTest;exit 0}

if(Get-Process -Name 'prototypef' -ErrorAction SilentlyContinue){throw 'Prototype is running. Close the game before exporting a stable evidence snapshot.'}

$Root=Resolve-PrototypeRoot $PrototypeRoot
$ActiveStage=Get-ActiveStage $Root
if($ActiveStage -eq 'none' -or $ActiveStage.StartsWith('unknown:')){throw "Cannot export from unmanaged active stage: $ActiveStage"}
$Cfg=Assert-Identity $Root $ActiveStage

$stateDir=Join-Path $Root '.homelander_promotion'
$statePath=Join-Path $stateDir 'state.json'
$State=$null
if(Test-Path -LiteralPath $statePath -PathType Leaf){
    $State=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if([string]$State.currentStage -ne $ActiveStage){throw "Promotion state mismatch: state=$($State.currentStage), active=$ActiveStage"}
}

if(!$OutputDirectory){$OutputDirectory=Join-Path $stateDir 'evidence_exports'}
$OutputDirectory=[System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$stamp=SafeStamp
$work=Join-Path ([System.IO.Path]::GetTempPath()) ('homelander_evidence_'+[Guid]::NewGuid().ToString('N'))
$payload=Join-Path $work 'payload'
New-Item -ItemType Directory -Force -Path $payload | Out-Null

try{
    $copied=[ordered]@{}
    $log=Join-Path $Root 'homelander_p1_runtime.log'
    $copied.runtimeLog=Copy-IfExists $log (Join-Path $payload 'homelander_p1_runtime.log')
    $copied.state=Copy-IfExists $statePath (Join-Path $payload 'state.json')
    $copied.receipts=Copy-TreeIfExists (Join-Path $stateDir 'receipts') (Join-Path $payload 'receipts')
    $copied.liveObserver=Copy-TreeIfExists (Join-Path $stateDir 'live_observer') (Join-Path $payload 'live_observer')

    $fileMeta=[ordered]@{}
    foreach($name in @('prototypef.exe','prototypeenginef.dll','homelander_p1.asi','binkw32.dll','binkw32Hooked.dll')){
        $p=Join-Path $Root $name
        if(Test-Path -LiteralPath $p -PathType Leaf){
            $fi=Get-Item -LiteralPath $p
            $fileMeta[$name]=[ordered]@{size=[int64]$fi.Length;sha256=(Get-Sha256 $p);lastWriteUtc=$fi.LastWriteTimeUtc.ToString('o')}
        }
    }
    $logMeta=$null
    if(Test-Path -LiteralPath $log -PathType Leaf){
        $fi=Get-Item -LiteralPath $log
        $logMeta=[ordered]@{size=[int64]$fi.Length;sha256=(Get-Sha256 $log);lastWriteUtc=$fi.LastWriteTimeUtc.ToString('o')}
    }

    $summary=[ordered]@{
        schema='homelander-p1-live-evidence-export/1.0'
        exportedUtc=UtcNow
        activeStage=$ActiveStage
        gate=$(if($Cfg){[string]$Cfg.gate}else{$null})
        buildId=$(if($Cfg){[string]$Cfg.buildId}else{'P1_RuntimeProbe_001'})
        prototypeRoot=$Root
        promotionStatePresent=[bool]($null -ne $State)
        currentStageFromState=$(if($State){[string]$State.currentStage}else{$null})
        passedStages=$(if($State){@($State.passedStages)}else{@()})
        copied=$copied
        runtimeLog=$logMeta
        identities=$fileMeta
        authoritativeReceiptsCopied=[bool]$copied.receipts
        observerEvidenceCopied=[bool]$copied.liveObserver
        note='Read-only export. This archive does not create, modify, or imply any live-gate PASS.'
    }
    $summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $payload 'EVIDENCE_SUMMARY.json') -Encoding UTF8

    $zipName='Homelander_P1_LiveEvidence_'+$ActiveStage+'_'+$stamp+'.zip'
    $zip=Join-Path $OutputDirectory $zipName
    $zipHash=Build-Archive $payload $zip
    $hashFile=$zip+'.sha256.txt'
    "$zipHash  $([System.IO.Path]::GetFileName($zip))" | Set-Content -LiteralPath $hashFile -Encoding ASCII

    Write-Host "EVIDENCE EXPORT PASS" -ForegroundColor Green
    Write-Host "Stage: $ActiveStage"
    Write-Host "ZIP: $zip"
    Write-Host "SHA256: $zipHash"
    Write-Host "Hash file: $hashFile"
    Write-Host 'No PASS state or gameplay file was modified.'
} finally {
    if(Test-Path -LiteralPath $work){Remove-Item -LiteralPath $work -Recurse -Force}
}
