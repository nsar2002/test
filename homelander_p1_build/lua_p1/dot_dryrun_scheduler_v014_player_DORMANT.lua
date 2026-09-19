-- Homelander P1 DOT Cadence Dry-Run Gate v0.14
-- DORMANT / READ-ONLY. Explicit F20 toggle only.
-- Emits diagnostic WOULD_DAMAGE schedule events; NEVER calls a damage API.

local PREFIX = "[HOMELANDER_P1_DOT_DRYRUN_V014] "
local INTERVAL = 0.10
local REQUIRED_SECONDS = 3.0
local REQUIRED_EVENTS = 10
local MAX_TOTAL_SECONDS = 15.0

local S = {
    enabled = false,
    target = nil,
    player = nil,
    generation = 0,
    total_elapsed = 0.0,
    segment_elapsed = 0.0,
    accumulator = 0.0,
    segment_events = 0,
    total_events = 0,
    breaks = 0,
    misses = 0,
    other_hits = 0,
    last_event_at = nil,
    min_event_gap = nil,
    spacing_violations = 0,
    last_health = nil,
    max_health = nil
}

HOMELANDER_DOT_DRYRUN_PASSED = false
HOMELANDER_DOT_DRYRUN_TARGET = nil
HOMELANDER_DOT_DRYRUN_PLAYER = nil
HOMELANDER_DOT_DRYRUN_INTERVAL = nil
HOMELANDER_DOT_DRYRUN_SECONDS = nil
HOMELANDER_DOT_DRYRUN_EVENTS = nil
HOMELANDER_DOT_DRYRUN_MIN_GAP = nil
HOMELANDER_DOT_DRYRUN_LAST_HEALTH = nil
HOMELANDER_DOT_DRYRUN_MAX_HEALTH = nil

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
        HOMELANDER_DOT_DRYRUN_PASSED = false
        HOMELANDER_DOT_DRYRUN_TARGET = nil
        HOMELANDER_DOT_DRYRUN_PLAYER = nil
    end
    if was then
        log("DISABLED" .. (reason and (" | " .. tostring(reason)) or ""))
    end
    return true
end

local function reset_segment(reason)
    if S.segment_elapsed > 0.0 or S.segment_events > 0 then
        S.breaks = S.breaks + 1
        log("LOCK BREAK | " .. tostring(reason) ..
            " segmentSeconds=" .. tostring(S.segment_elapsed) ..
            " segmentEvents=" .. tostring(S.segment_events))
    end
    S.segment_elapsed = 0.0
    S.accumulator = 0.0
    S.segment_events = 0
    S.last_event_at = nil
    S.min_event_gap = nil
    S.spacing_violations = 0
end

