$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Import-Module "$PSScriptRoot/P1_V003_GATE_PARSER.psm1" -Force

function Assert-True([bool]$Condition, [string]$Label) {
    if (!$Condition) { throw "ASSERT TRUE FAILED: $Label" }
}
function Assert-False([bool]$Condition, [string]$Label) {
    if ($Condition) { throw "ASSERT FALSE FAILED: $Label" }
}

$passLog = @'
READY build=P1_RuntimeProbe_003_FREEAIM_STAGED_20260918. F4=read-only math
F4: read-only discovery + flight math probe
[HOMELANDER_P1_PROBE_V3] HOMELANDER_PLAYER SET TO VERIFIED HANDLE (Lua global only; no gameplay mutation)
[HOMELANDER_P1_PROBE_V3] END — NO GAMEPLAY STATE WAS INTENTIONALLY MODIFIED
[HOMELANDER_P1_FLIGHT_MATH_V2_2] END — READ ONLY
F9: read-only free-aim camera/LOS probe
[HOMELANDER_P1_FREEAIM_V004] BEGIN — READ ONLY
[HOMELANDER_P1_FREEAIM_V004] CAMERA | axis=2 scores=1:0.1,2:0.91,3:0.2 margin=0.71 cameraPlayerDistance=5.25
[HOMELANDER_P1_FREEAIM_V004] HIT | fraction=0.375 pos=Vector(10,20,30) normal=Vector(0,1,0) hitGOH=nil hitName=nil
[HOMELANDER_P1_FREEAIM_V004] END — READ ONLY
'@
$r = Test-V003GateLog -LogText $passLog
Assert-True $r.pass "canonical synthetic PASS"
Assert-True $r.checks.camera_measurement "camera measurement"
Assert-True $r.checks.fresh_hit "fresh hit"
if ($r.camera_axis -ne 2) { throw "camera axis parse failed" }
if ([math]::Abs($r.camera_margin - 0.71) -gt 0.000001) { throw "camera margin parse failed" }
if ([math]::Abs($r.hit_fraction - 0.375) -gt 0.000001) { throw "hit fraction parse failed" }

$miss = $passLog -replace '\[HOMELANDER_P1_FREEAIM_V004\] HIT \|[^\r\n]+', '[HOMELANDER_P1_FREEAIM_V004] MISS | range=500'
$r = Test-V003GateLog -LogText $miss
Assert-False $r.pass "MISS must not pass"
Assert-False $r.checks.fresh_hit "MISS fresh_hit false"

$nl = [Environment]::NewLine
$abort = $passLog + $nl + "[HOMELANDER_P1_FREEAIM_V004] ABORT: camera frame invalid"
$r = Test-V003GateLog -LogText $abort
Assert-False $r.pass "ABORT must not pass"
Assert-False $r.checks.no_fatal_or_abort "abort marker"

$mutation = $passLog + $nl + "F6: enable flight"
$r = Test-V003GateLog -LogText $mutation
Assert-False $r.pass "mutation hotkey must not pass"
Assert-False $r.checks.no_mutation_hotkey_dispatch "F6 marker"

$zeroMargin = $passLog -replace 'margin=0\.71', 'margin=0'
$r = Test-V003GateLog -LogText $zeroMargin
Assert-False $r.pass "zero axis margin must not pass"
Assert-False $r.checks.camera_measurement "zero margin measurement"

$badFraction = $passLog -replace 'fraction=0\.375', 'fraction=1.5'
$r = Test-V003GateLog -LogText $badFraction
Assert-False $r.pass "fraction >1 must not pass"
Assert-False $r.checks.fresh_hit "bad fraction"

Write-Host "PASS: v003 parser synthetic positive/negative tests"
