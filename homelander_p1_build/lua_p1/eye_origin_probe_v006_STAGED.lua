-- Homelander P1 Eye Origin Probe v0.6
-- READ-ONLY / STAGED. Explicit F11 only.
-- Verifies the concrete EYEPOINT semantic on the current HOMELANDER_PLAYER.
-- No render, damage, VFX, velocity, physics, or target mutation.

local PREFIX = "[HOMELANDER_P1_EYE_ORIGIN_V006] "

local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end

local function valid_goh(h)
    if h == nil then return false end
    if type(go_IsValid) == "function" then
        local ok, v = pcall(go_IsValid, h)
        if not ok or not v then return false end
    end
    return true
end

function Homelander_EyeOriginProbeV006()
    log("BEGIN — READ ONLY")
    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        log("ABORT: HOMELANDER_PLAYER missing/invalid; run F4 first")
        return false
    end
    if type(go_GetJointPosition) ~= "function" then
        log("ABORT: go_GetJointPosition unavailable")
        return false
    end

    local okEye, eyePos = pcall(go_GetJointPosition, player, "EYEPOINT")
    if not okEye or eyePos == nil then
        log("ABORT: EYEPOINT did not resolve")
        return false
    end

    local playerPos = nil
    if type(go_GetPosition) == "function" then
        local okP, p = pcall(go_GetPosition, player)
        if okP then playerPos = p end
    end

    if playerPos ~= nil then
        local okD, d = pcall(function() return (eyePos - playerPos):magnitude() end)
        if okD then log("EYEPOINT distanceFromPlayerOrigin=" .. tostring(d)) end
    end

    HOMELANDER_EYE_ORIGIN_NAME = "EYEPOINT"
    HOMELANDER_EYE_ORIGIN = eyePos
    HOMELANDER_EYE_ORIGIN_VERIFIED = true
    HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER = player
    log("PASS: EYEPOINT resolved | pos=" .. tostring(eyePos))
    log("END — READ ONLY")
    return true
end

log("LOADED — v006 read-only EYEPOINT probe; explicit F11 only")
