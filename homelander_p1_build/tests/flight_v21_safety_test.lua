-- Flight V2.1 safety regression harness (Lua 5.1). Offline engine stubs only.
-- Does not launch Prototype, mutate a real game handle, or establish live proof.
local function assert_equal(got, wanted, tag)
    assert(got == wanted, tag .. ": expected " .. tostring(wanted) .. ", got " .. tostring(got))
end

local mt={}
mt.__index=mt
function mt.__add(a,b) return Vector(a.x+b.x,a.y+b.y,a.z+b.z) end
function mt.__sub(a,b) return Vector(a.x-b.x,a.y-b.y,a.z-b.z) end
function mt.__mul(a,b)
    if type(a)=="number" then a,b=b,a end
    return Vector(a.x*b,a.y*b,a.z*b)
end
function mt:magnitude() return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z) end
function mt:dot(v) return self.x*v.x+self.y*v.y+self.z*v.z end
function mt:cross(v)
    local x,y,z=self.y*v.z-self.z*v.y,self.z*v.x-self.x*v.z,self.x*v.y-self.y*v.x
    self.x,self.y,self.z=x,y,z
end
function mt:normalize()
    local n=self:magnitude()
    if n>0 then self.x,self.y,self.z=self.x/n,self.y/n,self.z/n end
    return n
end
function Vector(x,y,z)
    if type(x)=="table" then return setmetatable({x=x.x,y=x.y,z=x.z},mt) end
    return setmetatable({x=x or 0,y=y or 0,z=z or 0},mt)
end

local writes,valid,velocity=0,true,Vector(0,0,0)
HL_Log=function() end
HOMELANDER_PLAYER="player-1"
HOMELANDER_SETTER_ECHO_PASSED=true
go_IsValid=function(h) return valid and (h=="player-1" or h=="player-2") end
online_DeterminePlayerIndex=function(h) return h=="player-1" and 0 or (h=="player-2" and 1 or -1) end
go_GetPosition=function() return Vector(0,0,0) end
go_Local2World=function(_,v) return v end
ai_GetPhysicsVelocity=function() return velocity end
phys_SetLinearVelocity=function(h,v)
    assert_equal(h,"player-1","velocity write target")
    assert(v:magnitude()==v:magnitude(),"velocity write must be finite")
    writes=writes+1
end
time_GetSimulationDelta=function() return 0.016 end
-- Synthetic F5 mirrors the canonical two-level public/core call graph.
-- The independent V2.3 suite executes the REAL canonical v003 F5 source.
Homelander_SetterEchoProbe=function(handle)
    if handle==nil then HOMELANDER_SETTER_ECHO_PASSED=false;return false end
    HOMELANDER_SETTER_ECHO_PASSED=true
    return true
end
Homelander_SetterEchoProbe_Verified=function()
    return Homelander_SetterEchoProbe(HOMELANDER_PLAYER)
end

dofile("homelander_p1_build/lua_p1/flight_controller_v2_STAGED.lua")
assert(not Homelander_FlightEnableVerifiedV2(),"unbound preexisting F5 boolean rejected")
assert(Homelander_SetterEchoProbe_Verified(),"initial F5 echo bound to player-1")
assert_equal(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,"player-1","F5 bound identity")

-- Normal F6/F7 sequence: one active-tick submit plus one authorized restore.
assert(Homelander_FlightEnableVerifiedV2(),"valid flight enable")
assert(Homelander_FlightTickV2(1,0,0,false),"valid flight tick")
assert_equal(writes,1,"active submit count")
assert(Homelander_FlightDisableV2(true),"valid flight disable")
assert_equal(writes,2,"authorized F7 restore")

-- Player switch: never write saved velocity to an obsolete handle.
assert(Homelander_FlightEnableVerifiedV2(),"enable before player switch")
HOMELANDER_PLAYER="player-2"
Homelander_FlightDisableV2(true)
assert_equal(writes,2,"stale-player restore suppression")
HOMELANDER_PLAYER="player-1"

