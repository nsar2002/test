-- R033: observational GOH-global provenance in clone ONLY. No player assignment,
-- native setter, gate manipulation, automatic tick, address or GOH value logging.
-- Source of candidate NAMES: exact user's first real R031 F4 log 2026-09-19.
local PREFIX="[P1_R033_GOH_CANDIDATE] "
local function log(s)
 local sink=rawget(_G,"HL_Log")
 if type(sink)~="function" then sink=print end
 sink(PREFIX..s)
end
-- The pinned original v003 boot order executes runtime_probe.lua BEFORE
-- controller definition. F4 reexecutes it AFTER controller definition.
-- In a reinitialized Lua state or unexpected boot order fail closed.
if type(rawget(_G,"Homelander_FlightNativeTick"))~="function" then
 log("SKIP_BOOT | original v003 controller function not yet available")
 return
end
local function native(name,...)
 local f=rawget(_G,name)
 if type(f)~="function" then return "NO_API",nil end
 local ok,v=pcall(f,...)
 if not ok then return "ERROR",nil end
 return "OK",v
end
local gotCount,count=native("online_GetNumPlayers")
local countOK=(gotCount=="OK" and type(count)=="number" and count==count
 and count>=1 and count<=16 and count==math.floor(count))
log("BEGIN_F4 | exact R031 GOH aliases; observational, no player assignment")
if not countOK then
 log("STOP | player-count missing or invalid; no GOH native calls")
 return
end
log("PLAYER_COUNT="..count)
-- Negative controls are GOHs, not assumed invalid or NPCs.
local names={
 "MainCharacter","PLAYER_1","playerCharacterID",
 "gameFlowMachineGOH","mainMissionGOH"
}
local function isInteger(v)
 return type(v)=="number" and v==v and v==math.floor(v)
end
for _,name in ipairs(names) do
 local h=rawget(_G,name)
 local kind=type(h)
 log("CANDIDATE "..name.." type="..kind)
 -- This engine reports GOH as a custom type, NOT stock Lua userdata.
 if kind~="GOH" then
  log("RESULT "..name.." STOP_NOT_GOH")
 else
  local okValid,valid=native("go_IsValid",h)
  if okValid~="OK" or valid~=true then
   log("RESULT "..name.." STOP_GO_ISVALID_"..okValid..
       (okValid=="OK" and "_NOT_TRUE" or ""))
  else
   local okPos,pos=native("go_GetPosition",h)
   local okVel,vel=native("ai_GetPhysicsVelocity",h)
   -- Never serialize raw GOH/position/velocity values (including tostring).
   local posValid=(okPos=="OK" and pos~=nil)
   local velValid=(okVel=="OK" and vel~=nil)
   log("PHYS "..name.." position_available="..tostring(posValid)..
       " velocity_available="..tostring(velValid))
   if posValid and velValid then
    local okIdx,idx=native("online_DeterminePlayerIndex",h)
    if okIdx=="OK" and isInteger(idx) and idx>=0 and idx<count then
     log("INDEX "..name.." mapped="..idx.." of "..count..
         " | mapping is NOT proof of locally controlled Alex")
    elseif okIdx=="OK" and isInteger(idx) and idx>=-16 and idx<=16 then
     log("INDEX "..name.." rejected="..idx)
    else
     log("INDEX "..name.." unavailable_or_untrusted status="..okIdx)
    end
    -- Native debug name is optional and must not expose arbitrary game data.
    local okDebug,debugName=native("go_GetDebugName",h)
    if okDebug=="OK" and type(debugName)=="string" then
      log("DEBUG_NAME "..name.."="..
          string.sub(string.gsub(debugName,"[^%w%._%-]","_"),1,72))
    else
      log("DEBUG_NAME "..name.." unavailable_or_redacted")
    end
   else
    log("INDEX "..name.." skipped_without_position_and_velocity")
   end
  end
 end
end
log("END_F4 | no HOMELANDER_PLAYER write, no setter, no official PASS")
