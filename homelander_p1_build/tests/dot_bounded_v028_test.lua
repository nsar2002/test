-- Offline Lua 5.1 bounded heat-vision trial test. Mocked engine, NO Prototype process.
local function eq(a,b,label) assert(a==b,label..": got "..tostring(a).." expected "..tostring(b)) end
local mt={} mt.__index=mt
function Vector(x,y,z)
 if type(x)=="table" then return setmetatable({x=x.x,y=x.y,z=x.z},mt) end
 return setmetatable({x=x or 0,y=y or 0,z=z or 0},mt)
end
function mt.__add(a,b) return Vector(a.x+b.x,a.y+b.y,a.z+b.z) end
function mt.__sub(a,b) return Vector(a.x-b.x,a.y-b.y,a.z-b.z) end
function mt.__mul(a,b) if type(a)=="number" then a,b=b,a end return Vector(a.x*b,a.y*b,a.z*b) end
function mt:magnitude() return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z) end
function mt:dot(v) return self.x*v.x+self.y*v.y+self.z*v.z end
function mt:normalize()
 local n=self:magnitude()
 if n>0 then self.x,self.y,self.z=self.x/n,self.y/n,self.z/n end
 return n
end
local targetHealth=10.0
local damageCalls=0
local dt=0.05
local hit=true
local hitTarget="NPC"
local playerSwitch=false
HL_Log=function() end
HOMELANDER_PLAYER="A"
go_IsValid=function(h) return h=="A" or h=="B" or h=="NPC" end
online_DeterminePlayerIndex=function(h) return h=="A" and 0 or (h=="B" and 1 or -1) end
go_GetHealth=function(h)
 eq(h,"NPC","read target health")
 if playerSwitch then HOMELANDER_PLAYER="B" end
 return targetHealth
end
go_GetMaxHealth=function(h) eq(h,"NPC","read target max health");return 100 end
go_ApplyDamage=function(h,amount)
 eq(h,"NPC","damage remains pinned to original NPC")
 assert(amount>0 and amount<=0.1,"bounded damage amount")
 damageCalls=damageCalls+1
 assert(damageCalls<=3,"bounded damage quota")
 targetHealth=targetHealth-amount
end
time_GetSimulationDelta=function() return dt end
cm_GetCurrentRenderCameraPosition=function() return Vector(0,0,-5) end
HL_GetCameraFrame=function() return "0,0,-5,1,0,0,0,1,0,0,0,1" end
HL_LastRayHitGOH=function() return hitTarget end
go_GetPosition=function(h) eq(h,"A","player position");return Vector(0,0,0) end
fre_LineOfSightTest=function(start,finish,ignore,player)
 eq(player,"A","LOS ignored original player")
 return hit,0.5,hit and Vector(0,0,5) or nil,Vector(0,1,0)
end
local function proof()
 HOMELANDER_TARGET_CONTINUITY_PASSED=true
 HOMELANDER_IMPACT_VFX_SUBMITTED=true
 HOMELANDER_DOT_DRYRUN_PASSED=true
 HOMELANDER_TARGET_CONTINUITY_TARGET="NPC"
 HOMELANDER_DAMAGE_LAST_TARGET="NPC"
 HOMELANDER_DOT_DRYRUN_TARGET="NPC"
 HOMELANDER_DOT_DRYRUN_INTERVAL=0.10
 HOMELANDER_DOT_DRYRUN_SECONDS=3.20
 HOMELANDER_DOT_DRYRUN_EVENTS=31
 HOMELANDER_DOT_DRYRUN_MIN_GAP=0.10
end
dofile("homelander_p1_build/lua_p1/dot_bounded_damage_v028_DORMANT.lua")
eq(damageCalls,0,"no loading side effects")
eq(HOMELANDER_DOT_BOUNDED_ACTIVE,false,"disabled on load")
assert(not Homelander_DOTBoundedToggleV028(),"missing upstream evidence refuses enable")
proof()
HOMELANDER_DOT_DRYRUN_MIN_GAP=0.01
assert(not Homelander_DOTBoundedToggleV028(),"insufficient scheduler spacing refuses enable")
proof()
HOMELANDER_DOT_DRYRUN_TARGET="A"
assert(not Homelander_DOTBoundedToggleV028(),"player cannot be dryrun damage target")
proof()
assert(Homelander_DOTBoundedToggleV028(),"valid bounded manual enable")
eq(damageCalls,0,"enabling does not apply damage")
dt=0/0
assert(not Homelander_DOTBoundedTickV028(),"NaN simulation delta disables")
eq(damageCalls,0,"NaN delta cannot damage")
eq(HOMELANDER_DOT_DRYRUN_PASSED,false,"abort consumes old F20 proof")
proof()
dt=0.1;hit=false
assert(Homelander_DOTBoundedToggleV028(),"new proof enables for LOS-miss test")
assert(not Homelander_DOTBoundedTickV028(),"LOS miss disables without damage")
eq(damageCalls,0,"LOS miss zero damage")
proof();hit=true
assert(Homelander_DOTBoundedToggleV028(),"fresh proof enables for mid-callback switch")
playerSwitch=true
assert(not Homelander_DOTBoundedTickV028(),"player switch during health callback disables")
eq(damageCalls,0,"player switch zero damage")
playerSwitch=false;HOMELANDER_PLAYER="A"
proof()
assert(Homelander_DOTBoundedToggleV028(),"fresh proof enables final limited trial")
dt=0.05
assert(Homelander_DOTBoundedTickV028(),"first half cadence tick")
eq(damageCalls,0,"no damage before 0.1 simulation seconds")
assert(Homelander_DOTBoundedTickV028(),"second half cadence tick")
eq(damageCalls,1,"one event after 0.1 seconds")
eq(HOMELANDER_DOT_BOUNDED_LAST_EVENTS,1,"first event budget consumed")
-- A 0.25-second accepted frame is allowed only ONE damage submission.
dt=0.25
assert(Homelander_DOTBoundedTickV028(),"accepted long frame")
eq(damageCalls,2,"no catch-up burst on long frame")
dt=0.1
assert(Homelander_DOTBoundedTickV028(),"final bounded event tick")
eq(damageCalls,3,"exactly three maximum damage events")
eq(HOMELANDER_DOT_BOUNDED_ACTIVE,false,"auto-stop after third event")
eq(HOMELANDER_DOT_DRYRUN_PASSED,false,"completion consumes F20 proof")
proof()
assert(not Homelander_DOTBoundedToggleV028(),"cannot restart same Lua-state trial")
HOMELANDER_DOT_BOUNDED_LAST_EVENTS=0
assert(not Homelander_DOTBoundedToggleV028(),"manually resetting public telemetry cannot reset local quota")
eq(damageCalls,3,"total damage calls remain capped")
print("P1_DOT_BOUNDED_V028_PASS: no boot damage, F20/provenance guard, LOS/mid-callback fail-closed, 0.1s cadence, no burst, 3x0.1 cap, token consumption")
