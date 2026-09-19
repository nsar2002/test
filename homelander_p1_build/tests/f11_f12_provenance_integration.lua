-- Homelander P1 F9/F10/F11/F12 REAL-SOURCE mock integration (Lua 5.1).
-- No Prototype process; no native game writes. First fixture itself checks original F9/F10 regressions.
dofile("homelander_p1_build/tests/v003_f9_stale_target_failclosed_test.lua")
local function eq(a,b,msg) assert(a==b,(msg or "equal")..": "..tostring(a).." != "..tostring(b)) end
local writes=0
local mode="normal"
local laser_calls={}
go_GetJointPosition=function(player,joint)
 eq(player,"A","joint subject")
 eq(joint,"EYEPOINT","joint name")
 if mode=="eye_error" then error("synthetic eye getter exception") end
 if mode=="eye_switch" then HOMELANDER_PLAYER="B" end
 return Vector(0,1,0)
end
ai_Laser=function(player,source,source_offset,target,joint,local_offset)
 laser_calls[#laser_calls+1]={player=player,target=target,joint=joint}
 eq(player,"A","laser source")
 eq(target,"NPC","laser target")
 eq(joint,"","must use target base-local F10 offset")
 if mode=="laser_switch" and #laser_calls==1 then HOMELANDER_PLAYER="B" end
 if mode=="laser_false" and #laser_calls==1 then return false end
 if mode=="laser_throw" and #laser_calls==2 then error("synthetic right-eye exception") end
 return nil -- original Lua ABI may expose void return
end
local originalF11="homelander_p1_build/lua_p1/eye_origin_probe_v006_STAGED.lua"
local guardedF11="homelander_p1_build/lua_p1/eye_origin_probe_v006_failclosed_DORMANT.lua"
local originalF12="homelander_p1_build/lua_p1/dual_eye_freeaim_render_v007_STAGED.lua"
local guardedF12="homelander_p1_build/lua_p1/dual_eye_freeaim_render_v007_failclosed_DORMANT.lua"
local function refresh()
 HOMELANDER_PLAYER="A"
 mode="normal"
 assert(Homelander_FreeAimProbe(),"paired guarded F9 fresh hit")
 assert(Homelander_FreeAimLocalOffsetProbe(),"paired guarded F10 fresh offset")
 eq(HOMELANDER_FREEAIM_VERIFIED_PLAYER,"A","F9 player provenance")
end
refresh()
dofile(originalF11)
assert(Homelander_EyeOriginProbeV006(),"original F11 first good")
mode="eye_error"
assert(not Homelander_EyeOriginProbeV006(),"original F11 later error")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED,true,"original F11 incorrectly retains old verified proof")
print("P1_ORIGINAL_F11_STALE_SUCCESS_REPRODUCED")
dofile(guardedF11)
assert(not Homelander_EyeOriginProbeV006(),"guarded F11 after error")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED,false,"guarded F11 clears old success")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER,nil,"guarded F11 clears old identity")
refresh()
mode="eye_switch"
assert(not Homelander_EyeOriginProbeV006(),"guarded F11 rejects mid-callback player switch")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED,false,"no proof after switch")
refresh()
assert(Homelander_EyeOriginProbeV006(),"guarded F11 positive current A")
eq(HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER,"A","F11 subject binding")
dofile(originalF12)
laser_calls={}
mode="laser_switch"
assert(Homelander_DualEyeFreeAimRenderProbe(),"original F12 does not guard player switch after left")
eq(#laser_calls,2,"original submits two calls after player changes")
print("P1_ORIGINAL_F12_SECOND_CALL_AFTER_PLAYER_SWITCH_REPRODUCED")
refresh()
assert(Homelander_EyeOriginProbeV006(),"refresh F11 after switch")
dofile(guardedF12)
laser_calls={}
mode="laser_switch"
assert(not Homelander_DualEyeFreeAimRenderProbe(),"guarded F12 denies right after left changes player")
eq(#laser_calls,1,"guarded F12 prevents second laser call")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,false,"one-eye partial cannot be reported success")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_TARGET,nil,"one-eye partial clears target receipt")
refresh()
assert(Homelander_EyeOriginProbeV006(),"refresh F11 after switch guard")
laser_calls={}
HOMELANDER_FREEAIM_VERIFIED_PLAYER=nil
assert(not Homelander_DualEyeFreeAimRenderProbe(),"guarded F12 requires paired guarded F9 provenance")
eq(#laser_calls,0,"no call on unbound F9")
refresh()
assert(Homelander_EyeOriginProbeV006(),"F11 positive for engine-failure tests")
laser_calls={}
mode="laser_false"
assert(not Homelander_DualEyeFreeAimRenderProbe(),"explicit left-eye return false rejected")
eq(#laser_calls,1,"no right eye after explicit false")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,false,"false is not success")
mode="laser_throw";laser_calls={}
assert(not Homelander_DualEyeFreeAimRenderProbe(),"right-eye exception cannot claim both eyes")
eq(#laser_calls,2,"right-eye exception follows exactly two calls")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,false,"right error clears success")
mode="normal";laser_calls={}
assert(Homelander_DualEyeFreeAimRenderProbe(),"two successful render-only calls")
eq(#laser_calls,2,"two eyes submitted on positive mock")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,true,"positive receipt only after both calls")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_TARGET,"NPC","positive target receipt")
HOMELANDER_EYE_HALF_SEPARATION=0/0
laser_calls={}
assert(not Homelander_DualEyeFreeAimRenderProbe(),"nonfinite separation rejected")
eq(#laser_calls,0,"nonfinite separation never calls engine")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,false,"new failed attempt clears older render receipt")
HOMELANDER_EYE_HALF_SEPARATION=nil
-- No mutation calls in this suite: ai_Laser is mocked render API, not damage/physics.
print("P1_F11_F12_GUARDED_PROVENANCE_INTEGRATION_PASS")
