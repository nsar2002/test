-- Offline integration test: execute the unmodified canonical v003 F5 Lua source.
-- Only engine APIs and handles are mocked. No Prototype process is launched.
local function check(x, label) assert(x, label) end
local function eq(a,b,label) assert(a==b,label..": expected "..tostring(b).." got "..tostring(a)) end
local Vec={}
Vec.__index=Vec
function Vector(x,y,z)
    if type(x)=="table" then return setmetatable({x=x.x,y=x.y,z=x.z},Vec) end
    return setmetatable({x=x or 0,y=y or 0,z=z or 0},Vec)
end
function Vec.__add(a,b) return Vector(a.x+b.x,a.y+b.y,a.z+b.z) end
function Vec.__sub(a,b) return Vector(a.x-b.x,a.y-b.y,a.z-b.z) end
function Vec.__mul(a,b)
    if type(a)=="number" then a,b=b,a end
    return Vector(a.x*b,a.y*b,a.z*b)
end
function Vec:magnitude() return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z) end
function Vec:dot(b) return self.x*b.x+self.y*b.y+self.z*b.z end
function Vec:cross(b)
    local x,y,z=self.y*b.z-self.z*b.y,self.z*b.x-self.x*b.z,self.x*b.y-self.y*b.x
    self.x,self.y,self.z=x,y,z
end
function Vec:normalize()
    local n=self:magnitude()
    if n>0 then self.x,self.y,self.z=self.x/n,self.y/n,self.z/n end
    return n
end

local valid={A=true,B=true}
local velocities={A=Vector(0,0,0),B=Vector(0,0,0)}
local calls,mode=0,"normal"
HL_Log=function() end
PLAYER="A"
HOMELANDER_PLAYER="A"
HOMELANDER_SETTER_ECHO_PASSED=false
go_IsValid=function(h) return valid[h]==true end
online_DeterminePlayerIndex=function(h) return h=="A" and 0 or (h=="B" and 1 or -1) end
go_GetPosition=function(h) check(valid[h],"invalid position GOH");return Vector(0,0,0) end
go_Local2World=function(_,v) return Vector(v) end
ai_GetPhysicsVelocity=function(h) check(valid[h],"invalid velocity GOH");return Vector(velocities[h]) end
phys_SetLinearVelocity=function(h,v,selector)
    check(valid[h],"setter on invalid GOH")
    eq(selector,0,"canonical selector")
    calls=calls+1
    if mode=="raise" then error("mock setter exception") end
    velocities[h]=Vector(v)
    if mode=="drift" then velocities[h]=velocities[h]+Vector(1,0,0) end
    if mode=="switch" then HOMELANDER_PLAYER="B" end
end
time_GetSimulationDelta=function() return 0.016 end

-- This is the actual v003 verified/core/_PLAYER implementation, not a fake F5.
dofile("homelander_p1_build/v003_transfer/lua_p1/setter_echo_probe.lua")
local canonicalCore=Homelander_SetterEchoProbe
local canonicalVerified=Homelander_SetterEchoProbe_Verified
local canonicalPlayer=Homelander_SetterEchoProbe_PLAYER
check(type(canonicalCore)=="function" and type(canonicalVerified)=="function" and
      type(canonicalPlayer)=="function","canonical v003 F5 functions present")
dofile("homelander_p1_build/lua_p1/flight_controller_v2_STAGED.lua")

-- A stale externally assigned boolean has no handle-specific provenance.
HOMELANDER_SETTER_ECHO_PASSED=true
check(not Homelander_FlightEnableVerifiedV2(),"unbound true token must not enable flight")
HOMELANDER_SETTER_ECHO_PASSED=false

-- The real canonical F5 performs one same-vector setter echo on player A.
local before=calls
check(Homelander_SetterEchoProbe_Verified(),"real canonical F5 should pass for A")
eq(calls,before+1,"one real F5 echo")
eq(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,"A","F5 bound to A")
check(Homelander_FlightEnableVerifiedV2(),"A flight after own F5")
Homelander_FlightDisableV2(false)

