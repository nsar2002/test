-- R033 Lua 5.1 fixture: genuine game's custom type() reports GOH.
local source=assert(arg[1],"candidate-observer source path required")
local builtin_type=type
local h={}
for _,n in ipairs({"MainCharacter","PLAYER_1","playerCharacterID",
                     "gameFlowMachineGOH","mainMissionGOH"}) do
 h[n]=newproxy(true)
 local meta=getmetatable(h[n])
 meta.__tostring=function() error("must never stringify GOH object") end
 meta.__index=function() error("must never dereference GOH object") end
end
type=function(v)
 for _,candidate in pairs(h) do
  if rawequal(v,candidate) then return "GOH" end
 end
 return builtin_type(v)
end
for n,v in pairs(h) do _G[n]=v end
local logs,calls={},{}
HL_Log=function(x) logs[#logs+1]=x end
local function touched(n) calls[n]=(calls[n] or 0)+1 end
HOMELANDER_PLAYER=nil
HOMELANDER_SETTER_ECHO_PASSED=false
online_GetNumPlayers=function() touched("count");return 1 end
go_IsValid=function(g)
 touched("valid")
 if rawequal(g,h.gameFlowMachineGOH) then return false end
 return true
end
go_GetPosition=function(g)
 touched("pos")
 if rawequal(g,h.mainMissionGOH) then return nil end
 return {x=0,y=0,z=0}
end
ai_GetPhysicsVelocity=function(g)
 touched("vel")
 if rawequal(g,h.mainMissionGOH) then return nil end
 return {x=0,y=0,z=0}
end
online_DeterminePlayerIndex=function(g)
 touched("index")
 if rawequal(g,h.PLAYER_1) then return -1 end
 if rawequal(g,h.MainCharacter) or rawequal(g,h.playerCharacterID) then return 0 end
 error("negative control must not reach index probe")
end
go_GetDebugName=function(g)
 touched("debug")
 if rawequal(g,h.MainCharacter) then return "Alex Mercer" end
 return nil
end
for _,n in ipairs({"go_SetPosition","phys_SetLinearVelocity","go_ApplyDamage",
                   "cm_SetCameraAvatar","HL_LaserSightSubmitDual"}) do
 _G[n]=function() error("gameplay mutation forbidden: "..n) end
end
-- Original frozen v003 bootstrap loads runtime BEFORE flight controller.
Homelander_FlightNativeTick=nil
assert(loadfile(source))()
assert((calls.count or 0)==0)
assert(table.concat(logs,"\n"):find("SKIP_BOOT",1,true))
print("P1_R033_V003_BOOT_SKIP_ZERO_NATIVE_GOHCALLS_PASS")
Homelander_FlightNativeTick=function() end
logs={};calls={}
assert(loadfile(source))()
local out=table.concat(logs,"\n")
assert(out:find("CANDIDATE MainCharacter type=GOH",1,true))
assert(out:find("CANDIDATE PLAYER_1 type=GOH",1,true))
assert(out:find("CANDIDATE playerCharacterID type=GOH",1,true))
assert(out:find("INDEX MainCharacter mapped=0 of 1",1,true))
assert(out:find("INDEX PLAYER_1 rejected=-1",1,true))
assert(out:find("INDEX playerCharacterID mapped=0 of 1",1,true))
assert(out:find("RESULT gameFlowMachineGOH STOP_GO_ISVALID_OK_NOT_TRUE",1,true))
assert(out:find("INDEX mainMissionGOH skipped_without_position_and_velocity",1,true))
assert(out:find("DEBUG_NAME MainCharacter=Alex_Mercer",1,true))
assert(out:find("END_F4 | no HOMELANDER_PLAYER write, no setter, no official PASS",1,true))
assert((calls.count or 0)==1)
assert((calls.valid or 0)==5)
assert((calls.index or 0)==3)
assert(HOMELANDER_PLAYER==nil and HOMELANDER_SETTER_ECHO_PASSED==false)
for _,entry in ipairs(logs) do
 assert(not entry:find("userdata:",1,true))
 assert(not entry:find("table:",1,true))
end
print("P1_R033_GOHTYPE_NEGATIVE_CONTROLS_PLAYERINDEX_GOHDATA_REDACTION_PASS")
-- Fail closed if custom type is unexpectedly normal stock-Lua userdata.
type=builtin_type
logs={};calls={}
assert(loadfile(source))()
out=table.concat(logs,"\n")
assert(out:find("RESULT MainCharacter STOP_NOT_GOH",1,true))
assert((calls.valid or 0)==0 and (calls.index or 0)==0)
assert(HOMELANDER_PLAYER==nil)
print("P1_R033_UNEXPECTED_LUA_TYPE_FAILS_CLOSED_NO_NATIVE_CANDIDATE_PASS")
