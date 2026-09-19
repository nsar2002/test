# Synthetic-only regression. NEVER run or install any game executable.
# Runs BOTH the frozen R007 source manager and the separate R008 candidate
# with a fabricated non-executable "prototypef.exe" in a temporary directory.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$oldManager = Join-Path $repo 'tests\r005_windows_manager\P1_PROMOTION_MANAGER.ps1'
$newManager = Join-Path $PSScriptRoot 'P1_PROMOTION_MANAGER_ORDERED_CANDIDATE.ps1'
$work = Join-Path $env:RUNNER_TEMP ('p1_r008_ordered_' + [guid]::NewGuid().ToString('N'))
$root = Join-Path $work 'Game Root With Spaces'
$oldPack = Join-Path $work 'old_pack'
$newPack = Join-Path $work 'new_pack'
$null = New-Item -ItemType Directory -Force -Path $root,$oldPack,$newPack
try {
    [System.IO.File]::WriteAllText((Join-Path $root 'prototypef.exe'),'FAKE-SYNTHETIC-NOT-AN-EXECUTABLE')
    [System.IO.File]::WriteAllText((Join-Path $root 'homelander_p1.asi'),'FAKE-STAGE-V003')
    [System.IO.File]::WriteAllText((Join-Path $root 'binkw32.dll'),'FAKE-LOADER')
    [System.IO.File]::WriteAllText((Join-Path $root 'binkw32Hooked.dll'),'FAKE-BINK-ORIGINAL')
    function Hash([string]$Path) {
        return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $stageNames = @('v003','v004','v005','v006','v007','v009','v010','v011','v012','v013','v014','v015','v016')
    $stages = @()
    $pred = 'v001'
    foreach ($name in $stageNames) {
        $stages += [ordered]@{
            stage=$name;predecessor=$pred;display=('SYNTHETIC '+$name);
            package=('packages/'+$name+'.zip');packageSha256=('0'*64);driveId='none';
            asiPath='payload/homelander_p1.asi';luaRoot='payload/lua_p1';
            asiSha256=$(if ($name -eq 'v003') { Hash (Join-Path $root 'homelander_p1.asi') } else { '0'*64 });
            buildId=('SYNTHETIC_'+$name);gate='F9';keys='SYNTHETIC ONLY';visible=$false;
            required=@('READY build=SYNTHETIC_V003',
                'F4: read-only discovery \+ flight math probe',
                '\[HOMELANDER_P1_FREEAIM_V004\] CAMERA \|',
                '\[HOMELANDER_P1_FREEAIM_V004\] HIT \|[^\r\n]*hitGOH=(?!nil\b)')
        }
        $pred = $name
    }
    $manifest = [ordered]@{
        schema='homelander-p1-runtime-promotion/1.0'
        baseline=[ordered]@{
          stage='v001';asiSha256=('f'*64);
          loaderSha256=(Hash (Join-Path $root 'binkw32.dll'));
          originalBinkSha256=(Hash (Join-Path $root 'binkw32Hooked.dll'))
        }
        forbiddenLogRegex='(?im)(FATAL|FAIL signature|Lua compile error|Lua runtime error|Unhandled exception|Access violation|\bABORT:|\bREFUSED:)'
        stages=$stages
    }
    foreach ($pack in @($oldPack,$newPack)) {
        $manager = $(if ($pack -eq $oldPack) {$oldManager} else {$newManager})
        Copy-Item -LiteralPath $manager -Destination (Join-Path $pack 'P1_PROMOTION_MANAGER.ps1')
        $manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $pack 'promotion_manifest.json') -Encoding UTF8
    }
    function RunCheck([string]$Pack,[string]$Evidence,[int]$Expected) {
        [System.IO.File]::WriteAllText((Join-Path $root 'homelander_p1_runtime.log'),$Evidence)
        & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $Pack 'P1_PROMOTION_MANAGER.ps1') -Action Check -Stage v003 -PrototypeRoot $root | Out-Host
        $code=$LASTEXITCODE
        if ($code -ne $Expected) { throw "Unexpected Check exit=$code expected=$Expected" }
    }
    $ready="READY build=SYNTHETIC_V003`n"
    $f4="F4: read-only discovery + flight math probe`n"
    $f9="F9: read-only free-aim camera/LOS probe`n"
    $camera="[HOMELANDER_P1_FREEAIM_V004] CAMERA | axis=2`n"
    $hit="[HOMELANDER_P1_FREEAIM_V004] HIT | fraction=0.5 hitGOH=NPC`n"
    $miss="[HOMELANDER_P1_FREEAIM_V004] MISS | range=500`n"
    $unordered=$ready+$f9+$camera+$hit+$f4
    RunCheck $oldPack $unordered 0
    Write-Host 'P1_R007_ORIGINAL_CHECK_ACCEPTS_UNORDERED_F9_BEFORE_F4_REPRODUCED'
    $stateDir=Join-Path $root '.homelander_promotion'
    if (Test-Path $stateDir) { Remove-Item -LiteralPath $stateDir -Recurse -Force }
    RunCheck $newPack $unordered 1
    RunCheck $newPack ($ready+$f4+$f9+$camera+$hit+$ready) 1
    RunCheck $newPack ($ready+$f4+$f9+$camera+$hit+$f9+$miss) 1
    RunCheck $newPack ($ready+$f4+$f9+$hit+$camera) 1
    if (Test-Path $stateDir) { throw 'Candidate wrote a PASS receipt/state for an invalid fixture' }
    Write-Host 'P1_R008_ORDERED_CHECK_REJECTS_UNORDERED_STALE_AND_LATEST_MISS_PASS'
    RunCheck $newPack ($ready+$f4+$f9+$camera+$hit) 0
    $state = Get-Content -LiteralPath (Join-Path $stateDir 'state.json') -Raw | ConvertFrom-Json
    if (@($state.passedStages) -notcontains 'v003') { throw 'Candidate failed to record valid synthetic v003 proof' }
    $receipt = @(Get-ChildItem -LiteralPath (Join-Path $stateDir 'receipts') -Filter '*v003_PASS.json' -File)
    if ($receipt.Count -ne 1) { throw 'Expected one and only one valid synthetic v003 receipt' }
    Write-Host 'P1_R008_ORDERED_CHECK_VALID_FIRSTGATE_PASS_SYNTHETIC_ONLY'
    Write-Host 'P1_R008_SOURCE_CANDIDATE_NEVER_LAUNCHED_OR_MODIFIED_REAL_GAME'
} finally {
    if (Test-Path -LiteralPath $work) { Remove-Item -LiteralPath $work -Recurse -Force }
}
