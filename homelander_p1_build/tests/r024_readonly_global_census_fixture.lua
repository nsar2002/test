-- R024 independent Lua 5.1 engine-free fixture. Never executes Prototype.
local source=assert(arg[1], "source-only census Lua path required")
local logs={}
local validation_calls=0
HL_Log=function(x) logs[#logs+1]=x end
go_IsValid=function() validation_calls=validation_calls+1;error("forbidden dereference") end
online_DeterminePlayerIndex=function() validation_calls=validation_calls+1;error("forbidden player index probe") end
cm_SetCameraAvatar=function() validation_calls=validation_calls+1;error("forbidden camera mutation") end
go_FindGOHByName=function() validation_calls=validation_calls+1;error("forbidden guessed GOH lookup") end
local sentinel=newproxy(true)
getmetatable(sentinel).__tostring=function() error("MUST NEVER STRINGIFY HANDLE") end
getmetatable(sentinel).__index=function() error("MUST NEVER INDEX HANDLE") end
PLAYER=sentinel
LocalPlayerGOH=sentinel
CameraAvatarObject=setmetatable({}, {__index=function() error("MUST NOT INDEX GAME DATA") end,
                                  __tostring=function() error("MUST NOT SERIALIZE GAME DATA") end})
HeroLoc=nil
GlobalWithoutMatch=sentinel
local prior_player=PLAYER
local prior_camera=CameraAvatarObject
dofile(source)
assert(PLAYER==prior_player and CameraAvatarObject==prior_camera)
assert(validation_calls==0,"census must never call a game engine API")
local function count(fragment)
 local n=0
 for _,v in ipairs(logs) do if v:find(fragment,1,true) then n=n+1 end end
 return n
end
assert(count("BEGIN | only global KEY + Lua TYPE")==1)
assert(count("PLAYER global type=userdata")==1)
assert(count("KEY LocalPlayerGOH type=userdata")==1)
assert(count("KEY CameraAvatarObject type=table")==1)
assert(count("KEY GlobalWithoutMatch")==0)
assert(count("userdata:")==0 and count("table:")==0)
assert(count("no GOH validated and no gameplay mutation")==1)
print("P1_R024_SOURCE_ONLY_CENSUS_KEYS_TYPES_NO_USERDATA_VALUE_LEAK_PASS")
logs={}
PLAYER=nil
LocalPlayerGOH=nil
CameraAvatarObject=nil
for i=1,100 do _G[string.format("SyntheticPlayerCandidate_%03d",i)]=sentinel end
dofile(source)
assert(count("PLAYER global type=nil")==1)
assert(count("capped=true")==1)
local entries=0
for _,v in ipairs(logs) do if v:find("[P1_R024_GLOBAL_CENSUS] KEY ",1,true) then entries=entries+1 end end
assert(entries<=64 and entries>=1,"census must honor 64-name bound")
assert(validation_calls==0)
print("P1_R024_SOURCE_ONLY_GLOBAL_ENUMERATION_CAP_AND_NIL_PLAYER_PASS")
