-- Flight V2.5 exact-player safety across callbacks; actual controller + original v003 F5.
-- Engine APIs are deterministic Lua 5.1 mocks. No Prototype executable is launched.
local function eq(a,b,m) assert(a==b,m..": expected "..tostring(b).." got "..tostring(a)) end
local V={} V.__index=V
local magnitudeHook=false
function Vector(x,y,z)
 if type(x)=="table" then return setmetatable({x=x.x,y=x.y,z=x.z},V) end
 return setmetatable({x=x or 0,y=y or 0,z=z or 0},V)
end
function V.__add(a,b) return Vector(a.x+b.x,a.y+b.y,a.z+b.z) end
function V.__sub(a,b) return Vector(a.x-b.x,a.y-b.y,a.z-b.z) end
function V.__mul(a,b) if type(a)=="number" then a,b=b,a end return Vector(a.x*b,a.y*b,a.z*b) end
function V:magnitude()
 if magnitudeHook then magnitudeHook=false;HOMELANDER_PLAYER="B" end
 return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z)
end
function V:dot(v) return self.x*v.x+self.y*v.y+self.z*v.z end
function V:cross(v)
 local x,y,z=self.y*v.z-self.z*v.y,self.z*v.x-self.x*v.z,self.x*v.y-self.y*v.x
 self.x,self.y,self.z=x,y,z
end
function V:normalize()
 local n=self:magnitude()
 if n>0 then self.x,self.y,self.z=self.x/n,self.y/n,self.z/n end
 return n
end
local velocity,writes=Vector(0,0,0),0
local indexValue=0
local callback=nil
local callbackEnabled=false
local validityCalls,validitySwitchAt=0,nil
HL_Log=function() end
HOMELANDER_PLAYER="A"
PLAYER="A"
go_IsValid=function(h)
 validityCalls=validityCalls+1
 if validitySwitchAt and validityCalls==validitySwitchAt then HOMELANDER_PLAYER="B" end
 return h=="A" or h=="B"
end
online_DeterminePlayerIndex=function(h)
 if h=="A" then return indexValue end
 return h=="B" and 1 or -1
end
go_GetPosition=function() return Vector(0,0,0) end
go_Local2World=function(_,v)
 if callbackEnabled and callback=="basis" then HOMELANDER_PLAYER="B" end
 return Vector(v)
end
ai_GetPhysicsVelocity=function()
 if callbackEnabled and callback=="velocity" then HOMELANDER_PLAYER="B" end
 return Vector(velocity)
end
phys_SetLinearVelocity=function(h,v,selector)
 eq(h,"A","flight/echo writes only intended player A")
 eq(selector,0,"native setter selector")
 writes=writes+1;velocity=Vector(v)
end
time_GetSimulationDelta=function()
 if callbackEnabled and callback=="dt" then HOMELANDER_SETTER_ECHO_PASSED=false end
 return 0.016
end
dofile("homelander_p1_build/v003_transfer/lua_p1/setter_echo_probe.lua")
dofile("homelander_p1_build/lua_p1/flight_controller_v2_STAGED.lua")
local function rebind()
 callback=nil;callbackEnabled=false;validityCalls=0;validitySwitchAt=nil
 HOMELANDER_PLAYER="A";PLAYER="A";indexValue=0
 HOMELANDER_SETTER_ECHO_PASSED=false
 magnitudeHook=false;velocity=Vector(0,0,0)
 Homelander_FlightDisableV2(false)
 assert(Homelander_SetterEchoProbe_Verified(),"fresh original F5 for A")
 eq(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,"A","F5 provenance bound A")
end
local function refusal_proof(m)
 eq(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,nil,m.." must invalidate F5 binding")
 HOMELANDER_PLAYER="A";callbackEnabled=false;validitySwitchAt=nil
 assert(not Homelander_FlightEnableVerifiedV2(),m.." cannot reuse stale F5")
end
local function assert_no_write(fn,m)
 local before=writes
 assert(not fn(),m.." should fail closed")
 eq(writes,before,m.." must not write velocity")
