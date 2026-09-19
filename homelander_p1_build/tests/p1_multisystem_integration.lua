-- Combined staged Homelander P1 module integration, Lua 5.1 engine mock.
-- Uses actual unmodified canonical v003 F5, Flight V2.4, durability v0.2 and grab v0.1.
-- This is NOT an in-game test or a runtime installation recipe.
local function expect(x,m) assert(x,m) end
local function equal(x,y,m) assert(x==y,m..": expected "..tostring(y).." got "..tostring(x)) end
local Vec={} Vec.__index=Vec
function Vector(x,y,z)
 if type(x)=="table" then return setmetatable({x=x.x,y=x.y,z=x.z},Vec) end
 return setmetatable({x=x or 0,y=y or 0,z=z or 0},Vec)
end
function Vec.__add(a,b) return Vector(a.x+b.x,a.y+b.y,a.z+b.z) end
function Vec.__sub(a,b) return Vector(a.x-b.x,a.y-b.y,a.z-b.z) end
function Vec.__mul(a,b) if type(a)=="number" then a,b=b,a end return Vector(a.x*b,a.y*b,a.z*b) end
function Vec:magnitude() return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z) end
function Vec:dot(v) return self.x*v.x+self.y*v.y+self.z*v.z end
function Vec:cross(v)
 local x,y,z=self.y*v.z-self.z*v.y,self.z*v.x-self.x*v.z,self.x*v.y-self.y*v.x
 self.x,self.y,self.z=x,y,z
end
function Vec:normalize()
 local n=self:magnitude()
 if n>0 then self.x,self.y,self.z=self.x/n,self.y/n,self.z/n end
 return n
end

local velocities={A=Vector(0,0,0),B=Vector(0,0,0)}
local health={A=70,B=95}
local grabbed={A=false,B=true}
local mutationCount,healthReads,grabReads=0,0,0
local healthError=false
local grabError=false
HL_Log=function() end
HOMELANDER_PLAYER="A"
PLAYER="A"
go_IsValid=function(h) return h=="A" or h=="B" end
online_DeterminePlayerIndex=function(h) return h=="A" and 0 or (h=="B" and 1 or -1) end
go_GetPosition=function(h) expect(velocities[h]~=nil,"position only for valid GOH");return Vector(0,0,0) end
go_Local2World=function(_,v) return Vector(v) end
ai_GetPhysicsVelocity=function(h) return Vector(velocities[h]) end
phys_SetLinearVelocity=function(h,v,selector)
 expect(velocities[h]~=nil,"setter target is valid")
 equal(selector,0,"setter selector")
 velocities[h]=Vector(v)
 mutationCount=mutationCount+1
end
time_GetSimulationDelta=function() return 0.016 end
go_GetHealth=function(h)
 healthReads=healthReads+1
 if healthError then error("read failed") end
 return health[h]
end
go_GetMaxHealth=function() healthReads=healthReads+1;return 100 end
go_GetDamageScale=function() healthReads=healthReads+1;return 0.2 end
go_IsGrabbed=function(h)
 grabReads=grabReads+1
 if grabError then error("grab read failed") end
 return grabbed[h]
end
for _,name in ipairs({"go_SetHealth","go_SetMaxHealth","go_SetDamageScale",
 "go_GetGrabbedObject","go_GetGrabSlot","go_AttachObjectToGrabSlot","go_GrabbedDetach",
 "go_ApplyDamage","go_ApplyDamageAndHit","em_AddWorldEffect"}) do
 _G[name]=function() error("forbidden multisystem probe API "..name) end
end

dofile("homelander_p1_build/v003_transfer/lua_p1/setter_echo_probe.lua")
dofile("homelander_p1_build/lua_p1/flight_controller_v2_STAGED.lua")
dofile("homelander_p1_build/lua_p1/durability_snapshot_v02_DORMANT.lua")
dofile("homelander_p1_build/lua_p1/grab_state_v01_DORMANT.lua")
equal(mutationCount,0,"zero setter calls during module loading")
equal(healthReads,0,"zero durability reads during module loading")
equal(grabReads,0,"zero grab reads during module loading")
expect(HOMELANDER_FLIGHT_V2_ENABLED==false,"flight disabled on load")
expect(HOMELANDER_DURABILITY_SNAPSHOT_VALID==false,"durability not sampled on load")
expect(HOMELANDER_GRAB_STATE_VALID==false,"grab not sampled on load")

