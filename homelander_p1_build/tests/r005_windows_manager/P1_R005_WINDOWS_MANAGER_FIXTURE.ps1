# Windows runner only: actual unchanged R005 promotion manager against disposable synthetic files.
# NEVER point this at a user's real game. All names, logs and files are synthetic.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$src = Join-Path $PSScriptRoot 'P1_PROMOTION_MANAGER.ps1'
$actualManager = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLowerInvariant()
$expectedManager = 'dc3868b0c9e6ad416f85600fbc64ceb7957fa0e72475cc815c40f7f94d6d476a'
if ($actualManager -ne $expectedManager) { throw "Test manager is not byte-identical to R005: $actualManager" }
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
