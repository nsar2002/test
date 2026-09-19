-- Homelander P1 Damage+Hit Payload Dry-Run Gate v0.15
-- DORMANT / READ-ONLY. Explicit F21 one-shot only.
-- Builds hitPosition + incoming hitDirection payload but NEVER calls damage APIs.

local PREFIX = "[HOMELANDER_P1_DAMAGEHIT_PAYLOAD_V015] "

HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED = false
HOMELANDER_DAMAGEHIT_PAYLOAD_TARGET = nil
HOMELANDER_DAMAGEHIT_PAYLOAD_SOURCE = nil
HOMELANDER_DAMAGEHIT_PAYLOAD_HIT_POS = nil
HOMELANDER_DAMAGEHIT_PAYLOAD_DIRECTION = nil
HOMELANDER_DAMAGEHIT_PAYLOAD_DISTANCE = nil
HOMELANDER_DAMAGEHIT_PAYLOAD_HEALTH = nil
HOMELANDER_DAMAGEHIT_PAYLOAD_MAX_HEALTH = nil

local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end

local function finite_number(v)
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end

local function valid_goh(h)
    if h == nil then return false end
    if type(go_IsValid) == "function" then
        local ok, v = pcall(go_IsValid, h)
        if not ok or not v then return false end
    end
    return true
end

local function normalized(v)
    local c = Vector(v)
    local mag = c:normalize()
    if not finite_number(mag) or mag <= 0.0001 then return nil, mag end
    return c, mag
end

