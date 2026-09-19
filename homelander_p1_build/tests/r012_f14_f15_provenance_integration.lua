-- R012 F14/F15 exact native one-shot provenance and held lifetime regression.
-- All game functions mocked; no actual Prototype, ASI load or visual effect.
dofile("homelander_p1_build/tests/r011_f16_finite_integration.lua")
local repo="homelander_p1_build/lua_p1/"
local oldF14=repo.."lasersight_native_gate_v008_STAGED.lua"
local oldF15=repo.."lasersight_held_gate_v009_STAGED.lua"
local newF14=repo.."lasersight_native_gate_v008_provenance_DORMANT.lua"
local newF15=repo.."lasersight_held_gate_v009_provenance_finite_DORMANT.lua"
local function eq(a,b,msg) assert(a==b,(msg or "equal")..": "..tostring(a).." != "..tostring(b)) end
local laserCalls=0
HL_LaserSightSubmitDual=function(...)
 laserCalls=laserCalls+1
 return true
end
HL_LaserSightResetHeldGate=function() return true end
HOMELANDER_PLAYER="A"
HOMELANDER_LASERSIGHT_SHADER_PASSED=true
HOMELANDER_EYE_HALF_SEPARATION=nil
HOMELANDER_LASERSIGHT_MAX_HELD_FRAMES=nil
assert(Homelander_FreeAimProbe(),"fresh F9 for original F14")
assert(Homelander_FreeAimLocalOffsetProbe(),"fresh F10 for original F14")
assert(Homelander_EyeOriginProbeV006(),"fresh F11 for original F14")
dofile(oldF14)
dofile(oldF15)
assert(Homelander_LaserSightOneShotV008(),"original F14 synthetic positive submit")
eq(HOMELANDER_LASERSIGHT_ONESHOT_LAST_OK,true,"original F14 prior success")
HOMELANDER_LASERSIGHT_SHADER_PASSED=false
assert(not Homelander_LaserSightOneShotV008(),"original F14 next attempt fails shader gate")
eq(HOMELANDER_LASERSIGHT_ONESHOT_LAST_OK,true,"old F14 retains previous receipt despite latest failure")
print("P1_PREVIOUS_F14_FAILED_LATEST_ATTEMPT_RETAINS_STALE_SUCCESS_REPRODUCED")
HOMELANDER_LASERSIGHT_SHADER_PASSED=true
assert(Homelander_FreeAimProbe(),"fresh F9 on SAME target after previous F14")
assert(Homelander_FreeAimLocalOffsetProbe(),"fresh F10 on SAME target after previous F14")
assert(Homelander_LaserSightHeldToggleV009(),"old F15 incorrectly accepts previous F14 success from older hit")
print("P1_PREVIOUS_F15_ACCEPTS_STALE_F14_SAME_TARGET_REPRODUCED")

HOMELANDER_LASERSIGHT_MAX_HELD_FRAMES=0/0
local before=laserCalls
for i=1,65 do assert(Homelander_LaserSightHeldTickV009(),"old F15 still active after invalid maxFrames") end
eq(laserCalls,before+65,"old F15 sent 65 native ticks despite invalid timeout")
eq(Homelander_LaserSightHeldStatusV009(),true,"old F15 failed to stop at finite minimum 60 frames")
assert(Homelander_LaserSightHeldToggleV009(),"disable old F15")
print("P1_PREVIOUS_F15_NAN_MAX_FRAMES_DEFIES_HELD_TIMEOUT_REPRODUCED")

dofile(newF14)
dofile(newF15)
HOMELANDER_LASERSIGHT_MAX_HELD_FRAMES=nil
HOMELANDER_LASERSIGHT_SHADER_PASSED=true
assert(Homelander_LaserSightOneShotV008(),"new F14 current F9/F10/F11 exact proof")
eq(HOMELANDER_LASERSIGHT_ONESHOT_F9_EPOCH,HOMELANDER_FREEAIM_VERIFIED_EPOCH,"new F14 F9 proof")
eq(HOMELANDER_LASERSIGHT_ONESHOT_F10_ATTEMPT,HOMELANDER_FREEAIM_F10_VERIFIED_ATTEMPT,"new F14 F10 proof")
eq(HOMELANDER_LASERSIGHT_ONESHOT_F11_EPOCH,HOMELANDER_EYE_ORIGIN_VERIFIED_EPOCH,"new F14 F11 proof")
assert(Homelander_LaserSightHeldToggleV009(),"new F15 accepts fresh F14 exact proof")
assert(Homelander_FreeAimProbe(),"fresh F9 SAME NPC while held mode was armed")
assert(Homelander_FreeAimLocalOffsetProbe(),"fresh F10 SAME NPC while held mode was armed")
before=laserCalls
assert(not Homelander_LaserSightHeldTickV009(),"new F15 refuses stale F14 after new same-target F9/F10")
eq(laserCalls,before,"no native held submit after proof mismatch")
eq(Homelander_LaserSightHeldStatusV009(),false,"new F15 disables stale held mode")
print("P1_R012_F15_F14_EXACT_F9_F10_F11_LINEAGE_PASS")

assert(Homelander_LaserSightOneShotV008(),"new F14 fresh success after new F9/F10")
HOMELANDER_LASERSIGHT_SHADER_PASSED=false
assert(not Homelander_LaserSightOneShotV008(),"new F14 failed latest attempt")
eq(HOMELANDER_LASERSIGHT_ONESHOT_LAST_OK,false,"new failed F14 clears old success")
eq(HOMELANDER_LASERSIGHT_ONESHOT_LAST_TARGET,nil,"new failed F14 clears old GOH receipt")
HOMELANDER_LASERSIGHT_SHADER_PASSED=true
assert(not Homelander_LaserSightHeldToggleV009(),"new F15 cannot inherit failed F14 receipt")
print("P1_R012_FAILED_LATEST_F14_CLEARS_OLD_SUCCESS_F15_BLOCKED_PASS")

assert(Homelander_LaserSightOneShotV008(),"new F14 reset fresh one-shot success")
assert(Homelander_LaserSightHeldToggleV009(),"new F15 enable for invalid lifetime")
HOMELANDER_LASERSIGHT_MAX_HELD_FRAMES=0/0
before=laserCalls
assert(not Homelander_LaserSightHeldTickV009(),"new F15 rejects NaN timeout before native")
eq(laserCalls,before,"NaN lifetime triggers no native LaserSight")
eq(Homelander_LaserSightHeldStatusV009(),false,"NaN lifetime switches held mode off")
eq(HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED,false,"NaN lifetime invalidates held stability")
print("P1_R012_F15_NAN_LIFETIME_BLOCKS_NATIVE_SUBMISSION_PASS")

HOMELANDER_LASERSIGHT_MAX_HELD_FRAMES=60
assert(Homelander_LaserSightOneShotV008(),"new F14 fresh one-shot before finite held test")
assert(Homelander_LaserSightHeldToggleV009(),"new F15 enable for finite lifetime")
before=laserCalls
for i=1,60 do assert(Homelander_LaserSightHeldTickV009(),"new F15 valid held tick "..tostring(i)) end
eq(laserCalls,before+60,"finite held mode exactly 60 native ticks")
eq(Homelander_LaserSightHeldStatusV009(),false,"finite held auto timeout after 60 ticks")
print("P1_R012_F14_F15_VALID_REAL_SOURCE_60_TICK_MOCK_PASS")
HOMELANDER_LASERSIGHT_MAX_HELD_FRAMES=nil
