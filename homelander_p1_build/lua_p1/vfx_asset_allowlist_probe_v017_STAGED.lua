-- Homelander P1 VFX Asset Allowlist Gate v0.17
-- DORMANT / READ-ONLY. Explicit F23 one-shot only.
-- Resolves a statically audited effect candidate. NEVER spawns an effect.

local PREFIX = "[HOMELANDER_P1_VFX_ASSET_ALLOWLIST_V017] "
local AUDIT_SHA256 = "7359617402d7f9da2475f69d841e8b341e3b9cf45e9eea88fcd76e559ab37230"

HOMELANDER_VFX_ASSET_ALLOWLIST_PASSED = false
HOMELANDER_VFX_ASSET_TARGET = nil
HOMELANDER_VFX_ASSET_SOURCE_ROUTE = nil
HOMELANDER_VFX_ASSET_PRIMARY = nil
HOMELANDER_VFX_ASSET_ALTERNATES = nil
HOMELANDER_VFX_ASSET_AUDIT_SHA256 = nil
HOMELANDER_VFX_ASSET_RUNTIME_PROVEN = false

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

local ROUTES = {
    HELICOPTER_METAL = {
        primary = "debrisSparks001",
        alternates = {}
    },
    INFECTED_ORGANIC_UNRESOLVED = {
        primary = "squibBlood001",
        alternates = {
            "goreBloodMistFanOut001",
            "goreBloodGush001"
        }
    },
    MILITARY_UNRESOLVED = {
        primary = "missileImpact001",
        alternates = {}
    },
    GENERIC = {
        primary = "missileImpact001",
        alternates = {}
    }
}

function Homelander_VFXAssetAllowlistProbeV017()
    HOMELANDER_VFX_ASSET_ALLOWLIST_PASSED = false
    HOMELANDER_VFX_ASSET_TARGET = nil
    HOMELANDER_VFX_ASSET_SOURCE_ROUTE = nil
    HOMELANDER_VFX_ASSET_PRIMARY = nil
    HOMELANDER_VFX_ASSET_ALTERNATES = nil
    HOMELANDER_VFX_ASSET_AUDIT_SHA256 = nil
    HOMELANDER_VFX_ASSET_RUNTIME_PROVEN = false

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

    local route = HOMELANDER_VFX_ROUTE_KEY
    local entry = ROUTES[route]
    if entry == nil then
        log("REFUSED: unrecognized F22 route | " .. tostring(route))
        return false
    end

    local alternates = {}
    for i = 1, #entry.alternates do
        alternates[i] = entry.alternates[i]
    end

    HOMELANDER_VFX_ASSET_TARGET = target
    HOMELANDER_VFX_ASSET_SOURCE_ROUTE = route
    HOMELANDER_VFX_ASSET_PRIMARY = entry.primary
    HOMELANDER_VFX_ASSET_ALTERNATES = alternates
    HOMELANDER_VFX_ASSET_AUDIT_SHA256 = AUDIT_SHA256
    HOMELANDER_VFX_ASSET_RUNTIME_PROVEN = false
    HOMELANDER_VFX_ASSET_ALLOWLIST_PASSED = true

    local altText = ""
    for i = 1, #alternates do
        if i > 1 then altText = altText .. "," end
        altText = altText .. alternates[i]
    end

    log("PASS READ ONLY | route=" .. tostring(route) ..
        " primary=" .. tostring(entry.primary) ..
        " alternates=" .. altText ..
        " runtimeProven=false")
    return true
end

log("LOADED — v017 dormant F23 READ-ONLY VFX asset allowlist probe")
