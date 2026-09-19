-- R031: prioritized clone-only single-shot Lua5.1 diagnosis for a SEPARATE experimental
-- Prototype 1 copy with ONE verified executor ASI, never the active R007/v003.
-- Default performs ONLY bounded key/type census, NO native GOH API calls.
-- Explicit opt-in for camera candidate ONLY after user reviews crash risk:
local ENABLE_CAMERA_OBSERVER = false
local PREFIX = "[P1_R031_ONE_SHOT] "
local function log(s)
    local sink = rawget(_G, "HL_Log")
    if type(sink) ~= "function" then sink = print end
    sink(PREFIX .. s)
end
local function is_key(k)
    if type(k) ~= "string" or #k < 2 or #k > 72 then return false end
    if not string.match(k, "^[%w_]+$") then return false end
    local lower = string.lower(k)
    for _, term in ipairs({"player","alex","avatar","character","hero","actor","goh"}) do
        if string.find(lower,term,1,true) then return true end
    end
    return false
end
-- We must NOT keep the first 64 matching globals: engine function names
-- can exhaust that budget before a real opaque player reference appears.
-- Deterministic top-64 across all keys; priority is type ONLY, not value.
local MAX_KEYS = 64
local keys, matches = {}, 0
local totals = {userdata=0,table=0,other=0,func=0}
local function rank(k)
    if k == "userdata" then return 1 end
    if k == "table" then return 2 end
    if k == "function" then return 4 end
    return 3
end
local function less(a,b)
    if a.rank ~= b.rank then return a.rank < b.rank end
    return a.name < b.name
end
for key, value in next, _G do
    if is_key(key) then
        matches = matches + 1
        -- type() does not dereference userdata or inspect a metatable.
        local kind = type(value)
        local group = (kind=="userdata" and "userdata") or
            (kind=="table" and "table") or
            (kind=="function" and "func") or "other"
        totals[group] = totals[group] + 1
        local candidate={name=key,kind=kind,rank=rank(kind)}
        if #keys < MAX_KEYS then
            keys[#keys+1] = candidate
            table.sort(keys,less)
        elseif less(candidate,keys[#keys]) then
            keys[#keys] = candidate
            table.sort(keys,less)
        end
    end
end
-- Lua 5.1 table iteration order is not a public guarantee. Lexical sorting
-- inside each category makes the emitted set deterministic for the same _G.
log("BEGIN | only global key names + Lua types; no pointer/value logging; prioritized userdata and tables")
log("PLAYER global type=" .. type(rawget(_G,"PLAYER")))
for _,item in ipairs(keys) do
    log("GLOBAL | " .. item.name .. " type=" .. item.kind)
end
local emitted_user, emitted_table = 0,0
for _,item in ipairs(keys) do
    if item.kind=="userdata" then emitted_user=emitted_user+1 end
    if item.kind=="table" then emitted_table=emitted_table+1 end
end
log("CENSUS_END | entries=" .. #keys .. " total_matches=" .. matches ..
    " truncated=" .. tostring(matches > MAX_KEYS) ..
    " userdata_total=" .. totals.userdata ..
    " userdata_emitted=" .. emitted_user ..
    " table_total=" .. totals.table ..
    " table_emitted=" .. emitted_table ..
    " functions_total=" .. totals.func ..
    " others_total=" .. totals.other)
if not ENABLE_CAMERA_OBSERVER then
    log("CAMERA_NOT_RUN | optional native ABI experiment disabled by default")
    log("END | no game native GOH query, no player assignment, no gate PASS")
    return
end
-- WARNING: pcall cannot catch a native access violation/crash. Use ONLY on
-- a disposable game copy after explicit approval, not the real v003 install.
log("CAMERA_BEGIN | observed nearest character MAY BE NPC, never player proof")
local names = {"ai_GetClosestCharacterToCamera","online_GetNumPlayers",
               "go_IsValid","online_DeterminePlayerIndex",
               "go_GetPosition","ai_GetPhysicsVelocity"}
local funcs = {}
for _,name in ipairs(names) do
    funcs[name] = rawget(_G,name)
    if type(funcs[name]) ~= "function" then
        log("CAMERA_STOP | unavailable Lua API " .. name)
        return
    end
end
local function call(name,...)
    local ok, result = pcall(funcs[name],...)
    if not ok then
        log("CAMERA_STOP | native " .. name .. " raised error (value redacted)")
        return false,nil
    end
    return true,result
end
local okCount,num = call("online_GetNumPlayers")
if not okCount or type(num) ~= "number" or num ~= num or
   num < 1 or num > 16 or num ~= math.floor(num) then
    log("CAMERA_STOP | invalid available player count")
    return
end
local okCandidate, h = call("ai_GetClosestCharacterToCamera")
if not okCandidate or h == nil then
    log("CAMERA_STOP | no nearest character returned")
    return
end
log("CANDIDATE | Lua type=" .. type(h) .. "; not automatically Alex")
if type(h) ~= "userdata" then
    log("CAMERA_STOP | nonuserdata cannot be passed to native GOH APIs")
    return
end
local okValid, valid = call("go_IsValid",h)
if not okValid or valid ~= true then
    log("CAMERA_STOP | native GOH validation did not return true")
    return
end
local okIndex,idx = call("online_DeterminePlayerIndex",h)
if not okIndex or type(idx) ~= "number" or idx ~= idx or
   idx < 0 or idx >= num or idx ~= math.floor(idx) then
    log("CAMERA_STOP | independent player index unverified or outside count")
    return
end
local okPos, pos = call("go_GetPosition",h)
if not okPos or pos == nil then
    log("CAMERA_STOP | candidate position unavailable")
    return
end
local okVel, vel = call("ai_GetPhysicsVelocity",h)
if not okVel or vel == nil then
    log("CAMERA_STOP | candidate velocity unavailable")
    return
end
-- Never log h, pos, vel or any raw game userdata.
log("CAMERA_OBSERVED | one camera-nearest typed GOH has index=" .. idx ..
    " of " .. num .. "; local Alex identity still UNPROVEN")
log("END | no HOMELANDER_PLAYER write, no physics/laser/damage, NO v003 PASS")
