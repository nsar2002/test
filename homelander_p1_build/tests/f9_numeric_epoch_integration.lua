-- Actual-source Lua 5.1 F9 nonfinite geometry and ray-range regression.
-- Reuses full F9-F12 epoch suite; all engine functions are mocks.
dofile("homelander_p1_build/tests/f9_f12_epoch_reentrancy.lua")
local function eq(a,b,m) assert(a==b,(m or "eq")..": "..tostring(a).." ~= "..tostring(b)) end
local previousF9="homelander_p1_build/lua_p1/freeaim_probe_v004_epoch_DORMANT.lua"
local numericF9="homelander_p1_build/lua_p1/freeaim_probe_v004_numeric_epoch_DORMANT.lua"
local baseLOS=fre_LineOfSightTest
local oldFrame=HL_GetCameraFrame
HOMELANDER_PLAYER="A"
HOMELANDER_FREEAIM_RANGE=0/0
dofile(previousF9)
local oldCalls=0
fre_LineOfSightTest=function(start,finish,ignore,player)
 oldCalls=oldCalls+1
 assert(finish.z~=finish.z,"NaN range must reach original F9 native-LOS bridge to reproduce bug")
 return baseLOS(start,finish,ignore,player)
end
assert(Homelander_FreeAimProbe(),"old epoch F9 accepts NaN ray-range mock")
eq(oldCalls,1,"old F9 submits one nonfinite native LOS")
print("P1_PREVIOUS_EPOCH_F9_NAN_RANGE_REACHES_LOS_REPRODUCED")

-- New F9 refuses the same input before native LOS. No hit/target proof is published.
dofile(numericF9)
local newCalls=0
fre_LineOfSightTest=function(start,finish,ignore,player)
 newCalls=newCalls+1
 return baseLOS(start,finish,ignore,player)
end
assert(not Homelander_FreeAimProbe(),"new numeric F9 rejects NaN range")
eq(newCalls,0,"NaN range must not reach native LOS")
eq(HOMELANDER_FREEAIM_HIT,nil,"NaN F9 does not publish target")
eq(HOMELANDER_FREEAIM_VERIFIED_EPOCH,nil,"NaN F9 does not publish epoch")
eq(HOMELANDER_FREEAIM_F10_EPOCH,nil,"NaN F9 clears F10 epoch")
HOMELANDER_FREEAIM_RANGE=math.huge
assert(not Homelander_FreeAimProbe(),"new F9 rejects +Inf range")
eq(newCalls,0,"Inf range never reaches native LOS")
print("P1_F9_NONFINITE_RANGE_FAILCLOSED_PASS")

HOMELANDER_FREEAIM_RANGE=500
HL_GetCameraFrame=function() return "0,0,-5,1e309,0,0,0,1,0,0,0,1" end
assert(not Homelander_FreeAimProbe(),"nonfinite camera frame must be rejected")
eq(newCalls,0,"nonfinite frame cannot reach LOS")
HL_GetCameraFrame=oldFrame
assert(Homelander_FreeAimProbe(),"valid frame and finite range works")
eq(newCalls,1,"valid F9 calls LOS exactly once")
eq(HOMELANDER_FREEAIM_VERIFIED_EPOCH,HOMELANDER_FREEAIM_EPOCH,"fresh hit bound to F9 epoch")
assert(Homelander_FreeAimLocalOffsetProbe(),"F10 accepts valid finite F9 proof")
assert(Homelander_EyeOriginProbeV006(),"F11 accepts valid current eye")
assert(Homelander_DualEyeFreeAimRenderProbe(),"F12 accepts positive numeric F9 full chain")
print("P1_F9_NUMERIC_EPOCH_F9_TO_F12_INTEGRATION_PASS")
HOMELANDER_FREEAIM_RANGE=nil
fre_LineOfSightTest=baseLOS
