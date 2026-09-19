# Only synthetic Windows runtime fixture. Never uses any user's game or R007 package.
# Production tool pins stay immutable; ONLY a disposable COPY substitutes fake hashes.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$base=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$orig=Join-Path $PSScriptRoot 'P1_FIRST_GATE_READONLY_PREFLIGHT.ps1'
$tmp=Join-Path $env:RUNNER_TEMP ('r019_readonly_'+[guid]::NewGuid().ToString('N'))
$release=Join-Path $tmp 'synthetic_release'
$game=Join-Path $tmp 'synthetic_Prototype_game_root'
$fakezip=Join-Path $tmp 'fake_release.zip'
$tool=Join-Path $tmp 'ONLY_SYNTHETIC_PRECHECK.ps1'
New-Item -ItemType Directory -Force -Path $release,$game,(Join-Path $game 'lua_p1'),(Join-Path $release 'packages') | Out-Null
function Sha([string]$p){return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function WriteFake([string]$p,[string]$v){
 [IO.File]::WriteAllText($p,$v,[Text.Encoding]::ASCII)
}
function Snapshot([string]$p){
 return @(Get-ChildItem -LiteralPath $p -File -Recurse | Sort-Object FullName |
  ForEach-Object { $_.FullName.Substring($p.Length)+' '+(Sha $_.FullName) }) -join "`n"
}
try {
 WriteFake (Join-Path $game 'prototypef.exe') 'FAKE TEXT NOT AN EXECUTABLE'
 WriteFake (Join-Path $game 'binkw32.dll') 'SYNTHETIC-LOADER'
 WriteFake (Join-Path $game 'binkw32Hooked.dll') 'SYNTHETIC-ORIGINAL-BINK'
 WriteFake (Join-Path $game 'homelander_p1.asi') 'SYNTHETIC-BASELINE-ASI'
 $v001=Sha (Join-Path $game 'homelander_p1.asi')
 $v003file=Join-Path $tmp 'fake-v003.asi'
 WriteFake $v003file 'SYNTHETIC-STAGE-V003-ASI'
 $v003=Sha $v003file
 $baseSha=@{
  '577be0ad57823b8cf562bee014d2656819ff5c4159ef74b3c195e842d747b104'=$v001;
  '1845aff900e77f7c98e1ef0b37a2ea83c1c293ad74d01dc8fb136a198c9027c2'=$v003;
  'bc48bab2cf07eaf616e23ba9eef1922ea5e8590f722b6657a8f2ed986fe6f20e'=(Sha (Join-Path $game 'binkw32.dll'));
  'dba257f26517d57ecf3c62aca7cccfabbad868dddf97160f71c9ab81d37a8627'=(Sha (Join-Path $game 'binkw32Hooked.dll'))
 }
 $lua=@{
  'flight_controller_v1.lua'='4d84d44f39b2bb0cef7ae4513bf73f17eac717c80c80eb3263616207485f577b';
  'flight_math_probe.lua'='033bafec3a64f6e5c9466481d896eed35a67206703bf09be4054369e35150fa9';
  'heatvision_probe.lua'='914a6631f9e1e5c90fff8faf335443211b990000b985134f32b7b2d1633a2f51';
  'setter_echo_probe.lua'='ef6857400cceea36278514c5808ee8290fb15daf5827be3df35eb05ba5aa7b81';
  'runtime_probe.lua'='bd7a6ec2006466b0f7b46f966f384103d35d5d98020bcdce1112e9b4f363a650';
  'freeaim_probe_v004_STAGED.lua'='89885eecdf1dcd1f324c6cd3c3580013674639167e0849688ed7036c75678cd1'
 }
 foreach($name in $lua.Keys){
  $p=Join-Path (Join-Path $game 'lua_p1') $name
  WriteFake $p ('FAKE LUA FOR HASH VALIDATION ONLY '+$name)
  $baseSha[$lua[$name]]=Sha $p
 }
 $srcManifest=Join-Path $base 'tests\r006_windows_companions\promotion_manifest.json'
 $manifest=Get-Content -LiteralPath $srcManifest -Raw | ConvertFrom-Json
 $manifest.baseline.asiSha256=$v001
 $manifest.baseline.loaderSha256=$baseSha['bc48bab2cf07eaf616e23ba9eef1922ea5e8590f722b6657a8f2ed986fe6f20e']
 $manifest.baseline.originalBinkSha256=$baseSha['dba257f26517d57ecf3c62aca7cccfabbad868dddf97160f71c9ab81d37a8627']
 foreach($s in @($manifest.stages)){
  $dest=Join-Path $release ([string]$s.package).Replace('/','\')
  $work=Join-Path $tmp ('pack_'+$s.stage)
  New-Item -ItemType Directory -Force -Path $work | Out-Null
  WriteFake (Join-Path $work 'ONLY_SYNTHETIC_DO_NOT_INSTALL.txt') ('FAKE STAGE '+$s.stage)
  Compress-Archive -LiteralPath (Join-Path $work 'ONLY_SYNTHETIC_DO_NOT_INSTALL.txt') -DestinationPath $dest
  $s.packageSha256=Sha $dest
  if($s.stage -eq 'v003'){$s.asiSha256=$v003}
 }
 $manager=Join-Path $release 'P1_PROMOTION_MANAGER.ps1'
 WriteFake $manager 'FAKE MANAGER - NOT FOR INSTALL'
 $manifestfile=Join-Path $release 'promotion_manifest.json'
 $manifest | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $manifestfile -Encoding UTF8
 $pinhashes=@{
   'd2b815620c915ff819b5b62f571d5502c53c8a7e1ad91ea88843ad74bf384a3c'='';
   '50cef5262c61c8a7ad83ee49c9aabb1ba6a714252c130b1d03494788668d0e87'=(Sha $manager);
   '2febfe4159690de6a5e0ab953f049f68a3b14879c701089c33f1459513f37e45'=(Sha $manifestfile);
   '23e125109da26f268534a7db429a8c8d51af6cc63d06d2a374f874fb68f3a7f2'=([string]$manifest.stages[0].packageSha256)
 }
 foreach($p in $baseSha.Keys){$pinhashes[$p]=$baseSha[$p]}
 Compress-Archive -Path (Join-Path $release '*') -DestinationPath $fakezip
 $pinhashes['d2b815620c915ff819b5b62f571d5502c53c8a7e1ad91ea88843ad74bf384a3c']=Sha $fakezip
 $source=Get-Content -LiteralPath $orig -Raw
 foreach($pin in $pinhashes.Keys) {
  if(!$source.Contains($pin)){throw "Expected production pin not present: $pin"}
  $source=$source.Replace($pin,[string]$pinhashes[$pin])
 }
 [IO.File]::WriteAllText($tool,$source,[Text.Encoding]::UTF8)
 function Run([string]$action,[bool]$shouldPass,[string]$marker){
  $before=Snapshot $game
  $output=(& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $tool `
    -Action $action -ReleaseDirectory $release -R007ZipPath $fakezip -PrototypeRoot $game 2>&1 | Out-String)
  $code=$LASTEXITCODE
  $after=Snapshot $game
  if($after -cne $before){throw 'Sidecar mutated disposable game root!'}
  if($shouldPass -and ($code -ne 0 -or !$output.Contains($marker))){
   throw "Expected read-only $action positive / $marker, exit=$code output=$output"
  }
  if(!$shouldPass -and $code -eq 0){
   throw "Expected negative $action but sidecar returned 0: $output"
  }
  Write-Host ("SYNTHETIC "+$action+" "+$(if($shouldPass){'ACCEPT'}else{'REJECT'})+" PASS")
 }
 Run 'Preflight' $true 'READY_FOR_FIRST_V003_INSTALL_AND_GAME_TEST'
 Copy-Item -LiteralPath $v003file -Destination (Join-Path $game 'homelander_p1.asi') -Force
 $stateDir=Join-Path $game '.homelander_promotion'
 New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
 @{ currentStage='v003'; passedStages=@(); installHistory=@() } | ConvertTo-Json -Depth 8 |
  Set-Content -LiteralPath (Join-Path $stateDir 'state.json') -Encoding UTF8
 Run 'Preflight' $true 'READY_FOR_FIRST_V003_GAME_TEST'
 $b=[string]$manifest.stages[0].buildId
 $log=Join-Path $game 'homelander_p1_runtime.log'
 $good="READY build=$b`r`nF4: read-only discovery + flight math probe`r`nF9: read-only free-aim camera/LOS probe`r`n[HOMELANDER_P1_FREEAIM_V004] BEGIN - READ ONLY`r`n[HOMELANDER_P1_FREEAIM_V004] CAMERA | axis=3`r`n[HOMELANDER_P1_FREEAIM_V004] HIT | fraction=0.5 hitGOH=NPC`r`n[HOMELANDER_P1_FREEAIM_V004] END - READ ONLY`r`n"
 [IO.File]::WriteAllText($log,$good)
 Run 'InspectV003Log' $true 'LOG CHRONOLOGY CONSISTENT'
 Run 'Preflight' $false ''
 [IO.File]::WriteAllText($log,$good+"F9: read-only free-aim camera/LOS probe`r`n[HOMELANDER_P1_FREEAIM_V004] MISS | range=500`r`n")
 Run 'InspectV003Log' $false ''
 [IO.File]::WriteAllText($log,$good)
 WriteFake (Join-Path $game 'binkw32.dll') 'TAMPERED-SYNTHETIC-LOADER'
 Run 'InspectV003Log' $false ''
 Write-Host 'P1_R019_SYNTHETIC_FULL_ROOT_AND_TEMPORAL_LOG_PREFLIGHT_PASS'
 Write-Host 'P1_R019_SYNTHETIC_ZERO_GAME_ROOT_WRITES_PASS'
 Write-Host 'P1_R019_PRODUCTION_PINNED_SCRIPT_UNCHANGED_BY_FIXTURE_PASS'
}finally {
 if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Recurse -Force}
}
