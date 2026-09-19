-- Test only the actual staged read-only Lua and mock engine callbacks.
local reads,writes=0,0
local valid=true
local sample=false
local swap=false
local err=false
local index=0
HOMELANDER_PLAYER="player-A"
HL_Log=function() end
go_IsValid=function(h) return valid and h=="player-A" end
online_DeterminePlayerIndex=function(h) return h=="player-A" and index or -1 end
go_IsGrabbed=function(h)
 assert(h=="player-A","read current verified player only")
 reads=reads+1
 if err then error("read failure") end
 if swap then HOMELANDER_PLAYER="player-B" end
 return sample
end
for _,name in ipairs({"go_GetGrabbedObject","go_GetGrabSlot","go_AttachObjectToGrabSlot","go_GrabbedDetach",
 "go_SetHealth","go_ApplyDamage","phys_SetLinearVelocity"}) do
 _G[name]=function() writes=writes+1;error("forbidden call: "..name) end
end

dofile("homelander_p1_build/lua_p1/grab_state_v01_DORMANT.lua")
assert(reads==0 and writes==0,"loading a dormant probe must not touch engine")
local function cleared()
 assert(HOMELANDER_GRAB_STATE_VALID==false and HOMELANDER_GRAB_STATE_VALUE==nil
  and HOMELANDER_GRAB_STATE_PLAYER==nil,"failed sample clears stale data")
end
assert(Homelander_GrabStateProbeV01(),"valid false raw boolean accepted")
assert(HOMELANDER_GRAB_STATE_VALID and HOMELANDER_GRAB_STATE_VALUE==false
 and HOMELANDER_GRAB_STATE_PLAYER=="player-A")
sample=true
assert(Homelander_GrabStateProbeV01(),"valid true raw boolean accepted")
assert(HOMELANDER_GRAB_STATE_VALUE==true,"raw getter boolean preserved")
valid=false
assert(not Homelander_GrabStateProbeV01(),"invalid player refused");cleared()
valid=true
index=-1
assert(not Homelander_GrabStateProbeV01(),"invalid player index refused");cleared()
index=0
err=true
assert(not Homelander_GrabStateProbeV01(),"read error fails closed");cleared()
err=false
swap=true
assert(not Homelander_GrabStateProbeV01(),"callback player swap fails closed");cleared()
swap=false;HOMELANDER_PLAYER="player-A"
go_IsGrabbed=function() return 1 end
assert(not Homelander_GrabStateProbeV01(),"non-boolean return fails closed");cleared()
go_IsGrabbed=nil
assert(not Homelander_GrabStateProbeV01(),"missing getter fails closed");cleared()
go_IsValid=nil;online_DeterminePlayerIndex=nil
assert(not Homelander_GrabStateProbeV01(),"no validation route fails closed");cleared()
assert(writes==0,"no guessed two-argument getters, attach/detach or physics/health writes")
print("P1_GRAB_V01_READ_ONLY_PASS: actual script, valid false/true, stale clearing, handle-switch/error, zero object/slot/mutation calls")
