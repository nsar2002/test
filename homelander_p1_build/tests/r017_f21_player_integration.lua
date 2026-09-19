-- R017 actual-source F21 payload must not borrow F17-F20 proof from another player.
-- F21 remains READ ONLY; no real game process or game mutation allowed.
dofile("homelander_p1_build/tests/r016_f20_player_integration.lua")
local dir="homelander_p1_build/lua_p1/"
local old=dir.."damagehit_payload_probe_v015_STAGED.lua"
local guarded=dir.."damagehit_payload_probe_v015_player_DORMANT.lua"
local function eq(a,b,m) assert(a==b,(m or "equal")..": "..tostring(a).." != "..tostring(b)) end
HOMELANDER_PLAYER="A"
HOMELANDER_TARGET_CONTINUITY_PASSED=true
HOMELANDER_IMPACT_VFX_SUBMITTED=true
assert(Homelander_DOTDryRunToggleV014(),"rebuild A-only F20 prior to old F21 proof check")
for i=1,35 do
 if HOMELANDER_DOT_DRYRUN_PASSED==true then break end
 assert(Homelander_DOTDryRunTickV014(),"rebuild F20 A sample "..i)
end
eq(HOMELANDER_DOT_DRYRUN_PASSED,true,"actual guarded F20 A proof")
eq(HOMELANDER_DOT_DRYRUN_PLAYER,"A","F20 bound to F17/F19 A")
go_GetJointPosition=function(player,joint)
 assert(player=="A" or player=="B","F21 eye joint current A/B")
 eq(joint,"EYEPOINT","F21 read-only joint")
 return Vector(0,1,0)
end
local damageCalls,effectCalls=0,0
go_ApplyDamage=function(...) damageCalls=damageCalls+1;error("F21 must never call damage") end
em_AddWorldEffect=function(...) effectCalls=effectCalls+1;error("F21 must never create native world effects") end

HOMELANDER_PLAYER="B"
assert(Homelander_EyeOriginProbeV006(),"F11 can legitimately measure B eye for old F21")
dofile(old)
assert(Homelander_DamageHitPayloadProbeV015(),"old F21 wrongly builds B payload using F20 A success")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED,true,"old F21 publishes cross-player success")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_TARGET,"NPC","same NPC disguises different owner")
print("P1_PREVIOUS_F21_ACCEPTS_PLAYER_B_WITH_F17_F20_PLAYER_A_REPRODUCED")

dofile(guarded)
assert(not Homelander_DamageHitPayloadProbeV015(),"guarded F21 cannot borrow A chain for B")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED,false,"failed newer F21 clears old payload success")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PLAYER,nil,"no cross-player payload source")
HOMELANDER_PLAYER="A"
assert(Homelander_EyeOriginProbeV006(),"fresh F11 A for current A chain")
assert(Homelander_DamageHitPayloadProbeV015(),"guarded same-A F21 payload succeeds")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED,true,"guarded F21 positive")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PLAYER,"A","payload ties back to F17 A")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_EYE_EPOCH,HOMELANDER_EYE_ORIGIN_EPOCH,"current F11 eye generation")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_VERIFIED_ATTEMPT,HOMELANDER_DAMAGEHIT_PAYLOAD_ATTEMPT,"current F21 generation")
eq(damageCalls,0,"read-only F21 never damages")
eq(effectCalls,0,"read-only F21 never spawns effect")
print("P1_R017_F21_EXACT_ORIGINATING_PLAYER_AND_F11_EPOCH_PASS")

local priorHealth=go_GetHealth
go_GetHealth=function(target)
 HOMELANDER_PLAYER="B"
 return priorHealth(target)
end
assert(not Homelander_DamageHitPayloadProbeV015(),"F21 current player changed by native health getter")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED,false,"reentrant player switch no stale payload PASS")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PLAYER,nil,"failed latest F21 erases prior A")
go_GetHealth=priorHealth
HOMELANDER_PLAYER="A"
print("P1_R017_F21_HEALTH_CALLBACK_PLAYER_SWITCH_FAILCLOSED_PASS")

assert(Homelander_EyeOriginProbeV006(),"refresh A eye before eye-change test")
go_GetHealth=function(target)
 assert(Homelander_EyeOriginProbeV006(),"nested newer A F11 from health getter")
 return priorHealth(target)
end
local beforeEye=HOMELANDER_EYE_ORIGIN_EPOCH
assert(not Homelander_DamageHitPayloadProbeV015(),"F21 rejects F11 eye generation superseded during health getter")
eq(HOMELANDER_EYE_ORIGIN_EPOCH,beforeEye+1,"actual F11 newer measurement was obtained")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED,false,"stale F21 cannot publish old eye payload")
go_GetHealth=priorHealth
assert(Homelander_DamageHitPayloadProbeV015(),"fresh F21 after superseded eye still passes")
print("P1_R017_F21_NESTED_F11_SAME_PLAYER_REJECTS_STALE_EYE_PASS")

local priorMaxHealth=go_GetMaxHealth
local nested=false
go_GetMaxHealth=function(target)
 if not nested then
  nested=true
  assert(Homelander_DamageHitPayloadProbeV015(),"newer nested F21 uses same A and NPC")
 end
 return priorMaxHealth(target)
end
local priorAttempt=HOMELANDER_DAMAGEHIT_PAYLOAD_ATTEMPT
assert(not Homelander_DamageHitPayloadProbeV015(),"older F21 cannot publish over newer nested F21")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_ATTEMPT,priorAttempt+2,"older and nested new F21 attempts tracked")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_VERIFIED_ATTEMPT,HOMELANDER_DAMAGEHIT_PAYLOAD_ATTEMPT,"newest F21 proof survives")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PLAYER,"A","newest F21 remains same A")
go_GetMaxHealth=priorMaxHealth
eq(damageCalls,0,"F21 suite invokes no native damage")
eq(effectCalls,0,"F21 suite invokes no native world effect")
print("P1_R017_F21_SAME_PLAYER_NESTED_ATTEMPT_PRESERVES_NEWER_PROOF_PASS")
