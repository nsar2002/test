-- Actual F9/F10/F11/F12 source numerical regression under Lua 5.1 mocks.
-- Baseline suite verifies stale/identity safety and sets a positive same-player proof.
dofile("homelander_p1_build/tests/f11_f12_provenance_integration.lua")
local function eq(a,b,m) assert(a==b,(m or "eq")..": "..tostring(a).." ~= "..tostring(b)) end
local base=go_Local2World
local function corrupt_basis(kind)
 go_Local2World=function(h,v)
  if v.x==1 and v.y==0 and v.z==0 then
   return Vector(kind=="nan" and (0/0) or math.huge,0,0)
  end
  return base(h,v)
 end
end
local f10_original="homelander_p1_build/lua_p1/freeaim_local_offset_probe_v005_STAGED.lua"
local f10_finite="homelander_p1_build/lua_p1/freeaim_local_offset_probe_v005_finite_DORMANT.lua"
local f12_original="homelander_p1_build/lua_p1/dual_eye_freeaim_render_v007_STAGED.lua"
local f12_guard="homelander_p1_build/lua_p1/dual_eye_freeaim_render_v007_failclosed_DORMANT.lua"
HOMELANDER_PLAYER="A"
HOMELANDER_EYE_HALF_SEPARATION=nil
assert(Homelander_FreeAimProbe(),"fresh F9")
corrupt_basis("nan")
dofile(f10_original)
local original_ok=Homelander_FreeAimLocalOffsetProbe()
assert(original_ok,"source regression: original F10 incorrectly accepts NaN basis/offset")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,"NPC","original NaN target proof")
local bad_err=HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR
assert(type(bad_err)=="number" and bad_err~=bad_err,"original F10 publishes NaN error")
print("P1_ORIGINAL_F10_NAN_OFFSET_PROOF_REPRODUCED")
-- Original F12 checks only type(number) of the F10 error, not finiteness.
go_GetJointPosition=function(p,j)
 eq(p,"A","original F12 origin");eq(j,"EYEPOINT","eye joint")
 return Vector(0,1,0)
end
HOMELANDER_EYE_ORIGIN_VERIFIED=true
HOMELANDER_EYE_ORIGIN_NAME="EYEPOINT"
HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER="A"
local submits=0
ai_Laser=function() submits=submits+1;return nil end
dofile(f12_original)
assert(Homelander_DualEyeFreeAimRenderProbe(),"original F12 submits laser with nonfinite F10 proof")
eq(submits,2,"original F12 two submissions with NaN target offset")
print("P1_ORIGINAL_F12_ACCEPTS_NAN_F10_PROOF_REPRODUCED")
-- New F10 rejects and clears the bad proof before publishing anything.
dofile(f10_finite)
assert(not Homelander_FreeAimLocalOffsetProbe(),"finite F10 rejects NaN transform")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET,nil,"finite F10 invalidates offset")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,nil,"finite F10 invalidates target")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR,nil,"finite F10 invalidates error")
dofile(f12_guard)
submits=0
assert(not Homelander_DualEyeFreeAimRenderProbe(),"guarded F12 refuses failed F10")
eq(submits,0,"zero rendered eyes for failed F10")
-- Nonfinite (+Inf) basis must also be rejected, not just NaN.
corrupt_basis("inf")
assert(not Homelander_FreeAimLocalOffsetProbe(),"finite F10 rejects Inf transform")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,nil,"Inf cannot publish target")
-- Valid fresh transform still passes complete F9/F10/F11/F12 chain.
go_Local2World=base
assert(Homelander_FreeAimProbe(),"new F9 current A")
assert(Homelander_FreeAimLocalOffsetProbe(),"finite F10 accepts valid orthogonal transform")
assert(Homelander_EyeOriginProbeV006(),"guarded F11 accepts current A eye")
submits=0
assert(Homelander_DualEyeFreeAimRenderProbe(),"guarded F12 accepts valid current proof")
eq(submits,2,"two valid guarded eyes")
eq(HOMELANDER_DUAL_EYE_RENDER_LAST_OK,true,"valid receipt")
print("P1_F10_FINITE_TO_F12_SAME_PLAYER_INTEGRATION_PASS")
