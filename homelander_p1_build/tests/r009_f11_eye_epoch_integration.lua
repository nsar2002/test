-- Real-source F11 same-player nested callback regression and F12 cross-call eye epoch.
-- All engine calls mocked. No Prototype process, no effects on a real game.
dofile("homelander_p1_build/tests/f9_numeric_epoch_integration.lua")
local function eq(a,b,m)
 assert(a==b,(m or "equal")..": "..tostring(a).." != "..tostring(b))
end
HOMELANDER_PLAYER="A"
assert(Homelander_FreeAimProbe(),"fresh F9 before F11 regression")
assert(Homelander_FreeAimLocalOffsetProbe(),"fresh F10 before F11 regression")
local oldF11="homelander_p1_build/lua_p1/eye_origin_probe_v006_failclosed_DORMANT.lua"
local newF11="homelander_p1_build/lua_p1/eye_origin_probe_v006_epoch_DORMANT.lua"
local newF12="homelander_p1_build/lua_p1/dual_eye_freeaim_render_v007_f11_epoch_DORMANT.lua"
local mode="normal"
local nested=false
local jointCalls=0
go_GetJointPosition=function(h,joint)
 eq(h,"A","eye joint subject")
 eq(joint,"EYEPOINT","eye joint type")
 jointCalls=jointCalls+1
 if mode=="nested_f11" and not nested then
  nested=true
  assert(Homelander_EyeOriginProbeV006(),"newer nested F11 same player")
  return Vector(1,1,0) -- old callback resumes AFTER newer F11 has published x2
 end
 return Vector(2,1,0)
end

-- Prior F11 guard only checked same player and accepted an older callback.
dofile(oldF11)
mode="nested_f11";nested=false
assert(Homelander_EyeOriginProbeV006(),"prior F11 mistakenly accepts stale outer eye")
eq(HOMELANDER_EYE_ORIGIN.x,1,"old F11 overwrites nested eye position x2 with older x1")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED,true,"old F11 publishes stale proof")
print("P1_PREVIOUS_F11_SAME_PLAYER_NESTED_STALE_EYE_REPRODUCED")

-- New F11 preserves the newer eye proof and returns false for old callback.
dofile(newF11)
mode="nested_f11";nested=false
local first=HOMELANDER_EYE_ORIGIN_EPOCH
assert(not Homelander_EyeOriginProbeV006(),"new F11 rejects stale outer callback")
eq(HOMELANDER_EYE_ORIGIN.x,2,"newer nested F11 eye remains current")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED,true,"valid nested F11 proof is preserved")
eq(HOMELANDER_EYE_ORIGIN_EPOCH,first+2,"both eye generations advanced")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED_EPOCH,HOMELANDER_EYE_ORIGIN_EPOCH,"published proof current")
print("P1_F11_SAME_PLAYER_NESTED_EYE_FAILCLOSED_PASS")

mode="normal"
assert(Homelander_EyeOriginProbeV006(),"fresh latest F11")
dofile(newF12)
local lasers=0
ai_Laser=function(player,source,source_offset,target,joint,offset)
 lasers=lasers+1
 eq(player,"A","laser source")
 eq(target,"NPC","laser target")
 if mode=="nested_after_left" and lasers==1 then
  assert(Homelander_EyeOriginProbeV006(),"new eye measurement after left laser")
 end
 return nil
end
mode="nested_after_left";lasers=0
local prior=HOMELANDER_EYE_ORIGIN_VERIFIED_EPOCH
assert(not Homelander_DualEyeFreeAimRenderProbe(),"F12 rejects newer eye generation after first laser")
eq(lasers,1,"F12 never submits right-eye laser after changed eye proof")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED_EPOCH,prior+1,"newer F11 proof exists")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,false,"partial eye effect never claims dual success")
print("P1_F12_NEW_F11_GENERATION_AFTER_LEFT_PREVENTS_RIGHT_PASS")

-- A successful clean full F9->F12 operation retains both F9 & F11 proof.
HOMELANDER_PLAYER="A"
assert(Homelander_FreeAimProbe(),"fresh F9 positive")
assert(Homelander_FreeAimLocalOffsetProbe(),"fresh F10 positive")
mode="normal"
assert(Homelander_EyeOriginProbeV006(),"fresh F11 eye epoch")
lasers=0
assert(Homelander_DualEyeFreeAimRenderProbe(),"new F12 clean two-eye mock")
eq(lasers,2,"exactly two mocked laser submissions")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,true,"clean F12 publishes success")
print("P1_F9_F12_F11_EYE_EPOCH_INTEGRATION_PASS")

-- A failed newer F11 invalidates its own F11 proof and previous F12 receipt.
go_GetJointPosition=function() error("synthetic missing eye joint") end
assert(not Homelander_EyeOriginProbeV006(),"failed later F11 does not preserve old proof")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED,false,"failed F11 clears eye")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED_EPOCH,nil,"failed F11 clears epoch")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,false,"failed F11 invalidates previous render receipt")
lasers=0
assert(not Homelander_DualEyeFreeAimRenderProbe(),"F12 blocks unproven newer F11")
eq(lasers,0,"F12 never calls engine after failed F11")
print("P1_F11_FAILED_NEW_ATTEMPT_CLEARS_F12_RECEIPT_PASS")