function Homelander_DOTDryRunToggleV014()
    if S.enabled then
        return disable("manual F20 toggle")
    end

    -- A new F20 observation must never inherit success from a prior run.
    HOMELANDER_DOT_DRYRUN_PASSED = false
    HOMELANDER_DOT_DRYRUN_TARGET = nil
    HOMELANDER_DOT_DRYRUN_PLAYER = nil

    if HOMELANDER_TARGET_CONTINUITY_PASSED ~= true then
        log("REFUSED: F19 target-continuity proof missing")
        return false
    end
    if HOMELANDER_IMPACT_VFX_SUBMITTED ~= true then
        log("REFUSED: v011/F18 impact submission token missing")
        return false
    end
    if not required_api_ok() then
        log("REFUSED: required read-only scheduler API unavailable")
        return false
    end

    local player = HOMELANDER_PLAYER
    local target = HOMELANDER_TARGET_CONTINUITY_TARGET
    if not valid_goh(player) or not valid_goh(target) or target == player then
        log("REFUSED: player/continuity target invalid")
        return false
    end
    if HOMELANDER_DAMAGE_LAST_TARGET ~= target then
        log("REFUSED: F19 target no longer equals original F17 target")
        return false
    end
    if HOMELANDER_TARGET_CONTINUITY_PLAYER ~= player or
       HOMELANDER_DAMAGE_LAST_PLAYER ~= player then
        log("REFUSED: F20 player differs from F19/F17 originating player")
        return false
    end

    local h, m = read_health(target)
    if h == nil then
        log("REFUSED: health telemetry unavailable")
        return false
    end
    if HOMELANDER_PLAYER ~= player or
       HOMELANDER_TARGET_CONTINUITY_PLAYER ~= player or
       HOMELANDER_DAMAGE_LAST_PLAYER ~= player or
       HOMELANDER_IMPACT_VFX_SUBMITTED ~= true then
        log("REFUSED: player/F17/F19/F18 changed during dry-run health getter")
        return false
    end

    HOMELANDER_DOT_DRYRUN_PASSED = false
    HOMELANDER_DOT_DRYRUN_TARGET = nil
    HOMELANDER_DOT_DRYRUN_INTERVAL = INTERVAL
    HOMELANDER_DOT_DRYRUN_SECONDS = nil
    HOMELANDER_DOT_DRYRUN_EVENTS = nil
    HOMELANDER_DOT_DRYRUN_MIN_GAP = nil
    HOMELANDER_DOT_DRYRUN_LAST_HEALTH = h
    HOMELANDER_DOT_DRYRUN_MAX_HEALTH = m

    S.enabled = true
    S.generation = S.generation + 1
    S.player = player
    S.target = target
    S.total_elapsed = 0.0
    S.segment_elapsed = 0.0
    S.accumulator = 0.0
    S.segment_events = 0
    S.total_events = 0
    S.breaks = 0
    S.misses = 0
    S.other_hits = 0
    S.last_event_at = nil
    S.min_event_gap = nil
    S.spacing_violations = 0
    S.last_health = h
    S.max_health = m

    log("ENABLED — READ ONLY | interval=" .. tostring(INTERVAL) ..
        "s, no catch-up, no damage API")
    return true
end

function Homelander_DOTDryRunForceDisableV014()
    return disable("focus lost / bootstrap / explicit safety stop")
end

