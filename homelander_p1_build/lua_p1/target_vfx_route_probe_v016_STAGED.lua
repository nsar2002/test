-- Homelander P1 Target Classification / VFX Route Gate v0.16
-- DORMANT / READ-ONLY. Explicit F22 one-shot only.
-- Classifies the exact F21 target and stores a future VFX route; NEVER spawns an effect.

local PREFIX = "[HOMELANDER_P1_TARGET_VFX_ROUTE_V016] "

HOMELANDER_TARGET_CLASSIFICATION_PASSED = false
HOMELANDER_TARGET_CLASSIFICATION_TARGET = nil
HOMELANDER_TARGET_CLASSIFICATION_DEBUG_NAME = nil
HOMELANDER_TARGET_CLASSIFICATION_CLASS_NAME = nil
HOMELANDER_TARGET_CLASSIFICATION_HELICOPTER = nil
HOMELANDER_TARGET_CLASSIFICATION_MILITARY = nil
HOMELANDER_TARGET_CLASSIFICATION_INFECTED = nil
HOMELANDER_TARGET_CLASSIFICATION_HEALTH = nil
HOMELANDER_TARGET_CLASSIFICATION_MAX_HEALTH = nil
HOMELANDER_VFX_ROUTE_KEY = nil
HOMELANDER_VFX_EFFECT_CANDIDATE = nil
HOMELANDER_VFX_ROUTE_RUNTIME_PROVEN = false

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

local function query_value(label, fn, target)
    if type(fn) ~= "function" then
        log(label .. " unavailable")
        return nil, false
    end
    local ok, value = pcall(fn, target)
    if not ok then
        log(label .. " ERROR | " .. tostring(value))
        return nil, false
    end
    log(label .. " OK | " .. tostring(value))
    return value, true
end

local function normalize_bool(v)
    if v == true then return true end
    if v == false then return false end
    return nil
end

function Homelander_TargetVFXRouteProbeV016()
    HOMELANDER_TARGET_CLASSIFICATION_PASSED = false
    HOMELANDER_TARGET_CLASSIFICATION_TARGET = nil
    HOMELANDER_TARGET_CLASSIFICATION_DEBUG_NAME = nil
    HOMELANDER_TARGET_CLASSIFICATION_CLASS_NAME = nil
    HOMELANDER_TARGET_CLASSIFICATION_HELICOPTER = nil
    HOMELANDER_TARGET_CLASSIFICATION_MILITARY = nil
    HOMELANDER_TARGET_CLASSIFICATION_INFECTED = nil
    HOMELANDER_TARGET_CLASSIFICATION_HEALTH = nil
    HOMELANDER_TARGET_CLASSIFICATION_MAX_HEALTH = nil
    HOMELANDER_VFX_ROUTE_KEY = nil
    HOMELANDER_VFX_EFFECT_CANDIDATE = nil
    HOMELANDER_VFX_ROUTE_RUNTIME_PROVEN = false

    if HOMELANDER_DAMAGEHIT_PAYLOAD_PASSED ~= true then
        log("REFUSED: F21 DamageAndHit payload proof missing")
        return false
    end

    local player = HOMELANDER_PLAYER
    local target = HOMELANDER_DAMAGEHIT_PAYLOAD_TARGET

    if not valid_goh(player) or not valid_goh(target) or target == player then
        log("REFUSED: player/target invalid")
        return false
    end

    if HOMELANDER_DOT_DRYRUN_TARGET ~= target or
       HOMELANDER_TARGET_CONTINUITY_TARGET ~= target or
       HOMELANDER_DAMAGE_LAST_TARGET ~= target then
        log("REFUSED: F21/F20/F19/F17 target identity mismatch")
        return false
    end

    local debugName = nil
    local className = nil
    local helicopter = nil
    local military = nil
    local infected = nil

    do
        local v = query_value("go_GetDebugName", _G.go_GetDebugName, target)
        if v ~= nil then debugName = tostring(v) end
    end
    do
        local v = query_value("ai_GetClassName", _G.ai_GetClassName, target)
        if v ~= nil then className = tostring(v) end
    end
    do
        local v = query_value("go_IsHelicopter", _G.go_IsHelicopter, target)
        helicopter = normalize_bool(v)
    end
    do
        local v = query_value("go_IsFactionMilitary", _G.go_IsFactionMilitary, target)
        military = normalize_bool(v)
    end
    do
        local v = query_value("go_IsFactionInfected", _G.go_IsFactionInfected, target)
        infected = normalize_bool(v)
    end

    if type(go_GetHealth) ~= "function" or type(go_GetMaxHealth) ~= "function" then
        log("REFUSED: health telemetry APIs unavailable")
        return false
    end

    local okH, health = pcall(go_GetHealth, target)
    local okM, maxHealth = pcall(go_GetMaxHealth, target)
    if not okH or not okM or not finite_number(health) or not finite_number(maxHealth) then
        log("REFUSED: health telemetry failed")
        return false
    end

    local route = "GENERIC"
    local candidate = "missileImpact001"

    if helicopter == true then
        route = "HELICOPTER_METAL"
        candidate = "debrisSparks001"
    elseif infected == true then
        route = "INFECTED_ORGANIC_UNRESOLVED"
        candidate = "missileImpact001"
    elseif military == true then
        route = "MILITARY_UNRESOLVED"
        candidate = "missileImpact001"
    end

    HOMELANDER_TARGET_CLASSIFICATION_TARGET = target
    HOMELANDER_TARGET_CLASSIFICATION_DEBUG_NAME = debugName
    HOMELANDER_TARGET_CLASSIFICATION_CLASS_NAME = className
    HOMELANDER_TARGET_CLASSIFICATION_HELICOPTER = helicopter
    HOMELANDER_TARGET_CLASSIFICATION_MILITARY = military
    HOMELANDER_TARGET_CLASSIFICATION_INFECTED = infected
    HOMELANDER_TARGET_CLASSIFICATION_HEALTH = health
    HOMELANDER_TARGET_CLASSIFICATION_MAX_HEALTH = maxHealth
    HOMELANDER_VFX_ROUTE_KEY = route
    HOMELANDER_VFX_EFFECT_CANDIDATE = candidate
    HOMELANDER_VFX_ROUTE_RUNTIME_PROVEN = false
    HOMELANDER_TARGET_CLASSIFICATION_PASSED = true

    log("PASS READ ONLY | route=" .. route ..
        " candidate=" .. candidate ..
        " runtimeProven=false" ..
        " class=" .. tostring(className) ..
        " helicopter=" .. tostring(helicopter) ..
        " military=" .. tostring(military) ..
        " infected=" .. tostring(infected) ..
        " health=" .. tostring(health) .. "/" .. tostring(maxHealth))
    return true
end

log("LOADED — v016 dormant F22 READ-ONLY target classification/VFX route probe")
