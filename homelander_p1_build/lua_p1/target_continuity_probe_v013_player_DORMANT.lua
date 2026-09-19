-- Homelander P1 Target Continuity / Health Telemetry Gate v0.13
-- DORMANT / READ-ONLY. Explicit F19 toggle only.
-- Requires the v011/F18 submission chain but does not mutate gameplay.

local PREFIX = "[HOMELANDER_P1_CONTINUITY_V013] "
local S = {
    enabled = false,
    target = nil,
    player = nil,
    generation = 0,
    elapsed = 0.0,
    consecutive = 0.0,
    max_consecutive = 0.0,
    ticks = 0,
    same_samples = 0,
    consecutive_samples = 0,
    max_consecutive_samples = 0,
    misses = 0,
    other_hits = 0,
    breaks = 0,
    baseline_health = nil,
    last_health = nil,
    max_health = nil
}

HOMELANDER_TARGET_CONTINUITY_PASSED = false
HOMELANDER_TARGET_CONTINUITY_TARGET = nil
HOMELANDER_TARGET_CONTINUITY_PLAYER = nil
HOMELANDER_TARGET_CONTINUITY_SECONDS = nil
HOMELANDER_TARGET_CONTINUITY_SAMPLES = nil
HOMELANDER_TARGET_CONTINUITY_BASELINE_HEALTH = nil
HOMELANDER_TARGET_CONTINUITY_LAST_HEALTH = nil
HOMELANDER_TARGET_CONTINUITY_MAX_HEALTH = nil

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
    if not finite_number(mag) or mag <= 0.0001 then return nil end
    return c
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

local function read_health(target)
    local okH, h = pcall(go_GetHealth, target)
    local okM, m = pcall(go_GetMaxHealth, target)
    if not okH or not okM or not finite_number(h) or not finite_number(m) then
        return nil, nil
    end
    return h, m
end

local function required_api_ok()
    return type(Vector) == "function"
       and type(HL_GetCameraFrame) == "function"
       and type(HL_LastRayHitGOH) == "function"
       and type(cm_GetCurrentRenderCameraPosition) == "function"
       and type(go_GetPosition) == "function"
       and type(go_GetHealth) == "function"
       and type(go_GetMaxHealth) == "function"
       and type(time_GetSimulationDelta) == "function"
       and type(fre_LineOfSightTest) == "function"
end

local function disable(reason)
    local was = S.enabled
    S.enabled = false
    S.generation = S.generation + 1
    if was then
        HOMELANDER_TARGET_CONTINUITY_PASSED = false
        HOMELANDER_TARGET_CONTINUITY_TARGET = nil
        HOMELANDER_TARGET_CONTINUITY_PLAYER = nil
    end
    if was then
        log("DISABLED" .. (reason and (" | " .. tostring(reason)) or ""))
    end
    return true
end

local function reset_continuity()
    if S.consecutive > 0.0 or S.consecutive_samples > 0 then
        S.breaks = S.breaks + 1
    end
    S.consecutive = 0.0
    S.consecutive_samples = 0
end