function Homelander_DOTDryRunTickV014()
    if not S.enabled then return false end
    local tick_generation = S.generation
    local function current_owner()
        return S.enabled and S.generation == tick_generation
            and HOMELANDER_PLAYER == S.player
            and HOMELANDER_TARGET_CONTINUITY_PLAYER == S.player
            and HOMELANDER_DAMAGE_LAST_PLAYER == S.player
            and HOMELANDER_DAMAGE_LAST_TARGET == S.target
            and HOMELANDER_TARGET_CONTINUITY_TARGET == S.target
            and HOMELANDER_TARGET_CONTINUITY_PASSED == true
            and HOMELANDER_IMPACT_VFX_SUBMITTED == true
    end
    if not current_owner() then
        disable("originating F17/F19 player or proof no longer current")
        return false
    end

    if HOMELANDER_TARGET_CONTINUITY_PASSED ~= true or
       HOMELANDER_TARGET_CONTINUITY_TARGET ~= S.target or
       HOMELANDER_DAMAGE_LAST_TARGET ~= S.target then
        disable("upstream target proof invalidated")
        return false
    end
    if not valid_goh(S.target) or S.target == HOMELANDER_PLAYER then
        disable("stable target invalid/stale")
        return false
    end

    local okDt, dt = pcall(time_GetSimulationDelta)
    if not okDt or not finite_number(dt) or dt < 0.0 or dt > 0.25 then
        disable("simulation delta invalid/outside 0..0.25 s | " .. tostring(dt))
        return false
    end

    local h, m = read_health(S.target)
    if h == nil then
        disable("health telemetry failed")
        return false
    end
    if not current_owner() then
        disable("F20 player or source changed during health getters")
        return false
    end
    S.last_health = h
    S.max_health = m
    HOMELANDER_DOT_DRYRUN_LAST_HEALTH = h
    HOMELANDER_DOT_DRYRUN_MAX_HEALTH = m

    if dt == 0.0 then return true end
    S.total_elapsed = S.total_elapsed + dt

    local player = HOMELANDER_PLAYER
    if not valid_goh(player) then
        disable("player invalid")
        return false
    end

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

    local range = tonumber(HOMELANDER_DOT_DRYRUN_RANGE) or 500.0
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

    if not current_owner() then
        disable("F20 owner/source changed during camera/LOS/GOH callback")
        return false
    end

    if not same then
        reset_segment("fresh LOS target mismatch/miss")
        if S.total_elapsed >= MAX_TOTAL_SECONDS then
            disable("timeout without stable dry-run segment")
        end
        return true
    end

    S.segment_elapsed = S.segment_elapsed + dt
    S.accumulator = S.accumulator + dt

    -- Safety rule: at most one scheduler event per GOM tick.
    -- No while-loop catch-up and no backlog carry after an event.
    if S.accumulator >= INTERVAL then
        local eventAt = S.segment_elapsed
        if S.last_event_at ~= nil then
            local gap = eventAt - S.last_event_at
            if S.min_event_gap == nil or gap < S.min_event_gap then
                S.min_event_gap = gap
            end
            if gap + 0.000001 < INTERVAL then
                S.spacing_violations = S.spacing_violations + 1
            end
        end

        S.segment_events = S.segment_events + 1
        S.total_events = S.total_events + 1
        S.last_event_at = eventAt
        S.accumulator = 0.0

        log("WOULD_DAMAGE | segmentEvent=" .. tostring(S.segment_events) ..
            " t=" .. tostring(eventAt) ..
            " healthReadOnly=" .. tostring(S.last_health))
    end

    if S.segment_elapsed >= REQUIRED_SECONDS and
       S.segment_events >= REQUIRED_EVENTS and
       S.spacing_violations == 0 then
        if not current_owner() then
            disable("F20 owner/source replaced before dry-run success")
            return false
        end
        HOMELANDER_DOT_DRYRUN_PLAYER = S.player
        HOMELANDER_DOT_DRYRUN_PASSED = true
        HOMELANDER_DOT_DRYRUN_TARGET = S.target
        HOMELANDER_DOT_DRYRUN_INTERVAL = INTERVAL
        HOMELANDER_DOT_DRYRUN_SECONDS = S.segment_elapsed
        HOMELANDER_DOT_DRYRUN_EVENTS = S.segment_events
        HOMELANDER_DOT_DRYRUN_MIN_GAP = S.min_event_gap
        HOMELANDER_DOT_DRYRUN_LAST_HEALTH = S.last_health
        HOMELANDER_DOT_DRYRUN_MAX_HEALTH = S.max_health

        log("PASS | READ ONLY | seconds=" .. tostring(S.segment_elapsed) ..
            " events=" .. tostring(S.segment_events) ..
            " minGap=" .. tostring(S.min_event_gap) ..
            " breaks=" .. tostring(S.breaks))
        S.enabled = false
        return true
    end

    if S.total_elapsed >= MAX_TOTAL_SECONDS then
        disable("timeout | totalEvents=" .. tostring(S.total_events) ..
            " breaks=" .. tostring(S.breaks) ..
            " misses=" .. tostring(S.misses) ..
            " otherHits=" .. tostring(S.other_hits))
    end

    return true
end

function Homelander_DOTDryRunStatusV014()
    return S.enabled, S.total_elapsed, S.segment_elapsed, S.segment_events,
           S.total_events, S.breaks, S.misses, S.other_hits,
           S.min_event_gap, S.spacing_violations, S.last_health, S.max_health
end

log("LOADED — v014 dormant F20 READ-ONLY DOT cadence dry-run; WOULD_DAMAGE only")
