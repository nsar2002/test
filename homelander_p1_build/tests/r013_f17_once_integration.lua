-- Actual source F17 void native mutation/reentrancy regression. Prototype never runs.
dofile("homelander_p1_build/tests/r012_f14_f15_provenance_integration.lua")
local path="homelander_p1_build/lua_p1/"
local old=path.."heatvision_damage_gate_v011_STAGED.lua"
local new=path.."heatvision_damage_gate_v011_reserved_DORMANT.lua"
local function eq(a,b,m) assert(a==b,(m or "equal")..": "..tostring(a).." != "..tostring(b)) end
local originalLOS=fre_LineOfSightTest
local originalGOH=HL_LastRayHitGOH
local originalValid=go_IsValid
local originalPlayer=HOMELANDER_PLAYER
local calls,nested=0,false
local mode="normal"
local fakeTarget="NPC"
local fakePlayer="A"
HOMELANDER_PLAYER=fakePlayer
HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED=true
HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES=120
HOMELANDER_LASERSIGHT_SHADER_PASSED=true
HL_LaserSightDynamicStabilityProbe=function() return true end
fre_LineOfSightTest=function(start,finish,ignore,player)
 eq(player,"A","F17 ray player")
 if mode=="player_switch" then HOMELANDER_PLAYER="B" end
 return true,0.5,Vector(0,0,5),Vector(0,1,0)
end
HL_LastRayHitGOH=function() return fakeTarget end
go_IsValid=function(h) return h=="A" or h=="B" or h=="NPC" end
go_ApplyDamage=function(target,amount)
 calls=calls+1
 eq(target,"NPC","one-shot damage target")
 assert(amount>=0.01 and amount<=1.0,"finite bounded one-shot damage amount")
 if mode=="nested_native" and not nested then
  nested=true
  assert(Homelander_HeatVisionDamageOneShotV011(),"old unreserved source permits nested second F17")
 end
 if mode=="throw_after_effect" then error("mock void binding threw after side effect") end
 return nil
end
dofile(old)
mode="nested_native";nested=false;calls=0
assert(Homelander_HeatVisionDamageOneShotV011(),"original outer one-shot success")
eq(calls,2,"original F17 submits twice if native damage callback synchronously invokes F17")
print("P1_PREVIOUS_F17_NATIVE_REENTRANCY_TWO_DAMAGE_SUBMITS_REPRODUCED")
mode="normal";calls=0
dofile(new)
HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED=true
HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES=120
HOMELANDER_PLAYER="A"
assert(Homelander_HeatVisionDamageOneShotV011(),"new reserved one-shot success")
eq(calls,1,"new one-shot submits exactly once")
eq(HOMELANDER_DAMAGE_ONESHOT_RESERVED,true,"success consumes native attempt")
eq(HOMELANDER_DAMAGE_ONESHOT_PASSED,true,"only successful native call may mint F18 proof")
assert(not Homelander_HeatVisionDamageOneShotV011(),"second call refused after success")
eq(calls,1,"no extra call after completed submission")
print("P1_R013_F17_SINGLE_NATIVE_SUBMISSION_AND_F18_SUCCESS_PROOF_PASS")

dofile(new) -- synthetic new Lua-state bootstrap ONLY, no game.
HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED=true
HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES=120
HOMELANDER_PLAYER="A"
mode="throw_after_effect";calls=0
assert(not Homelander_HeatVisionDamageOneShotV011(),"unknown native outcome is not a success")
eq(calls,1,"one possibly mutated native call")
eq(HOMELANDER_DAMAGE_ONESHOT_RESERVED,true,"uncertain native attempt remains permanently consumed")
eq(HOMELANDER_DAMAGE_ONESHOT_PASSED,false,"ambiguous damage never unlocks F18 VFX")
eq(HOMELANDER_DAMAGE_LAST_TARGET,nil,"ambiguous submission never exposes last success target")
assert(not Homelander_HeatVisionDamageOneShotV011(),"ambiguous mutation cannot retry")
eq(calls,1,"no double damage after void binding throws")
print("P1_R013_F17_AMBIGUOUS_VOID_EXCEPTION_CONSUMED_NO_RETRY_NO_F18_PASS")

dofile(new)
mode="player_switch";calls=0
HOMELANDER_PLAYER="A"
HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED=true
HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES=120
assert(not Homelander_HeatVisionDamageOneShotV011(),"native LOS player switch refuses damage")
eq(calls,0,"player change during LOS never damages stale target")
eq(HOMELANDER_DAMAGE_ONESHOT_RESERVED,false,"no native submission consumed before LOS validation")
eq(HOMELANDER_DAMAGE_ONESHOT_PASSED,false,"no mutation proof after switch")
print("P1_R013_F17_PLAYER_SWITCH_DURING_LOS_BLOCKS_DAMAGE_PASS")

-- Recent F17's native dynamic stability must be current at moment of submission.
dofile(new)
mode="normal";calls=0
HOMELANDER_PLAYER="A"
HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED=true
HOMELANDER_DYNAMIC_AIM_STABILITY_RENDER_FRAMES=120
HL_LaserSightDynamicStabilityProbe=function() return true end
local priorGOH=HL_LastRayHitGOH
HL_LastRayHitGOH=function()
 HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED=false
 return "NPC"
end
assert(not Homelander_HeatVisionDamageOneShotV011(),"F16 stability revoked inside hit callback")
eq(calls,0,"stale F16 proof causes no damage")
eq(HOMELANDER_DAMAGE_ONESHOT_RESERVED,false,"pre-submit rejection is not consumed")
HL_LastRayHitGOH=priorGOH
print("P1_R013_F17_REVOKED_F16_PROOF_BLOCKS_NATIVE_DAMAGE_PASS")
fre_LineOfSightTest=originalLOS
HL_LastRayHitGOH=originalGOH
go_IsValid=originalValid
HOMELANDER_PLAYER=originalPlayer
