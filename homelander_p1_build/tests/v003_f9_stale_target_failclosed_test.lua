-- Offline Lua 5.1 regression: actual immutable v003 F9 source vs isolated safe F9.
-- Actual F10 follows both versions. All engine functions here are MOCKS.
local function eq(a,b,m) assert(a==b,m..": expected "..tostring(b).." got "..tostring(a)) end
local V={} V.__index=V
function Vector(x,y,z)
 if type(x)=="table" then return setmetatable({x=x.x,y=x.y,z=x.z},V) end
 return setmetatable({x=x or 0,y=y or 0,z=z or 0},V)
end
function V.__add(a,b) return Vector(a.x+b.x,a.y+b.y,a.z+b.z) end
function V.__sub(a,b) return Vector(a.x-b.x,a.y-b.y,a.z-b.z) end
function V.__mul(a,b) if type(a)=="number" then a,b=b,a end return Vector(a.x*b,a.y*b,a.z*b) end
function V:magnitude() return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z) end
function V:dot(v) return self.x*v.x+self.y*v.y+self.z*v.z end
function V:normalize()
 local n=self:magnitude()
 if n>0 then self.x,self.y,self.z=self.x/n,self.y/n,self.z/n end
 return n
end
local logs={}
HL_Log=function(msg) logs[#logs+1]=tostring(msg) end
local defaultFrame="0,0,-5,1,0,0,0,1,0,0,0,1"
local frame=defaultFrame
local hit=true
local candidate="NPC"
local switchAt=nil
local mutators=0
HOMELANDER_PLAYER="A"
go_IsValid=function(h) return h=="A" or h=="B" or h=="NPC" end
go_GetPosition=function(h) eq(h,"A","current player position");return Vector(0,0,0) end
cm_GetCurrentRenderCameraPosition=function() return Vector(0,0,-5) end
HL_GetCameraFrame=function() return frame end
HL_LastRayHitGOH=function()
 if switchAt=="goh" then HOMELANDER_PLAYER="B" end
 return candidate
end
go_GetDebugName=function(h)
 if switchAt=="debug" then HOMELANDER_PLAYER="B" end
 return tostring(h)
end
local transformFault=nil
go_Local2World=function(h,v)
 eq(h,"NPC","target local offset must use original NPC")
 if transformFault=="error" then error("mock target transform getter failed") end
 if transformFault=="switch" then HOMELANDER_PLAYER="B" end
 return Vector(v)
end
fre_LineOfSightTest=function(start,finish,ignore,player)
 eq(player,"A","LOS ignores original A")
 if switchAt=="los" then HOMELANDER_PLAYER="B" end
 return hit,0.5,hit and Vector(0,0,5) or nil,Vector(0,1,0)
end
for _,name in ipairs({"go_ApplyDamage","go_ApplyDamageAndHit","go_SetHealth",
 "phys_SetLinearVelocity","go_Teleport","em_AddWorldEffect"}) do
 _G[name]=function() mutators=mutators+1;error("forbidden gameplay mutation: "..name) end
end
dofile("homelander_p1_build/v003_transfer/lua_p1/freeaim_probe_v004_STAGED.lua")
dofile("homelander_p1_build/lua_p1/freeaim_local_offset_probe_v005_STAGED.lua")
assert(Homelander_FreeAimProbe(),"original F9 valid NPC")
eq(HOMELANDER_FREEAIM_HIT,"NPC","original valid F9 GOH")
assert(Homelander_FreeAimLocalOffsetProbe(),"original F10 gets valid prior F9")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,"NPC","original F10 verified GOH")
frame="broken"
assert(not Homelander_FreeAimProbe(),"original F9 refuses invalid frame")
eq(HOMELANDER_FREEAIM_HIT,"NPC","original F9 FAIL retains stale prior GOH")
assert(Homelander_FreeAimLocalOffsetProbe(),"original F10 wrongly reuses stale prior F9 target")
print("P1_V003_ORIGINAL_STALE_GOAL_REPRODUCED: failed later F9 retains earlier NPC and F10 accepts that prior hit")

-- Load only the NEW separate staged source. Original v003 file remains unchanged.
dofile("homelander_p1_build/lua_p1/freeaim_probe_v004_failclosed_DORMANT.lua")
eq(HOMELANDER_FREEAIM_HIT,"NPC","loading a dormant script has no gameplay mutation or clearing")
HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET="SENTINEL"
assert(not Homelander_FreeAimProbe(),"guarded F9 rejects invalid frame")
eq(HOMELANDER_FREEAIM_HIT,nil,"guarded F9 clears stale GOH on early abort")
eq(HOMELANDER_FREEAIM_HIT_POS,nil,"guarded F9 clears stale position")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET,nil,"guarded F9 clears F10 output on new attempt")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,nil,"guarded F9 clears stale F10 GOH")
assert(not Homelander_FreeAimLocalOffsetProbe(),"guarded F10 refuses after failed later F9")
print("P1_V003_F9_EARLY_ABORT_STALE_TARGET_CLEARED_PASS")

