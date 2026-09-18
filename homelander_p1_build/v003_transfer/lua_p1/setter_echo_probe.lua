-- Homelander P1 Setter Echo Probe v2
-- GUARDED / MANUAL ONLY. Loading performs NO physics mutation.
-- Successful echo validation sets HOMELANDER_SETTER_ECHO_PASSED=true.




local PREFIX = "[HOMELANDER_P1_SETTER_ECHO_V2] "
local function log(msg)
    local line = PREFIX .. tostring(msg)
    if type(HL_Log) == "function" then HL_Log(line) else print(line) end
end
local function hasfn(name) return type(_G[name]) == "function" end




local function valid_handle(h)
    if h == nil then return false, "handle is nil" end
    if hasfn("go_IsValid") then
        local ok, v = pcall(go_IsValid, h)
        if not ok then return false, "go_IsValid error: " .. tostring(v) end
        if not v then return false, "go_IsValid returned false" end
    end
    if hasfn("online_DeterminePlayerIndex") then
        local ok, idx = pcall(online_DeterminePlayerIndex, h)
        if not ok then return false, "DeterminePlayerIndex error: " .. tostring(idx) end
        if type(idx) ~= "number" or idx < 0 then return false, "not a verified player index: " .. tostring(idx) end
    end
    if hasfn("go_GetPosition") then
        local ok, err = pcall(go_GetPosition, h)
        if not ok then return false, "go_GetPosition rejected handle: " .. tostring(err) end
    end
    return true
end




function Homelander_SetterEchoProbe(handle)
    HOMELANDER_SETTER_ECHO_PASSED = false
    log("BEGIN")




    if not hasfn("ai_GetPhysicsVelocity") then log("ABORT: ai_GetPhysicsVelocity unavailable"); return false end
    if not hasfn("phys_SetLinearVelocity") then log("ABORT: phys_SetLinearVelocity unavailable"); return false end




    local ok_handle, why = valid_handle(handle)
    if not ok_handle then log("ABORT: invalid/unproven handle | " .. tostring(why)); return false end




    local ok_read, before = pcall(ai_GetPhysicsVelocity, handle)
    if not ok_read or before == nil then log("ABORT: velocity read failed | " .. tostring(before)); return false end




    -- Defensive copy: preserve the readback value for comparison.
    local echo = (type(Vector) == "function") and Vector(before) or before
    log("velocity_before=" .. tostring(before))
    log("calling phys_SetLinearVelocity(handle, SAME_VECTOR, 0)")




    -- Statically proven exposed ABI:
    -- void phys_SetLinearVelocity(engine::LuaGOH, math::Vector, int)
    local ok_set, set_err = pcall(phys_SetLinearVelocity, handle, echo, 0)
    if not ok_set then log("FAIL: setter rejected call | " .. tostring(set_err)); return false end




    local ok_after, after = pcall(ai_GetPhysicsVelocity, handle)
    if not ok_after or after == nil then log("FAIL: post-read failed | " .. tostring(after)); return false end
    log("velocity_after=" .. tostring(after))




    if type(Vector) == "function" then
        local ok_delta, delta_mag = pcall(function()
            local d = after - before
            return d:magnitude()
        end)
        if not ok_delta then log("FAIL: could not compare velocity vectors | " .. tostring(delta_mag)); return false end
        log("echo delta magnitude=" .. tostring(delta_mag))
        if delta_mag > 0.001 then
            log("FAIL: echo changed velocity beyond tolerance")
            return false
        end
    end




    HOMELANDER_SETTER_ECHO_PASSED = true
    log("PASS: setter ABI/player route validated; gate opened")
    return true
end




function Homelander_SetterEchoProbe_Verified()
    if HOMELANDER_PLAYER == nil then
        log("ABORT: HOMELANDER_PLAYER is not verified")
        return false
    end
    return Homelander_SetterEchoProbe(HOMELANDER_PLAYER)
end




function Homelander_SetterEchoProbe_PLAYER()
    if PLAYER == nil then log("ABORT: PLAYER global is nil"); return false end
    return Homelander_SetterEchoProbe(PLAYER)
end




log("LOADED — no physics mutation performed. Explicit probe call required.")