-- Gameplay mutation is limited to explicit canonical F5 echo and flight tick.
expect(Homelander_SetterEchoProbe_Verified(),"canonical F5 verifies A")
equal(mutationCount,1,"one canonical F5 echo")
expect(Homelander_FlightEnableVerifiedV2(),"A enables flight")
expect(Homelander_FlightTickV2(1,0,0,false),"A flight tick")
equal(mutationCount,2,"one active Flight setter")
local before=mutationCount
expect(Homelander_DurabilitySnapshotV02(),"durability sample A")
expect(Homelander_GrabStateProbeV01(),"raw grab bool A")
equal(mutationCount,before,"read-only observers cannot change flight velocity")
equal(HOMELANDER_DURABILITY_SNAPSHOT.player,"A","A durability provenance")
equal(HOMELANDER_DURABILITY_SNAPSHOT.health,70,"A health")
equal(HOMELANDER_GRAB_STATE_VALUE,false,"A grab raw false")
equal(HOMELANDER_GRAB_STATE_PLAYER,"A","A grab provenance")

-- Player replacement: observers rebind only to freshly verified current player;
-- active Flight must refuse further mutation with A's stale F5 proof.
HOMELANDER_PLAYER="B"
expect(not Homelander_FlightTickV2(1,0,0,false),"flight stops after player replacement")
equal(mutationCount,before,"no flight setter on replaced handle")
expect(Homelander_DurabilitySnapshotV02(),"fresh B durability sample")
expect(Homelander_GrabStateProbeV01(),"fresh B grab sample")
equal(HOMELANDER_DURABILITY_SNAPSHOT.player,"B","B durability provenance")
equal(HOMELANDER_DURABILITY_SNAPSHOT.health,95,"B health")
equal(HOMELANDER_GRAB_STATE_VALUE,true,"B grab raw true")
equal(HOMELANDER_GRAB_STATE_PLAYER,"B","B grab provenance")
equal(mutationCount,before,"B read-only samples did not mutate")
expect(not Homelander_FlightEnableVerifiedV2(),"B cannot reuse A F5 proof")

-- Errors must each invalidate only their own observation, not forge F5 approval.
healthError=true
expect(not Homelander_DurabilitySnapshotV02(),"health failure invalidates snapshot")
equal(HOMELANDER_DURABILITY_SNAPSHOT_VALID,false,"health snapshot invalid")
equal(HOMELANDER_DURABILITY_SNAPSHOT,nil,"no stale health snapshot")
expect(HOMELANDER_GRAB_STATE_VALID,"grab sample remains independent")
healthError=false
grabError=true
expect(not Homelander_GrabStateProbeV01(),"grab failure invalidates sample")
equal(HOMELANDER_GRAB_STATE_VALID,false,"grab snapshot invalid")
equal(HOMELANDER_GRAB_STATE_VALUE,nil,"no stale grab bool")
grabError=false
equal(mutationCount,before,"observation errors cannot mutate")

-- Explicit fresh canonical F5 B authorizes only B flight. Observers remain read-only.
PLAYER="B"
expect(Homelander_SetterEchoProbe_Verified(),"fresh B F5")
equal(mutationCount,before+1,"only F5 echo writes")
expect(Homelander_FlightEnableVerifiedV2(),"B flight after own F5")
before=mutationCount
expect(Homelander_DurabilitySnapshotV02(),"B health sampling while flight active")
expect(Homelander_GrabStateProbeV01(),"B grab sampling while flight active")
equal(mutationCount,before,"no cross-system extra velocity submissions")
expect(Homelander_FlightForceDisableV2(),"B focus-loss disables")
equal(mutationCount,before,"focus loss does not rewrite velocity")
print("P1_MULTISYSTEM_INTEGRATION_PASS: actual canonical F5 + Flight V2.4 + durability V0.2 + grab V0.1, zero autoload mutation, read-only isolation, A/B identity and fail-closed state")
