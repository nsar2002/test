-- Homelander P1 Exact VFX Candidate Resolver Gate v0.17
-- DORMANT / READ-ONLY. Explicit F23 one-shot only.
-- Resolves exact startup_effects names but NEVER spawns an effect.

local PREFIX = "[HOMELANDER_P1_VFX_CANDIDATE_V017] "

HOMELANDER_VFX_CANDIDATE_PASSED = false
HOMELANDER_VFX_CANDIDATE_TARGET = nil
HOMELANDER_VFX_CANDIDATE_ROUTE = nil
HOMELANDER_VFX_CANDIDATE_PRIMARY = nil
HOMELANDER_VFX_CANDIDATE_SECONDARY = nil
HOMELANDER_VFX_CANDIDATE_FALLBACK = nil
HOMELANDER_VFX_CANDIDATE_STATIC_PROVEN = false
HOMELANDER_VFX_CANDIDATE_RUNTIME_PROVEN = false

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

local CATALOG = {
    missileImpact001 = true,
    squibMetal001 = true,
    debrisSparks001 = true,
    squibBlood001 = true,
    goreBloodMistFanOut001 = true
}

local ROUTES = {
    HELICOPTER_METAL = {
        primary = "squibMetal001",
        secondary = "debrisSparks001",
        fallback = "missileImpact001"
    },
    INFECTED_ORGANIC_UNRESOLVED = {
        primary = "squibBlood001",
        secondary = "goreBloodMistFanOut001",
        fallback = "missileImpact001"
    },
    MILITARY_UNRESOLVED = {
        primary = "missileImpact001",
        secondary = nil,
        fallback = "missileImpact001"
    },
    GENERIC = {
        primary = "missileImpact001",
        secondary = nil,
        fallback = "missileImpact001"
    }
}

local function catalog_ok(name)
    return type(name) == "string" and CATALOG[name] == true
end

function Homelander_VFXCandidateResolveV017()
    HOMELANDER_VFX_CANDIDATE_PASSED = false
    HOMELANDER_VFX_CANDIDATE_TARGET = nil
    HOMELANDER_VFX_CANDIDATE_ROUTE = nil
    HOMELANDER_VFX_CANDIDATE_PRIMARY = nil
    HOMELANDER_VFX_CANDIDATE_SECONDARY = nil
    HOMELANDER_VFX_CANDIDATE_FALLBACK = nil
    HOMELANDER_VFX_CANDIDATE_STATIC_PROVEN = false
    HOMELANDER_VFX_CANDIDATE_RUNTIME_PROVEN = false

    if HOMELANDER_TARGET_CLASSIFICATION_PASSED ~= true then
        log("REFUSED: F22 target classification proof missing")
        return false
    end

    local player = HOMELANDER_PLAYER
    local target = HOMELANDER_TARGET_CLASSIFICATION_TARGET
    if not valid_goh(player) or not valid_goh(target) or target == player then
        log("REFUSED: player/target invalid")
        return false
    end

    if HOMELANDER_DAMAGEHIT_PAYLOAD_TARGET ~= target or
       HOMELANDER_DOT_DRYRUN_TARGET ~= target or
       HOMELANDER_TARGET_CONTINUITY_TARGET ~= target or
       HOMELANDER_DAMAGE_LAST_TARGET ~= target then
        log("REFUSED: F22/F21/F20/F19/F17 target identity mismatch")
        return false
    end

    if HOMELANDER_VFX_ROUTE_RUNTIME_PROVEN ~= false then
        log("REFUSED: unexpected F22 runtime-proven state")
        return false
    end

    local route = HOMELANDER_VFX_ROUTE_KEY
    local spec = ROUTES[route]
    if spec == nil then
        log("REFUSED: unknown route " .. tostring(route))
        return false
    end

    if not catalog_ok(spec.primary) or not catalog_ok(spec.fallback) then
        log("REFUSED: primary/fallback not in static exact-name catalog")
        return false
    end
    if spec.secondary ~= nil and not catalog_ok(spec.secondary) then
        log("REFUSED: secondary not in static exact-name catalog")
        return false
    end

    HOMELANDER_VFX_CANDIDATE_TARGET = target
    HOMELANDER_VFX_CANDIDATE_ROUTE = route
    HOMELANDER_VFX_CANDIDATE_PRIMARY = spec.primary
    HOMELANDER_VFX_CANDIDATE_SECONDARY = spec.secondary
    HOMELANDER_VFX_CANDIDATE_FALLBACK = spec.fallback
    HOMELANDER_VFX_CANDIDATE_STATIC_PROVEN = true
    HOMELANDER_VFX_CANDIDATE_RUNTIME_PROVEN = false
    HOMELANDER_VFX_CANDIDATE_PASSED = true

    log("PASS READ ONLY | route=" .. tostring(route) ..
        " primary=" .. tostring(spec.primary) ..
        " secondary=" .. tostring(spec.secondary) ..
        " fallback=" .. tostring(spec.fallback) ..
        " staticProven=true runtimeProven=false")
    return true
end

log("LOADED — v017 dormant F23 READ-ONLY exact VFX candidate resolver")