function Homelander_TargetContinuityToggleV013()
    if S.enabled then
        return disable("manual F19 toggle")
    end

    -- Starting a new F19 observation invalidates any previous F19->F20 proof,
    -- including when the new attempt fails before the health getter.
    HOMELANDER_TARGET_CONTINUITY_PASSED = false
    HOMELANDER_TARGET_CONTINUITY_TARGET = nil
    HOMELANDER_TARGET_CONTINUITY_PLAYER = nil

    if HOMELANDER_IMPACT_VFX_SUBMITTED ~= true then
        log("REFUSED: v011/F18 impact submission token missing")
        return false
    end
    if not required_api_ok() then
        log("REFUSED: required read-only telemetry API unavailable")
        return false
    end

    local player = HOMELANDER_PLAYER
    local target = HOMELANDER_DAMAGE_LAST_TARGET
    if not valid_goh(player) or not valid_goh(target) or target == player then
        log("REFUSED: player/target state invalid or target is player")
        return false
    end

    if HOMELANDER_DAMAGE_LAST_PLAYER ~= player then
        log("REFUSED: original F17 was submitted by another player")
        return false
    end
    local h, m = read_health(target)
    if h == nil then
        log("REFUSED: target health/max-health read failed")
        return false
    end
    if HOMELANDER_PLAYER ~= player or HOMELANDER_DAMAGE_LAST_PLAYER ~= player or
       HOMELANDER_DAMAGE_LAST_TARGET ~= target or
       HOMELANDER_IMPACT_VFX_SUBMITTED ~= true then
        log("REFUSED: player/F17/F18 source changed during F19 health callbacks")
        return false
    end

    HOMELANDER_TARGET_CONTINUITY_PASSED = false
    HOMELANDER_TARGET_CONTINUITY_TARGET = nil
    HOMELANDER_TARGET_CONTINUITY_SECONDS = nil
    HOMELANDER_TARGET_CONTINUITY_SAMPLES = nil
    HOMELANDER_TARGET_CONTINUITY_BASELINE_HEALTH = h
    HOMELANDER_TARGET_CONTINUITY_LAST_HEALTH = h
    HOMELANDER_TARGET_CONTINUITY_MAX_HEALTH = m

    S.enabled = true
    S.generation = S.generation + 1
    S.player = player
    S.target = target
    S.elapsed = 0.0
    S.consecutive = 0.0
    S.max_consecutive = 0.0
    S.ticks = 0
    S.same_samples = 0
    S.consecutive_samples = 0
    S.max_consecutive_samples = 0
    S.misses = 0
    S.other_hits = 0
    S.breaks = 0
    S.baseline_health = h
    if not current_player() then
        disable("player/source changed during F19 health callbacks")
        return false
    end
    S.last_health = h
    S.max_health = m

    log("ENABLED — read-only target continuity/health telemetry | baselineHealth=" ..
        tostring(h) .. " maxHealth=" .. tostring(m))
    return true
end

function Homelander_TargetContinuityForceDisableV013()
    return disable("focus lost / bootstrap / explicit safety stop")
end

