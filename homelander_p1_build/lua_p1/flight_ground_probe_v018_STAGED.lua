-- Homelander P1 Flight Ground Telemetry v0.18
-- READ-ONLY. Invoked from F4 in the staged Flight V2 branch.
-- Purpose: measure real standing/air ground-distance semantics before any landing threshold is used.

local PREFIX = "[HOMELANDER_P1_FLIGHT_GROUND_V018] "

local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end

local function valid_player(h)
    if h == nil then return false end
    if type(go_IsValid) == "function" then
        local ok, v = pcall(go_IsValid, h)
        if not ok or not v then return false end
    end
    if type(online_DeterminePlayerIndex) == "function" then
        local ok, idx = pcall(online_DeterminePlayerIndex, h)
        if not ok or type(idx) ~= "number" or idx < 0 then return false end
    end
    return true
end

local function finite(n)
    return type(n) == "number" and n == n and n ~= math.huge and n ~= -math.huge
end

function Homelander_FlightGroundProbeV018()
    HOMELANDER_FLIGHT_GROUND_PROBE_VALID = false
    HOMELANDER_FLIGHT_GROUND_HIT = false
    HOMELANDER_FLIGHT_GROUND_FRACTION = nil
    HOMELANDER_FLIGHT_GROUND_HIT_POS = nil
    HOMELANDER_FLIGHT_GROUND_HIT_NORMAL = nil
    HOMELANDER_FLIGHT_GROUND_PLAYER_DISTANCE = nil
    HOMELANDER_FLIGHT_GROUND_RAY_DISTANCE = nil
    HOMELANDER_FLIGHT_GROUND_HIT_GOH = nil

    local player = HOMELANDER_PLAYER
    if not valid_player(player) then
        log("ABORT: verified player missing")
        return false
    end
    if type(Vector) ~= "function" or type(go_GetPosition) ~= "function" or
       type(fre_LineOfSightTest) ~= "function" then
        log("ABORT: required read-only API unavailable")
        return false
    end

    local okPos, playerPos = pcall(go_GetPosition, player)
    if not okPos or playerPos == nil then
        log("ABORT: player position read failed | " .. tostring(playerPos))
        return false
    end

    local startUp = tonumber(HOMELANDER_FLIGHT_GROUND_START_UP) or 1.0
    local rayDown = tonumber(HOMELANDER_FLIGHT_GROUND_RAY_DOWN) or 8.0
    if not finite(startUp) then startUp = 1.0 end
    if not finite(rayDown) then rayDown = 8.0 end
    if startUp < 0.1 then startUp = 0.1 end
    if startUp > 3.0 then startUp = 3.0 end
    if rayDown < 2.0 then rayDown = 2.0 end
    if rayDown > 20.0 then rayDown = 20.0 end

    local up = Vector(0,1,0)
    local okRay, start, rayEnd = pcall(function()
        return playerPos + up * startUp, playerPos - up * rayDown
    end)
    if not okRay or start == nil or rayEnd == nil then
        log("ABORT: downward ray geometry invalid")
        return false
    end

    local ok, hit, fraction, hitPos, hitNormal =
        pcall(fre_LineOfSightTest, start, rayEnd, true, player)
    if not ok then
        log("ABORT: downward LOS error | " .. tostring(hit))
        return false
    end

    HOMELANDER_FLIGHT_GROUND_PROBE_VALID = true
    HOMELANDER_FLIGHT_GROUND_HIT = not not hit

    if not hit then
        log("MISS READ ONLY | startUp=" .. tostring(startUp) ..
            " rayDown=" .. tostring(rayDown) ..
            " playerPos=" .. tostring(playerPos))
        return true
    end

    if hitPos == nil then
        log("ABORT: ground hit without hit position")
        HOMELANDER_FLIGHT_GROUND_PROBE_VALID = false
        return false
    end
    local okDistance, playerDistance, rayDistance = pcall(function()
        return (playerPos - hitPos):magnitude(), (start - hitPos):magnitude()
    end)
    if not okDistance or not finite(playerDistance) or not finite(rayDistance) then
        log("ABORT: non-finite ground distance")
        HOMELANDER_FLIGHT_GROUND_PROBE_VALID = false
        return false
    end

    local hitGOH = nil
    if type(HL_LastRayHitGOH) == "function" then
        local okH, h = pcall(HL_LastRayHitGOH)
        if okH and h ~= player then hitGOH = h end
    end

    HOMELANDER_FLIGHT_GROUND_FRACTION = fraction
    HOMELANDER_FLIGHT_GROUND_HIT_POS = hitPos
    HOMELANDER_FLIGHT_GROUND_HIT_NORMAL = hitNormal
    HOMELANDER_FLIGHT_GROUND_PLAYER_DISTANCE = playerDistance
    HOMELANDER_FLIGHT_GROUND_RAY_DISTANCE = rayDistance
    HOMELANDER_FLIGHT_GROUND_HIT_GOH = hitGOH

    log("HIT READ ONLY | fraction=" .. tostring(fraction) ..
        " playerDistance=" .. tostring(playerDistance) ..
        " rayDistance=" .. tostring(rayDistance) ..
        " hitPos=" .. tostring(hitPos) ..
        " normal=" .. tostring(hitNormal) ..
        " hitGOH=" .. tostring(hitGOH))
    return true
end

log("LOADED — read-only downward ground telemetry; no landing threshold is assumed")
