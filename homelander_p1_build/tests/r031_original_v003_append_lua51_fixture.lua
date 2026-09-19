-- R031 actual original v003 source with appended prioritized census in Lua5.1 mocks.
local assembled=assert(arg[1],"original v003+R031 combined Lua path required")
local log={}
HL_Log=function(v) log[#log+1]=v end
PLAYER=nil
HOMELANDER_PLAYER=nil
HOMELANDER_SETTER_ECHO_PASSED=false
online_GetNumPlayers=function()return 1 end
go_FindGOHByName=function()return nil end
go_FindTransientGOHByName=function()return nil end
local native_calls=0
for _,name in ipairs({"ai_GetClosestCharacterToCamera","cm_SetCameraAvatar",
 "go_SetPosition","go_IsValid","go_GetPosition",
 "ai_GetPhysicsVelocity","online_DeterminePlayerIndex"}) do
 _G[name]=function() native_calls=native_calls+1;error("unverified native call prohibited") end
end
assert(type(io.stdout)=="userdata")
PlayerCandidateHandle=io.stdout
for i=1,512 do _G[string.format("PlayerEngineFunction%04d",i)]=function()end end
for round=1,2 do
 assert(loadfile(assembled))()
 assert(HOMELANDER_PLAYER==nil and HOMELANDER_SETTER_ECHO_PASSED==false)
 assert(native_calls==0)
end
local function count(x)
 local n=0
 for _,v in ipairs(log) do if v:find(x,1,true) then n=n+1 end end
 return n
end
assert(count("NO VERIFIED PLAYER HANDLE")==2)
assert(count("GLOBAL | PlayerCandidateHandle type=userdata")==2)
assert(count("CAMERA_NOT_RUN")==2)
assert(count("CENSUS_END | entries=")==2)
for _,v in ipairs(log) do
 assert(not v:find("userdata:",1,true))
 assert(not v:find("table:",1,true))
end
print("P1_R031_EXACT_ORIGINAL_V003_F4_FAILCLOSED_PLUS_USERDATA_PRIORITY_TWO_RUNS_PASS")
