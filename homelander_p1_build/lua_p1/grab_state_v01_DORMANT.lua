-- Homelander P1 Grab State Probe v0.1: DORMANT / READ ONLY.
-- Static ABI: bool go_IsGrabbed(engine::LuaGOH). Runtime semantics are unproven.
local PREFIX="[HOMELANDER_P1_GRAB_READ_ONLY_V01] "
local function log(msg)
 local line=PREFIX..tostring(msg)
 if type(HL_Log)=="function" then HL_Log(line) else print(line) end
end
local function hasfn(name) return type(_G[name])=="function" end
local function valid_player(h)
 if h==nil or not (hasfn("go_IsValid") or hasfn("online_DeterminePlayerIndex")) then return false end
 if hasfn("go_IsValid") then
  local ok,v=pcall(go_IsValid,h)
  if not ok or v~=true then return false end
 end
 if hasfn("online_DeterminePlayerIndex") then
  local ok,index=pcall(online_DeterminePlayerIndex,h)
  if not ok or type(index)~="number" or index~=index or
     index==math.huge or index==-math.huge or index<0 then return false end
 end
 return true
end

HOMELANDER_GRAB_STATE_VALID=false
HOMELANDER_GRAB_STATE_VALUE=nil
HOMELANDER_GRAB_STATE_PLAYER=nil
function Homelander_GrabStateProbeV01()
 HOMELANDER_GRAB_STATE_VALID=false
 HOMELANDER_GRAB_STATE_VALUE=nil
 HOMELANDER_GRAB_STATE_PLAYER=nil
 local player=HOMELANDER_PLAYER
 if not valid_player(player) or not hasfn("go_IsGrabbed") then
  log("ABORT: player not verified or read-only getter unavailable")
  return false
 end
 local ok,value=pcall(go_IsGrabbed,player)
 if not ok or type(value)~="boolean" then
  log("ABORT: getter error or non-boolean result")
  return false
 end
 if HOMELANDER_PLAYER~=player or not valid_player(player) then
  log("ABORT: player changed while reading")
  return false
 end
 HOMELANDER_GRAB_STATE_VALID=true
 HOMELANDER_GRAB_STATE_VALUE=value
 HOMELANDER_GRAB_STATE_PLAYER=player
 log("RAW BOOL READ ONLY | value="..tostring(value)..
     " | meaning for player in gameplay UNVERIFIED")
 return true
end

log("LOADED definition only; does not grab, attach, detach, or mutate")