end

-- 1. A non-finite / fractional player discriminator is not a verified index.
for _,idx in ipairs({math.huge,-math.huge,0.5}) do
 rebind()
 indexValue=idx
 assert_no_write(Homelander_FlightEnableVerifiedV2,"invalid player index "..tostring(idx))
 refusal_proof("invalid index")
end
rebind()
indexValue=0/0
assert_no_write(Homelander_FlightEnableVerifiedV2,"NaN player index")
refusal_proof("NaN index")

-- 2. Player can switch during F6's initial velocity read: do not commit session.
rebind()
callback="velocity";callbackEnabled=true
assert_no_write(Homelander_FlightEnableVerifiedV2,"enable velocity callback switch")
eq(HOMELANDER_FLIGHT_V2_ENABLED,false,"enable still disabled")
refusal_proof("enable callback")

-- 3. Player can switch during F6's camera/player basis call.
rebind()
callback="basis";callbackEnabled=true
assert_no_write(Homelander_FlightEnableVerifiedV2,"enable basis callback switch")
refusal_proof("enable camera")

-- 4. Existing flight loses its exact-player proof during read of simulation dt.
rebind()
assert(Homelander_FlightEnableVerifiedV2(),"flight enabled before dt mutation")
callback="dt";callbackEnabled=true
assert_no_write(function() return Homelander_FlightTickV2(1,0,0,false) end,"tick dt revocation")
eq(HOMELANDER_FLIGHT_V2_ENABLED,false,"tick dt revocation disabled")
refusal_proof("tick dt")

-- 5. Player can switch after first tick guard, inside velocity read.
rebind()
assert(Homelander_FlightEnableVerifiedV2(),"flight enabled before velocity mutation")
callback="velocity";callbackEnabled=true
assert_no_write(function() return Homelander_FlightTickV2(1,0,0,false) end,"tick velocity callback")
eq(HOMELANDER_FLIGHT_V2_ENABLED,false,"tick velocity callback disabled")
refusal_proof("tick velocity")

-- 6. Player can switch in camera/player local basis after initial guard.
rebind()
assert(Homelander_FlightEnableVerifiedV2(),"flight enabled before basis mutation")
callback="basis";callbackEnabled=true
assert_no_write(function() return Homelander_FlightTickV2(1,0,0,false) end,"tick basis callback")
eq(HOMELANDER_FLIGHT_V2_ENABLED,false,"tick basis callback disabled")
refusal_proof("tick basis")

-- 7. Even the FINAL validity callback can switch HOMELANDER_PLAYER.
rebind()
assert(Homelander_FlightEnableVerifiedV2(),"flight enabled before validity mutation")
validityCalls=0;validitySwitchAt=2
assert_no_write(function() return Homelander_FlightTickV2(1,0,0,false) end,"final validity callback")
eq(HOMELANDER_FLIGHT_V2_ENABLED,false,"final validity callback disabled")
refusal_proof("final validity")

-- 8. Saved-velocity magnitude callback can change player AFTER first F7 guard.
rebind()
assert(Homelander_FlightEnableVerifiedV2(),"flight enabled before saved velocity callback")
magnitudeHook=true
local n=writes
Homelander_FlightDisableV2(true)
eq(writes,n,"F7 skips restore after saved velocity callback replaced player")
eq(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,nil,"F7 invalidates stale proof")
refusal_proof("F7 magnitude")

-- 9. Unchanged callbacks preserve normal tick and exactly one explicit F7 restore.
rebind()
assert(Homelander_FlightEnableVerifiedV2(),"ordinary enable remains valid")
n=writes
assert(Homelander_FlightTickV2(1,0,0,false),"ordinary active tick")
eq(writes,n+1,"ordinary tick writes once")
Homelander_FlightDisableV2(true)
eq(writes,n+2,"ordinary F7 restores once")
print("FLIGHT_V25_CALLBACK_GUARD_PASS: NaN/Inf/fraction player index, F6/tick/F7 callback switch, F5 invalidation, normal tick and restore")
