-- R024 optional READ-ONLY Lua 5.1 key/type census, source-only and NOT
-- integrated into frozen R007/v003 or installed in user's active game.
-- No pointer/value logging, GOH dereference, engine getter/setter calls,
-- global writes, registry reads, debug hooks, or automatic per-frame sampling.
local PREFIX = "[P1_R024_GLOBAL_CENSUS] "
local max_entries = 64
local max_name_len = 72
local emitted = 0
local matching = 0
local keys = {}
local function relevant(name)
    if type(name) ~= "string" or #name < 2 or #name > max_name_len then
        return false
    end
    if not string.match(name, "^[%w_]+$") then return false end
    local lower = string.lower(name)
    return string.find(lower, "player", 1, true) ~= nil
        or string.find(lower, "alex", 1, true) ~= nil
        or string.find(lower, "avatar", 1, true) ~= nil
        or string.find(lower, "character", 1, true) ~= nil
        or string.find(lower, "hero", 1, true) ~= nil
        or string.find(lower, "actor", 1, true) ~= nil
        or string.find(lower, "goh", 1, true) ~= nil
end
-- Use the engine's supplied HL_Log if present; the ONLY intended side-effect
-- is bounded diagnostic log emission. Do not call any game API or userdata.
local log_fn = rawget(_G, "HL_Log")
if type(log_fn) ~= "function" then log_fn = print end
local function log(s)
    log_fn(PREFIX .. s)
end
for key, value in next, _G do
    if relevant(key) then
        matching = matching + 1
        if #keys < max_entries then
            -- Never tostring(value), inspect metatable, or dereference a GOH.
            keys[#keys + 1] = {name = key, kind = type(value)}
        end
    end
end
table.sort(keys, function(a, b) return a.name < b.name end)
log("BEGIN | only global KEY + Lua TYPE; no player verification implied")
log("PLAYER global type=" .. type(rawget(_G, "PLAYER")))
for _, item in ipairs(keys) do
    emitted = emitted + 1
    log("KEY " .. item.name .. " type=" .. item.kind)
end
log("END | emitted=" .. emitted .. " matching=" .. matching ..
    " capped=" .. tostring(matching > max_entries) ..
    " no GOH validated and no gameplay mutation")
