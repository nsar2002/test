# Windows runner only: actual unchanged R005 promotion manager against disposable synthetic files.
# NEVER point this at a user's real game. All names, logs and files are synthetic.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$src = Join-Path (Split-Path -Parent $PSScriptRoot) 'r005_windows_manager\P1_PROMOTION_MANAGER.ps1'
$managerText = [System.IO.File]::ReadAllText($src, [System.Text.Encoding]::UTF8).Replace("`r`n", "`n")
$normalizedSource = Join-Path $env:RUNNER_TEMP ('p1_r005_manager_normalized_' + [guid]::NewGuid().ToString('N') + '.ps1')
[System.IO.File]::WriteAllText($normalizedSource, $managerText, ([System.Text.UTF8Encoding]::new($false)))
$actualManager = (Get-FileHash -LiteralPath $normalizedSource -Algorithm SHA256).Hash.ToLowerInvariant()
$expectedManager = '4a7f8f03dd3f63c2e024214a434a3948852f31257ca7616096e0f4784b70d735'
if ($actualManager -ne $expectedManager) { throw "Test manager normalized source does not match R006 ASCII manager: $actualManager" }
$work = Join-Path $env:RUNNER_TEMP ('P1_R005_SYNTHETIC_' + [guid]::NewGuid().ToString('N'))
$pack = Join-Path $work 'pack'
$root = Join-Path $work 'Game Root With Spaces'
$null = New-Item -ItemType Directory -Force -Path $pack,$root,(Join-Path $pack 'packages'),(Join-Path $root 'lua_p1')
Copy-Item -LiteralPath $src -Destination (Join-Path $pack 'P1_PROMOTION_MANAGER.ps1') -Force
function Sha([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
function RunManager([string[]]$ManagerArgs, [int]$Expected=0) {
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pack 'P1_PROMOTION_MANAGER.ps1') @ManagerArgs -PrototypeRoot $root | Out-Host
  $rc = $LASTEXITCODE
  if ($rc -ne $Expected) { throw "Manager exit code: expected=$Expected actual=$rc arguments=$($ManagerArgs -join ' ')" }
}

# Fake v001 game's bytes. The zero-byte/ASCII stub is NEVER launched.
$fakeFiles = [ordered]@{ 'prototypef.exe'='SYNTHETIC-EXE'; 'homelander_p1.asi'='SYNTHETIC-V001'; 'binkw32.dll'='SYNTHETIC-ASI-LOADER'; 'binkw32Hooked.dll'='SYNTHETIC-ORIGINAL-BINK' }
foreach ($entry in $fakeFiles.GetEnumerator()) {
  [System.IO.File]::WriteAllText((Join-Path $root $entry.Key),$entry.Value)
}
[System.IO.File]::WriteAllText((Join-Path $root 'lua_p1\original-v1.lua'),'-- synthetic original Lua')
$baseHash = Sha (Join-Path $root 'homelander_p1.asi')
$loaderHash = Sha (Join-Path $root 'binkw32.dll')
$binkHash = Sha (Join-Path $root 'binkw32Hooked.dll')
$names = @('v003','v004','v005','v006','v007','v009','v010','v011','v012','v013','v014','v015','v016')
$previous = 'v001'
$stages = @()
foreach ($name in $names) {
  $source = Join-Path $work ('payloadsrc_' + $name)
  $lua = Join-Path $source 'payload\lua_p1'
  $null = New-Item -ItemType Directory -Force -Path $lua
  [System.IO.File]::WriteAllText((Join-Path $source 'payload\homelander_p1.asi'), ('SYNTHETIC_ASI_' + $name))
  [System.IO.File]::WriteAllText((Join-Path $lua ($name + '.lua')),('-- synthetic stage script ' + $name))
  $zip = Join-Path $pack ('packages\' + $name + '.zip')
  Compress-Archive -Path (Join-Path $source 'payload') -DestinationPath $zip -CompressionLevel Optimal
  $stages += [ordered]@{
    stage=$name; predecessor=$previous; display=('Synthetic ' + $name); package=('packages/' + $name + '.zip'); packageSha256=(Sha $zip);
    asiPath='payload/homelander_p1.asi'; luaRoot='payload/lua_p1'; asiSha256=(Sha (Join-Path $source 'payload\homelander_p1.asi'));
    buildId=('SYNTHETIC_' + $name); gate='F9'; keys='SYNTHETIC F9'; visible=$false; required=@(('READY ' + $name),'F9 SYNTHETIC PASS')
  }
  $previous = $name
}
$manifest = [ordered]@{
  schema='homelander-p1-runtime-promotion/1.0';
  baseline=[ordered]@{stage='v001';asiSha256=$baseHash;loaderSha256=$loaderHash;originalBinkSha256=$binkHash};
  forbiddenLogRegex='(?i)(FATAL|ABORT:|REFUSED:)'; stages=$stages
}
$manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $pack 'promotion_manifest.json') -Encoding UTF8

# All 13 packages are synthetic but processed by ACTUAL R005 PowerShell manager on Windows.
RunManager -ManagerArgs @('-Action','ValidatePack')
Write-Host 'R005_WINDOWS_MANAGER_VALIDATE_13_SYNTHETIC_PACKAGES_PASS'
RunManager -ManagerArgs @('-Action','Status')
RunManager -ManagerArgs @('-Action','Install','-Stage','v004') -Expected 1
if ((Sha (Join-Path $root 'homelander_p1.asi')) -ne $baseHash) { throw 'Out-of-order install changed baseline' }
Write-Host 'R005_WINDOWS_MANAGER_STAGE_SKIP_REJECT_PASS'
RunManager -ManagerArgs @('-Action','Install','-Stage','v003')
if ((Sha (Join-Path $root 'homelander_p1.asi')) -ne $stages[0].asiSha256) { throw 'Synthetic v003 ASI not installed' }
if ((Sha (Join-Path $root 'binkw32.dll')) -ne $loaderHash -or (Sha (Join-Path $root 'binkw32Hooked.dll')) -ne $binkHash) { throw 'Loader changed unexpectedly' }
if (!(Test-Path -LiteralPath (Join-Path $root 'lua_p1\v003.lua'))) { throw 'Synthetic v003 Lua not staged' }
Write-Host 'R005_WINDOWS_MANAGER_INSTALL_V003_AND_LOADER_PRESERVATION_PASS'
RunManager -ManagerArgs @('-Action','Install','-Stage','v004') -Expected 1
Write-Host 'R005_WINDOWS_MANAGER_NO_LATER_STAGE_WITHOUT_PASS'
RunManager -ManagerArgs @('-Action','Check','-Stage','v003') -Expected 1
$log = Join-Path $root 'homelander_p1_runtime.log'
[System.IO.File]::WriteAllText($log,"READY v003`nABORT: simulated error`nF9 SYNTHETIC PASS`n")
RunManager -ManagerArgs @('-Action','Check','-Stage','v003') -Expected 1
Write-Host 'R005_WINDOWS_MANAGER_REJECT_MISSING_AND_FORBIDDEN_LOG_PASS'
RunManager -ManagerArgs @('-Action','ResetLog')
if (Test-Path -LiteralPath $log) { throw 'ResetLog should archive synthetic failed evidence' }
[System.IO.File]::WriteAllText($log,"READY v003`nF9 SYNTHETIC PASS`n")
RunManager -ManagerArgs @('-Action','Check','-Stage','v003')
$state = Get-Content -LiteralPath (Join-Path $root '.homelander_promotion\state.json') -Raw | ConvertFrom-Json
if (@($state.passedStages) -notcontains 'v003') { throw 'Synthetic test gate state not saved' }
Write-Host 'R005_WINDOWS_MANAGER_SYNTHETIC_LOG_GATE_STATE_PASS_NOT_REAL_GAME'
RunManager -ManagerArgs @('-Action','Rollback')
if ((Sha (Join-Path $root 'homelander_p1.asi')) -ne $baseHash) { throw 'Rollback failed v001 ASI byte restore' }
if (!(Test-Path -LiteralPath (Join-Path $root 'lua_p1\original-v1.lua'))) { throw 'Rollback lost original Lua' }
if (Test-Path -LiteralPath (Join-Path $root 'lua_p1\v003.lua')) { throw 'Rollback retained newer synthetic Lua' }
if ((Sha (Join-Path $root 'binkw32.dll')) -ne $loaderHash -or (Sha (Join-Path $root 'binkw32Hooked.dll')) -ne $binkHash) { throw 'Rollback modified loader chain' }
Write-Host 'R005_WINDOWS_MANAGER_ROLLBACK_RESTORES_SYNTHETIC_V001_PASS'
Write-Host 'R005_WINDOWS_MANAGER_SYNTHETIC_FIXTURE_PASS: all checks on disposable fake game only; no Prototype executable run'

# END-TO-END FIRST GATE REHEARSAL WITH BENIGN SYNTHETIC EXE.
# This tests the ORIGINAL R006 START_V003_LIVE_TEST.ps1 -> manager Install ->
# observer Observe chain. The fake executable writes a two-line fixture log only.
$companionDir = Join-Path $env:GITHUB_WORKSPACE 'homelander_p1_build/tests/r006_windows_companions'
Copy-Item -LiteralPath (Join-Path $companionDir 'START_V003_LIVE_TEST.ps1') -Destination (Join-Path $pack 'START_V003_LIVE_TEST.ps1') -Force
Copy-Item -LiteralPath (Join-Path $companionDir 'P1_LIVE_GATE_ASSISTANT.ps1') -Destination (Join-Path $pack 'P1_LIVE_GATE_ASSISTANT.ps1') -Force
$fakeSource = @'
using System;
using System.IO;
using System.Threading;
internal static class Program {
    private static void Main() {
        string log = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "homelander_p1_runtime.log");
        File.AppendAllText(log, "READY v003\nF9 SYNTHETIC PASS\n");
        Thread.Sleep(4000);
    }
}
'@
Add-Type -TypeDefinition $fakeSource -Language CSharp -OutputAssembly (Join-Path $root 'prototypef.exe') -OutputType ConsoleApplication -ErrorAction Stop
Write-Host 'R006_WINDOWS_FIRST_GATE_SYNTHETIC_FAKE_EXE_CREATED'
$launcher = Join-Path $pack 'START_V003_LIVE_TEST.ps1'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher -PrototypeRoot $root | Out-Host
$launchRC = $LASTEXITCODE
if ($launchRC -ne 0) { throw "First-v003-launcher+observer synthetic run failed: $launchRC" }
if ((Sha (Join-Path $root 'homelander_p1.asi')) -ne $stages[0].asiSha256) { throw 'Launcher did not install synthetic v003' }
$candidates = Join-Path $root '.homelander_promotion\live_observer\candidates'
$receipt = Get-ChildItem -LiteralPath $candidates -Filter '*LOG_COMPLETE.json' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($null -eq $receipt) { throw 'No non-authoritative synthetic LOG_COMPLETE observer candidate after first-v003 launcher' }
$proof = Get-Content -LiteralPath $receipt.FullName -Raw | ConvertFrom-Json
if ($proof.authoritative -ne $false -or $proof.visualConfirmed -ne $false -or $proof.allRequiredFound -ne $true) {
    throw 'Observer candidate violated non-authoritative boundary'
}
$liveState = Get-Content -LiteralPath (Join-Path $root '.homelander_promotion\state.json') -Raw | ConvertFrom-Json
if (@($liveState.passedStages).Count -ne 0) { throw 'First live launcher illegally recorded synthetic PASS state' }
Write-Host 'R006_WINDOWS_FIRST_GATE_SYNTHETIC_OBSERVER_CHAIN_PASS_NO_AUTHORITY'
Write-Host 'R006_WINDOWS_FIRST_GATE_SYNTHETIC_FIXTURE_PASS_NO_REAL_GAME'

