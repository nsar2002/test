<#
R019 first-live gate READ-ONLY PC preflight & log assessor.
This is a sidecar, NOT a replacement for frozen official R007 manager.
No Install, Check, ResetLog, Rollback, game launch or game-root writes.
#>
param(
 [ValidateSet('Preflight','InspectV003Log','SelfTest')][string]$Action='Preflight',
 [string]$R007ZipPath='',
 [string]$ReleaseDirectory='',
 [string]$PrototypeRoot=''
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$PIN_PACK='d2b815620c915ff819b5b62f571d5502c53c8a7e1ad91ea88843ad74bf384a3c'
$PIN_MANAGER='50cef5262c61c8a7ad83ee49c9aabb1ba6a714252c130b1d03494788668d0e87'
$PIN_MANIFEST='2febfe4159690de6a5e0ab953f049f68a3b14879c701089c33f1459513f37e45'
$PIN_V003='23e125109da26f268534a7db429a8c8d51af6cc63d06d2a374f874fb68f3a7f2'
$PIN_V003_ASI='1845aff900e77f7c98e1ef0b37a2ea83c1c293ad74d01dc8fb136a198c9027c2'
$PIN_V001='577be0ad57823b8cf562bee014d2656819ff5c4159ef74b3c195e842d747b104'
$PIN_LOADER='bc48bab2cf07eaf616e23ba9eef1922ea5e8590f722b6657a8f2ed986fe6f20e'
$PIN_BINK='dba257f26517d57ecf3c62aca7cccfabbad868dddf97160f71c9ab81d37a8627'
$BaseLua=[ordered]@{
 'flight_controller_v1.lua'='4d84d44f39b2bb0cef7ae4513bf73f17eac717c80c80eb3263616207485f577b'
 'flight_math_probe.lua'='033bafec3a64f6e5c9466481d896eed35a67206703bf09be4054369e35150fa9'
 'heatvision_probe.lua'='914a6631f9e1e5c90fff8faf335443211b990000b985134f32b7b2d1633a2f51'
 'setter_echo_probe.lua'='ef6857400cceea36278514c5808ee8290fb15daf5827be3df35eb05ba5aa7b81'
 'runtime_probe.lua'='bd7a6ec2006466b0f7b46f966f384103d35d5d98020bcdce1112e9b4f363a650'
}
function Sha([string]$Path) {
 if(!(Test-Path -LiteralPath $Path -PathType Leaf)){throw "MISSING FILE: $Path"}
 (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Same([string]$Path,[string]$Expected,[string]$Label) {
 $actual=Sha $Path
 if($actual -ne $Expected){throw "BLOCKED $Label hash mismatch (original bytes untouched): $Path expected=$Expected actual=$actual"}
}
function Test-Ordered([string]$Raw,[string]$Build) {
 $lines=[regex]::Split($Raw,'\r?\n')
 $idx=-1
 for($i=0;$i -lt $lines.Length;$i++){
  if($lines[$i] -match ('READY build='+[regex]::Escape($Build)+'\b')){$idx=$i}
 }
 if($idx -lt 0){return 'NO_LATEST_READY_FOR_V003'}
 $f4=-1
 for($i=$idx+1;$i -lt $lines.Length;$i++){
  if($lines[$i] -match 'F4: read-only discovery \+ flight math probe'){$f4=$i}
 }
 if($f4 -lt 0){return 'F4_NOT_AFTER_LAST_READY'}
 $f9=-1
 for($i=$idx+1;$i -lt $lines.Length;$i++){
  if($lines[$i] -match 'F9: read-only free-aim camera/LOS probe'){$f9=$i}
 }
 if($f9 -le $f4){return 'LATEST_F9_MISSING_OR_PRECEDES_F4'}
 $begin=-1;$cam=-1;$hit=-1;$end=-1
 for($i=$f9+1;$i -lt $lines.Length;$i++){
  if($lines[$i] -match 'READY build='){return 'NEW_READY_AFTER_LAST_F9'}
  if($lines[$i] -match '\[HOMELANDER_P1_FREEAIM_V004\] BEGIN.*READ ONLY'){$begin=$i;break}
 }
 if($begin -lt 0){return 'F9_BEGIN_MISSING'}
 for($i=$begin+1;$i -lt $lines.Length;$i++){
  if($lines[$i] -match 'READY build=|F9: read-only free-aim camera/LOS probe'){return 'F9_REPLACED_BEFORE_EVIDENCE_COMPLETE'}
  if($lines[$i] -match '\[HOMELANDER_P1_FREEAIM_V004\] MISS \|'){return 'LATEST_F9_WAS_MISS'}
  if($lines[$i] -match '\[HOMELANDER_P1_FREEAIM_V004\] CAMERA \|'){$cam=$i;break}
  if($lines[$i] -match '\[HOMELANDER_P1_FREEAIM_V004\] (ABORT|END)'){return 'F9_ABORT_OR_END_BEFORE_CAMERA'}
 }
 if($cam -lt 0){return 'F9_CAMERA_MISSING'}
 for($i=$cam+1;$i -lt $lines.Length;$i++){
  if($lines[$i] -match 'READY build=|F9: read-only free-aim camera/LOS probe'){return 'F9_REPLACED_BEFORE_HIT'}
  if($lines[$i] -match '\[HOMELANDER_P1_FREEAIM_V004\] MISS \|'){return 'LATEST_F9_WAS_MISS'}
  if($lines[$i] -match '\[HOMELANDER_P1_FREEAIM_V004\] HIT \|[^\r\n]*hitGOH=(?!nil\b)\S+'){$hit=$i;break}
  if($lines[$i] -match '\[HOMELANDER_P1_FREEAIM_V004\] (ABORT|END)'){return 'F9_ABORT_OR_END_BEFORE_VALID_NONPLAYER_HIT'}
 }
 if($hit -lt 0){return 'F9_VALID_OBJECT_HIT_MISSING'}
 for($i=$hit+1;$i -lt $lines.Length;$i++){
  if($lines[$i] -match 'READY build=|F9: read-only free-aim camera/LOS probe'){return 'F9_REPLACED_BEFORE_END'}
  if($lines[$i] -match '\[HOMELANDER_P1_FREEAIM_V004\] END.*READ ONLY'){$end=$i;break}
 }
 if($end -lt 0){return 'F9_END_MISSING'}
 return 'ORDERED_F4_F9_HIT_END_CONSISTENT'
}
function SelfTest {
 $b='P1_RuntimeProbe_003_FREEAIM_STAGED_20260918'
 $a="READY build=$b`n"
 $f4="F4: read-only discovery + flight math probe`n"
 $f9="F9: read-only free-aim camera/LOS probe`n"
 $start="[HOMELANDER_P1_FREEAIM_V004] BEGIN - READ ONLY`n"
 $cam="[HOMELANDER_P1_FREEAIM_V004] CAMERA | axis=3`n"
 $hit="[HOMELANDER_P1_FREEAIM_V004] HIT | fraction=0.5 hitGOH=NPC`n"
 $end="[HOMELANDER_P1_FREEAIM_V004] END - READ ONLY`n"
 $valid=$a+$f4+$f9+$start+$cam+$hit+$end
 if((Test-Ordered $valid $b) -ne 'ORDERED_F4_F9_HIT_END_CONSISTENT'){throw 'valid chronological test failed'}
 foreach($bad in @(
  ($a+$f9+$start+$cam+$hit+$end+$f4),
  ($valid+$f9+$start+$cam+'[HOMELANDER_P1_FREEAIM_V004] MISS | range=500'),
  ($valid+$a),
  ($a+$f4+$f9+$start+$hit+$cam+$end),
  ($a+$f4+$f9+$start+$cam+'[HOMELANDER_P1_FREEAIM_V004] HIT | hitGOH=nil'+$end)
 )){
   if((Test-Ordered $bad $b) -eq 'ORDERED_F4_F9_HIT_END_CONSISTENT'){throw 'invalid chronological evidence accepted'}
 }
 Write-Host 'R019 READ-ONLY TEMPORAL SELFTEST PASS: good + five invalid sessions'
}
if($Action -eq 'SelfTest'){SelfTest;exit 0}
foreach($v in @($ReleaseDirectory,$R007ZipPath,$PrototypeRoot)){
 if([string]::IsNullOrWhiteSpace($v)){throw 'Provide -ReleaseDirectory, -R007ZipPath and -PrototypeRoot explicitly; no path guessing.'}
}
$ReleaseDirectory=[IO.Path]::GetFullPath($ReleaseDirectory)
$PrototypeRoot=[IO.Path]::GetFullPath($PrototypeRoot)
Same $R007ZipPath $PIN_PACK 'original R007 archive'
Same (Join-Path $ReleaseDirectory 'P1_PROMOTION_MANAGER.ps1') $PIN_MANAGER 'official R007 manager'
Same (Join-Path $ReleaseDirectory 'promotion_manifest.json') $PIN_MANIFEST 'official frozen manifest'
$m=Get-Content -LiteralPath (Join-Path $ReleaseDirectory 'promotion_manifest.json') -Raw | ConvertFrom-Json
if([string]$m.schema -ne 'homelander-p1-runtime-promotion/1.0' -or
   [string]$m.baseline.asiSha256 -ne $PIN_V001 -or
   [string]$m.baseline.loaderSha256 -ne $PIN_LOADER -or
   [string]$m.baseline.originalBinkSha256 -ne $PIN_BINK){throw 'BLOCKED: manifest incompatible with R007 frozen baseline'}
$stages=@($m.stages)
if($stages.Count -ne 13 -or [string]$stages[0].stage -ne 'v003' -or
   [string]$stages[0].packageSha256 -ne $PIN_V003 -or
   [string]$stages[0].asiSha256 -ne $PIN_V003_ASI){throw 'BLOCKED: first stage/manifest incompatible with frozen R007'}
foreach($s in $stages){
 $stageZip=Join-Path $ReleaseDirectory ([string]$s.package).Replace('/','\')
 Same $stageZip (([string]$s.packageSha256).ToLowerInvariant()) ("stage "+[string]$s.stage)
}
Write-Host 'R019 RELEASE AUTHENTICITY PASS: original ZIP, manager, manifest, all 13 stage packages'
if(!(Test-Path -LiteralPath (Join-Path $PrototypeRoot 'prototypef.exe') -PathType Leaf)){
 throw 'BLOCKED: -PrototypeRoot must be the existing game directory containing prototypef.exe'
}
if(Get-Process -Name prototypef -ErrorAction SilentlyContinue){
 throw 'BLOCKED: game is running; exit Prototype before preflight or log assessment'
}
Same (Join-Path $PrototypeRoot 'binkw32.dll') $PIN_LOADER 'game original verified ASI loader'
Same (Join-Path $PrototypeRoot 'binkw32Hooked.dll') $PIN_BINK 'game preserved original bink'
$asi=Sha (Join-Path $PrototypeRoot 'homelander_p1.asi')
$stage=if($asi -eq $PIN_V001){'v001'}elseif($asi -eq $PIN_V003_ASI){'v003'}else{throw "BLOCKED: game ASI is neither frozen v001 nor original v003; sha256=$asi"}
$statePath=Join-Path $PrototypeRoot '.homelander_promotion\state.json'
$state=$null
if(Test-Path -LiteralPath $statePath -PathType Leaf){
 $state=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
 if([string]$state.currentStage -ne $stage){throw 'BLOCKED: manager state != actual active ASI'}
}
if($stage -eq 'v003' -and $null -eq $state){throw 'BLOCKED: v003 stage is active but original manager state is missing'}
foreach($name in $BaseLua.Keys){
 Same (Join-Path (Join-Path $PrototypeRoot 'lua_p1') $name) ([string]$BaseLua[$name]) ("game canonical Lua "+$name)
}
if($stage -eq 'v003'){
 Same (Join-Path (Join-Path $PrototypeRoot 'lua_p1') 'freeaim_probe_v004_STAGED.lua') '89885eecdf1dcd1f324c6cd3c3580013674639167e0849688ed7036c75678cd1' 'original installed read-only F9 Lua'
}
Write-Host "R019 GAME FILE READINESS PASS: exact loader/ASI/baseline Lua hashes; active stage=$stage"
$log=Join-Path $PrototypeRoot 'homelander_p1_runtime.log'
if($Action -eq 'Preflight'){
 if($stage -eq 'v003' -and (Test-Path -LiteralPath $log -PathType Leaf)){
  if((Get-Item -LiteralPath $log).Length -gt 0){
   throw 'BLOCKED: nonempty v003 runtime log; preserve/export evidence; original R007 ResetLog only after review'
  }
 }
 if($state -and @($state.passedStages) -contains 'v003'){
  throw 'BLOCKED: first-live gate already recorded PASS; do not restart/overwrite its evidence'
 }
 if($stage -eq 'v001'){
  Write-Host 'R019 READY_FOR_FIRST_V003_INSTALL_AND_GAME_TEST: run ORIGINAL R007 ValidatePack, then START_V003_LIVE_TEST.cmd'
 }else{
  Write-Host 'R019 READY_FOR_FIRST_V003_GAME_TEST: original v003 installed and clean log; run ORIGINAL START_V003_LIVE_TEST.cmd'
 }
 Write-Host 'This tool has not installed, launched, altered, reset, or granted a game gate.'
 exit 0
}
if($stage -ne 'v003'){throw 'BLOCKED: read-only v003 evidence assessment requires the installed original v003 stage'}
if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'BLOCKED: authentic game runtime log missing'}
$raw=Get-Content -LiteralPath $log -Raw
if($raw -match [string]$m.forbiddenLogRegex){throw ('BLOCKED: fatal/abort/refused runtime log evidence: '+[regex]::Match($raw,[string]$m.forbiddenLogRegex).Value)}
$result=Test-Ordered $raw ([string]$stages[0].buildId)
if($result -ne 'ORDERED_F4_F9_HIT_END_CONSISTENT'){throw "R019 LIVE EVIDENCE INCOMPLETE: $result"}
Write-Host 'R019 LOG CHRONOLOGY CONSISTENT: latest READY -> F4 -> F9 -> BEGIN -> CAMERA -> valid object HIT -> END.'
Write-Host 'NOT AN AUTHENTICATED GAME RESULT OR PASS RECEIPT. Only original R007 manager Check records a gate after real game exit.'
