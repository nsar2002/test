-- R034 Lua5.1 fixture: execute actual original v003 + R031 + R033 integrated source; custom engine GOH.
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
assert((calls.count or 0)==1)
 assert((calls.valid or 0)==0 and (calls.pos or 0)==0)
 assert(table.concat(logs,"\\n"):find("[P1_R031_ONE_SHOT] CENSUS_END |",1,true))
assert(table.concat(logs,"\n"):find("SKIP_BOOT",1,true))
print("P1_R034_COMBINED_V003_BOOT_SKIPS_R033_NATIVE_GOHCALLS_PASS")
Homelander_FlightNativeTick=function() end
logs={};calls={}
assert(loadfile(source))()
local out=table.concat(logs,"\n")
assert(out:find("[P1_R031_ONE_SHOT] CENSUS_END |",1,true))
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
assert((calls.count or 0)==2)
assert((calls.valid or 0)==5)
assert((calls.index or 0)==3)
assert(HOMELANDER_PLAYER==nil and HOMELANDER_SETTER_ECHO_PASSED==false)
for _,entry in ipairs(logs) do
 assert(not entry:find("userdata:",1,true))
 assert(not entry:find("table:",1,true))
end
print("P1_R034_REAL_COMBINED_LUA51_F4_FIVE_GOHS_NEGATIVES_AND_NO_CAMERA_PASS")
-- Reexecute F4 in the SAME Lua state: no stale player global, setter or
-- camera mutation may survive. R033 must be reached twice, not only at BOOT.
local previous=table.concat(logs,"\n")
assert(loadfile(source))()
out=table.concat(logs,"\n")
assert(out:find("[P1_R031_ONE_SHOT] CENSUS_END |",1,true))
assert((calls.valid or 0)==10)
assert((calls.index or 0)==6)
assert(HOMELANDER_PLAYER==nil and HOMELANDER_SETTER_ECHO_PASSED==false)
assert(out:find("END_F4 | no HOMELANDER_PLAYER write, no setter, no official PASS",1,true))
print("P1_R034_REAL_COMBINED_REPEATED_F4_NO_GLOBAL_PLAYER_OR_GATE_PASS")
-- Fail closed if custom type is unexpectedly normal stock-Lua userdata.
type=builtin_type
logs={};calls={}
assert(loadfile(source))()
out=table.concat(logs,"\n")
assert(out:find("RESULT MainCharacter STOP_NOT_GOH",1,true))
assert((calls.valid or 0)==0 and (calls.index or 0)==0)
assert(HOMELANDER_PLAYER==nil)
print("P1_R034_CUSTOM_TYPE_UNKNOWN_FAILS_CLOSED_NO_NATIVE_CANDIDATE_PASS")
