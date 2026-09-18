-- Homelander P1 Heat Vision Acquisition Probe v0.1
-- READ-ONLY. No damage, effect, shooting, target mutation, or physics mutation.
-- Purpose: prove target acquisition + aim point + LOS before any heat-vision setter/damage call.


local PREFIX = "[HOMELANDER_P1_HEATVISION_PROBE_V0_1] "


local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end


local function hasfn(name) return type(_G[name]) == "function" end


local function safe(label, fn)
    local ok, a = pcall(fn)
    if ok then
        log(label .. " OK | " .. tostring(a))
        return true, a
    end
    log(label .. " ERROR | " .. tostring(a))
    return false, nil
end


local function valid_goh(h)
    if h == nil then return false end
    if hasfn("go_IsValid") then
        local ok, v = pcall(go_IsValid, h)
        if not ok or not v then return false end
    end
    return true
end


local function candidate(label, getter, player)
    if type(getter) ~= "function" then
        log(label .. " unavailable")
        return nil
    end


    local ok, h = pcall(getter, player)
    if not ok then
        log(label .. " ERROR | " .. tostring(h))
        return nil
    end


    log(label .. " raw=" .. tostring(h))
    if not valid_goh(h) then
        log(label .. " invalid/nil")
        return nil
    end


    if h == player then
        log(label .. " rejected: target equals player")
        return nil
    end


    return h
end


function Homelander_HeatVisionAcquisitionProbe()
    log("BEGIN")


    local player = HOMELANDER_PLAYER
    if player == nil then
        log("ABORT: HOMELANDER_PLAYER not verified")
        return false
    end


    if hasfn("online_DeterminePlayerIndex") then
        local ok, idx = pcall(online_DeterminePlayerIndex, player)
        if not ok or type(idx) ~= "number" or idx < 0 then
            log("ABORT: player handle no longer verifies | " .. tostring(idx))
            return false
        end
    end


    local target = candidate("ai_GetTarget", _G.ai_GetTarget, player)
    if target == nil then target = candidate("ai_GetFixedTarget", _G.ai_GetFixedTarget, player) end
    if target == nil then target = candidate("ai_GetTemporaryTarget", _G.ai_GetTemporaryTarget, player) end


    if target == nil then
        log("NO TARGET — acquire/lock an in-game target and rerun probe")
        return false
    end


    log("TARGET VERIFIED | " .. tostring(target))


    if hasfn("go_GetDebugName") then
        safe("target debug name", function() return go_GetDebugName(target) end)
    end
    if hasfn("go_GetHealth") then
        safe("target health", function() return go_GetHealth(target) end)
    end


    local target_point = nil
    if hasfn("ai_GetRangedTargetPoint") then
        local ok, p = safe("target ranged point", function() return ai_GetRangedTargetPoint(target) end)
        if ok then target_point = p end
    end


    if target_point == nil and hasfn("go_GetPosition") then
        local ok, p = safe("target fallback position", function() return go_GetPosition(target) end)
        if ok then target_point = p end
    end


    if target_point == nil then
        log("ABORT: no target point")
        return false
    end


    if hasfn("ai_HasLineOfSight") then
        safe("player LOS to target point", function()
            return ai_HasLineOfSight(player, target_point)
        end)
    end


    if hasfn("cm_CheckLineOfSight") then
        -- Signature remains under static investigation; do NOT guess-call it yet.
        log("cm_CheckLineOfSight present; intentionally not called until ABI is fully proven")
    end


    HOMELANDER_HEATVISION_TARGET = target
    HOMELANDER_HEATVISION_TARGET_POINT = target_point
    log("stored target/point as Lua globals only; gameplay state unchanged")
    log("END — READ ONLY")
    return true
end


log("LOADED — read-only; explicit call required.")