frame=defaultFrame
assert(Homelander_FreeAimProbe(),"guarded F9 preserves valid NPC hit")
eq(HOMELANDER_FREEAIM_HIT,"NPC","guarded positive F9 target")
assert(Homelander_FreeAimLocalOffsetProbe(),"guarded F10 preserves valid target-local roundtrip")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,"NPC","guarded positive F10 target")

switchAt="los"
assert(not Homelander_FreeAimProbe(),"guarded F9 refuses player switch during LOS callback")
eq(HOMELANDER_FREEAIM_HIT,nil,"LOS switch clears target")
assert(not Homelander_FreeAimLocalOffsetProbe(),"F10 fails after LOS player switch")
HOMELANDER_PLAYER="A";switchAt=nil
assert(Homelander_FreeAimProbe(),"guarded F9 still works after previous aborted switch")
switchAt="goh"
assert(not Homelander_FreeAimProbe(),"guarded F9 refuses player switch during last-hit callback")
eq(HOMELANDER_FREEAIM_HIT,nil,"last-hit switch clears target")
eq(HOMELANDER_FREEAIM_HIT_POS,nil,"last-hit switch clears world hitpoint")
eq(HOMELANDER_FREEAIM_VERIFIED_PLAYER,nil,"last-hit switch clears originating F9 player")
HOMELANDER_PLAYER="A";switchAt=nil
switchAt="debug"
assert(not Homelander_FreeAimProbe(),"guarded F9 rejects switch from optional hit debug-name getter")
eq(HOMELANDER_FREEAIM_HIT,nil,"debug getter switch clears target")
eq(HOMELANDER_FREEAIM_VERIFIED_PLAYER,nil,"debug getter switch clears proof token")
HOMELANDER_PLAYER="A";switchAt=nil

-- A legitimate F9 MISS must never leave an earlier target or F10 offset behind.
assert(Homelander_FreeAimProbe(),"fresh positive F9")
assert(Homelander_FreeAimLocalOffsetProbe(),"fresh positive F10")
hit=false
assert(Homelander_FreeAimProbe(),"normal F9 miss is not an exception")
eq(HOMELANDER_FREEAIM_HIT,nil,"miss clears old NPC")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET,nil,"miss clears old local offset")
assert(not Homelander_FreeAimLocalOffsetProbe(),"F10 refuses after F9 miss")
-- ORIGINAL F10 itself retains a previously verified offset after a later transform error.
hit=true
frame=defaultFrame
HOMELANDER_PLAYER="A"
assert(Homelander_FreeAimProbe(),"fresh guarded F9 before F10 transform regression")
assert(Homelander_FreeAimLocalOffsetProbe(),"original F10 positive before error")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,"NPC","original F10 prior GOH")
transformFault="error"
assert(not Homelander_FreeAimLocalOffsetProbe(),"original F10 returns false on transform exception")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,"NPC","original F10 FAIL retains stale local-offset GOH")
print("P1_V004_ORIGINAL_F10_STALE_OFFSET_REPRODUCED: later failed F10 retains earlier NPC transform proof")

-- Only the isolated staged F10 entrypoint clears its previous published offset.
dofile("homelander_p1_build/lua_p1/freeaim_local_offset_probe_v005_failclosed_DORMANT.lua")
assert(not Homelander_FreeAimLocalOffsetProbe(),"guarded F10 returns false on transform exception")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET,nil,"guarded failed F10 must clear prior offset")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,nil,"guarded failed F10 must clear prior GOH")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR,nil,"guarded failed F10 must clear prior roundtrip proof")
transformFault=nil
assert(Homelander_FreeAimProbe(),"guarded F9 still works after failed F10")
assert(Homelander_FreeAimLocalOffsetProbe(),"guarded F10 still accepts valid transform")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,"NPC","guarded F10 positive target")
eq(HOMELANDER_FREEAIM_VERIFIED_PLAYER,"A","guarded F9 GOH has exact originating player token")
HOMELANDER_PLAYER="B"
assert(not Homelander_FreeAimLocalOffsetProbe(),"guarded F10 refuses NPC proof from other player despite same GOH")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,nil,"cross-player F10 clears earlier offset")
HOMELANDER_PLAYER="A"
assert(Homelander_FreeAimProbe(),"fresh F9 after B->A player return")
assert(Homelander_FreeAimLocalOffsetProbe(),"fresh same-player F10 passes after new F9")

-- A native transform getter can switch current player while F10 is running.
transformFault="switch"
assert(not Homelander_FreeAimLocalOffsetProbe(),"guarded F10 rejects player switch in transform callbacks")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET,nil,"guarded F10 player switch cannot publish offset")
eq(HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH,nil,"guarded F10 player switch cannot publish GOH")
HOMELANDER_PLAYER="A";transformFault=nil
eq(mutators,0,"F9/F10 test must not call damage/physics/world setters")
print("P1_V003_F9_F10_FAILCLOSED_PASS: original F9/F10 stale states reproduced, both staged guards prevent reuse; positive hits work, no setters")
