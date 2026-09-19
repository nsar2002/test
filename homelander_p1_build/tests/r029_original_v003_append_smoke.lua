-- R029 independent Lua 5.1 source-only smoke of actual v003 runtime_probe
-- concatenated at END with exact standalone R027, no fake player insertion.
local assembled=assert(arg[1],"combined original v003+R027 source path required")
local log={}
local engine_native_calls=0
HL_Log=function(s) log[#log+1]=tostring(s) end
PLAYER=nil
HOMELANDER_PLAYER=nil
HOMELANDER_SETTER_ECHO_PASSED=false
LocalPlayerGOH=newproxy(true)
getmetatable(LocalPlayerGOH).__tostring=function() error("must not stringify candidate object") end
getmetatable(LocalPlayerGOH).__index=function() error("must not dereference candidate object") end
CameraAvatarOpaque=setmetatable({},{
 __tostring=function() error("must not log table values") end,
 __index=function() error("must not traverse game table") end
})
online_GetNumPlayers=function() return 1 end
go_FindGOHByName=function() return nil end
go_FindTransientGOHByName=function() return nil end
for _,f in ipairs({"ai_GetClosestCharacterToCamera","cm_SetCameraAvatar",
 "go_IsValid","go_GetPosition","ai_GetPhysicsVelocity","online_DeterminePlayerIndex"}) do
 _G[f]=function() engine_native_calls=engine_native_calls+1
   error("NO candidate GOH means native object functions must not run")
 end
end
local function count(needle)
 local n=0
 for _,line in ipairs(log) do
   if string.find(line,needle,1,true) then n=n+1 end
   assert(not string.find(line,"userdata:",1,true),"must not log userdata pointer")
   assert(not string.find(line,"table:",1,true),"must not log table pointer")
 end
 return n
end
for round=1,2 do
 dofile(assembled)
 assert(HOMELANDER_PLAYER==nil,"actual original v003 F4 must remain unresolved with absent genuine player")
 assert(HOMELANDER_SETTER_ECHO_PASSED==false,"R027 append must never authorize physics")
 assert(engine_native_calls==0,"clone-only default R027 must never call game object or camera native functions")
 assert(count("NO VERIFIED PLAYER HANDLE")==round)
 assert(count("[P1_R027_ONE_SHOT] BEGIN | only global key names + Lua types")==round)
 assert(count("[P1_R027_ONE_SHOT] PLAYER global type=nil")==round)
 assert(count("[P1_R027_ONE_SHOT] GLOBAL | LocalPlayerGOH type=userdata")==round)
 assert(count("[P1_R027_ONE_SHOT] CAMERA_NOT_RUN | optional native ABI experiment disabled by default")==round)
 assert(count("[P1_R027_ONE_SHOT] END | no game native GOH query, no player assignment, no gate PASS")==round)
end
print("P1_R029_ORIGINAL_V003_REEXECUTED_TWICE_APPENDED_R027_WITHOUT_SECOND_ASI_PASS")
print("P1_R029_REAL_GAME_PLAYER_STILL_UNKNOWN_OFFLINE_NO_LIVE_GATE_PASS")
