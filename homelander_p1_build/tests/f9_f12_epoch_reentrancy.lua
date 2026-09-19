-- Deterministic Lua 5.1 real-source nested F9/F10/F12 provenance regression.
-- Reuses original-source baseline tests, but engine callbacks below are mocks only.
dofile("homelander_p1_build/tests/f10_finite_to_f12_integration.lua")
local function eq(a,b,m) assert(a==b,(m or "eq")..": "..tostring(a).." ~= "..tostring(b)) end
local oldF10="homelander_p1_build/lua_p1/freeaim_local_offset_probe_v005_finite_DORMANT.lua"
local newF9="homelander_p1_build/lua_p1/freeaim_probe_v004_epoch_DORMANT.lua"
local newF10="homelander_p1_build/lua_p1/freeaim_local_offset_probe_v005_epoch_DORMANT.lua"
local newF12="homelander_p1_build/lua_p1/dual_eye_freeaim_render_v007_epoch_DORMANT.lua"
local originalTransform=go_Local2World
local hitZ=5
fre_LineOfSightTest=function(start,finish,ignore,player)
 eq(player,"A","same original player")
 return true,0.5,Vector(0,0,hitZ),Vector(0,1,0)
end
HOMELANDER_PLAYER="A"
HOMELANDER_EYE_HALF_SEPARATION=nil
dofile(oldF10)
assert(Homelander_FreeAimProbe(),"baseline guarded F9 A/NPC hit at z5")
local nested=false
go_Local2World=function(h,v)
 if not nested then
  nested=true
  hitZ=6
  assert(Homelander_FreeAimProbe(),"nested F9 A/NPC hit at z6")
 end
 return originalTransform(h,v)
end
assert(Homelander_FreeAimLocalOffsetProbe(),"old finite F10 accepts old hit despite nested newer same-player/target F9")
eq(HOMELANDER_FREEAIM_HIT_POS.z,6,"current F9 world hit")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET.z,5,"stale F10 local target offset")
print("P1_OLD_GUARDED_F10_REENTRANT_SAME_TARGET_STALE_OFFSET_REPRODUCED")

go_Local2World=originalTransform
dofile(newF9)
dofile(newF10)
dofile(newF12)
hitZ=5
assert(Homelander_FreeAimProbe(),"epoch F9 good at z5")
local firstEpoch=HOMELANDER_FREEAIM_VERIFIED_EPOCH
eq(HOMELANDER_FREEAIM_EPOCH,firstEpoch,"F9 attempt/verified epoch")
local nestedAgain=false
go_Local2World=function(h,v)
 if not nestedAgain then
  nestedAgain=true
  hitZ=6
  assert(Homelander_FreeAimProbe(),"newer epoch F9 in F10 getter")
 end
 return originalTransform(h,v)
end
assert(not Homelander_FreeAimLocalOffsetProbe(),"epoch F10 refuses old hit even same A and NPC")
eq(HOMELANDER_FREEAIM_F10_EPOCH,nil,"old F10 never publishes epoch")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET,nil,"old F10 never publishes offset")
eq(HOMELANDER_FREEAIM_EPOCH,firstEpoch+1,"nested F9 advances unique attempt")
eq(HOMELANDER_FREEAIM_VERIFIED_EPOCH,firstEpoch+1,"nested F9 keeps newest proof")
eq(HOMELANDER_FREEAIM_HIT_POS.z,6,"nested current target z6 retained")
print("P1_F10_F9_REENTRANCY_FAILCLOSED_PASS")
go_Local2World=originalTransform
assert(Homelander_FreeAimLocalOffsetProbe(),"fresh F10 accepts newest F9")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET.z,6,"fresh offset z6")
eq(HOMELANDER_FREEAIM_F10_EPOCH,HOMELANDER_FREEAIM_VERIFIED_EPOCH,"F10 bound to exact F9 attempt")
assert(Homelander_EyeOriginProbeV006(),"fresh same-player F11")
local submits=0
ai_Laser=function() submits=submits+1 end
assert(Homelander_DualEyeFreeAimRenderProbe(),"F12 accepts same-epoch F9/F10")
eq(submits,2,"two mocked eyes on positive epoch")

-- A fresh F10 invalidates a prior successful F12 receipt even for the same hit.
assert(Homelander_FreeAimLocalOffsetProbe(),"repeated F10 valid")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,false,"new F10 resets prior F12 success")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_TARGET,nil,"new F10 resets prior rendered target")
assert(Homelander_DualEyeFreeAimRenderProbe(),"new F12 after fresh F10")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,true,"new F12 sets fresh success")
local camera=HL_GetCameraFrame
HL_GetCameraFrame=function() return "broken" end
assert(not Homelander_FreeAimProbe(),"new failed F9 refuses malformed frame")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,false,"new F9 attempt clears earlier rendered success")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_TARGET,nil,"failed F9 clears earlier render target")
HL_GetCameraFrame=camera
assert(Homelander_FreeAimProbe(),"rebuild F9 proof after failed new attempt")
assert(Homelander_FreeAimLocalOffsetProbe(),"rebuild F10 proof")
assert(Homelander_EyeOriginProbeV006(),"rebuild F11 proof")
assert(Homelander_DualEyeFreeAimRenderProbe(),"rebuild F12 proof")
print("P1_F9_F10_INVALIDATE_OLD_F12_RECEIPT_PASS")

