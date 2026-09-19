-- R027 isolated Lua5.1 fixture: zero gameplay in test and no GAME binaries.
local source=assert(arg[1],"standalone one-shot R027 source required")
local f=assert(io.open(source,"rb"))
local code=f:read("*a");f:close()
assert(code:find("local ENABLE_CAMERA_OBSERVER = false",1,true))
local before="UNVERIFIED_KEEP"
HOMELANDER_PLAYER=before
HOMELANDER_SETTER_ECHO_PASSED=false
local logs, hits={},{}
HL_Log=function(s) logs[#logs+1]=tostring(s) end
local function hit(k) hits[k]=(hits[k] or 0)+1 end
local h=newproxy(true)
getmetatable(h).__tostring=function() error("userdata secret must not be printed") end
getmetatable(h).__index=function() error("userdata secret must not be indexed by Lua") end
PLAYER=h
LocalPlayerGOH=h
CameraAvatar=setmetatable({},{
 __tostring=function() error("table values must not be printed") end,
 __index=function() error("table values must not be traversed") end,
})
for _,n in ipairs({"go_SetHealth","go_ApplyDamage","phys_SetLinearVelocity",
 "go_Teleport","cm_SetCameraAvatar","em_AddWorldEffect","HL_LaserSightSubmitDual"}) do
 _G[n]=function() error("FORBIDDEN GAME WRITE: "..n) end
end
online_GetNumPlayers=function() hit("count");error("default must never query engine") end
ai_GetClosestCharacterToCamera=function() hit("closest");error("default must never query engine") end
go_IsValid=function() hit("valid");error("default must never query engine") end
online_DeterminePlayerIndex=function() hit("index");error("default must never query engine") end
go_GetPosition=function() hit("position");error("default must never query engine") end
ai_GetPhysicsVelocity=function() hit("velocity");error("default must never query engine") end
local function census()
 logs={};hits={}
 assert(loadstring(code))()
 assert(HOMELANDER_PLAYER==before and HOMELANDER_SETTER_ECHO_PASSED==false)
 assert(next(hits)==nil,"default diagnostics must never invoke native GOH methods")
 local found={}
 for _,line in ipairs(logs) do
   assert(not line:find("userdata:",1,true),"must not print raw userdata")
   assert(not line:find("table:",1,true),"must not print raw tables")
   assert(not line:find(before,1,true),"must not expose existing player handle")
   found[line]=true
 end
 return table.concat(logs,"\n")
end
local out=census()
assert(out:find("GLOBAL | LocalPlayerGOH type=userdata",1,true))
assert(out:find("GLOBAL | CameraAvatar type=table",1,true))
assert(out:find("CAMERA_NOT_RUN | optional native ABI experiment disabled by default",1,true))
print("P1_R027_DEFAULT_ONE_SHOT_CENSUS_NO_ENGINE_CALLS_NO_GAME_WRITES_PASS")
for i=1,100 do _G[string.format("R027_SyntheticPlayer_%03d",i)]=h end
PLAYER=nil
out=census()
assert(out:find("PLAYER global type=nil",1,true))
assert(out:find("truncated=true",1,true))
local emitted=0
for _,line in ipairs(logs) do if line:find("GLOBAL | ",1,true) then emitted=emitted+1 end end
assert(emitted<=64)
print("P1_R027_CENSUS_64_ENTRY_CAP_NIL_PLAYER_AND_NO_HANDLE_LEAK_PASS")
-- The synthetic experiment never modifies the dormant shipped default source.
local enabled,num,nearest,valid,index,pos,vel=nil,1,h,true,0,{x=1},{x=0}
enabled=code:gsub("local ENABLE_CAMERA_OBSERVER = false","local ENABLE_CAMERA_OBSERVER = true",1)
assert(enabled~=code and enabled:find("local ENABLE_CAMERA_OBSERVER = true",1,true))
local function install()
 online_GetNumPlayers=function() hit("count");return num end
 ai_GetClosestCharacterToCamera=function() hit("closest");return nearest end
 go_IsValid=function(v) hit("valid");assert(v==h);return valid end
 online_DeterminePlayerIndex=function(v) hit("index");assert(v==h);return index end
 go_GetPosition=function(v) hit("position");assert(v==h);return pos end
 ai_GetPhysicsVelocity=function(v) hit("velocity");assert(v==h);return vel end
end
local function run_camera()
 logs={};hits={};install()
 assert(loadstring(enabled))()
 assert(HOMELANDER_PLAYER==before)
 assert(HOMELANDER_SETTER_ECHO_PASSED==false)
 for _,line in ipairs(logs) do
   assert(not line:find("userdata:",1,true))
   assert(not line:find("table:",1,true))
 end
 return table.concat(logs,"\n")
end
num=1;nearest=h;valid=true;index=0;pos={x=1};vel={x=0}
out=run_camera()
assert(out:find("CAMERA_OBSERVED | one camera-nearest typed GOH has index=0 of 1",1,true))
assert(hits.closest==1 and hits.valid==1 and hits.index==1 and hits.position==1 and hits.velocity==1)
print("P1_R027_OPTED_CAMERA_OBSERVATION_ONLY_NO_PLAYER_ASSIGNMENT_PASS")
index=-1;out=run_camera()
assert(out:find("CAMERA_STOP | independent player index unverified",1,true))
assert((hits.position or 0)==0 and (hits.velocity or 0)==0)
index=0;nearest="NPC";
out=run_camera()
assert(out:find("CAMERA_STOP | nonuserdata",1,true))
assert((hits.valid or 0)==0)
nearest=h;num=0;
out=run_camera()
assert(out:find("CAMERA_STOP | invalid available player count",1,true))
assert((hits.closest or 0)==0)
num=1;valid=false;
out=run_camera()
assert(out:find("CAMERA_STOP | native GOH validation did not return true",1,true))
valid=true;pos=nil;
out=run_camera()
assert(out:find("CAMERA_STOP | candidate position unavailable",1,true))
pos={x=1};vel=nil
out=run_camera()
assert(out:find("CAMERA_STOP | candidate velocity unavailable",1,true))
vel={x=0}
local originalIndex=online_DeterminePlayerIndex
install()
online_DeterminePlayerIndex=function() hit("index");error("mock engine failure") end
logs={};hits={};assert(loadstring(enabled))()
assert(table.concat(logs,"\n"):find("raised error",1,true))
assert(HOMELANDER_PLAYER==before)
print("P1_R027_CAMERA_NPC_BAD_INDEX_TYPE_COUNT_NIL_ERROR_FAILCLOSED_PASS")
print("P1_R027_NO_REAL_GAME_EVIDENCE_NO_ORIGINAL_V003_GATE_PASS")