local function parse_frame(raw)
    if type(raw) ~= "string" or raw == "" then return nil end
    local values = {}
    for token in string.gmatch(raw, "[^,]+") do
        local n = tonumber(token)
        if not finite_number(n) then return nil end
        values[#values + 1] = n
    end
    if #values ~= 12 then return nil end
    return values
end

local function select_view_axis(frame, player_pos)
    local camera_pos = Vector(frame[1], frame[2], frame[3])
    local to_player = normalized(player_pos - camera_pos)
    if to_player == nil then return nil, nil end

    local axes = {
        Vector(frame[4], frame[5], frame[6]),
        Vector(frame[7], frame[8], frame[9]),
        Vector(frame[10], frame[11], frame[12])
    }

    local best_axis = nil
    local best_score = -1.0
    local signed_dot = nil
    for i = 1, 3 do
        local axis = normalized(axes[i])
        if axis == nil then return nil, nil end
        local d = axis:dot(to_player)
        if not finite_number(d) then return nil, nil end
        local score = math.abs(d)
        if score > best_score then
            best_score = score
            best_axis = axis
            signed_dot = d
        end
    end
    if best_axis == nil then return nil, nil end
    if signed_dot < 0.0 then best_axis = best_axis * -1.0 end
    return camera_pos, best_axis
end

local function vector_components(v)
    if v == nil or type(Vector) ~= "function" then return nil end
    local ex = Vector(1, 0, 0)
    local ey = Vector(0, 1, 0)
    local ez = Vector(0, 0, 1)
    local okx, x = pcall(function() return v:dot(ex) end)
    local oky, y = pcall(function() return v:dot(ey) end)
    local okz, z = pcall(function() return v:dot(ez) end)
    if not okx or not oky or not okz or
       not finite_number(x) or not finite_number(y) or not finite_number(z) then
        return nil
    end
    return x, y, z
end

local function required_api_ok()
    return type(Vector) == "function"
       and type(HL_GetCameraFrame) == "function"
       and type(HL_LastRayHitGOH) == "function"
       and type(cm_GetCurrentRenderCameraPosition) == "function"
       and type(go_GetPosition) == "function"
       and type(go_GetJointPosition) == "function"
       and type(go_GetHealth) == "function"
       and type(go_GetMaxHealth) == "function"
       and type(fre_LineOfSightTest) == "function"
end

function Homelander_DamageHitPayloadProbeV015()
    HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED = false
    HOMELANDER_DAMAGEHIT_PAYLOAD_TARGET = nil
    HOMELANDER_DAMAGEHIT_PAYLOAD_SOURCE = nil
    HOMELANDER_DAMAGEHIT_PAYLOAD_HIT_POS = nil
    HOMELANDER_DAMAGEHIT_PAYLOAD_DIRECTION = nil
    HOMELANDER_DAMAGEHIT_PAYLOAD_DISTANCE = nil
    HOMELANDER_DAMAGEHIT_PAYLOAD_HEALTH = nil
    HOMELANDER_DAMAGEHIT_PAYLOAD_MAX_HEALTH = nil

    if HOMELANDER_DOT_DRYRUN_PASSED ~= true then
        log("REFUSED: F20 DOT dry-run proof missing")
        return false
    end
    if not required_api_ok() then
        log("REFUSED: required read-only payload API unavailable")
        return false
    end

    local player = HOMELANDER_PLAYER
    local target = HOMELANDER_DOT_DRYRUN_TARGET
    if not valid_goh(player) or not valid_goh(target) or target == player then
        log("REFUSED: player/target invalid")
        return false
    end
    if HOMELANDER_TARGET_CONTINUITY_TARGET ~= target or
       HOMELANDER_DAMAGE_LAST_TARGET ~= target then
        log("REFUSED: F20/F19/F17 target identity mismatch")
        return false
    end
    if HOMELANDER_EYE_ORIGIN_VERIFIED ~= true or
       HOMELANDER_EYE_ORIGIN_NAME ~= "EYEPOINT" or
       HOMELANDER_EYE_ORIGIN_VERIFIED_PLAYER ~= player then
        log("REFUSED: F11 EYEPOINT proof missing/stale")
        return false
    end

    local okCam, camPos = pcall(cm_GetCurrentRenderCameraPosition)
    if not okCam or camPos == nil then
        log("REFUSED: render-camera getter failed")
        return false
    end
    local okFrame, rawFrame = pcall(HL_GetCameraFrame)
    if not okFrame then
        log("REFUSED: HL_GetCameraFrame failed")
        return false
    end
    local frame = parse_frame(rawFrame)
    if frame == nil then
        log("REFUSED: camera frame invalid")
        return false
    end

    local okP, playerPos = pcall(go_GetPosition, player)
    if not okP or playerPos == nil then
        log("REFUSED: player position unavailable")
        return false
    end
    local start, forward = select_view_axis(frame, playerPos)
    if start == nil or forward == nil then
        log("REFUSED: camera forward resolution failed")
        return false
    end

    local range = tonumber(HOMELANDER_DAMAGEHIT_DRYRUN_RANGE) or 500.0
    if not finite_number(range) then
        log("REFUSED: range non-finite")
        return false
    end
    if range < 10.0 then range = 10.0 end
    if range > 1000.0 then range = 1000.0 end
    local rayEnd = start + forward * range

    local okLOS, hit, fraction, hitPos, hitNormal =
        pcall(fre_LineOfSightTest, start, rayEnd, true, player)
    if not okLOS or not hit or hitPos == nil then
        log("REFUSED: fresh LOS did not produce a hit position")
        return false
    end

    local okGOH, candidate = pcall(HL_LastRayHitGOH)
    if not okGOH or not valid_goh(candidate) or candidate ~= target then
        log("REFUSED: fresh LOS target != F20-proven target")
        return false
    end

    local okEye, eyePos = pcall(go_GetJointPosition, player, "EYEPOINT")
    if not okEye or eyePos == nil then
        log("REFUSED: fresh EYEPOINT lookup failed")
        return false
    end

    local hx, hy, hz = vector_components(hitPos)
    local ex, ey, ez = vector_components(eyePos)
    if hx == nil or ex == nil then
        log("REFUSED: non-finite source/hit position")
        return false
    end

    local direction, distance = normalized(hitPos - eyePos)
    if direction == nil or not finite_number(distance) or distance <= 0.001 then
        log("REFUSED: source-to-hit direction degenerate")
        return false
    end

    local dx, dy, dz = vector_components(direction)
    if dx == nil then
        log("REFUSED: normalized hit direction non-finite")
        return false
    end

    local okH, health = pcall(go_GetHealth, target)
    local okM, maxHealth = pcall(go_GetMaxHealth, target)
    if not okH or not okM or not finite_number(health) or not finite_number(maxHealth) then
        log("REFUSED: health telemetry failed")
        return false
    end

    HOMELANDER_DAMAGEHIT_PAYLOAD_TARGET = target
    HOMELANDER_DAMAGEHIT_PAYLOAD_SOURCE = eyePos
    HOMELANDER_DAMAGEHIT_PAYLOAD_HIT_POS = hitPos
    HOMELANDER_DAMAGEHIT_PAYLOAD_DIRECTION = direction
    HOMELANDER_DAMAGEHIT_PAYLOAD_DISTANCE = distance
    HOMELANDER_DAMAGEHIT_PAYLOAD_HEALTH = health
    HOMELANDER_DAMAGEHIT_PAYLOAD_MAX_HEALTH = maxHealth
    HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED = true

    log("PASS READ ONLY | target stable | distance=" .. tostring(distance) ..
        " hit=(" .. tostring(hx) .. "," .. tostring(hy) .. "," .. tostring(hz) .. ")" ..
        " dir=(" .. tostring(dx) .. "," .. tostring(dy) .. "," .. tostring(dz) .. ")" ..
        " health=" .. tostring(health) .. "/" .. tostring(maxHealth))
    return true
end

log("LOADED — v015 dormant F21 READ-ONLY DamageAndHit payload probe")
