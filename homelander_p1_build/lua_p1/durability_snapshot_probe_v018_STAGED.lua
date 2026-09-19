-- Homelander P1 Durability Snapshot Probe v0.18
-- F24 READ ONLY. Captures only fields with proven getter+setter symmetry.
-- Does NOT call any setter.

local PREFIX = "[HOMELANDER_P1_DURABILITY_SNAPSHOT_V018] "

HOMELANDER_DURABILITY_SNAPSHOT_PASSED = false
HOMELANDER_DURABILITY_SNAPSHOT_PLAYER = nil
HOMELANDER_DURABILITY_SNAPSHOT_HEALTH = nil
HOMELANDER_DURABILITY_SNAPSHOT_MAX_HEALTH = nil
HOMELANDER_DURABILITY_SNAPSHOT_DAMAGE_SCALE = nil
HOMELANDER_DURABILITY_MUTATION_AUTHORIZED = false

local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end

local function finite(v)
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
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

local function read_float(name, fn, target)
    if type(fn) ~= "function" then
        return nil, name .. " unavailable"
    end
    local ok, v = pcall(fn, target)
    if not ok then
        return nil, name .. " error | " .. tostring(v)
    end
    if not finite(v) then
        return nil, name .. " non-finite | " .. tostring(v)
    end
    return v, nil
end

function Homelander_DurabilitySnapshotV018()
    HOMELANDER_DURABILITY_SNAPSHOT_PASSED = false
    HOMELANDER_DURABILITY_SNAPSHOT_PLAYER = nil
    HOMELANDER_DURABILITY_SNAPSHOT_HEALTH = nil
    HOMELANDER_DURABILITY_SNAPSHOT_MAX_HEALTH = nil
    HOMELANDER_DURABILITY_SNAPSHOT_DAMAGE_SCALE = nil
    HOMELANDER_DURABILITY_MUTATION_AUTHORIZED = false

    local player = HOMELANDER_PLAYER
    if not valid_player(player) then
        log("ABORT: verified player missing; run F4 first")
        return false
    end

    local health, errH = read_float("go_GetHealth", _G.go_GetHealth, player)
    if health == nil then log("ABORT: " .. tostring(errH)); return false end

    local maxHealth, errM = read_float("go_GetMaxHealth", _G.go_GetMaxHealth, player)
    if maxHealth == nil then log("ABORT: " .. tostring(errM)); return false end

    local damageScale, errD = read_float("go_GetDamageScale", _G.go_GetDamageScale, player)
    if damageScale == nil then log("ABORT: " .. tostring(errD)); return false end

    if maxHealth <= 0.0 then
        log("ABORT: non-positive maxHealth=" .. tostring(maxHealth))
        return false
    end
    if damageScale < 0.0 then
        log("ABORT: negative damageScale=" .. tostring(damageScale))
        return false
    end

    HOMELANDER_DURABILITY_SNAPSHOT_PLAYER = player
    HOMELANDER_DURABILITY_SNAPSHOT_HEALTH = health
    HOMELANDER_DURABILITY_SNAPSHOT_MAX_HEALTH = maxHealth
    HOMELANDER_DURABILITY_SNAPSHOT_DAMAGE_SCALE = damageScale
    HOMELANDER_DURABILITY_MUTATION_AUTHORIZED = false
    HOMELANDER_DURABILITY_SNAPSHOT_PASSED = true

    log("PASS READ ONLY | health=" .. tostring(health) ..
        " maxHealth=" .. tostring(maxHealth) ..
        " damageScale=" .. tostring(damageScale) ..
        " mutationAuthorized=false")
    return true
end

log("LOADED — F24 read-only durability snapshot; one-way durability setters excluded")
