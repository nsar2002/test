-- R011 nonfinite dynamic F16 ray/limit regression using actual Lua source.
-- Entire test runs mock game APIs; no real Prototype process or native effects.
dofile("homelander_p1_build/tests/r010_f10_attempt_integration.lua")
local old="homelander_p1_build/lua_p1/lasersight_dynamic_aim_gate_v010_STAGED.lua"
local new="homelander_p1_build/lua_p1/lasersight_dynamic_aim_gate_v010_finite_DORMANT.lua"
local function eq(a,b,m) assert(a==b,(m or "equal")..": "..tostring(a).." != "..tostring(b)) end
local oldLOS=fre_LineOfSightTest
local losCalls,laserCalls=0,0
fre_LineOfSightTest=function(start,finish,ignore,player)
  losCalls=losCalls+1
  if HOMELANDER_DYNAMIC_FREEAIM_RANGE ~= nil and
     HOMELANDER_DYNAMIC_FREEAIM_RANGE ~= HOMELANDER_DYNAMIC_FREEAIM_RANGE then
    assert(finish.z~=finish.z,"NaN ray endpoint must reach old native LOS bridge")
  end
  return true,0.5,Vector(0,0,5),Vector(0,1,0)
end
HL_LaserSightHeldStabilityProbe=function() return true end
HL_LaserSightDynamicStabilityProbe=function() return true end
HL_LaserSightResetDynamicGate=function() return true end
HL_LaserSightSubmitDual=function(...)
 laserCalls=laserCalls+1
 return true
end
HOMELANDER_PLAYER="A"
HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED=true
HOMELANDER_LASERSIGHT_SHADER_PASSED=true
HOMELANDER_EYE_ORIGIN_VERIFIED=true
HOMELANDER_EYE_ORIGIN_NAME="EYEPOINT"
HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER="A"
go_GetJointPosition=function(player,joint)
 eq(player,"A","dynamic mock eye player")
 eq(joint,"EYEPOINT","dynamic mock eye joint")
 return Vector(0,1,0)
end

dofile(old)
HOMELANDER_DYNAMIC_FREEAIM_RANGE=0/0
assert(Homelander_DynamicAimToggleV010(),"old F16 synthetic enable")
assert(Homelander_DynamicAimTickV010(),"old F16 accepts nonfinite ray and submits native LOS")
eq(losCalls,1,"old F16 sends NaN into LOS")
eq(laserCalls,1,"old F16 accepts the mocked hit")
assert(Homelander_DynamicAimToggleV010(),"disable previous F16")
print("P1_PREVIOUS_F16_NAN_RANGE_REACHES_NATIVE_LOS_REPRODUCED")

HOMELANDER_DYNAMIC_FREEAIM_RANGE=500
HOMELANDER_DYNAMIC_MAX_RENDER_FRAMES=0/0
HOMELANDER_DYNAMIC_MAX_TICKS=0/0
assert(Homelander_DynamicAimToggleV010(),"old F16 synthetic enable with NaN timeouts")
assert(Homelander_DynamicAimTickV010(),"old F16 accepts nonfinite timeout limits")
eq(losCalls,2,"old F16 enters LOS despite invalid limits")
assert(Homelander_DynamicAimToggleV010(),"disable previous F16 again")
print("P1_PREVIOUS_F16_NAN_LIMITS_ENTER_NATIVE_TICK_REPRODUCED")

dofile(new)
HOMELANDER_DYNAMIC_FREEAIM_RANGE=0/0
HOMELANDER_DYNAMIC_MAX_RENDER_FRAMES=nil
HOMELANDER_DYNAMIC_MAX_TICKS=nil
HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED=true
HOMELANDER_LASERSIGHT_SHADER_PASSED=true
assert(Homelander_DynamicAimToggleV010(),"new F16 synthetic enable")
local before=losCalls
assert(not Homelander_DynamicAimTickV010(),"new F16 rejects NaN range before native LOS")
eq(losCalls,before,"new F16 invalid ray causes no LOS call")
eq(laserCalls,2,"new F16 invalid ray causes no new laser submit")
local enabled=Homelander_DynamicAimStatusV010()
eq(enabled,false,"invalid range shuts off dynamic mode")
print("P1_R011_F16_NAN_RANGE_FAILCLOSED_NO_NATIVE_LOS_PASS")

HOMELANDER_DYNAMIC_FREEAIM_RANGE=500
HOMELANDER_DYNAMIC_MAX_RENDER_FRAMES=0/0
assert(Homelander_DynamicAimToggleV010(),"new F16 synthetic enable with NaN render frames")
before=losCalls
assert(not Homelander_DynamicAimTickV010(),"new F16 rejects NaN maxFrames early")
eq(losCalls,before,"NaN maxFrames causes zero LOS calls")
eq(Homelander_DynamicAimStatusV010(),false,"NaN maxFrames disables mode")
HOMELANDER_DYNAMIC_MAX_RENDER_FRAMES=nil
HOMELANDER_DYNAMIC_MAX_TICKS=0/0
assert(Homelander_DynamicAimToggleV010(),"new F16 synthetic enable with NaN maxTicks")
assert(not Homelander_DynamicAimTickV010(),"new F16 rejects NaN maxTicks")
eq(losCalls,before,"NaN maxTicks causes zero LOS calls")
eq(Homelander_DynamicAimStatusV010(),false,"NaN maxTicks disables mode")
print("P1_R011_F16_NAN_LIMITS_FAILCLOSED_BEFORE_NATIVE_PASS")

HOMELANDER_DYNAMIC_MAX_TICKS=nil
HOMELANDER_DYNAMIC_FREEAIM_RANGE=500
assert(Homelander_DynamicAimToggleV010(),"new F16 valid enable")
before=losCalls
local beforeLaser=laserCalls
assert(Homelander_DynamicAimTickV010(),"new F16 valid tick still submits")
eq(losCalls,before+1,"valid F16 exactly one LOS call")
eq(laserCalls,beforeLaser+1,"valid F16 exactly one native laser submit")
assert(Homelander_DynamicAimToggleV010(),"new F16 manual disable")
print("P1_R011_F16_VALID_RANGE_AND_TIMEOUT_POSITIVE_TICK_PASS")
fre_LineOfSightTest=oldLOS
HOMELANDER_DYNAMIC_FREEAIM_RANGE=nil
HOMELANDER_DYNAMIC_MAX_RENDER_FRAMES=nil
HOMELANDER_DYNAMIC_MAX_TICKS=nil