-- A second valid player must not inherit F5 proof from the first player.
HOMELANDER_PLAYER="player-2"
assert(not Homelander_FlightEnableVerifiedV2(),"new valid player cannot reuse stale F5 boolean")
assert(Homelander_SetterEchoProbe_Verified(),"fresh F5 echo on player-2")
assert_equal(HOMELANDER_FLIGHT_V22_ECHO_PLAYER,"player-2","new F5 bound identity")
assert(Homelander_FlightEnableVerifiedV2(),"new player allowed only after own verified F5")
Homelander_FlightDisableV2(false)
HOMELANDER_PLAYER="player-1"
assert(not Homelander_FlightEnableVerifiedV2(),"old player cannot reuse another player F5")
assert(Homelander_SetterEchoProbe_Verified(),"fresh F5 rebind to original player")

-- Invalid player: F7 restore must not call a physics setter.
assert(Homelander_FlightEnableVerifiedV2(),"enable before invalidation")
valid=false
Homelander_FlightDisableV2(true)
assert_equal(writes,2,"invalid-player restore suppression")
valid=true

-- Revoked F5 proof: F7 restore must not write.
assert(Homelander_FlightEnableVerifiedV2(),"enable before revoked setter proof")
HOMELANDER_SETTER_ECHO_PASSED=false
Homelander_FlightDisableV2(true)
assert_equal(writes,2,"revoked-setter restore suppression")
HOMELANDER_SETTER_ECHO_PASSED=true

-- Focus-loss disable must never write a replacement velocity.
assert(Homelander_FlightEnableVerifiedV2(),"enable before focus loss")
Homelander_FlightForceDisableV2()
assert_equal(writes,2,"focus-loss restore suppression")

-- A non-finite input is neutralized before it reaches velocity computation.
assert(Homelander_FlightEnableVerifiedV2(),"enable before non-finite input")
local nan=0/0
assert(Homelander_FlightTickV2(nan,0,0,false),"non-finite input neutralized")
assert_equal(writes,3,"non-finite input produces only normal tick submit")
Homelander_FlightDisableV2(false)

-- Non-finite physical velocity must disable the controller without writing.
velocity=Vector(nan,0,0)
assert(not Homelander_FlightEnableVerifiedV2(),"non-finite preflight velocity rejected")
velocity=Vector(0,0,0)
assert(Homelander_FlightEnableVerifiedV2(),"valid enable before velocity corruption")
velocity=Vector(nan,0,0)
assert(not Homelander_FlightTickV2(1,0,0,false),"non-finite current velocity rejected")
assert_equal(writes,3,"non-finite current velocity causes no write")
Homelander_FlightDisableV2(true)
assert_equal(writes,3,"disabled controller causes no stale restore")

dofile("homelander_p1_build/lua_p1/flight_ground_probe_v018_STAGED.lua")
HOMELANDER_FLIGHT_GROUND_START_UP=nan
HOMELANDER_FLIGHT_GROUND_RAY_DOWN=math.huge
fre_LineOfSightTest=function(start,finish,ignore,player)
    assert(start.y==start.y and finish.y==finish.y,"ground ray must be finite")
    assert_equal(start.y,1,"NaN ground start fallback")
    assert_equal(finish.y,-8,"Inf ground length fallback")
    assert_equal(player,"player-1","ground ray player identity")
    return false
end
assert(Homelander_FlightGroundProbeV018(),"non-finite ground configuration safely defaulted")
assert_equal(HOMELANDER_FLIGHT_GROUND_PROBE_VALID,true,"ground miss is valid telemetry")

fre_LineOfSightTest=function() return true,0.5,nil,Vector(0,1,0) end
assert(not Homelander_FlightGroundProbeV018(),"malformed hit fails closed")
assert_equal(HOMELANDER_FLIGHT_GROUND_PROBE_VALID,false,"malformed ground telemetry invalidated")
print("FLIGHT_V22_F5_BINDING_TEST_PASS: exact-player F5 proof, authorized restore, stale/invalid/revoked suppression, focus loss, non-finite inputs/velocity/config, malformed hit")