# FULL CHAIN: all generated stage packages and log lines are explicitly SYNTHETIC.
# The first launcher produced only a non-authoritative observer candidate.
RunManager -ManagerArgs @('-Action','Install','-Stage','v004') -Expected 1
Write-Host 'R006_WINDOWS_FULLCHAIN_OBSERVER_CANNOT_UNLOCK_V004'
RunManager -ManagerArgs @('-Action','Check','-Stage','v003')
for ($i=1; $i -lt $stages.Count; $i++) {
    $cfg=$stages[$i]
    $expectedPrevious=$stages[$i-1].stage
    if ((Sha (Join-Path $root 'homelander_p1.asi')) -ne $stages[$i-1].asiSha256) {
        throw "Before stage $($cfg.stage) install the prior stage ASI is not intact: $expectedPrevious"
    }
    if ($i -eq 1) {
        $zip=Join-Path $pack 'packages\v004.zip'
        $savedZip=Join-Path $pack 'packages\v004.hidden.for.failure.test'
        Move-Item -LiteralPath $zip -Destination $savedZip
        try {
            RunManager -ManagerArgs @('-Action','Install','-Stage','v004') -Expected 1
            if ((Sha (Join-Path $root 'homelander_p1.asi')) -ne $stages[0].asiSha256) {
                throw 'Missing package failure changed active v003'
            }
            Write-Host 'R006_WINDOWS_FULLCHAIN_MISSING_STAGE_PACKAGE_FAIL_CLOSED'
        } finally {
            Move-Item -LiteralPath $savedZip -Destination $zip
        }
    }
    RunManager -ManagerArgs @('-Action','Install','-Stage',$cfg.stage)
    if ((Sha (Join-Path $root 'homelander_p1.asi')) -ne $cfg.asiSha256) {
        throw "Installed ASI hash not current for $($cfg.stage)"
    }
    if (!(Test-Path -LiteralPath (Join-Path $root ('lua_p1\' + $cfg.stage + '.lua')))) {
        throw "Stage Lua file absent after install: $($cfg.stage)"
    }
    if ((Sha (Join-Path $root 'binkw32.dll')) -ne $loaderHash -or
        (Sha (Join-Path $root 'binkw32Hooked.dll')) -ne $binkHash) {
        throw "One of the two loader DLLs changed during synthetic install $($cfg.stage)"
    }
    $nextIndex=$i+1
    if ($nextIndex -lt $stages.Count) {
        RunManager -ManagerArgs @('-Action','Install','-Stage',$stages[$nextIndex].stage) -Expected 1
        if ((Sha (Join-Path $root 'homelander_p1.asi')) -ne $cfg.asiSha256) {
            throw "Later stage install bypassed missing current-stage evidence: $($cfg.stage)"
        }
    }
    # A fresh per-stage log is synthesized for the CI test, NOT from Prototype.
    $log=Join-Path $root 'homelander_p1_runtime.log'
    if (Test-Path -LiteralPath $log) { throw "Install failed to archive previous stage's test log: $($cfg.stage)" }
    [System.IO.File]::WriteAllText($log,"READY $($cfg.stage)\`nF9 SYNTHETIC PASS\`n")
    RunManager -ManagerArgs @('-Action','Check','-Stage',$cfg.stage)
    $state=Get-Content -LiteralPath (Join-Path $root '.homelander_promotion\state.json') -Raw | ConvertFrom-Json
    if ([string]$state.currentStage -ne $cfg.stage -or
        @($state.passedStages) -notcontains $cfg.stage) {
        throw "Synthetic check failed to record current stage $($cfg.stage)"
    }
    if (@($state.passedStages).Count -ne ($i+1)) {
        throw "Synthetic state pass-count mismatch at $($cfg.stage)"
    }
    Write-Host ("R006_WINDOWS_FULLCHAIN_SYNTHETIC_STAGE_PASS_NOT_REAL_GAME " + $cfg.stage)
}
RunManager -ManagerArgs @('-Action','Next')
$allState=Get-Content -LiteralPath (Join-Path $root '.homelander_promotion\state.json') -Raw | ConvertFrom-Json
if (@($allState.passedStages).Count -ne 13) {
    throw 'Synthetic complete chain did not record 13 stages'
}
Write-Host 'R006_WINDOWS_FULLCHAIN_SYNTHETIC_13_OF_13_PASS_NOT_REAL_GAME'
for ($i=$stages.Count-1; $i -ge 0; $i--) {
    RunManager -ManagerArgs @('-Action','Rollback')
    $expected=if ($i -eq 0) {'v001'} else {$stages[$i-1].stage}
    $current=Get-Content -LiteralPath (Join-Path $root '.homelander_promotion\state.json') -Raw | ConvertFrom-Json
    if ($current.currentStage -ne $expected) {
        throw "Rollback to $expected failed at iteration $i"
    }
    if ((Sha (Join-Path $root 'binkw32.dll')) -ne $loaderHash -or
        (Sha (Join-Path $root 'binkw32Hooked.dll')) -ne $binkHash) {
        throw "Loader chain changed on rollback $i"
    }
    Write-Host ("R006_WINDOWS_FULLCHAIN_SYNTHETIC_ROLLBACK_PASS " + $expected)
}
$finalState=Get-Content -LiteralPath (Join-Path $root '.homelander_promotion\state.json') -Raw | ConvertFrom-Json
if (@($finalState.passedStages).Count -ne 0 -or
    @($finalState.installHistory).Count -ne 0 -or
    $finalState.currentStage -ne 'v001') {
    throw 'After 13 rollbacks synthetic promotion state is not exact v001'
}
if ((Sha (Join-Path $root 'homelander_p1.asi')) -ne $baseHash) {
    throw 'After 13 rollbacks the original v001 ASI bytes were not restored'
}
if (!(Test-Path -LiteralPath (Join-Path $root 'lua_p1\original-v1.lua'))) {
    throw 'After 13 rollbacks the original v001 Lua file is absent'
}
foreach ($stage in $names) {
    if (Test-Path -LiteralPath (Join-Path $root ('lua_p1\' + $stage + '.lua'))) {
        throw "Unexpected synthetic stage Lua remained after rollback to v001: $stage"
    }
}
Write-Host 'R006_WINDOWS_FULLCHAIN_SYNTHETIC_13_ROLLBACKS_TO_V001_PASS_NO_REAL_GAME'
