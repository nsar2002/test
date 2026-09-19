-- R010 real-source F10 same-F9, same-player nested attempt bug and full provenance.
-- No Prototype process. Reuses full previous R009/F9-F12 actual-source mocks.
dofile("homelander_p1_build/tests/r009_f11_eye_epoch_integration.lua")
local function eq(a,b,msg) assert(a==b,(msg or "equal")..": "..tostring(a).." != "..tostring(b)) end
local repo="homelander_p1_build/lua_p1/"
local priorF10=repo.."freeaim_local_offset_probe_v005_epoch_DORMANT.lua"
local newestF10=repo.."freeaim_local_offset_probe_v005_attempt_DORMANT.lua"
local newestF9=repo.."freeaim_probe_v004_numeric_f10attempt_DORMANT.lua"
local newestF12=repo.."dual_eye_freeaim_render_v007_f10_f11_epoch_DORMANT.lua"
local previousLog=HL_Log
local previousTransform=go_Local2World
local shift=0
local armed=false
local nested=false
go_Local2World=function(h,local_pos)
 eq(h,"NPC","target transform identity")
 return Vector(local_pos.x,local_pos.y,local_pos.z+shift)
end
HL_Log=function(msg)
 if armed and not nested and type(msg)=="string" and string.find(msg,"ROUNDTRIP |",1,true) then
  nested=true
  shift=1
  assert(Homelander_FreeAimLocalOffsetProbe(),"newer nested F10 for identical F9 and target")
 end
 return previousLog(msg)
end
HOMELANDER_PLAYER="A"
dofile(newestF9)
dofile(priorF10)
assert(Homelander_FreeAimProbe(),"fresh F9 at world z5")
shift=0;armed=true;nested=false
assert(Homelander_FreeAimLocalOffsetProbe(),"previous F10 overwrites newer nested offset")
eq(nested,true,"old F10 nested during ROUNDTRIP log")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET.z,5,"prior F10 wrongly replaced newer z4 offset with stale z5")
eq(HOMELANDER_FREEAIM_F10_EPOCH,HOMELANDER_FREEAIM_VERIFIED_EPOCH,"old F10 F9 epoch alone does not detect nested F10")
print("P1_PREVIOUS_F10_SAME_F9_REENTRANT_STALE_OFFSET_REPRODUCED")

dofile(newestF10)
shift=0;armed=false
assert(Homelander_FreeAimProbe(),"fresh numeric F9 after previous test")
shift=0;armed=true;nested=false
local priorAttempt=HOMELANDER_FREEAIM_F10_ATTEMPT or 0
assert(not Homelander_FreeAimLocalOffsetProbe(),"new F10 outer must reject nested newer offset")
eq(HOMELANDER_FREEAIM_F10_ATTEMPT,priorAttempt+2,"nested F10 increments its own attempt")
eq(HOMELANDER_FREEAIM_F10_VERIFIED_ATTEMPT,HOMELANDER_FREEAIM_F10_ATTEMPT,"newer nested F10 publishes its own attempt")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET.z,4,"newest F10 z4 persists despite old callback")
print("P1_R010_F10_SAME_F9_NESTED_STALE_OFFSET_FAILCLOSED_PASS")

armed=false
assert(Homelander_FreeAimLocalOffsetProbe(),"fresh latest F10 revalidates same F9")
dofile(newestF12)
go_GetJointPosition=function(player,joint)
 eq(player,"A","eye joint player")
 eq(joint,"EYEPOINT","joint")
 return Vector(0,1,0)
end
assert(Homelander_EyeOriginProbeV006(),"fresh current F11 eye")
local lasers=0
ai_Laser=function() lasers=lasers+1 end
assert(Homelander_DualEyeFreeAimRenderProbe(),"clean full R010 F9-F12 two-eye mock")
eq(lasers,2,"two mock eye callbacks after fresh F10 attempt")
print("P1_R010_F9_F10_F11_F12_FULL_CHAIN_PASS")

-- F12 guard must reject a newer attempted F10 even if the offset object,
-- target, F9 generation and player identity are unchanged.
local currentOffset=HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET
local lastF10=HOMELANDER_FREEAIM_F10_ATTEMPT
HOMELANDER_FREEAIM_F10_ATTEMPT=lastF10+1
lasers=0
assert(not Homelander_DualEyeFreeAimRenderProbe(),"F12 rejects newer F10 generation")
eq(lasers,0,"no eye submission with stale F10 generation")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET,currentOffset,"only generation changed")
HOMELANDER_FREEAIM_F10_ATTEMPT=lastF10
print("P1_R010_F12_EXACT_F10_ATTEMPT_PROVENANCE_PASS")

assert(Homelander_FreeAimProbe(),"next F9 clears downstream offset")
eq(HOMELANDER_FREEAIM_F10_VERIFIED_ATTEMPT,nil,"new F9 clears F10 attempt provenance")
assert(not Homelander_DualEyeFreeAimRenderProbe(),"F12 refuses old F10 after new F9")
print("P1_R010_NEW_F9_CLEARS_F10_ATTEMPT_AND_F12_PASS")
HL_Log=previousLog
go_Local2World=previousTransform
