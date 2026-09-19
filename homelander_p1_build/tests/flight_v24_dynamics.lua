-- Flight V2.4 offline dynamics and native held-key bridge regression.
-- Actual flight_controller_v2_STAGED.lua + actual v003 setter echo; only engine is mocked.
local function eq(a,b,name) assert(a==b,name.." expected "..tostring(b).." got "..tostring(a)) end
local function near(a,b,name) assert(math.abs(a-b)<0.00001,name.." expected "..tostring(b).." got "..tostring(a)) end
local V={} V.__index=V
function Vector(x,y,z)
 if type(x)=="table" then return setmetatable({x=x.x,y=x.y,z=x.z},V) end
 return setmetatable({x=x or 0,y=y or 0,z=z or 0},V)
end
function V.__add(a,b) return Vector(a.x+b.x,a.y+b.y,a.z+b.z) end
function V.__sub(a,b) return Vector(a.x-b.x,a.y-b.y,a.z-b.z) end
function V.__mul(a,b) if type(a)=="number" then a,b=b,a end return Vector(a.x*b,a.y*b,a.z*b) end
function V:magnitude() return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z) end
function V:dot(b) return self.x*b.x+self.y*b.y+self.z*b.z end
function V:cross(b)
 local x,y,z=self.y*b.z-self.z*b.y,self.z*b.x-self.x*b.z,self.x*b.y-self.y*b.x
 self.x,self.y,self.z=x,y,z
end
function V:normalize()
 local n=self:magnitude()
 if n>0 then self.x,self.y,self.z=self.x/n,self.y/n,self.z/n end
 return n
end
local vel=Vector(0,0,0)
local writes=0
local delta=0.016
HL_Log=function() end
HOMELANDER_PLAYER="A"
PLAYER="A"
go_IsValid=function(h) return h=="A" end
online_DeterminePlayerIndex=function(h) return h=="A" and 0 or -1 end
go_GetPosition=function() return Vector(0,0,0) end
go_Local2World=function(_,v) return Vector(v) end
ai_GetPhysicsVelocity=function() return Vector(vel) end
phys_SetLinearVelocity=function(h,v,selector)
 eq(h,"A","setter current player")
 eq(selector,0,"setter selector")
 vel=Vector(v) writes=writes+1
end
time_GetSimulationDelta=function() return delta end

-- Initial camera frame: render camera at z=-5 and its three measured axes.
local cameraFrame="0,0,-5,1,0,0,0,1,0,0,0,1"
cm_GetCurrentRenderCameraPosition=function() return Vector(0,0,-5) end
HL_GetCameraFrame=function() return cameraFrame end

dofile("homelander_p1_build/v003_transfer/lua_p1/setter_echo_probe.lua")
dofile("homelander_p1_build/lua_p1/flight_controller_v2_STAGED.lua")
assert(Homelander_SetterEchoProbe_Verified(),"real canonical F5 setter echo")
eq(writes,1,"one F5 setter echo before flight")
assert(Homelander_FlightEnableVerifiedV2(),"enable after real F5")

local function keys(set)
 for _,k in ipairs({"W","S","A","D","SPACE","C","CTRL","SHIFT"}) do
  _G["HL_KEY_"..k]=set[k] and "1" or "0"
 end
end
local function tick(set)
 keys(set)
 local n=writes
 assert(Homelander_FlightNativeTickV2(),"native held input tick")
 eq(writes,n+1,"exactly one physics setter each active tick")
end

-- 55 units/s2 x 0.016 s from rest. Measured camera forward is +z.
tick({W=true})
near(vel.x,0,"W x")
near(vel.y,0,"W y")
near(vel.z,0.88,"W accel")
tick({})
near(vel.z,0,"released W air-brakes to rest")

-- Right axis must be +x for measured +z forward.
tick({D=true})
near(vel.x,0.88,"D right x")
near(vel.z,0,"D z")
tick({})
near(vel.x,0,"released D air brake")

tick({SPACE=true})
near(vel.y,0.96,"Space vertical accel")
tick({})
near(vel.y,0,"Space release hover brake")
tick({CTRL=true})
near(vel.y,-0.96,"CTRL descent accel")
tick({})
near(vel.y,0,"CTRL release hover brake")
tick({C=true})
near(vel.y,-0.96,"C alternate descent")
tick({})
near(vel.y,0,"C release hover brake")
tick({SPACE=true,CTRL=true})
near(vel.y,0,"opposed vertical inputs cancel")

tick({W=true,SHIFT=true})
near(vel.z,1.44,"boost acceleration 90 units/s2")
tick({S=true,SHIFT=true})
near(vel.z,0,"opposite boost brakes within one step")
tick({W=true,S=true})
near(vel.z,0,"opposed forward inputs cancel")
tick({A=true,D=true})
near(vel.x,0,"opposed lateral inputs cancel")

-- dt=0 does not write or advance flight, dt cap prevents huge velocity leaps.
delta=0
local before=writes
keys({W=true})
assert(Homelander_FlightNativeTickV2(),"zero dt harmless")
eq(writes,before,"zero dt does not submit")
delta=0.20
tick({W=true})
near(vel.z,2.75,"dt integration cap 0.05")
tick({})
near(vel.z,0,"dt cap air brake 4.0")
delta=0.016

-- Change measured camera forward to +x (camera at x=-5), W moves +x.
cameraFrame="-5,0,0,1,0,0,0,1,0,0,0,1"
cm_GetCurrentRenderCameraPosition=function() return Vector(-5,0,0) end
tick({W=true})
near(vel.x,0.88,"camera x measured forward")
near(vel.z,0,"camera x no z drift")
tick({})
near(vel.x,0,"camera measured air brake")

-- Broken measured camera frame and missing legacy camera position: player local fallback.
cameraFrame="broken"
cm_GetCurrentRenderCameraPosition=nil
cm_GetCurrentCameraPosition=nil
cm_GetCurrentInGameCameraPosition=nil
tick({W=true})
near(vel.z,0.88,"fallback player-local forward")
tick({})
near(vel.z,0,"fallback player-local air brake")

-- Continuous flight with lost focus disables without an extra setter.
tick({W=true})
before=writes
assert(Homelander_FlightForceDisableV2(),"focus-loss disables enabled flight")
eq(writes,before,"no velocity rewrite on focus loss")
eq(HOMELANDER_FLIGHT_V2_ENABLED,false,"flight disabled")
keys({W=true})
assert(not Homelander_FlightNativeTickV2(),"post-focus no active tick")
eq(writes,before,"post-focus no setter")

-- Neither enabled flight nor an invalid dt can submit velocity.
assert(Homelander_FlightEnableVerifiedV2(),"re-enable after focus loss with valid bound proof")
delta=0.26
before=writes
keys({W=true})
assert(not Homelander_FlightNativeTickV2(),"invalid dt disables")
eq(writes,before,"invalid dt no setter")
eq(HOMELANDER_FLIGHT_V2_ENABLED,false,"invalid dt fails closed")
assert(not Homelander_FlightNativeTickV2(),"failed controller remains off")
eq(writes,before,"no repeated setter after failed tick")
print("FLIGHT_V24_DYNAMICS_PASS: measured camera W/D, fallback, acceleration, air braking, hover/ascent/descent, boost, held-key conflicts, dt clamp, focus-loss, invalid dt")
