-- Homelander P1 Runtime Probe v3
-- READ-ONLY with respect to gameplay state.
-- Purpose: discover and VERIFY the player GOH before any physics mutation.




local PREFIX = "[HOMELANDER_P1_PROBE_V3] "




local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end
local function hasfn(name) return type(_G[name]) == "function" end




local function try(label, fn)
    local ok, a, b, c = pcall(fn)
    if ok then
        log(label .. " OK | " .. tostring(a) .. (b ~= nil and (" | " .. tostring(b)) or "") .. (c ~= nil and (" | " .. tostring(c)) or ""))
        return true, a, b, c
    end
    log(label .. " ERROR | " .. tostring(a))
    return false, nil
end




local function probe_handle(label, h)
    if h == nil then
        log(label .. " = nil")
        return false, nil
    end




    log(label .. " type=" .. type(h) .. " value=" .. tostring(h))




    local valid = nil
    if hasfn("go_IsValid") then
        local ok, v = try(label .. ".go_IsValid", function() return go_IsValid(h) end)
        if ok then valid = v end
        if valid == false then return false, nil end
    end




    local pos_ok = false
    if hasfn("go_GetPosition") then
        pos_ok = select(1, try(label .. ".go_GetPosition", function() return go_GetPosition(h) end))
    end




    if hasfn("go_GetOrientation") then
        try(label .. ".go_GetOrientation", function() return go_GetOrientation(h) end)
    end




    local vel_ok = false
    if hasfn("ai_GetPhysicsVelocity") then
        vel_ok = select(1, try(label .. ".ai_GetPhysicsVelocity", function() return ai_GetPhysicsVelocity(h) end))
    end




    if hasfn("go_GetDebugName") then
        try(label .. ".go_GetDebugName", function() return go_GetDebugName(h) end)
    end




    if hasfn("go_GetHealth") then
        try(label .. ".go_GetHealth", function() return go_GetHealth(h) end)
    end




    local player_index = nil
    if pos_ok and vel_ok and hasfn("online_DeterminePlayerIndex") then
        local ok, idx = try(label .. ".online_DeterminePlayerIndex", function()
            return online_DeterminePlayerIndex(h)
        end)
        if ok and type(idx) == "number" then
            player_index = idx
            if idx >= 0 then
                log(label .. " VERIFIED PLAYER INDEX=" .. tostring(idx))
            end
        end
    end




    return pos_ok and vel_ok, player_index
end




-- Any rediscovery invalidates the prior handle-specific setter gate.
HOMELANDER_PLAYER = nil
HOMELANDER_SETTER_ECHO_PASSED = false
log("BEGIN")
log("_VERSION=" .. tostring(_VERSION))
log("type(PLAYER)=" .. type(PLAYER))
log("type(Vector)=" .. type(Vector))




local api_names = {
    "go_IsValid",
    "go_FindGOHByName",
    "go_FindTransientGOHByName",
    "go_GetPosition",
    "go_GetOrientation",
    "go_Local2World",
    "go_GetDebugName",
    "go_GetHealth",
    "ai_GetPhysicsVelocity",
    "online_DeterminePlayerIndex",
    "online_GetNumPlayers",
    "phys_SetLinearVelocity",
    "phys_SetAngularVelocity",
    "cm_GetCurrentCameraPosition",
    "time_GetSimulationDelta"
}
for _, n in ipairs(api_names) do
    log("API " .. n .. "=" .. type(_G[n]))
end




if hasfn("online_GetNumPlayers") then
    try("online_GetNumPlayers", function() return online_GetNumPlayers() end)
end




local verified = nil




-- Highest-priority route: an engine-provided PLAYER global.
if PLAYER ~= nil then
    local ok, idx = probe_handle("PLAYER", PLAYER)
    if ok and (idx == nil or idx >= 0) then
        -- If DeterminePlayerIndex exists, require a non-negative result.
        if not hasfn("online_DeterminePlayerIndex") or (idx ~= nil and idx >= 0) then
            verified = PLAYER
        end
    end
end




-- Fallback names are candidates only. When online_DeterminePlayerIndex is available,
-- a named candidate is accepted only if it maps to player index >= 0.
local names = {
    "alex", "Alex", "player", "Player",
    "ALEX_DEFAULT", "DriverPlayer", "NIS_Player"
}
local finders = { "go_FindGOHByName", "go_FindTransientGOHByName" }




if verified == nil then
    for _, finder_name in ipairs(finders) do
        local finder = _G[finder_name]
        if type(finder) == "function" then
            for _, name in ipairs(names) do
                local ok_find, h = try(finder_name .. ":" .. name, function() return finder(name) end)
                if ok_find and h ~= nil then
                    local ok_handle, idx = probe_handle(finder_name .. ":" .. name, h)
                    if ok_handle then
                        local accept = false
                        if hasfn("online_DeterminePlayerIndex") then
                            accept = (type(idx) == "number" and idx >= 0)
                        else
                            -- Without the discriminator, log only; do not auto-verify a guessed name.
                            accept = false
                        end
                        if accept then
                            verified = h
                            log("VERIFIED PLAYER SOURCE=" .. finder_name .. ":" .. name)
                            break
                        end
                    end
                end
            end
        end
        if verified ~= nil then break end
    end
end




if verified ~= nil then
    HOMELANDER_PLAYER = verified
    log("HOMELANDER_PLAYER SET TO VERIFIED HANDLE (Lua global only; no gameplay mutation)")
else
    log("NO VERIFIED PLAYER HANDLE — HOMELANDER_PLAYER not changed")
end




log("END — NO GAMEPLAY STATE WAS INTENTIONALLY MODIFIED")