function Homelander_TargetContinuityTickV013()
    if not S.enabled then return false end
    local tick_generation = S.generation
    local function current_player()
        return S.enabled and S.generation == tick_generation
           and HOMELANDER_PLAYER == S.player
           and HOMELANDER_DAMAGE_LAST_PLAYER == S.player
           and HOMELANDER_DAMAGE_LAST_TARGET == S.target
           and HOMELANDER_IMPACT_VFX_SUBMITTED == true
    end
    if not current_player() then
        disable("current player/F17/F18 lineage replaced since F19 enabled")
        return false
    end

    S.ticks = S.ticks + 1

    if not valid_goh(S.target) or S.target == HOMELANDER_PLAYER then
        disable("original F17 target became invalid/stale")
        return false
    end

    local okDt, dt = pcall(time_GetSimulationDelta)
    if not okDt or not finite_number(dt) or dt < 0.0 or dt > 0.25 then
        disable("simulation delta invalid/outside 0..0.25 s | " .. tostring(dt))
        return false
    end

    local h, m = read_health(S.target)
    if h == nil then
        disable("target health telemetry failed")
        return false
    end
    S.last_health = h
    S.max_health = m
    HOMELANDER_TARGET_CONTINUITY_LAST_HEALTH = h
    HOMELANDER_TARGET_CONTINUITY_MAX_HEALTH = m

    if dt == 0.0 then
        return true
    end
    S.elapsed = S.elapsed + dt

    local okCam, camPos = pcall(cm_GetCurrentRenderCameraPosition)
    if not okCam or camPos == nil then
        disable("render-camera getter failed")
        return false
    end

    local okFrame, rawFrame = pcall(HL_GetCameraFrame)
    if not okFrame then
        disable("HL_GetCameraFrame failed")
        return false
    end
    local frame = parse_frame(rawFrame)
    if frame == nil then
        disable("camera frame invalid")
        return false
    end

    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        disable("player invalid")
        return false
    end
    local okP, playerPos = pcall(go_GetPosition, player)
    if not okP or playerPos == nil then
        disable("player position unavailable")
        return false
    end

    local start, forward = select_view_axis(frame, playerPos)
    if start == nil or forward == nil then
        disable("camera forward resolution failed")
        return false
    end

    local range = tonumber(HOMELANDER_CONTINUITY_RANGE) or 500.0
    if not finite_number(range) then
        disable("range non-finite")
        return false
    end
    if range < 10.0 then range = 10.0 end
    if range > 1000.0 then range = 1000.0 end
    local rayEnd = start + forward * range

    local okLOS, hit = pcall(fre_LineOfSightTest, start, rayEnd, true, player)
    if not okLOS then
        disable("fre_LineOfSightTest error")
        return false
    end

    local same = false
    if hit then
        local okGOH, candidate = pcall(HL_LastRayHitGOH)
        if okGOH and valid_goh(candidate) and candidate == S.target then
            same = true
        elseif okGOH and valid_goh(candidate) then
            S.other_hits = S.other_hits + 1
        else
            S.misses = S.misses + 1
        end
    else
        S.misses = S.misses + 1
    end

    if not current_player() then
        disable("player/source changed during F19 camera/LOS/GOH callbacks")
        return false
    end

    if same then
        S.same_samples = S.same_samples + 1
        S.consecutive_samples = S.consecutive_samples + 1
        S.consecutive = S.consecutive + dt
        if S.consecutive > S.max_consecutive then
            S.max_consecutive = S.consecutive
        end
        if S.consecutive_samples > S.max_consecutive_samples then
            S.max_consecutive_samples = S.consecutive_samples
        end
    else
        reset_continuity()
    end

    local requiredSeconds = tonumber(HOMELANDER_CONTINUITY_REQUIRED_SECONDS) or 2.0
    if not finite_number(requiredSeconds) then requiredSeconds = 2.0 end
    if requiredSeconds < 1.0 then requiredSeconds = 1.0 end
    if requiredSeconds > 5.0 then requiredSeconds = 5.0 end

    local requiredSamples = tonumber(HOMELANDER_CONTINUITY_REQUIRED_SAMPLES) or 30
    if not finite_number(requiredSamples) then requiredSamples = 30 end
    requiredSamples = math.floor(requiredSamples)
    if requiredSamples < 15 then requiredSamples = 15 end
    if requiredSamples > 300 then requiredSamples = 300 end

    if S.consecutive >= requiredSeconds and S.consecutive_samples >= requiredSamples then
        if not current_player() then
            disable("player/source changed before F19 success")
            return false
        end
        HOMELANDER_TARGET_CONTINUITY_PLAYER = S.player
        HOMELANDER_TARGET_CONTINUITY_PASSED = true
        HOMELANDER_TARGET_CONTINUITY_TARGET = S.target
        HOMELANDER_TARGET_CONTINUITY_SECONDS = S.consecutive
        HOMELANDER_TARGET_CONTINUITY_SAMPLES = S.consecutive_samples
        HOMELANDER_TARGET_CONTINUITY_BASELINE_HEALTH = S.baseline_health
        HOMELANDER_TARGET_CONTINUITY_LAST_HEALTH = S.last_health
        HOMELANDER_TARGET_CONTINUITY_MAX_HEALTH = S.max_health
        log("PASS | sameTargetSeconds=" .. tostring(S.consecutive) ..
            " samples=" .. tostring(S.consecutive_samples) ..
            " health=" .. tostring(S.last_health) ..
            " maxHealth=" .. tostring(S.max_health) ..
            " breaks=" .. tostring(S.breaks))
        S.enabled = false
        return true
    end

    local maxElapsed = tonumber(HOMELANDER_CONTINUITY_MAX_SECONDS) or 12.0
    if not finite_number(maxElapsed) then maxElapsed = 12.0 end
    if maxElapsed < 3.0 then maxElapsed = 3.0 end
    if maxElapsed > 30.0 then maxElapsed = 30.0 end
    if S.elapsed >= maxElapsed then
        disable("timeout | maxConsecutive=" .. tostring(S.max_consecutive) ..
            " maxSamples=" .. tostring(S.max_consecutive_samples) ..
            " breaks=" .. tostring(S.breaks) ..
            " misses=" .. tostring(S.misses) ..
            " otherHits=" .. tostring(S.other_hits))
    end

    return true
end

function Homelander_TargetContinuityStatusV013()
    return S.enabled, S.elapsed, S.consecutive, S.same_samples,
           S.consecutive_samples, S.breaks, S.misses, S.other_hits,
           S.baseline_health, S.last_health, S.max_health
end

log("LOADED — v013 dormant F19 read-only target continuity/health telemetry")
