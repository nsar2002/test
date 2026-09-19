-- R018: independently run the actual ASSEMBLED 22-Lua SOURCE payload in the
-- immutable native definition-load order, then call F9->F21 in one mock game.
-- This is NOT an executable/native ABI test and NEVER launches Prototype.
local stage = assert(arg[1],"source-only assembled directory required")
local order = assert(arg[2],"actual native load order filename required")
local V={} V.__index=V
function Vector(x,y,z)
 if type(x)=="table" then return setmetatable({x=x.x,y=x.y,z=x.z},V) end
 return setmetatable({x=x or 0,y=y or 0,z=z or 0},V)
end
function V.__add(a,b) return Vector(a.x+b.x,a.y+b.y,a.z+b.z) end
function V.__sub(a,b) return Vector(a.x-b.x,a.y-b.y,a.z-b.z) end
function V.__mul(a,b)
 if type(a)=="number" then a,b=b,a end
 return Vector(a.x*b,a.y*b,a.z*b)
end
function V:magnitude() return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z) end
function V:dot(v) return self.x*v.x+self.y*v.y+self.z*v.z end
function V:normalize()
 local n=self:magnitude()
 if n>0 then self.x,self.y,self.z=self.x/n,self.y/n,self.z/n end
 return n
end
function V:__tostring() return "("..self.x..","..self.y..","..self.z..")" end
local function eq(a,b,m) assert(a==b,(m or "equal")..": "..tostring(a).." != "..tostring(b)) end
local damage_calls,effect_calls,eye_calls=0,0,0
local shader_queries,native_oneshot,native_held,native_dynamic=0,false,0,0
local laser_one_shot,laser_held,laser_dynamic=0,0,0
local logs={}
HL_Log=function(line) logs[#logs+1]=tostring(line) end
HOMELANDER_PLAYER="A" -- simulated successful F4 identity; NOT proof F4 works in-game
go_IsValid=function(h) return h=="A" or h=="NPC" end
go_GetDebugName=function(h) return tostring(h) end
go_GetPosition=function(h) eq(h,"A","mock player GOH");return Vector(0,0,0) end
go_GetJointPosition=function(h,joint)
 eq(h,"A","mock joint owner")
 eq(joint,"EYEPOINT","mock eye semantic")
 return Vector(0,1,0)
end
go_Local2World=function(h,offset)
 eq(h,"NPC","mock target transform owner")
 return Vector(offset)
end
cm_GetCurrentRenderCameraPosition=function() return Vector(0,0,-5) end
HL_GetCameraFrame=function() return "0,0,-5,1,0,0,0,1,0,0,0,1" end
HL_LastRayHitGOH=function() return "NPC" end
local los_calls=0
fre_LineOfSightTest=function(start,finish,ignore,player)
 eq(player,"A","mock ray owner")
 assert(finish.x==finish.x and finish.y==finish.y and finish.z==finish.z,"no NaN LOS endpoint")
 los_calls=los_calls+1
 return true,0.5,Vector(0,0,5),Vector(0,1,0)
end
ai_Laser=function(player,source,sourceOffset,target,targetJoint,localOffset)
 eq(player,"A","mock eye render source")
 eq(target,"NPC","mock eye render target")
 eq(source,"EYEPOINT","mock eye render joint")
 eye_calls=eye_calls+1
 return nil
end
HL_LaserSightShaderProbe=function()
 shader_queries=shader_queries+1
 return true
end
HL_LaserSightResetHeldGate=function()
 native_held=0
 return true
end
HL_LaserSightHeldStabilityProbe=function() return native_held>=120 end
HL_LaserSightResetDynamicGate=function()
 native_dynamic=0
 return true
end
HL_LaserSightDynamicStabilityProbe=function() return native_dynamic>=120 end
HL_LaserSightSubmitDual=function(...)
 local argv={...}
 eq(argv[1],"A","mock native LaserSight player")
 for i=2,13 do
  assert(type(argv[i])=="number" and argv[i]==argv[i],"invalid mock laser numeric arg "..i)
 end
 local mode=argv[14]
 if mode==nil then
  laser_one_shot=laser_one_shot+1
  native_oneshot=true
 elseif mode==1 then
  assert(native_oneshot,"held native cannot precede one-shot")
  native_held=native_held+1
  laser_held=laser_held+1
 elseif mode==2 then
  assert(native_held>=120,"dynamic native cannot precede held stability")
  native_dynamic=native_dynamic+1
  laser_dynamic=laser_dynamic+1
 else error("unknown native LaserSight test mode: "..tostring(mode)) end
 return true
end
time_GetSimulationDelta=function() return 0.1 end
local health=80
go_GetHealth=function(target) eq(target,"NPC","health target");return health end
go_GetMaxHealth=function(target) eq(target,"NPC","max health target");return 100 end
go_ApplyDamage=function(target,amount)
 eq(target,"NPC","native damage target")
 assert(amount>0 and amount<=1,"mock damage bounded")
 damage_calls=damage_calls+1
 health=health-amount
 return nil -- void native result
end
em_AddWorldEffect=function(effect,pos,scale)
 eq(effect,"missileImpact001","allowlisted native VFX")
 assert(pos~=nil and scale>0 and scale<=0.5,"bounded native VFX arguments")
 effect_calls=effect_calls+1
 return nil
end
local prohibited={"go_ApplyDamageAndHit","go_SetHealth","phys_SetLinearVelocity","phys_SetAngularVelocity","go_Teleport","go_Kill"}
for _,name in ipairs(prohibited) do
 _G[name]=function() error("forbidden game mutation by F9-F21 smoke: "..name) end
end

local file_count,loaded=0,{}
for name in io.lines(order) do
 assert(name:match("^[%w_]+%.lua$"),"unexpected native module path: "..tostring(name))
 assert(not loaded[name],"native module loaded twice: "..name)
 loaded[name]=true
 assert(dofile(stage.."/lua_p1/"..name)==nil or true)
 file_count=file_count+1
end
eq(file_count,22,"actual assembled native module count")
eq(damage_calls,0,"zero autoload damage")
eq(effect_calls,0,"zero autoload VFX")
eq(laser_one_shot,0,"zero autoload laser")
print("P1_R018_ASSEMBLED_22_SCRIPT_NATIVE_ORDER_ZERO_AUTO_MUTATION_PASS")

assert(Homelander_FreeAimProbe(),"F9 assembled fresh camera/LOS target")
assert(Homelander_FreeAimLocalOffsetProbe(),"F10 assembled exact F9 target-local hit")
assert(Homelander_EyeOriginProbeV006(),"F11 assembled eye for current A")
assert(Homelander_DualEyeFreeAimRenderProbe(),"F12 assembled mock two eyes")
eq(eye_calls,2,"F12 two independently submitted mock eye lasers")
assert(Homelander_LaserSightShaderProbeV008(),"F13 shader resolution")
assert(Homelander_LaserSightOneShotV008(),"F14 native one shot")
eq(laser_one_shot,1,"one native F14 mock submit")
assert(Homelander_LaserSightHeldToggleV009(),"F15 enable after F14")
for i=1,120 do assert(Homelander_LaserSightHeldTickV009(),"F15 held mock frame "..i) end
eq(laser_held,120,"120 held native mock submissions")
eq(HOMELANDER_LASERSIGHT_HELD_STABILITY_PASSED,true,"Lua F15 stability proof")
assert(HL_LaserSightHeldStabilityProbe(),"native held mock stability proof")
assert(Homelander_DynamicAimToggleV010(),"F16 enable after F15 proof")
for i=1,120 do assert(Homelander_DynamicAimTickV010(),"F16 dynamic mock frame "..i) end
eq(laser_dynamic,120,"120 dynamic native mock submissions")
eq(HOMELANDER_DYNAMIC_AIM_STABILITY_PASSED,true,"Lua F16 stability proof")
assert(HL_LaserSightDynamicStabilityProbe(),"native F16 mock stability proof")
eq(damage_calls,0,"no damage during F9-F16 stage")
eq(effect_calls,0,"no VFX during F9-F16 stage")
print("P1_R018_ASSEMBLED_F9_F16_CAMERA_EYES_SHADER_HELD_DYNAMIC_CHAIN_PASS")

assert(Homelander_HeatVisionDamageOneShotV011(),"F17 single mock native damage")
eq(damage_calls,1,"only one F17 damage submission")
eq(HOMELANDER_DAMAGE_LAST_PLAYER,"A","F17 owner A")
eq(HOMELANDER_DAMAGE_ONESHOT_RESERVED,true,"F17 native reservation")
assert(not Homelander_HeatVisionDamageOneShotV011(),"F17 replay refused")
eq(damage_calls,1,"F17 replay produced no extra damage")
assert(Homelander_ImpactVFXOneShotV012(),"F18 single native VFX")
eq(effect_calls,1,"only one F18 impact effect")
assert(not Homelander_ImpactVFXOneShotV012(),"F18 replay refused")
eq(effect_calls,1,"F18 replay produced no extra effect")
eq(HOMELANDER_DAMAGE_ONESHOT_PASSED,false,"F17 proof consumed after F18")
print("P1_R018_ASSEMBLED_F17_F18_AT_MOST_ONE_DAMAGE_AND_VFX_PASS")

HOMELANDER_CONTINUITY_REQUIRED_SECONDS=1
HOMELANDER_CONTINUITY_REQUIRED_SAMPLES=15
assert(Homelander_TargetContinuityToggleV013(),"F19 enable current A/NPC")
for i=1,15 do assert(Homelander_TargetContinuityTickV013(),"F19 read-only sample "..i) end
eq(HOMELANDER_TARGET_CONTINUITY_PASSED,true,"F19 stable same target")
eq(HOMELANDER_TARGET_CONTINUITY_PLAYER,"A","F19 same F17 owner")
assert(Homelander_DOTDryRunToggleV014(),"F20 enable after F19 stable target")
for i=1,35 do
 if HOMELANDER_DOT_DRYRUN_PASSED==true then break end
 assert(Homelander_DOTDryRunTickV014(),"F20 dryrun mock frame "..i)
end
eq(HOMELANDER_DOT_DRYRUN_PASSED,true,"F20 read-only scheduler pass")
eq(HOMELANDER_DOT_DRYRUN_PLAYER,"A","F20 same origin A")
eq(damage_calls,1,"F19/F20 must not submit another damage")
eq(effect_calls,1,"F19/F20 must not submit another impact")
assert(Homelander_DamageHitPayloadProbeV015(),"F21 read-only payload exact A origin and F11 eye")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED,true,"F21 verified read-only payload")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PLAYER,"A","F21 exact original player")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_EYE_EPOCH,HOMELANDER_EYE_ORIGIN_EPOCH,"F21 current F11 eye generation")
eq(damage_calls,1,"F21 never sends additional native damage")
eq(effect_calls,1,"F21 never sends additional native effect")
print("P1_R018_ASSEMBLED_F17_F21_PLAYER_LOCKED_READONLY_CONTINUITY_PASS")

-- Negative test on this very same assembled state: B may not steal any A chain.
HOMELANDER_PLAYER="B"
assert(not Homelander_DamageHitPayloadProbeV015(),"B cannot borrow A's F17-F20 chain")
eq(HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED,false,"failed new F21 revokes A payload receipt")
eq(damage_calls,1,"cross-player attempt never mutates")
eq(effect_calls,1,"cross-player attempt never spawns VFX")
print("P1_R018_ASSEMBLED_F21_CROSS_PLAYER_FAILCLOSED_PASS")
print("P1_R018_SOURCE_ONLY_FULL_F9_F21_STAGED_CHAIN_MOCK_PASS")
