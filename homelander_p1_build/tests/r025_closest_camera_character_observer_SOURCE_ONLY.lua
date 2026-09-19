-- R025: optional ONE-SHOT, READ-ONLY closest-camera-character provenance
-- experiment. NOT part of original frozen v003 game, NOT an installable mod.
-- Static original user's PE32 shows ai_GetClosestCharacterToCamera registered
-- with an engine routine that selects closest game character to camera.
-- Closest may be an NPC. A non-nil GOH is NEVER sufficient player proof.
local PREFIX = "[P1_R025_CLOSEST_CAMERA_CANDIDATE] "
local function log(s)
    local fn = rawget(_G, "HL_Log")
    if type(fn) ~= "function" then fn = print end
    fn(PREFIX .. s)
end
local function fn(name)
    local v = rawget(_G, name)
    if type(v) ~= "function" then return nil end
    return v
end
local function safe(name, ...)
    local f = fn(name)
    if not f then
        log("STOP | " .. name .. " is not an available Lua function")
        return false, nil
    end
    local ok, value = pcall(f, ...)
    if not ok then
        log("STOP | " .. name .. " raised error; no value/handle logged")
        return false, nil
    end
    return true, value
end
local function valid_count(n)
    return type(n) == "number" and n == n and
           n >= 1 and n <= 16 and n == math.floor(n)
end
local function valid_index(i,n)
    return type(i) == "number" and i == i and
           i >= 0 and i < n and i == math.floor(i)
end
function Homelander_R025_ObserveClosestCameraCharacter()
    -- This function NEVER sets HOMELANDER_PLAYER, a gate, or an engine global,
    -- never calls a setter or a damage/physics/effect/laser function.
    log("BEGIN | optional diagnostic only; no original v003 PASS possible")
    local required = {
        "ai_GetClosestCharacterToCamera", "go_IsValid",
        "go_GetPosition", "ai_GetPhysicsVelocity",
        "online_DeterminePlayerIndex", "online_GetNumPlayers"
    }
    for _, name in ipairs(required) do
        if not fn(name) then
            log("STOP | required read-only function absent: " .. name)
            return false
        end
    end
    local okCount, count = safe("online_GetNumPlayers")
    if not okCount or not valid_count(count) then
        log("STOP | network player count invalid/unavailable")
        return false
    end
    local okCandidate, candidate = safe("ai_GetClosestCharacterToCamera")
    if not okCandidate or candidate == nil then
        log("STOP | closest camera character unavailable; no candidate")
        return false
    end
    -- Avoid tostring(candidate), raw addresses, nested userdata access.
    log("CANDIDATE | Lua type=" .. type(candidate) ..
        " ; closest-to-camera is NOT synonymous with player")
    local okValid, valid = safe("go_IsValid", candidate)
    if not okValid or valid ~= true then
        log("REJECT | candidate is not explicitly valid GOH")
        return false
    end
    local okIndex, index = safe("online_DeterminePlayerIndex", candidate)
    if not okIndex or not valid_index(index, count) then
        log("REJECT | independent online player index absent/out of range")
        return false
    end
    local okP, position = safe("go_GetPosition", candidate)
    if not okP or position == nil then
        log("REJECT | camera candidate has no valid position result")
        return false
    end
    local okV, velocity = safe("ai_GetPhysicsVelocity", candidate)
    if not okV or velocity == nil then
        log("REJECT | camera candidate has no valid velocity result")
        return false
    end
    -- A single static observation does not establish LOCAL-player identity
    -- in multiplayer, nor reliable current on-screen Alex in a cutscene.
    log("OBSERVED | closest camera character passed current player-index range " ..
        "(idx=" .. index .. " of " .. count ..
        "); engine game type/identity still unverified; NO gate granted")
    log("END | NO PLAYER GLOBAL SET, NO LASER/PHYSICS/DAMAGE, NO PASS")
    return true -- observation success ONLY; caller MUST NOT treat as game gate
end
log("LOADED | dormant, explicit invocation only; no game state touched")