-- Prevent forged stale same-player/target proof if F9 generation changes.
local saved_epoch=HOMELANDER_FREEAIM_EPOCH
HOMELANDER_FREEAIM_EPOCH=saved_epoch+1
submits=0
assert(not Homelander_DualEyeFreeAimRenderProbe(),"F12 refuses mismatched F9 generation")
eq(submits,0,"no laser after changed generation")
HOMELANDER_FREEAIM_EPOCH=saved_epoch

-- Nested F9 from LOS callbacks must not permit an older F9 to overwrite newer proof.
hitZ=8
local priorLos=fre_LineOfSightTest
local inside=false
fre_LineOfSightTest=function(start,finish,ignore,player)
 if not inside then
  inside=true
  hitZ=9
  assert(Homelander_FreeAimProbe(),"nested F9 in earlier F9 LOS")
  return true,0.5,Vector(0,0,8),Vector(0,1,0)
 end
 return priorLos(start,finish,ignore,player)
end
assert(not Homelander_FreeAimProbe(),"older F9 returns false after nested newer LOS")
eq(HOMELANDER_FREEAIM_HIT_POS.z,9,"newest F9 hit retained, not overwritten")
eq(HOMELANDER_FREEAIM_VERIFIED_EPOCH,HOMELANDER_FREEAIM_EPOCH,"newest F9 epoch kept")
fre_LineOfSightTest=priorLos
assert(Homelander_FreeAimLocalOffsetProbe(),"F10 accepts retained newest F9 z9")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET.z,9,"newest offset z9")
print("P1_F9_NESTED_LOS_SUPERSEDED_ATTEMPT_PASS")

-- A validity callback can also dispatch a later F9 with another target:
-- the outer attempt must NOT overwrite the newer target after that callback.
local originalValid=go_IsValid
local originalLastGOH=HL_LastRayHitGOH
local targetName="NPC"
local triggerNPC=false
go_IsValid=function(h)
 if h=="NPC" and triggerNPC then
  triggerNPC=false
  hitZ=11
  targetName="NPC2"
  assert(Homelander_FreeAimProbe(),"new F9 from target go_IsValid")
 end
 return h=="NPC2" or originalValid(h)
end
HL_LastRayHitGOH=function() return targetName end
targetName="NPC";hitZ=10;triggerNPC=true
assert(not Homelander_FreeAimProbe(),"old F9 must abort on nested target-validity F9")
eq(HOMELANDER_FREEAIM_HIT,"NPC2","new NPC2 GOH not overwritten by old NPC")
eq(HOMELANDER_FREEAIM_HIT_POS.z,11,"new NPC2 hit point not overwritten")
eq(HOMELANDER_FREEAIM_VERIFIED_EPOCH,HOMELANDER_FREEAIM_EPOCH,"new NPC2 proof remains current")
print("P1_F9_TARGET_VALIDITY_CALLBACK_REENTRANCY_PASS")

-- Diagnostics may also call a synchronous Lua callback via HL_Log.
local originalLog=HL_Log
local triggerCameraLog=false
HL_Log=function(msg)
 if triggerCameraLog and type(msg)=="string" and string.find(msg,"CAMERA |",1,true) then
  triggerCameraLog=false
  hitZ=13
  targetName="NPC2"
  assert(Homelander_FreeAimProbe(),"new F9 inside old F9 CAMERA log")
 end
 return originalLog(msg)
end
targetName="NPC";hitZ=12;triggerCameraLog=true
assert(not Homelander_FreeAimProbe(),"old F9 aborts when camera log nests new F9")
eq(HOMELANDER_FREEAIM_HIT,"NPC2","new log-callback NPC2 GOH retained")
eq(HOMELANDER_FREEAIM_HIT_POS.z,13,"new log-callback hit point retained")
eq(HOMELANDER_FREEAIM_VERIFIED_EPOCH,HOMELANDER_FREEAIM_EPOCH,"new log-callback proof current")
HL_Log=originalLog
go_IsValid=originalValid
HL_LastRayHitGOH=originalLastGOH
print("P1_F9_CAMERA_LOG_CALLBACK_REENTRANCY_PASS")
print("P1_F9_F12_EPOCH_PROVENANCE_INTEGRATION_PASS")
