-- R025 exact source one-shot camera-character observer mock tests.
-- No Prototype binary, installer or original v003 stage is used by CI.
local source=assert(arg[1],"R025 source path required")
local candidate=newproxy(true)
getmetatable(candidate).__tostring=function() error("user object value must NEVER be logged") end
getmetatable(candidate).__index=function() error("userdata must NEVER be dereferenced by Lua") end
local player="original_v003_unverified"
HOMELANDER_PLAYER=player
HOMELANDER_SETTER_ECHO_PASSED=false
local logs,calls={},{}
HL_Log=function(s) logs[#logs+1]=s end
local function hit(n) calls[n]=(calls[n] or 0)+1 end
local count,which,valid,index,position,velocity=1,candidate,true,0,{x=1}, {x=0}
online_GetNumPlayers=function() hit("count");return count end
ai_GetClosestCharacterToCamera=function() hit("closest");return which end
go_IsValid=function(h) hit("valid");assert(h==candidate);return valid end
online_DeterminePlayerIndex=function(h) hit("index");assert(h==candidate);return index end
go_GetPosition=function(h) hit("pos");assert(h==candidate);return position end
ai_GetPhysicsVelocity=function(h) hit("vel");assert(h==candidate);return velocity end
for _,name in ipairs({"go_SetPosition","phys_SetLinearVelocity","go_ApplyDamage",
  "em_AddWorldEffect","cm_SetCameraAvatar","go_Kill"}) do
 _G[name]=function() error("forbidden gameplay mutation by R025: "..name) end
end
local before=HOMELANDER_PLAYER
dofile(source)
assert(HOMELANDER_PLAYER==before)
assert((calls.closest or 0)==0,"module load must not call camera/engine")
local function grep(q)
 for _,line in ipairs(logs) do if line:find(q,1,true) then return true end end
 return false
end
local function run(expected,reason)
 logs={};calls={}
 local success=Homelander_R025_ObserveClosestCameraCharacter()
 assert(success==expected,(reason or "")..": unexpected observation result "..tostring(success))
 assert(HOMELANDER_PLAYER==before,"R025 must not set the game player")
 assert(HOMELANDER_SETTER_ECHO_PASSED==false,"R025 must not set setter gate")
 for _,line in ipairs(logs) do
  assert(not line:find("userdata:",1,true),"must not expose userdata address")
  assert(not line:find("table:",1,true),"must not expose table address")
  assert(not line:find("original_v003_unverified",1,true),"must not leak old player")
 end
 return calls
end
local cs=run(true,"one independently verified mock GOH")
assert(grep("OBSERVED | closest camera character passed current player-index range"))
assert(grep("NO PLAYER GLOBAL SET"))
assert(cs.closest==1 and cs.valid==1 and cs.index==1 and cs.pos==1 and cs.vel==1)
print("P1_R025_SOURCE_ONLY_CAMERA_GOHCANDIDATE_VERIFIED_INDEX_OBSERVATION_NO_GLOBAL_ASSIGN_PASS")
which=nil
cs=run(false,"no character")
assert(cs.closest==1 and (cs.valid or 0)==0)
which=candidate
index=-1
cs=run(false,"nearest NPC is not a player")
assert(grep("REJECT | independent online player index absent"))
assert(cs.index==1 and (cs.pos or 0)==0)
index=2
run(false,"out-of-range candidate index")
index=0.5
run(false,"fractional candidate index")
index=0/0
run(false,"nonfinite candidate index")
index=0
count=0
cs=run(false,"no network player count")
assert((cs.closest or 0)==0,"must not ask for closest without valid player count")
count=1.5
run(false,"fractional network count")
count=1
which="NPC_wrong_Lua_type"
cs=run(false,"non-userdata candidate must be rejected before any native GOH query")
assert((cs.valid or 0)==0)
which=candidate
valid=false
cs=run(false,"engine rejects GOH validity")
assert(cs.valid==1 and (cs.index or 0)==0)
valid=true
position=nil
cs=run(false,"unavailable position")
assert(cs.pos==1 and (cs.vel or 0)==0)
position={x=1}
velocity=nil
run(false,"unavailable velocity")
velocity={x=0}
local origIndex=online_DeterminePlayerIndex
online_DeterminePlayerIndex=function(h) hit("index");error("mock native engine index error") end
run(false,"engine index exception")
online_DeterminePlayerIndex=origIndex
local origClosest=ai_GetClosestCharacterToCamera
ai_GetClosestCharacterToCamera=function() hit("closest");error("mock native camera query error") end
run(false,"engine camera query exception")
ai_GetClosestCharacterToCamera=origClosest
local origValid=go_IsValid
go_IsValid=nil
cs=run(false,"required go_IsValid API unavailable")
assert((cs.closest or 0)==0)
go_IsValid=origValid
assert(HOMELANDER_PLAYER==player)
print("P1_R025_SOURCE_ONLY_NIL_NPC_INVALID_INDEX_NONUSERDATA_ERROR_AND_MISSING_API_FAILCLOSED_PASS")
print("P1_R025_SOURCE_ONLY_NO_PLAYER_IDENTITY_PROOF_NO_ORIGINAL_V003_GATE_PASS")
