-- R014 original/new F18 void native world-effect submission regression.
-- Engine APIs are deterministic Lua mocks; NO real Prototype process.
dofile("homelander_p1_build/tests/r013_f17_once_integration.lua")
local dir="homelander_p1_build/lua_p1/"
local original=dir.."impact_vfx_gate_v012_STAGED.lua"
local guarded=dir.."impact_vfx_gate_v012_reserved_DORMANT.lua"
local function eq(a,b,m) assert(a==b,(m or "equal")..": "..tostring(a).." != "..tostring(b)) end
local calls,nested,mode=0,false,"normal"
local hit=Vector(1,2,3)
local function synthetic_f17_success()
 -- The full actual-source F17 success/exception gating is independently
 -- established in R013 above; this fixture isolates the F18 native boundary.
 HOMELANDER_DAMAGE_ONESHOT_PASSED=true
 HOMELANDER_DAMAGE_ONESHOT_RESERVED=true
 HOMELANDER_DAMAGE_LAST_TARGET="NPC"
 HOMELANDER_DAMAGE_LAST_HIT_POS=hit
end
em_AddWorldEffect=function(effect,pos,scale)
 calls=calls+1
 eq(effect,"missileImpact001","allowlisted VFX identifier")
 eq(pos,hit,"exact stored F17 impact point")
 assert(scale>=0.05 and scale<=0.50,"bounded VFX scale")
 if mode=="nested" and not nested then
  nested=true
  assert(Homelander_ImpactVFXOneShotV012(),"old unreserved F18 permits nested effect")
 end
 if mode=="throw_after_effect" then error("native VFX threw AFTER simulated submission") end
 return nil
end

dofile(original)
synthetic_f17_success()
mode="nested";nested=false;calls=0
assert(Homelander_ImpactVFXOneShotV012(),"old outer F18 returns after nested F18")
eq(calls,2,"old F18 submits twice via native reentrancy")
print("P1_PREVIOUS_F18_NATIVE_REENTRANCY_TWO_WORLD_EFFECTS_REPRODUCED")

dofile(guarded)
synthetic_f17_success()
mode="normal";calls=0
assert(Homelander_ImpactVFXOneShotV012(),"guarded F18 successful once")
eq(calls,1,"exactly one native VFX submission")
eq(HOMELANDER_IMPACT_VFX_RESERVED,true,"irreversible effect reservation")
eq(HOMELANDER_IMPACT_VFX_SUBMITTED,true,"F18 success only after returned native call")
eq(HOMELANDER_DAMAGE_ONESHOT_PASSED,false,"F17 proof consumed before effect")
assert(not Homelander_ImpactVFXOneShotV012(),"repeated F18 must refuse")
eq(calls,1,"no extra world effect")
print("P1_R014_F18_SINGLE_NATIVE_VFX_AND_F17_PROOF_CONSUMPTION_PASS")

dofile(guarded)
synthetic_f17_success()
mode="throw_after_effect";calls=0
assert(not Homelander_ImpactVFXOneShotV012(),"native effect exception is ambiguous, not success")
eq(calls,1,"one possibly effective native VFX submission")
eq(HOMELANDER_IMPACT_VFX_RESERVED,true,"ambiguous attempt permanently consumed")
eq(HOMELANDER_IMPACT_VFX_SUBMITTED,false,"no F19 success proof on ambiguous native VFX")
eq(HOMELANDER_DAMAGE_ONESHOT_PASSED,false,"upstream F17 cannot be replayed after ambiguous VFX")
assert(not Homelander_ImpactVFXOneShotV012(),"ambiguous native effect cannot retry")
eq(calls,1,"no duplicate world effect after exception")
print("P1_R014_F18_AMBIGUOUS_NATIVE_EXCEPTION_CONSUMED_NO_F19_PASS")

dofile(guarded)
synthetic_f17_success()
mode="normal";calls=0
HOMELANDER_IMPACT_VFX_SCALE=0/0
assert(not Homelander_ImpactVFXOneShotV012(),"nonfinite scale rejected before native effect")
eq(calls,0,"invalid scale zero native effects")
eq(HOMELANDER_IMPACT_VFX_RESERVED,false,"pre-submit failure has not consumed a valid F17 proof")
eq(HOMELANDER_DAMAGE_ONESHOT_PASSED,true,"pre-submit failure preserves F17 for valid retry")
HOMELANDER_IMPACT_VFX_SCALE=nil
assert(Homelander_ImpactVFXOneShotV012(),"valid retry after pre-submit error")
eq(calls,1,"exactly one VFX after corrected input")
print("P1_R014_F18_PRESUBMIT_REJECTION_PRESERVES_SAFE_RETRY_PASS")

dofile(guarded)
synthetic_f17_success()
mode="normal";calls=0
local oldDamagePos=HOMELANDER_DAMAGE_LAST_HIT_POS
local originalVector=Vector
local triggered=false
Vector=function(...)
 local r=originalVector(...)
 if not triggered then
  triggered=true
  HOMELANDER_DAMAGE_LAST_HIT_POS=originalVector(7,8,9)
 end
 return r
end
assert(not Homelander_ImpactVFXOneShotV012(),"F17 changed while vector components measured")
eq(calls,0,"no effect on superseded F17 impact location")
eq(HOMELANDER_IMPACT_VFX_RESERVED,false,"superseded source before native remains unconsumed")
Vector=originalVector
HOMELANDER_DAMAGE_LAST_HIT_POS=oldDamagePos
print("P1_R014_F18_SUPERSEDED_F17_HITPOINT_BLOCKS_VFX_PASS")
