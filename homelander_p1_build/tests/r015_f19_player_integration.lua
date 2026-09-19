-- R015 actual staged F17/F18 -> F19 continuity/player switch regression.
-- Only mocked engine APIs; no real Prototype executable or binary mutation.
dofile("homelander_p1_build/tests/r014_f18_vfx_once_integration.lua")
local dir="homelander_p1_build/lua_p1/"
local f17=dir.."heatvision_damage_gate_v011_reserved_player_DORMANT.lua"
local f18=dir.."impact_vfx_gate_v012_reserved_DORMANT.lua"
local oldF19=dir.."target_continuity_probe_v013_STAGED.lua"
local newF19=dir.."target_continuity_probe_v013_player_DORMANT.lua"
local function eq(a,b,msg) assert(a==b,(msg or "equal")..": "..tostring(a).." != "..tostring(b)) end
HOMELANDER_PLAYER="A"
HOMELANDER_LASERSIGHT_SHADER_PASSED=true
HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED=true
HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES=120
HL_LaserSightDynamicStabilityProbe=function() return true end
HL_LaserSightResetDynamicGate=function() return true end
go_IsValid=function(h) return h=="A" or h=="B" or h=="NPC" end
go_GetPosition=function(player)
 assert(player=="A" or player=="B","fake position only for valid player")
 return Vector(0,0,0)
end
cm_GetCurrentRenderCameraPosition=function() return Vector(0,0,-5) end
HL_GetCameraFrame=function() return "0,0,-5,1,0,0,0,1,0,0,0,1" end
fre_LineOfSightTest=function(start,finish,ignore,player)
 assert(player=="A" or player=="B","mock ray player identity")
 return true,0.5,Vector(0,0,5),Vector(0,1,0)
end
HL_LastRayHitGOH=function() return "NPC" end
go_GetHealth=function(target) eq(target,"NPC","health target");return 70 end
go_GetMaxHealth=function(target) eq(target,"NPC","max health target");return 100 end
time_GetSimulationDelta=function() return 0.10 end
local damageCalls,effectCalls=0,0
go_ApplyDamage=function(target,amount)
 eq(target,"NPC","actual-source F17 target")
 damageCalls=damageCalls+1
end
em_AddWorldEffect=function(effect,hitPos,scale)
 eq(effect,"missileImpact001","actual-source F18 allowlisted VFX")
 effectCalls=effectCalls+1
end
dofile(f17)
assert(Homelander_HeatVisionDamageOneShotV011(),"mock native F17 success")
eq(HOMELANDER_DAMAGE_LAST_PLAYER,"A","actual F17 binds source A")
eq(HOMELANDER_DAMAGE_LAST_TARGET,"NPC","actual F17 binds target NPC")
eq(damageCalls,1,"only one F17 mock mutation")
dofile(f18)
assert(Homelander_ImpactVFXOneShotV012(),"mock native F18 success")
eq(effectCalls,1,"one F18 mock effect")
eq(HOMELANDER_IMPACT_VFX_SUBMITTED,true,"actual guarded F18 provenance")
print("P1_R015_ACTUAL_SOURCE_F17_F18_MOCK_CHAIN_PLAYER_A_PASS")

HOMELANDER_CONTINUITY_REQUIRED_SECONDS=1
HOMELANDER_CONTINUITY_REQUIRED_SAMPLES=15
dofile(oldF19)
assert(Homelander_TargetContinuityToggleV013(),"old F19 enabled by actual F17/F18 source")
for i=1,4 do assert(Homelander_TargetContinuityTickV013(),"old F19 initial A frame") end
HOMELANDER_PLAYER="B"
for i=1,11 do assert(Homelander_TargetContinuityTickV013(),"old F19 illegitimately counts B frame") end
eq(HOMELANDER_TARGET_CONTINUITY_PASSED,true,"original mixes A and B in single F19 proof")
eq(HOMELANDER_TARGET_CONTINUITY_TARGET,"NPC","same NPC hides player change")
print("P1_PREVIOUS_F19_MIXED_PLAYER_A_B_CONTINUITY_PASS_REPRODUCED")

dofile(newF19)
HOMELANDER_PLAYER="A"
assert(Homelander_TargetContinuityToggleV013(),"new F19 enabled for originating A")
for i=1,4 do assert(Homelander_TargetContinuityTickV013(),"new F19 initial A frames") end
HOMELANDER_PLAYER="B"
assert(not Homelander_TargetContinuityTickV013(),"new F19 stops after current player B replaces originating A")
eq(HOMELANDER_TARGET_CONTINUITY_PASSED,false,"no false F20 proof")
eq(HOMELANDER_TARGET_CONTINUITY_PLAYER,nil,"no cross-player proof publication")
eq(Homelander_TargetContinuityStatusV013(),false,"new F19 disabled after player switch")
print("P1_R015_F19_MIXED_PLAYER_SAMPLES_FAILCLOSED_PASS")

HOMELANDER_PLAYER="A"
assert(Homelander_TargetContinuityToggleV013(),"new F19 fresh A only")
for i=1,15 do assert(Homelander_TargetContinuityTickV013(),"new F19 A-only frame "..tostring(i)) end
eq(HOMELANDER_TARGET_CONTINUITY_PASSED,true,"same-player target continuity succeeds")
eq(HOMELANDER_TARGET_CONTINUITY_PLAYER,"A","success bound to exact originating F17 player")
eq(HOMELANDER_TARGET_CONTINUITY_TARGET,"NPC","F17 NPC target unchanged")
print("P1_R015_F19_ORIGINATING_PLAYER_15_FRAME_POSITIVE_PASS")

HOMELANDER_IMPACT_VFX_SUBMITTED=false
assert(not Homelander_TargetContinuityToggleV013(),"failed new F19 attempt with revoked F18")
eq(HOMELANDER_TARGET_CONTINUITY_PASSED,false,"new failed attempt clears old F20 success")
eq(HOMELANDER_TARGET_CONTINUITY_PLAYER,nil,"new failed attempt clears old player")
HOMELANDER_IMPACT_VFX_SUBMITTED=true
print("P1_R015_F19_FAILED_NEW_ATTEMPT_REVOKES_STALE_F20_PASS")

local savedHealth=go_GetHealth
go_GetHealth=function(target)
 HOMELANDER_PLAYER="B"
 return savedHealth(target)
end
HOMELANDER_PLAYER="A"
assert(not Homelander_TargetContinuityToggleV013(),"reentrant health getter changes player during activation")
eq(HOMELANDER_TARGET_CONTINUITY_PASSED,false,"health callback player switch cannot mint F19 proof")
eq(Homelander_TargetContinuityStatusV013(),false,"no active F19 after stale enable")
go_GetHealth=savedHealth
print("P1_R015_F19_ENABLE_HEALTH_CALLBACK_PLAYER_SWITCH_FAILCLOSED_PASS")
