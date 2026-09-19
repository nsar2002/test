-- R016 F20 dry-run original mixed-player bug and paired guard regression.
-- Runs full guarded F17->F18->F19 actual-source mock chain; NEVER real game.
dofile("homelander_p1_build/tests/r015_f19_player_integration.lua")
local dir="homelander_p1_build/lua_p1/"
local original=dir.."dot_dryrun_scheduler_v014_STAGED.lua"
local guarded=dir.."dot_dryrun_scheduler_v014_player_DORMANT.lua"
local function eq(a,b,m) assert(a==b,(m or "equal")..": "..tostring(a).." != "..tostring(b)) end
HOMELANDER_PLAYER="A"
HOMELANDER_IMPACT_VFX_SUBMITTED=true
HOMELANDER_CONTINUITY_REQUIRED_SECONDS=1.0
HOMELANDER_CONTINUITY_REQUIRED_SAMPLES=15
assert(Homelander_TargetContinuityToggleV013(),"fresh F19 continuity A after preceding regressions")
for i=1,15 do assert(Homelander_TargetContinuityTickV013(),"fresh source F19 A sample "..i) end
eq(HOMELANDER_TARGET_CONTINUITY_PASSED,true,"F19 proof current")
eq(HOMELANDER_TARGET_CONTINUITY_PLAYER,"A","F19 provenance bound to F17 A")
local damageCalls,worldEffectCalls=0,0
go_ApplyDamage=function(...) damageCalls=damageCalls+1;error("F20 is read-only: native damage forbidden") end
em_AddWorldEffect=function(...) worldEffectCalls=worldEffectCalls+1;error("F20 is read-only: VFX forbidden") end
dofile(original)
HOMELANDER_PLAYER="B"
assert(Homelander_DOTDryRunToggleV014(),"original F20 wrongly allows B using A F19 pass")
for i=1,33 do
 if Homelander_DOTDryRunStatusV014()==false then break end
 assert(Homelander_DOTDryRunTickV014(),"old dryrun B mock tick "..i)
end
eq(HOMELANDER_DOT_DRYRUN_PASSED,true,"old F20 reaches PASS for B despite F17/F19 A origin")
eq(HOMELANDER_DOT_DRYRUN_TARGET,"NPC","same NPC masks source player mismatch")
print("P1_PREVIOUS_F20_ACCEPTS_PLAYER_B_WITH_F17_F19_PLAYER_A_REPRODUCED")

dofile(guarded)
HOMELANDER_PLAYER="B"
assert(not Homelander_DOTDryRunToggleV014(),"guarded F20 rejects B with A F17/F19")
eq(HOMELANDER_DOT_DRYRUN_PASSED,false,"failed new F20 invalidates old dryrun PASS")
eq(HOMELANDER_DOT_DRYRUN_PLAYER,nil,"failed attempt cannot expose provenance")
HOMELANDER_PLAYER="A"
assert(Homelander_DOTDryRunToggleV014(),"guarded F20 starts with actual F17/F19 player A")
for i=1,9 do assert(Homelander_DOTDryRunTickV014(),"new F20 initial A sample "..i) end
HOMELANDER_PLAYER="B"
assert(not Homelander_DOTDryRunTickV014(),"guarded F20 rejects new player B before any more samples")
eq(Homelander_DOTDryRunStatusV014(),false,"guarded F20 stops after source player replacement")
eq(HOMELANDER_DOT_DRYRUN_PASSED,false,"mixed A/B scheduler never publishes F21 proof")
eq(HOMELANDER_DOT_DRYRUN_PLAYER,nil,"no mixed-player provenance")
eq(damageCalls,0,"no native damage by F20")
eq(worldEffectCalls,0,"no native VFX by F20")
print("P1_R016_F20_MIXED_PLAYER_DRYRUN_FAILCLOSED_NO_DAMAGE_PASS")

HOMELANDER_PLAYER="A"
assert(Homelander_DOTDryRunToggleV014(),"guarded F20 re-arms for originating player A")
for i=1,35 do
 if HOMELANDER_DOT_DRYRUN_PASSED==true then break end
 assert(Homelander_DOTDryRunTickV014(),"new F20 A-only tick "..i)
end
eq(HOMELANDER_DOT_DRYRUN_PASSED,true,"valid same-player dry-run finishes")
eq(HOMELANDER_DOT_DRYRUN_PLAYER,"A","success bound to F17/F19 A")
eq(HOMELANDER_DOT_DRYRUN_TARGET,"NPC","F21 proof same target")
eq(damageCalls,0,"dryrun did not damage")
eq(worldEffectCalls,0,"dryrun did not spawn world effect")
print("P1_R016_F20_ORIGINATING_PLAYER_VALID_DRYRUN_PASS")

HOMELANDER_TARGET_CONTINUITY_PASSED=false
assert(not Homelander_DOTDryRunToggleV014(),"new F20 attempt refuses now revoked F19 proof")
eq(HOMELANDER_DOT_DRYRUN_PASSED,false,"new failed F20 attempt clears previous F21 success")
eq(HOMELANDER_DOT_DRYRUN_PLAYER,nil,"new failed F20 clears prior originating player")
HOMELANDER_TARGET_CONTINUITY_PASSED=true
print("P1_R016_F20_FAILED_NEW_ATTEMPT_REVOKES_STALE_F21_PASS")

local oldGOH=HL_LastRayHitGOH
HOMELANDER_PLAYER="A"
assert(Homelander_DOTDryRunToggleV014(),"new F20 starts for reentrancy test")
HL_LastRayHitGOH=function()
 HOMELANDER_PLAYER="B"
 return "NPC"
end
assert(not Homelander_DOTDryRunTickV014(),"player switched inside F20 target getter")
eq(HOMELANDER_DOT_DRYRUN_PASSED,false,"no proof after reentrant B switch")
eq(Homelander_DOTDryRunStatusV014(),false,"switch disables F20")
HL_LastRayHitGOH=oldGOH
HOMELANDER_PLAYER="A"
print("P1_R016_F20_LOS_CALLBACK_PLAYER_SWITCH_FAILCLOSED_PASS")