-- The canonical public _PLAYER route targets PLAYER=B while verified player is A.
-- Its echo must invalidate A's binding even though the boolean becomes true.
PLAYER="B"
before=calls
check(Homelander_SetterEchoProbe_PLAYER(),"real alternate _PLAYER echo succeeds for B")
eq(calls,before+1,"alternate setter echo count")
eq(HOMELANDER_SETTER_ECHO_PASSED,true,"alternate echo sets global boolean")
eq(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,nil,"alternate entrypoint invalidates A binding")
check(not Homelander_FlightEnableVerifiedV2(),"A cannot inherit B echo after alternate entrypoint")
PLAYER="A"

-- Reacquisition requires a fresh, valid canonical F5.
check(Homelander_SetterEchoProbe_Verified(),"real verified F5 rebinds A")
check(Homelander_FlightEnableVerifiedV2(),"rebound A may fly")
Homelander_FlightDisableV2(false)

-- Any failed core echo clears both boolean and bound identity.
mode="raise"
check(not Homelander_SetterEchoProbe_Verified(),"original setter exception must fail F5")
eq(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,nil,"failed echo binding cleared")
eq(HOMELANDER_SETTER_ECHO_PASSED,false,"failed echo token cleared")
check(not Homelander_FlightEnableVerifiedV2(),"failed echo cannot enable")
mode="drift"
check(not Homelander_SetterEchoProbe_Verified(),"canonical delta mismatch must fail")
eq(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,nil,"drift mismatch clears bound handle")
mode="normal"
velocities.A=Vector(0,0,0)

-- Real setter path may change player during its callback; do not bind the old GOH.
mode="switch"
check(not Homelander_SetterEchoProbe_Verified(),"player switch during real echo must fail")
eq(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,nil,"mid-F5 switch never bound")
mode="normal"
HOMELANDER_PLAYER="A"

-- A separate verified F5 is required on a distinct, valid B player.
HOMELANDER_PLAYER="B"
check(Homelander_SetterEchoProbe_Verified(),"real F5 may bind B")
eq(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,"B","real F5 B binding")
HOMELANDER_PLAYER="A"
check(not Homelander_FlightEnableVerifiedV2(),"real B F5 not reusable by A")
check(Homelander_SetterEchoProbe_Verified(),"rebind A after B")
check(Homelander_FlightEnableVerifiedV2(),"A active before alternate echo")
PLAYER="B"
check(Homelander_SetterEchoProbe_PLAYER(),"alternate B echo while A flying")
before=calls
check(not Homelander_FlightTickV2(0,0,0,false),"active flight fails closed on lost provenance")
eq(calls,before,"lost provenance creates no flight tick write")
Homelander_FlightDisableV2(true)
eq(calls,before,"lost provenance creates no F7 restore")
PLAYER="A"

-- Replacing either wrapped F5 entrypoint invalidates the runtime provenance.
check(Homelander_SetterEchoProbe_Verified(),"fresh A F5 before replacement")
local wrappedCore=Homelander_SetterEchoProbe
local wrappedVerified=Homelander_SetterEchoProbe_Verified
Homelander_SetterEchoProbe=canonicalCore
check(not Homelander_FlightEnableVerifiedV2(),"replaced core refuses old proof")
Homelander_SetterEchoProbe=wrappedCore
Homelander_SetterEchoProbe_Verified=canonicalVerified
check(not Homelander_FlightEnableVerifiedV2(),"replaced verified refuses old proof")
Homelander_SetterEchoProbe_Verified=wrappedVerified

print("FLIGHT_V23_REAL_F5_INTEGRATION_PASS: canonical v003 verified/core/_PLAYER, alternate-route invalidation, fail-closed errors, player switching, disabled tick/restore, replaced entrypoints")
