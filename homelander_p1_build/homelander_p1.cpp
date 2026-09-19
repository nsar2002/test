// Homelander Prototype 1 minimal runtime bridge
// Target: Prototype 1 Win32 / prototypeenginef.dll active build
// Reference signatures validated 1/1 against user's active DLL on 2026-09-18.
// No ImGui, no D3DX, no DirectInput, no third-party hook library.

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <cstdint>
#include <cmath>
#include <cstdio>
#include <cstdarg>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>
#include <limits>

namespace hl
{
    constexpr int LUA_GLOBALSINDEX = -10002;
    constexpr const char* kBuildId = "P1_RuntimeProbe_008_DYNAMIC_AIM_STAGED_20260919";

    HMODULE g_self = nullptr;
    HMODULE g_engine = nullptr;
    HWND g_window = nullptr;
    std::string g_root;
    SRWLOCK g_logLock = SRWLOCK_INIT;

    using LuaPcallFn        = int(__cdecl*)(int, int, int, int);
    using LuaGetFieldFn     = void(__cdecl*)(int, int, const char*);
    using LuaSetTopFn       = void(__cdecl*)(int, int);
    using LuaGetTopFn       = int(__cdecl*)(int);
    using LuaToLStringFn    = const char*(__cdecl*)(int, int, size_t*);
    using LuaLoadBufferFn   = int(__cdecl*)(int, const char*, size_t, const char*);
    using LuaPushCClosureFn = void(__cdecl*)(int, void*, int);
    using LuaPushLStringFn  = void(__cdecl*)(int, const char*, size_t);
    using LuaSetFieldFn     = void(__cdecl*)(int, int, const char*);
    // Prototype LuaGOH is represented on the Lua stack as LIGHTUSERDATA:
    // raw encoding high16=slot index, low16=generation.
    using LuaPushGOHFn      = void(__cdecl*)(int, uint32_t);
    using LuaToUserDataFn   = void*(__cdecl*)(int, int);
    using LuaToNumberFn     = float(__cdecl*)(int, int);
    using LuaPushBooleanFn  = void(__cdecl*)(int, int);

    struct Vec3
    {
        float x;
        float y;
        float z;
    };

    struct EngineName
    {
        uint32_t a;
        uint32_t b;
    };

    struct LaserSightPayload
    {
        int32_t handle;
        uint32_t context;
        uint8_t flag;
        uint8_t pad09[3];
        Vec3 endpointA;
        Vec3 endpointB;
        float thickness;
        float r;
        float g;
        float b;
        float a;
        void* shader;
    };
    static_assert(sizeof(LaserSightPayload) == 0x3C, "LaserSightPayload must be 0x3C bytes");

    using RenderCameraPositionFn = Vec3*(__thiscall*)(void*, Vec3*);
    using NameCtorFn             = EngineName*(__thiscall*)(EngineName*, const char*, int);
    using JointLocalToWorldFn    = Vec3*(__cdecl*)(Vec3*, void*, EngineName*, const Vec3*);
    using ShaderLookupFn         = void*(__thiscall*)(void*, const EngineName*);
    using LaserEventAllocFn      = LaserSightPayload*(__cdecl*)(void*);
    using LaserHandleAllocFn     = int32_t*(__cdecl*)(int32_t*, void*, int);
    using LaserHandleValidFn     = bool(__thiscall*)(int32_t*);
    using LaserHandleReleaseFn   = void(__cdecl*)(int32_t*, int);
    using LaserSubmitFn          = void(__cdecl*)();
    using RenderContextFn        = uint32_t(__cdecl*)();

    LuaPcallFn        LuaPcall = nullptr;
    LuaGetFieldFn     LuaGetField = nullptr;
    LuaSetTopFn       LuaSetTop = nullptr;
    LuaGetTopFn       LuaGetTop = nullptr;
    LuaToLStringFn    LuaToLString = nullptr;
    LuaLoadBufferFn   LuaLoadBuffer = nullptr;
    LuaPushCClosureFn LuaPushCClosure = nullptr;
    LuaPushLStringFn  LuaPushLString = nullptr;
    LuaSetFieldFn     LuaSetField = nullptr;
    LuaPushGOHFn      LuaPushGOH = nullptr;
    LuaToUserDataFn   LuaToUserData = nullptr;
    LuaToNumberFn     LuaToNumber = nullptr;
    LuaPushBooleanFn  LuaPushBoolean = nullptr;

    NameCtorFn           NameCtor = nullptr;
    JointLocalToWorldFn  JointLocalToWorld = nullptr;
    ShaderLookupFn       ShaderLookup = nullptr;
    LaserEventAllocFn    LaserEventAlloc = nullptr;
    LaserHandleAllocFn   LaserHandleAlloc = nullptr;
    LaserHandleValidFn   LaserHandleValid = nullptr;
    LaserHandleReleaseFn LaserHandleRelease = nullptr;
    LaserSubmitFn        LaserSubmit = nullptr;
    RenderContextFn      RenderContext = nullptr;

    void** g_luaScriptManagerSlot = nullptr;

    // Free-aim v003 static bridges. These remain read-only.
    uintptr_t* g_gohTableGlobal = nullptr;
    uintptr_t* g_physicsManagerGlobal = nullptr;

    void** g_shaderManagerSlot = nullptr;
    void** g_renderEventGlobalSlot = nullptr;
    EngineName* g_protoLitGlowNameGlobal = nullptr;
    EngineName* g_eyePointNameGlobal = nullptr;
    void* g_laserSightCallback = nullptr;
    void* g_laserShader = nullptr;
    bool g_laserShaderGatePassed = false;
    bool g_laserOneShotPassed = false;
    bool g_laserHeldStabilityPassed = false;
    uint32_t g_laserHeldSubmitFrames = 0;
    int32_t g_laserSightHandles[2] = {-1, -1};

    RenderCameraPositionFn g_originalRenderCameraPosition = nullptr;
    uint8_t* g_renderCameraTarget = nullptr;
    uint8_t g_originalRenderCameraBytes[5]{};
    void* g_lastRenderCamera = nullptr;
    Vec3 g_lastRenderCameraPosition{};
    bool g_lastRenderCameraPositionValid = false;

    uint8_t* g_lineOfSightCaptureTarget = nullptr;
    uint8_t g_originalLineOfSightBytes[6]{};
    void* g_lineOfSightCaptureStub = nullptr;
    uint8_t g_lastRayHitRecord[0x30]{};
    bool g_lastRayHitValid = false;

    using GOMUpdateFn = int(__stdcall*)(int, int, float);
    GOMUpdateFn g_originalGOMUpdate = nullptr;
    uint8_t* g_gomTarget = nullptr;
    uint8_t g_originalGOMBytes[9]{};

    int g_lastLuaState = 0;
    bool g_scriptsReady = false;
    bool g_f4Prev = false;
    bool g_f5Prev = false;
    bool g_f6Prev = false;
    bool g_f7Prev = false;
    bool g_f8Prev = false;
    bool g_f9Prev = false;
    bool g_f10Prev = false;
    bool g_f11Prev = false;
    bool g_f12Prev = false;
    bool g_f13Prev = false;
    bool g_f14Prev = false;
    bool g_f15Prev = false;
    bool g_f16Prev = false;
    bool g_freeAimReady = false;
    bool g_localOffsetReady = false;
    bool g_eyeOriginReady = false;
    bool g_dualEyeRenderReady = false;
    bool g_laserSightNativeReady = false;
    bool g_laserSightHeldReady = false;
    bool g_laserSightDynamicReady = false;

    const char* kSigLuaPcall =
        "8B 4C 24 ? 83 EC ? 85 C9 56";
    const char* kSigLuaGetField =
        "8B 4C 24 ? 83 EC ? 53 56 8B 74 24 ? 57 8B D6 E8 ? ? ? ? "
        "8B 54 24 ? 8B F8 8B C2 8D 58 ? 8A 08 83 C0 ? 84 C9 75 ? "
        "2B C3 50 52 56 E8 ? ? ? ? 89 44 24 ? 8B 46 ? 50";
    const char* kSigLuaSetTop =
        "8B 4C 24 ? 85 C9 8B 44 24 ? 7C";
    const char* kSigLuaGetTop =
        "8B 4C 24 ? 8B 41 ? 2B 41 ? C1 F8";
    const char* kSigLuaToLString =
        "56 8B 74 24 ? 57 8B 7C 24 ? 8B CF 8B D6";
    const char* kSigLuaLoadBuffer =
        "55 8B EC 83 EC ? 8B 45 ? 8B 55";
    const char* kSigLuaPushCClosure =
        "56 8B 74 24 ? 8B 46 ? 8B 48 ? 3B 48 ? 57 72 ? 56 E8 ? ? ? ? "
        "83 C4 ? 8B C6";
    const char* kSigLuaPushLString =
        "56 8B 74 24 ? 8B 46 ? 8B 48 ? 3B 48 ? 57 72 ? 56 E8 ? ? ? ? "
        "83 C4 ? 8B 54 24 ? 8B 44 24 ? 8B 7E ? 52 50 56 E8 ? ? ? ? "
        "83 C4 ? 89 07 C7 47 ? ? ? ? ? 83 46 ? ? 5F 5E C3 8B 54 24";
    const char* kSigLuaSetField =
        "8B 4C 24 ? 83 EC ? 53 56 8B 74 24 ? 57 8B D6 E8 ? ? ? ? "
        "8B 54 24 ? 8B F8 8B C2 8D 58 ? 8A 08 83 C0 ? 84 C9 75 ? "
        "2B C3 50 52 56 E8 ? ? ? ? 89 44 24 ? 8B 46 ? 83 E8";
    const char* kSigLuaManager =
        "8B 0D ? ? ? ? 85 C9 74 ? 8B 01 8B 10 6A ? FF D2 A1";
    const char* kSigGOMUpdate =
        "53 55 56 57 E8 ? ? ? ? E8 ? ? ? ? E8";

    // Proven against the user's active Prototype 1 DLL on 2026-09-18.
    const char* kSigLuaPushGOH =
        "8B 44 24 04 8B 48 08 8B 54 24 08 89 11 C7 41 04 02 00 00 00 83 40 08 08 C3";
    const char* kSigRenderCameraPosition =
        "8B 41 14 85 C0 74 28 8B 48 44 85 C9 74 21 8B 44 24 04 "
        "D9 81 C0 00 00 00";
    const char* kSigLineOfSightCapture =
        "8B 74 24 14 6A 00 55 E8 ? ? ? ? 83 C4 08 85 F6 5F 5B 0F 84";
    const char* kSigPhysicsManagerRef =
        "0F B7 01 8B 0D ? ? ? ? 8B 51 0C 8B 04 C2 C3";
    const char* kSigGOHTableRef =
        "0F B7 01 66 3D FF FF 74 ? 8B 15 ? ? ? ? 0F B7 C0 8D 04 C2 "
        "66 8B 50 04 66 3B 51 02 75 03 8B 00 C3 33 C0 C3";

    // v006 real LaserSight native route.
    const char* kSigLuaToUserData =
        "8B 4C 24 08 8B 54 24 04 E8 ? ? ? ? 8B 48 04 83 E9 02 74 ? "
        "83 E9 05 74 ? 33 C0 C3";
    const char* kSigLuaToNumber =
        "8B 4C 24 08 8B 54 24 04 83 EC 08 E8 ? ? ? ? 83 78 04 03 74 ? "
        "8D 0C 24 51 50 E8 ? ? ? ? 83 C4 08 85 C0 75 ? D9 EE 83 C4 08 C3 "
        "D9 00 83 C4 08 C3";
    const char* kSigLuaPushBoolean =
        "8B 44 24 04 8B 48 08 33 D2 39 54 24 08 C7 41 04 01 00 00 00 "
        "0F 95 C2 89 11 83 40 08 08 C3";
    const char* kSigNameCtor =
        "8B 44 24 04 56 6A 00 6A 00 50 8B F1 E8 ? ? ? ? 89 06 83 C4 0C "
        "89 56 04 8B C6 5E C2 08 00";
    const char* kSigJointLocalToWorld =
        "83 EC 40 56 8B 4C 24 4C 8B 41 1C F3 0F 10 40 04 83 C0 04 "
        "F3 0F 11 44 24 04";
    const char* kSigLaserShaderRoute =
        "8B 47 1C 8B 0D ? ? ? ? 53 83 C0 18 50 E8 ? ? ? ? 8B D8 85 DB";
    const char* kSigLaserEventCreate =
        "56 68 ? ? ? ? E8 ? ? ? ? 6A 01 8D 54 24 ? 6A 00 52 8B F0 "
        "E8 ? ? ? ? 8B 00 83 C4 10 89 06 E8 ? ? ? ? 89 46 04 C6 46 08 00";
    const char* kSigLaserCleanupRoute =
        "8D 6F 2C 8B CD E8 ? ? ? ? 84 C0 74 ? 6A 00 55 E8 ? ? ? ? 83 C4 08";
    const char* kSigLaserSubmit =
        "A1 ? ? ? ? 50 E8 ? ? ? ? 83 C4 04 C7 05 ? ? ? ? 00 00 00 00 C3";

    std::string SelfRoot()
    {
        char path[MAX_PATH]{};
        const DWORD n = GetModuleFileNameA(g_self, path, MAX_PATH);
        if (!n || n >= MAX_PATH)
            return ".";
        std::string s(path, n);
        const auto pos = s.find_last_of("\\/");
        return pos == std::string::npos ? "." : s.substr(0, pos);
    }

    void Log(const char* fmt, ...)
    {
        char message[2048]{};
        va_list args;
        va_start(args, fmt);
        std::vsnprintf(message, sizeof(message), fmt, args);
        message[sizeof(message) - 1] = '\0';
        va_end(args);

        std::string line = "[HOMELANDER_P1_ASI] ";
        line += message;
        line += "\r\n";
        OutputDebugStringA(line.c_str());

        AcquireSRWLockExclusive(&g_logLock);
        const std::string path = g_root.empty() ? "homelander_p1_runtime.log" : (g_root + "\\homelander_p1_runtime.log");
        HANDLE h = CreateFileA(path.c_str(), FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                               nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
        if (h != INVALID_HANDLE_VALUE)
        {
            DWORD written = 0;
            WriteFile(h, line.data(), static_cast<DWORD>(line.size()), &written, nullptr);
            CloseHandle(h);
        }
        ReleaseSRWLockExclusive(&g_logLock);
    }

    std::vector<int> ParsePattern(const char* pattern)
    {
        std::vector<int> bytes;
        std::istringstream stream(pattern);
        std::string token;
        while (stream >> token)
        {
            if (token == "?" || token == "??")
            {
                bytes.push_back(-1);
            }
            else
            {
                bytes.push_back(static_cast<int>(std::strtoul(token.c_str(), nullptr, 16)));
            }
        }
        return bytes;
    }

    struct ScanResult
    {
        uintptr_t address = 0;
        size_t count = 0;
    };

    ScanResult ScanExecutableSections(HMODULE module, const char* pattern)
    {
        ScanResult result{};
        if (!module)
            return result;

        auto base = reinterpret_cast<uint8_t*>(module);
        auto dos = reinterpret_cast<IMAGE_DOS_HEADER*>(base);
        if (dos->e_magic != IMAGE_DOS_SIGNATURE)
            return result;
        auto nt = reinterpret_cast<IMAGE_NT_HEADERS*>(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE)
            return result;

        const auto pat = ParsePattern(pattern);
        if (pat.empty())
            return result;

        auto section = IMAGE_FIRST_SECTION(nt);
        for (unsigned i = 0; i < nt->FileHeader.NumberOfSections; ++i, ++section)
        {
            if ((section->Characteristics & IMAGE_SCN_MEM_EXECUTE) == 0 ||
                (section->Characteristics & IMAGE_SCN_MEM_READ) == 0)
                continue;

            uint8_t* begin = base + section->VirtualAddress;
            const size_t size = section->Misc.VirtualSize;
            if (size < pat.size())
                continue;

            for (size_t off = 0; off <= size - pat.size(); ++off)
            {
                bool match = true;
                for (size_t j = 0; j < pat.size(); ++j)
                {
                    if (pat[j] >= 0 && begin[off + j] != static_cast<uint8_t>(pat[j]))
                    {
                        match = false;
                        break;
                    }
                }
                if (match)
                {
                    if (result.count == 0)
                        result.address = reinterpret_cast<uintptr_t>(begin + off);
                    ++result.count;
                }
            }
        }
        return result;
    }

    uintptr_t RequireUnique(const char* name, const char* pattern)
    {
        const auto r = ScanExecutableSections(g_engine, pattern);
        if (r.count != 1)
        {
            Log("FAIL signature %-20s count=%zu (required exactly 1)", name, r.count);
            return 0;
        }
        Log("PASS signature %-20s RVA=0x%08X", name,
            static_cast<unsigned>(r.address - reinterpret_cast<uintptr_t>(g_engine)));
        return r.address;
    }

    uintptr_t RequireConsistentImm32(const char* name, const char* pattern, size_t immOffset)
    {
        if (!g_engine)
            return 0;

        auto base = reinterpret_cast<uint8_t*>(g_engine);
        auto dos = reinterpret_cast<IMAGE_DOS_HEADER*>(base);
        if (dos->e_magic != IMAGE_DOS_SIGNATURE)
            return 0;
        auto nt = reinterpret_cast<IMAGE_NT_HEADERS*>(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE)
            return 0;

        const auto pat = ParsePattern(pattern);
        if (pat.empty() || immOffset + sizeof(uint32_t) > pat.size())
            return 0;

        uintptr_t resolved = 0;
        size_t count = 0;
        bool mismatch = false;

        auto section = IMAGE_FIRST_SECTION(nt);
        for (unsigned i = 0; i < nt->FileHeader.NumberOfSections; ++i, ++section)
        {
            if ((section->Characteristics & IMAGE_SCN_MEM_EXECUTE) == 0 ||
                (section->Characteristics & IMAGE_SCN_MEM_READ) == 0)
                continue;

            uint8_t* begin = base + section->VirtualAddress;
            const size_t size = section->Misc.VirtualSize;
            if (size < pat.size())
                continue;

            for (size_t off = 0; off <= size - pat.size(); ++off)
            {
                bool match = true;
                for (size_t j = 0; j < pat.size(); ++j)
                {
                    if (pat[j] >= 0 && begin[off + j] != static_cast<uint8_t>(pat[j]))
                    {
                        match = false;
                        break;
                    }
                }
                if (!match)
                    continue;

                uint32_t imm = 0;
                std::memcpy(&imm, begin + off + immOffset, sizeof(imm));
                if (count == 0)
                    resolved = static_cast<uintptr_t>(imm);
                else if (resolved != static_cast<uintptr_t>(imm))
                    mismatch = true;
                ++count;
            }
        }

        if (count == 0 || mismatch || resolved == 0)
        {
            Log("FAIL consistent ref %-17s count=%zu mismatch=%s value=0x%08X",
                name, count, mismatch ? "true" : "false", static_cast<unsigned>(resolved));
            return 0;
        }

        Log("PASS consistent ref %-17s count=%zu absolute=0x%08X",
            name, count, static_cast<unsigned>(resolved));
        return resolved;
    }

    int GetLuaState()
    {
        if (!g_luaScriptManagerSlot || !*g_luaScriptManagerSlot)
            return 0;
        return *reinterpret_cast<int*>(reinterpret_cast<uintptr_t>(*g_luaScriptManagerSlot) + 0x0C);
    }

    std::string LuaErrorString(int L)
    {
        if (!LuaToLString)
            return "<Lua error>";
        const char* s = LuaToLString(L, -1, nullptr);
        return s ? s : "<Lua error without string>";
    }

    bool ReadTextFile(const std::string& path, std::string& out)
    {
        std::ifstream file(path, std::ios::in | std::ios::binary);
        if (!file)
            return false;
        out.assign(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
        return true;
    }

    bool ExecuteLuaFile(int L, const char* relativePath)
    {
        if (!L || !LuaLoadBuffer || !LuaPcall || !LuaGetTop || !LuaSetTop)
            return false;

        std::string full = g_root + "\\" + relativePath;
        std::string source;
        if (!ReadTextFile(full, source))
        {
            Log("Lua file missing: %s", full.c_str());
            return false;
        }

        const char* chunkData = source.data();
        size_t chunkSize = source.size();
        if (chunkSize >= 3 &&
            static_cast<unsigned char>(chunkData[0]) == 0xEF &&
            static_cast<unsigned char>(chunkData[1]) == 0xBB &&
            static_cast<unsigned char>(chunkData[2]) == 0xBF)
        {
            chunkData += 3;
            chunkSize -= 3;
            Log("Lua UTF-8 BOM stripped: %s", relativePath);
        }

        const int top = LuaGetTop(L);
        const int load = LuaLoadBuffer(L, chunkData, chunkSize, relativePath);
        if (load != 0)
        {
            Log("Lua compile error [%s]: %s", relativePath, LuaErrorString(L).c_str());
            LuaSetTop(L, top);
            return false;
        }

        const int call = LuaPcall(L, 0, 0, 0);
        if (call != 0)
        {
            Log("Lua runtime error [%s]: %s", relativePath, LuaErrorString(L).c_str());
            LuaSetTop(L, top);
            return false;
        }

        LuaSetTop(L, top);
        Log("Lua loaded: %s", relativePath);
        return true;
    }

    int __cdecl LuaLogHook(int L)
    {
        if (!LuaGetTop || !LuaToLString)
            return 0;
        const int n = LuaGetTop(L);
        std::string line;
        for (int i = 1; i <= n; ++i)
        {
            if (i > 1) line += "\t";
            const char* s = LuaToLString(L, i, nullptr);
            line += s ? s : "<non-string>";
        }
        Log("LUA %s", line.c_str());
        return 0;
    }

    uint32_t SwapGOHHalves(uint32_t raw)
    {
        return (raw << 16) | (raw >> 16);
    }

    uintptr_t ResolveRel32Target(uintptr_t callSite)
    {
        if (!callSite || *reinterpret_cast<const uint8_t*>(callSite) != 0xE8)
            return 0;
        int32_t rel = 0;
        std::memcpy(&rel, reinterpret_cast<const void*>(callSite + 1), sizeof(rel));
        return callSite + 5 + static_cast<intptr_t>(rel);
    }

    bool IsReadableMemory(const void* ptr, size_t bytes);

    uintptr_t FindUniqueAsciiString(HMODULE module, const char* text)
    {
        if (!module || !text || !*text)
            return 0;

        auto base = reinterpret_cast<uint8_t*>(module);
        auto dos = reinterpret_cast<IMAGE_DOS_HEADER*>(base);
        if (dos->e_magic != IMAGE_DOS_SIGNATURE)
            return 0;
        auto nt = reinterpret_cast<IMAGE_NT_HEADERS*>(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE)
            return 0;

        const size_t length = std::strlen(text) + 1; // require NUL terminator too
        uintptr_t found = 0;
        size_t count = 0;

        auto section = IMAGE_FIRST_SECTION(nt);
        for (unsigned i = 0; i < nt->FileHeader.NumberOfSections; ++i, ++section)
        {
            if ((section->Characteristics & IMAGE_SCN_MEM_READ) == 0)
                continue;

            uint8_t* begin = base + section->VirtualAddress;
            const size_t size = section->Misc.VirtualSize;
            if (size < length)
                continue;

            for (size_t off = 0; off <= size - length; ++off)
            {
                if (std::memcmp(begin + off, text, length) == 0)
                {
                    if (count == 0)
                        found = reinterpret_cast<uintptr_t>(begin + off);
                    ++count;
                }
            }
        }

        if (count != 1)
        {
            Log("FAIL ASCII %-24s count=%zu (required exactly 1)", text, count);
            return 0;
        }

        Log("PASS ASCII %-24s RVA=0x%08X", text,
            static_cast<unsigned>(found - reinterpret_cast<uintptr_t>(module)));
        return found;
    }

    EngineName* ResolveProtoLitGlowNameGlobal()
    {
        const uintptr_t stringAddress = FindUniqueAsciiString(g_engine, "proto_lit_glow");
        if (!stringAddress)
            return nullptr;

        auto base = reinterpret_cast<uint8_t*>(g_engine);
        auto dos = reinterpret_cast<IMAGE_DOS_HEADER*>(base);
        auto nt = reinterpret_cast<IMAGE_NT_HEADERS*>(base + dos->e_lfanew);

        uintptr_t xref = 0;
        size_t xrefCount = 0;
        auto section = IMAGE_FIRST_SECTION(nt);
        for (unsigned i = 0; i < nt->FileHeader.NumberOfSections; ++i, ++section)
        {
            if ((section->Characteristics & IMAGE_SCN_MEM_EXECUTE) == 0 ||
                (section->Characteristics & IMAGE_SCN_MEM_READ) == 0)
                continue;

            uint8_t* begin = base + section->VirtualAddress;
            const size_t size = section->Misc.VirtualSize;
            if (size < 5)
                continue;

            for (size_t off = 0; off <= size - 5; ++off)
            {
                if (begin[off] != 0x68)
                    continue;
                uint32_t imm = 0;
                std::memcpy(&imm, begin + off + 1, sizeof(imm));
                if (static_cast<uintptr_t>(imm) == stringAddress)
                {
                    if (xrefCount == 0)
                        xref = reinterpret_cast<uintptr_t>(begin + off);
                    ++xrefCount;
                }
            }
        }

        if (xrefCount != 1 || !xref)
        {
            Log("FAIL proto_lit_glow initializer xref count=%zu (required exactly 1)", xrefCount);
            return nullptr;
        }

        if (!IsReadableMemory(reinterpret_cast<const void*>(xref), 42))
        {
            Log("FAIL proto_lit_glow initializer range unreadable");
            return nullptr;
        }

        const uint8_t* p = reinterpret_cast<const uint8_t*>(xref);
        // Exact initializer skeleton:
        // push <string>; lea ecx,[esp+8]; call; lea eax,[esp]; push eax;
        // lea ecx,[esp+8]; call; lea ecx,[esp+4]; push ecx; mov ecx,<Name global>; call
        const bool skeleton =
            p[5] == 0x8D && p[6] == 0x4C && p[7] == 0x24 && p[8] == 0x08 &&
            p[9] == 0xE8 &&
            p[14] == 0x8D && p[15] == 0x04 && p[16] == 0x24 &&
            p[17] == 0x50 &&
            p[18] == 0x8D && p[19] == 0x4C && p[20] == 0x24 && p[21] == 0x08 &&
            p[22] == 0xE8 &&
            p[27] == 0x8D && p[28] == 0x4C && p[29] == 0x24 && p[30] == 0x04 &&
            p[31] == 0x51 && p[32] == 0xB9 && p[37] == 0xE8;

        if (!skeleton)
        {
            Log("FAIL proto_lit_glow initializer skeleton mismatch");
            return nullptr;
        }

        uint32_t globalAddress = 0;
        std::memcpy(&globalAddress, p + 33, sizeof(globalAddress));

        const uintptr_t moduleBase = reinterpret_cast<uintptr_t>(g_engine);
        const uintptr_t moduleEnd =
            moduleBase + static_cast<uintptr_t>(nt->OptionalHeader.SizeOfImage);
        const uintptr_t nameAddress = static_cast<uintptr_t>(globalAddress);

        if (!globalAddress ||
            nameAddress < moduleBase ||
            nameAddress + sizeof(EngineName) < nameAddress ||
            nameAddress + sizeof(EngineName) > moduleEnd ||
            !IsReadableMemory(reinterpret_cast<const void*>(nameAddress), sizeof(EngineName)))
        {
            Log("FAIL proto_lit_glow Name global outside/unreadable in engine image");
            return nullptr;
        }

        Log("PASS proto_lit_glow Name global RVA=0x%08X",
            static_cast<unsigned>(
                static_cast<uintptr_t>(globalAddress) -
                reinterpret_cast<uintptr_t>(g_engine)));
        return reinterpret_cast<EngineName*>(static_cast<uintptr_t>(globalAddress));
    }

    EngineName* ResolveEyePointNameGlobal()
    {
        const uintptr_t stringAddress = FindUniqueAsciiString(g_engine, "EYEPOINT");
        if (!stringAddress)
            return nullptr;

        auto base = reinterpret_cast<uint8_t*>(g_engine);
        auto dos = reinterpret_cast<IMAGE_DOS_HEADER*>(base);
        auto nt = reinterpret_cast<IMAGE_NT_HEADERS*>(base + dos->e_lfanew);

        uintptr_t xref = 0;
        size_t xrefCount = 0;
        auto section = IMAGE_FIRST_SECTION(nt);
        for (unsigned i = 0; i < nt->FileHeader.NumberOfSections; ++i, ++section)
        {
            if ((section->Characteristics & IMAGE_SCN_MEM_EXECUTE) == 0 ||
                (section->Characteristics & IMAGE_SCN_MEM_READ) == 0)
                continue;

            uint8_t* begin = base + section->VirtualAddress;
            const size_t size = section->Misc.VirtualSize;
            if (size < 5)
                continue;

            for (size_t off = 0; off <= size - 5; ++off)
            {
                if (begin[off] != 0x68)
                    continue;
                uint32_t imm = 0;
                std::memcpy(&imm, begin + off + 1, sizeof(imm));
                if (static_cast<uintptr_t>(imm) == stringAddress)
                {
                    if (xrefCount == 0)
                        xref = reinterpret_cast<uintptr_t>(begin + off);
                    ++xrefCount;
                }
            }
        }

        if (xrefCount != 1 || !xref ||
            !IsReadableMemory(reinterpret_cast<const void*>(xref), 15))
        {
            Log("FAIL EYEPOINT initializer xref count/range count=%zu", xrefCount);
            return nullptr;
        }

        const uint8_t* p = reinterpret_cast<const uint8_t*>(xref);
        // push <EYEPOINT>; mov ecx,<preconstructed Name global>; call <Name ctor thunk>
        if (p[0] != 0x68 || p[5] != 0xB9 || p[10] != 0xE8)
        {
            Log("FAIL EYEPOINT initializer skeleton mismatch");
            return nullptr;
        }

        uint32_t globalAddress = 0;
        std::memcpy(&globalAddress, p + 6, sizeof(globalAddress));

        uintptr_t ctorThunk = ResolveRel32Target(xref + 10);
        if (!ctorThunk)
        {
            Log("FAIL EYEPOINT Name ctor thunk unresolved");
            return nullptr;
        }

        uintptr_t ctorTarget = ctorThunk;
        if (*reinterpret_cast<const uint8_t*>(ctorThunk) == 0xE9)
        {
            int32_t rel = 0;
            std::memcpy(&rel, reinterpret_cast<const void*>(ctorThunk + 1), sizeof(rel));
            ctorTarget = ctorThunk + 5 + static_cast<intptr_t>(rel);
        }

        if (!NameCtor || ctorTarget != reinterpret_cast<uintptr_t>(NameCtor))
        {
            Log("FAIL EYEPOINT initializer does not resolve to proven NameCtor");
            return nullptr;
        }

        const uintptr_t moduleBase = reinterpret_cast<uintptr_t>(g_engine);
        const uintptr_t moduleEnd =
            moduleBase + static_cast<uintptr_t>(nt->OptionalHeader.SizeOfImage);
        const uintptr_t nameAddress = static_cast<uintptr_t>(globalAddress);

        if (!globalAddress ||
            nameAddress < moduleBase ||
            nameAddress + sizeof(EngineName) < nameAddress ||
            nameAddress + sizeof(EngineName) > moduleEnd ||
            !IsReadableMemory(reinterpret_cast<const void*>(nameAddress), sizeof(EngineName)))
        {
            Log("FAIL EYEPOINT Name global outside/unreadable in engine image");
            return nullptr;
        }

        Log("PASS EYEPOINT Name global RVA=0x%08X",
            static_cast<unsigned>(nameAddress - moduleBase));
        return reinterpret_cast<EngineName*>(nameAddress);
    }

    bool IsReadableMemory(const void* ptr, size_t bytes)
    {
        if (!ptr || bytes == 0)
            return false;
        MEMORY_BASIC_INFORMATION mbi{};
        if (!VirtualQuery(ptr, &mbi, sizeof(mbi)) || mbi.State != MEM_COMMIT)
            return false;
        const DWORD prot = mbi.Protect & 0xFFu;
        if (prot == PAGE_NOACCESS || (mbi.Protect & PAGE_GUARD))
            return false;
        const uintptr_t start = reinterpret_cast<uintptr_t>(ptr);
        const uintptr_t end = start + bytes;
        const uintptr_t regionEnd = reinterpret_cast<uintptr_t>(mbi.BaseAddress) + mbi.RegionSize;
        return end >= start && end <= regionEnd;
    }

    void PushLuaBool(int L, bool value)
    {
        if (LuaPushBoolean)
            LuaPushBoolean(L, value ? 1 : 0);
    }

    void* ResolveLuaGOHObject(int L, int stackIndex)
    {
        if (!LuaToUserData || !g_gohTableGlobal)
            return nullptr;

        const uintptr_t encoded =
            reinterpret_cast<uintptr_t>(LuaToUserData(L, stackIndex));
        if (encoded > 0xFFFFFFFFu)
            return nullptr;

        const uint32_t raw = static_cast<uint32_t>(encoded);
        const uint16_t index = static_cast<uint16_t>(raw >> 16);
        const uint16_t generation = static_cast<uint16_t>(raw & 0xFFFFu);
        if (index == 0xFFFFu || generation == 0xFFFFu)
            return nullptr;

        const uintptr_t gohTable = *g_gohTableGlobal;
        if (!gohTable || index >= 0x1800u)
            return nullptr;

        const uintptr_t slot = gohTable + static_cast<uintptr_t>(index) * 8u;
        if (!IsReadableMemory(reinterpret_cast<const void*>(slot), 8))
            return nullptr;

        const uint16_t storedGeneration =
            *reinterpret_cast<const uint16_t*>(slot + 4);
        if (storedGeneration != generation)
            return nullptr;

        return *reinterpret_cast<void* const*>(slot);
    }

    bool FiniteVec(const Vec3& v)
    {
        return std::isfinite(v.x) && std::isfinite(v.y) && std::isfinite(v.z);
    }

    float Distance(const Vec3& a, const Vec3& b)
    {
        const float dx = a.x - b.x;
        const float dy = a.y - b.y;
        const float dz = a.z - b.z;
        return std::sqrt(dx * dx + dy * dy + dz * dz);
    }

    void CleanupLaserSightHandles()
    {
        if (!LaserHandleValid || !LaserHandleRelease)
            return;

        for (int32_t& handle : g_laserSightHandles)
        {
            if (handle == -1)
                continue;

            if (LaserHandleValid(&handle))
            {
                LaserHandleRelease(&handle, 0);
                Log("LaserSight one-shot handle released");
            }
            else
            {
                handle = -1;
            }
        }
    }

    bool SubmitLaserSightEvent(int slot, const Vec3& from, const Vec3& to,
                               float thickness, float r, float g, float b, float a)
    {
        if (slot < 0 || slot >= 2 || !FiniteVec(from) || !FiniteVec(to) ||
            !g_laserShaderGatePassed || !g_laserShader ||
            !LaserEventAlloc || !LaserHandleAlloc || !LaserHandleValid ||
            !LaserHandleRelease || !LaserSubmit || !RenderContext ||
            !g_renderEventGlobalSlot || !g_laserSightCallback)
            return false;

        if (!IsReadableMemory(g_laserShader, sizeof(void*)) ||
            !IsReadableMemory(*reinterpret_cast<void**>(g_laserShader), sizeof(void*)))
        {
            Log("LaserSight REFUSED: cached shader/vtable is no longer readable");
            g_laserShaderGatePassed = false;
            g_laserOneShotPassed = false;
            g_laserHeldStabilityPassed = false;
            g_laserHeldSubmitFrames = 0;
            return false;
        }

        if (g_laserSightHandles[slot] != -1)
        {
            Log("LaserSight REFUSED: slot %d still owns a live handle; wait for next GOM cleanup", slot);
            return false;
        }

        if (*g_renderEventGlobalSlot != nullptr)
        {
            Log("LaserSight REFUSED: engine render-event staging slot is already occupied");
            return false;
        }

        int32_t handle = -1;
        int32_t* handleResult = LaserHandleAlloc(&handle, nullptr, 1);
        if (handleResult != &handle || handle == -1 || !LaserHandleValid(&handle))
        {
            Log("F14 FAIL: LaserSight handle allocation/validation failed");
            return false;
        }

        LaserSightPayload* payload = LaserEventAlloc(g_laserSightCallback);
        if (!*g_renderEventGlobalSlot || reinterpret_cast<uintptr_t>(payload) < 0x10000u)
        {
            LaserHandleRelease(&handle, 0);
            Log("F14 FAIL: StructRenderEvent<LaserSightStruct> allocation failed");
            return false;
        }

        payload->handle = handle;
        payload->context = RenderContext();
        payload->flag = 0;
        payload->pad09[0] = payload->pad09[1] = payload->pad09[2] = 0;
        payload->endpointA = from;
        payload->endpointB = to;
        payload->thickness = thickness;
        payload->r = r;
        payload->g = g;
        payload->b = b;
        payload->a = a;
        payload->shader = g_laserShader;

        g_laserSightHandles[slot] = handle;
        LaserSubmit();

        if (*g_renderEventGlobalSlot != nullptr)
        {
            Log("F14 FAIL: render-event submit did not clear staging slot");
            return false;
        }
        return true;
    }

    int __cdecl LuaLaserSightShaderProbeHook(int L)
    {
        g_laserShaderGatePassed = false;
        g_laserOneShotPassed = false;
        g_laserHeldStabilityPassed = false;
        g_laserHeldSubmitFrames = 0;
        g_laserShader = nullptr;

        bool ok = false;
        if (ShaderLookup && g_shaderManagerSlot && *g_shaderManagerSlot &&
            g_protoLitGlowNameGlobal && LuaPushBoolean)
        {
            void* shader =
                ShaderLookup(*g_shaderManagerSlot, g_protoLitGlowNameGlobal);
            if (shader && IsReadableMemory(shader, sizeof(void*)))
            {
                void* vtable = *reinterpret_cast<void**>(shader);
                if (vtable && IsReadableMemory(vtable, sizeof(void*)))
                {
                    g_laserShader = shader;
                    g_laserShaderGatePassed = true;
                    ok = true;
                    Log("F13 PASS: proto_lit_glow resolved as pure3d::Shader*=%p vtable=%p",
                        shader, vtable);
                }
            }
        }

        if (!ok)
            Log("F13 FAIL: allowlisted proto_lit_glow shader did not resolve safely");

        PushLuaBool(L, ok);
        return LuaPushBoolean ? 1 : 0;
    }

    int __cdecl LuaLaserSightResetHeldGateHook(int L)
    {
        g_laserHeldStabilityPassed = false;
        g_laserHeldSubmitFrames = 0;
        PushLuaBool(L, true);
        Log("F15 native stability counter reset");
        return LuaPushBoolean ? 1 : 0;
    }

    int __cdecl LuaLaserSightHeldStabilityProbeHook(int L)
    {
        PushLuaBool(L, g_laserHeldStabilityPassed);
        return LuaPushBoolean ? 1 : 0;
    }

    int __cdecl LuaLaserSightSubmitDualHook(int L)
    {
        bool ok = false;

        if (!LuaGetTop || !LuaToNumber || !LuaToUserData || !LuaPushBoolean ||
            !JointLocalToWorld || !g_eyePointNameGlobal)
        {
            Log("F14 FAIL: one or more native bridge primitives unresolved");
            PushLuaBool(L, false);
            return LuaPushBoolean ? 1 : 0;
        }

        const int argc = LuaGetTop(L);
        int submitMode = 0; // 0=F14 one-shot, 1=F15 held, 2=F16 dynamic
        if (argc == 14)
        {
            const float rawMode = LuaToNumber(L, 14);
            if (rawMode > 0.5f && rawMode < 1.5f)
                submitMode = 1;
            else if (rawMode > 1.5f && rawMode < 2.5f)
                submitMode = 2;
            else
            {
                Log("LaserSight REFUSED: unsupported submit mode %.3f", rawMode);
                PushLuaBool(L, false);
                return 1;
            }
        }

        const bool heldSubmit = submitMode == 1;
        const bool dynamicSubmit = submitMode == 2;
        const char* gateLabel = dynamicSubmit ? "F16" : (heldSubmit ? "F15" : "F14");

        if (argc != 13 && argc != 14)
        {
            Log("%s REFUSED: expected 13 args or 14 args with mode 1/2", gateLabel);
            PushLuaBool(L, false);
            return 1;
        }

        if (heldSubmit && !g_laserOneShotPassed)
        {
            Log("F15 REFUSED: native F14 one-shot gate has not passed in this session");
            PushLuaBool(L, false);
            return 1;
        }

        if (dynamicSubmit && !g_laserHeldStabilityPassed)
        {
            Log("F16 REFUSED: native 120-frame held stability gate has not passed");
            PushLuaBool(L, false);
            return 1;
        }

        void* playerObject = ResolveLuaGOHObject(L, 1);
        const Vec3 expectedEye{
            LuaToNumber(L, 2), LuaToNumber(L, 3), LuaToNumber(L, 4)};
        const Vec3 target{
            LuaToNumber(L, 5), LuaToNumber(L, 6), LuaToNumber(L, 7)};
        float halfSep = LuaToNumber(L, 8);
        const float thickness = LuaToNumber(L, 9);
        const float red = LuaToNumber(L, 10);
        const float green = LuaToNumber(L, 11);
        const float blue = LuaToNumber(L, 12);
        const float alpha = LuaToNumber(L, 13);

        if (!playerObject || !FiniteVec(expectedEye) || !FiniteVec(target) ||
            !std::isfinite(halfSep) || !std::isfinite(thickness) ||
            !std::isfinite(red) || !std::isfinite(green) ||
            !std::isfinite(blue) || !std::isfinite(alpha))
        {
            Log("F14 REFUSED: invalid player/NaN/Inf input");
            PushLuaBool(L, false);
            return 1;
        }

        halfSep = std::fabs(halfSep);
        if (halfSep > 0.25f || thickness < 0.001f || thickness > 0.50f ||
            red < 0.0f || red > 1.0f || green < 0.0f || green > 1.0f ||
            blue < 0.0f || blue > 1.0f || alpha < 0.0f || alpha > 1.0f)
        {
            Log("F14 REFUSED: separation/thickness/RGBA outside safety bounds");
            PushLuaBool(L, false);
            return 1;
        }

        const Vec3 centerLocal{0.0f, 0.0f, 0.0f};
        const Vec3 leftLocal{-halfSep, 0.0f, 0.0f};
        const Vec3 rightLocal{halfSep, 0.0f, 0.0f};
        Vec3 actualEye{};
        Vec3 leftEye{};
        Vec3 rightEye{};

        JointLocalToWorld(&actualEye, playerObject, g_eyePointNameGlobal, &centerLocal);
        JointLocalToWorld(&leftEye, playerObject, g_eyePointNameGlobal, &leftLocal);
        JointLocalToWorld(&rightEye, playerObject, g_eyePointNameGlobal, &rightLocal);

        if (!FiniteVec(actualEye) || !FiniteVec(leftEye) || !FiniteVec(rightEye))
        {
            Log("F14 REFUSED: joint-local endpoint transform produced invalid vector");
            PushLuaBool(L, false);
            return 1;
        }

        const float centerError = Distance(actualEye, expectedEye);
        if (!std::isfinite(centerError) || centerError > 0.02f)
        {
            Log("F14 REFUSED: native EYEPOINT center disagrees with fresh Lua getter | error=%.6f",
                centerError);
            PushLuaBool(L, false);
            return 1;
        }

        const float beamDistance = Distance(actualEye, target);
        if (!std::isfinite(beamDistance) || beamDistance < 0.05f || beamDistance > 1200.0f)
        {
            Log("F14 REFUSED: target distance outside 0.05..1200 | distance=%.3f",
                beamDistance);
            PushLuaBool(L, false);
            return 1;
        }

        const bool leftOK =
            SubmitLaserSightEvent(0, leftEye, target, thickness, red, green, blue, alpha);
        const bool rightOK =
            leftOK && SubmitLaserSightEvent(
                1, rightEye, target, thickness, red, green, blue, alpha);

        ok = leftOK && rightOK;
        if (!ok)
        {
            // Do not release a successfully queued first beam in the same call.
            // Match LaserAction lifetime: any allocated/submitted handle is released
            // by CleanupLaserSightHandles() at the beginning of the next GOM tick.
            Log("%s FAIL/PARTIAL: dual LaserSight submit did not complete; any live handle will release next tick",
                gateLabel);
        }
        else if (submitMode == 0)
        {
            g_laserOneShotPassed = true;
            g_laserHeldStabilityPassed = false;
            g_laserHeldSubmitFrames = 0;
            Log("F14 PASS: two real LaserSight render events submitted | centerError=%.6f distance=%.3f",
                centerError, beamDistance);
        }
        else if (heldSubmit)
        {
            if (g_laserHeldSubmitFrames < 0xFFFFFFFFu)
                ++g_laserHeldSubmitFrames;
            if (!g_laserHeldStabilityPassed && g_laserHeldSubmitFrames >= 120u)
            {
                g_laserHeldStabilityPassed = true;
                Log("F15 NATIVE STABILITY PASS: 120 consecutive successful held submits");
            }
        }

        PushLuaBool(L, ok);
        return 1;
    }

    bool ResolvePhysicsOwnerGOH(uint32_t physicsHandle, uint32_t& outRawGOH)
    {
        outRawGOH = 0;
        if (!g_physicsManagerGlobal || !g_gohTableGlobal)
            return false;

        const uintptr_t physicsManager = *g_physicsManagerGlobal;
        const uintptr_t gohTable = *g_gohTableGlobal;
        if (!physicsManager || !gohTable)
            return false;

        const uint16_t physicsIndex = static_cast<uint16_t>(physicsHandle & 0xFFFFu);
        const uint16_t physicsGeneration = static_cast<uint16_t>(physicsHandle >> 16);

        const uint16_t physicsCapacity = *reinterpret_cast<const uint16_t*>(physicsManager + 0x14);
        if (physicsIndex >= physicsCapacity)
            return false;

        const uintptr_t physicsSlots = *reinterpret_cast<const uintptr_t*>(physicsManager + 0x0C);
        if (!physicsSlots)
            return false;

        const uintptr_t physicsSlot = physicsSlots + static_cast<uintptr_t>(physicsIndex) * 8u;
        const uint32_t storedGeneration = *reinterpret_cast<const uint32_t*>(physicsSlot + 4);
        if (static_cast<uint16_t>(storedGeneration) != physicsGeneration)
            return false;

        void* physicsObject = *reinterpret_cast<void* const*>(physicsSlot);
        if (!physicsObject)
            return false;

        void** vtable = *reinterpret_cast<void***>(physicsObject);
        if (!vtable || !vtable[5]) // +0x14
            return false;

        using GetOwnerFn = void*(__thiscall*)(void*);
        auto getOwner = reinterpret_cast<GetOwnerFn>(vtable[5]);
        void* owner = getOwner(physicsObject);
        if (!owner)
            return false;

        // Proven GOH store: 0xC000 bytes / 8 bytes per slot = 0x1800 slots.
        constexpr uint32_t kGOHCapacity = 0x1800u;
        for (uint32_t index = 0; index < kGOHCapacity; ++index)
        {
            const uintptr_t slot = gohTable + static_cast<uintptr_t>(index) * 8u;
            if (*reinterpret_cast<void* const*>(slot) != owner)
                continue;

            const uint16_t generation = *reinterpret_cast<const uint16_t*>(slot + 4);
            outRawGOH = (static_cast<uint32_t>(generation) << 16) | index;
            return true;
        }
        return false;
    }

    int __cdecl LuaLastRayHitGOHHook(int L)
    {
        if (!LuaPushGOH || !g_lastRayHitValid)
            return 0;

        uint32_t physicsHandle = 0;
        std::memcpy(&physicsHandle, g_lastRayHitRecord + 0x08, sizeof(physicsHandle));

        uint32_t rawGOH = 0;
        if (!ResolvePhysicsOwnerGOH(physicsHandle, rawGOH))
            return 0;

        const uint32_t encodedGOH = SwapGOHHalves(rawGOH);
        LuaPushGOH(L, encodedGOH);
        return 1;
    }

    int __cdecl LuaGetCameraFrameHook(int L)
    {
        if (!LuaPushLString || !g_lastRenderCamera)
            return 0;

        const uintptr_t camera = reinterpret_cast<uintptr_t>(g_lastRenderCamera);
        const float* matrix = reinterpret_cast<const float*>(camera + 0x90);
        const float* position = reinterpret_cast<const float*>(camera + 0xC0);

        // Runtime cross-check: the output just returned by
        // cm_GetCurrentRenderCameraPosition must agree with this camera's
        // dedicated position fields before exposing the frame to Lua.
        if (!g_lastRenderCameraPositionValid ||
            !std::isfinite(position[0]) || !std::isfinite(position[1]) ||
            !std::isfinite(position[2]) ||
            std::fabs(position[0] - g_lastRenderCameraPosition.x) > 0.0001f ||
            std::fabs(position[1] - g_lastRenderCameraPosition.y) > 0.0001f ||
            std::fabs(position[2] - g_lastRenderCameraPosition.z) > 0.0001f)
            return 0;

        const float values[12] = {
            position[0], position[1], position[2],
            matrix[0], matrix[1], matrix[2],
            matrix[4], matrix[5], matrix[6],
            matrix[8], matrix[9], matrix[10]
        };
        for (float value : values)
        {
            if (!std::isfinite(value))
                return 0;
        }

        char buffer[384]{};
        const int n = std::snprintf(
            buffer, sizeof(buffer),
            "%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g",
            values[0], values[1], values[2], values[3], values[4], values[5],
            values[6], values[7], values[8], values[9], values[10], values[11]);
        if (n <= 0 || static_cast<size_t>(n) >= sizeof(buffer))
            return 0;

        LuaPushLString(L, buffer, static_cast<size_t>(n));
        return 1;
    }

    void InstallLuaBridges(int L)
    {
        if (!LuaPushCClosure || !LuaSetField)
            return;

        LuaPushCClosure(L, reinterpret_cast<void*>(&LuaLogHook), 0);
        LuaSetField(L, LUA_GLOBALSINDEX, "HL_Log");

        LuaPushCClosure(L, reinterpret_cast<void*>(&LuaGetCameraFrameHook), 0);
        LuaSetField(L, LUA_GLOBALSINDEX, "HL_GetCameraFrame");

        LuaPushCClosure(L, reinterpret_cast<void*>(&LuaLastRayHitGOHHook), 0);
        LuaSetField(L, LUA_GLOBALSINDEX, "HL_LastRayHitGOH");

        LuaPushCClosure(L, reinterpret_cast<void*>(&LuaLaserSightShaderProbeHook), 0);
        LuaSetField(L, LUA_GLOBALSINDEX, "HL_LaserSightShaderProbe");

        LuaPushCClosure(L, reinterpret_cast<void*>(&LuaLaserSightSubmitDualHook), 0);
        LuaSetField(L, LUA_GLOBALSINDEX, "HL_LaserSightSubmitDual");

        Log("Installed Lua bridges: HL_Log, HL_GetCameraFrame, HL_LastRayHitGOH, HL_LaserSightShaderProbe, HL_LaserSightSubmitDual");
    }

    bool CallLua0(int L, const char* name, bool logFailure = true)
    {
        if (!LuaGetField || !LuaPcall || !LuaGetTop || !LuaSetTop)
            return false;

        const int top = LuaGetTop(L);
        LuaGetField(L, LUA_GLOBALSINDEX, name);
        const int rc = LuaPcall(L, 0, 0, 0);
        if (rc != 0)
        {
            if (logFailure)
                Log("Lua callback failed [%s]: %s", name, LuaErrorString(L).c_str());
            LuaSetTop(L, top);
            return false;
        }
        LuaSetTop(L, top);
        return true;
    }

    bool Held(int vk)
    {
        return (GetAsyncKeyState(vk) & 0x8000) != 0;
    }

    bool RisingEdge(int vk, bool& previous, bool inputEnabled)
    {
        const bool now = inputEnabled && Held(vk);
        const bool rising = now && !previous;
        previous = now;
        return rising;
    }

    void SetLuaBoolString(int L, const char* name, bool value)
    {
        if (!LuaPushLString || !LuaSetField)
            return;
        const char* s = value ? "1" : "0";
        LuaPushLString(L, s, 1);
        LuaSetField(L, LUA_GLOBALSINDEX, name);
    }

    void PublishHeldInput(int L, bool inputEnabled)
    {
        SetLuaBoolString(L, "HL_KEY_W", inputEnabled && Held('W'));
        SetLuaBoolString(L, "HL_KEY_S", inputEnabled && Held('S'));
        SetLuaBoolString(L, "HL_KEY_A", inputEnabled && Held('A'));
        SetLuaBoolString(L, "HL_KEY_D", inputEnabled && Held('D'));
        SetLuaBoolString(L, "HL_KEY_SPACE", inputEnabled && Held(VK_SPACE));
        SetLuaBoolString(L, "HL_KEY_C", inputEnabled && Held('C'));
        SetLuaBoolString(L, "HL_KEY_CTRL", inputEnabled && (Held(VK_LCONTROL) || Held(VK_RCONTROL)));
        SetLuaBoolString(L, "HL_KEY_SHIFT", inputEnabled && (Held(VK_LSHIFT) || Held(VK_RSHIFT)));
        SetLuaBoolString(L, "HL_BRIDGE_READY", true);
    }

    void BootstrapLuaState(int L)
    {
        g_scriptsReady = false;
        InstallLuaBridges(L);

        // runtime probe is read-only; definition files below do not mutate physics at load time.
        ExecuteLuaFile(L, "lua_p1\\runtime_probe.lua");
        const bool setter = ExecuteLuaFile(L, "lua_p1\\setter_echo_probe.lua");
        const bool math = ExecuteLuaFile(L, "lua_p1\\flight_math_probe.lua");
        const bool controller = ExecuteLuaFile(L, "lua_p1\\flight_controller_v1.lua");
        const bool heatProbe = ExecuteLuaFile(L, "lua_p1\\heatvision_probe.lua");
        g_freeAimReady = ExecuteLuaFile(L, "lua_p1\\freeaim_probe_v004_STAGED.lua");
        g_localOffsetReady = ExecuteLuaFile(L, "lua_p1\\freeaim_local_offset_probe_v005_STAGED.lua");
        g_eyeOriginReady = ExecuteLuaFile(L, "lua_p1\\eye_origin_probe_v006_STAGED.lua");
        g_dualEyeRenderReady = ExecuteLuaFile(L, "lua_p1\\dual_eye_freeaim_render_v007_STAGED.lua");
        g_laserSightNativeReady = ExecuteLuaFile(L, "lua_p1\\lasersight_native_gate_v008_STAGED.lua");
        g_laserSightHeldReady = ExecuteLuaFile(L, "lua_p1\\lasersight_held_gate_v009_STAGED.lua");

        g_laserShaderGatePassed = false;
        g_laserOneShotPassed = false;
        g_laserHeldStabilityPassed = false;
        g_laserHeldSubmitFrames = 0;
        g_laserShader = nullptr;
        CleanupLaserSightHandles();

        g_scriptsReady = setter && math && controller;
        g_f4Prev = g_f5Prev = g_f6Prev = g_f7Prev = g_f8Prev = g_f9Prev = g_f10Prev =
            g_f11Prev = g_f12Prev = g_f13Prev = g_f14Prev = g_f15Prev = false;
        Log("Lua bootstrap scriptsReady=%s heatProbe=%s freeAim=%s localOffset=%s eyeOrigin=%s dualEyeRender=%s laserSightNative=%s heldLaserSight=%s",
            g_scriptsReady ? "true" : "false",
            heatProbe ? "true" : "false",
            g_freeAimReady ? "true" : "false",
            g_localOffsetReady ? "true" : "false",
            g_eyeOriginReady ? "true" : "false",
            g_dualEyeRenderReady ? "true" : "false",
            g_laserSightNativeReady ? "true" : "false",
            g_laserSightHeldReady ? "true" : "false");
    }

    void BridgeTick(int L)
    {
        if (L != g_lastLuaState)
        {
            g_lastLuaState = L;
            BootstrapLuaState(L);
        }

        if (!g_window || !IsWindow(g_window))
            g_window = FindWindowA("prototypeWindowClass", nullptr);

        // Mimic LaserAction lifecycle: a one-shot F14 handle survives one update
        // and is released at the beginning of the next GOM tick.
        CleanupLaserSightHandles();

        const bool inputEnabled = g_window && GetForegroundWindow() == g_window;
        PublishHeldInput(L, inputEnabled);

        if (!inputEnabled && g_laserSightHeldReady)
            CallLua0(L, "Homelander_LaserSightHeldForceDisableV009", false);

        if (!g_scriptsReady)
            return;

        if (RisingEdge(VK_F4, g_f4Prev, inputEnabled))
        {
            Log("F4: read-only discovery + flight math probe");
            ExecuteLuaFile(L, "lua_p1\\runtime_probe.lua");
            CallLua0(L, "Homelander_FlightMathProbe_Verified");
        }

        if (RisingEdge(VK_F5, g_f5Prev, inputEnabled))
        {
            Log("F5: player rediscovery + setter echo gate");
            ExecuteLuaFile(L, "lua_p1\\runtime_probe.lua");
            CallLua0(L, "Homelander_SetterEchoProbe_Verified");
        }

        if (RisingEdge(VK_F6, g_f6Prev, inputEnabled))
        {
            Log("F6: flight enable requested");
            CallLua0(L, "Homelander_FlightEnableVerified");
        }

        if (RisingEdge(VK_F7, g_f7Prev, inputEnabled))
        {
            Log("F7: flight disable requested");
            CallLua0(L, "Homelander_FlightDisable");
        }

        if (RisingEdge(VK_F8, g_f8Prev, inputEnabled))
        {
            Log("F8: read-only heat-vision acquisition probe");
            CallLua0(L, "Homelander_HeatVisionAcquisitionProbe");
        }

        if (RisingEdge(VK_F9, g_f9Prev, inputEnabled))
        {
            if (g_freeAimReady)
            {
                Log("F9: read-only free-aim camera/LOS probe");
                CallLua0(L, "Homelander_FreeAimProbe");
            }
            else
            {
                Log("F9 ignored: free-aim staged Lua did not load");
            }
        }

        if (RisingEdge(VK_F10, g_f10Prev, inputEnabled))
        {
            if (g_localOffsetReady)
            {
                Log("F10: read-only free-aim target-local roundtrip probe");
                CallLua0(L, "Homelander_FreeAimLocalOffsetProbe");
            }
            else
            {
                Log("F10 ignored: local-offset staged Lua did not load");
            }
        }

        if (RisingEdge(VK_F11, g_f11Prev, inputEnabled))
        {
            if (g_eyeOriginReady)
            {
                Log("F11: read-only EYEPOINT verification probe");
                CallLua0(L, "Homelander_EyeOriginProbeV006");
            }
            else
            {
                Log("F11 ignored: eye-origin staged Lua did not load");
            }
        }

        if (RisingEdge(VK_F12, g_f12Prev, inputEnabled))
        {
            if (g_dualEyeRenderReady)
            {
                Log("F12: legacy ai_Laser falsification probe (not final renderer)");
                CallLua0(L, "Homelander_DualEyeFreeAimRenderProbe");
            }
            else
            {
                Log("F12 ignored: dual-eye render staged Lua did not load");
            }
        }

        if (RisingEdge(VK_F13, g_f13Prev, inputEnabled))
        {
            if (g_laserSightNativeReady)
            {
                Log("F13: read-only pure3d::Shader resolution gate");
                CallLua0(L, "Homelander_LaserSightShaderProbeV008");
            }
            else
            {
                Log("F13 ignored: native LaserSight staged Lua did not load");
            }
        }

        if (RisingEdge(VK_F14, g_f14Prev, inputEnabled))
        {
            if (g_laserSightNativeReady)
            {
                Log("F14: one-shot REAL LaserSight dual-eye render event");
                CallLua0(L, "Homelander_LaserSightOneShotV008");
            }
            else
            {
                Log("F14 ignored: native LaserSight staged Lua did not load");
            }
        }

        if (RisingEdge(VK_F15, g_f15Prev, inputEnabled))
        {
            if (g_laserSightHeldReady)
            {
                Log("F15: toggle held native LaserSight at F10-proven impact point");
                CallLua0(L, "Homelander_LaserSightHeldToggleV009");
            }
            else
            {
                Log("F15 ignored: held LaserSight staged Lua did not load");
            }
        }

        if (inputEnabled && g_laserSightHeldReady)
            CallLua0(L, "Homelander_LaserSightHeldTickV009", false);

        // Silent while disabled. The Lua controller returns immediately.
        CallLua0(L, "Homelander_FlightNativeTick", false);
    }

    int __stdcall GOMUpdateHook(int a1, int a2, float deltaTime)
    {
        const int L = GetLuaState();
        if (L != 0)
            BridgeTick(L);

        return g_originalGOMUpdate ? g_originalGOMUpdate(a1, a2, deltaTime) : 0;
    }

    bool FitsRel32(uintptr_t fromAfterInstruction, uintptr_t to)
    {
        const int64_t d = static_cast<int64_t>(to) - static_cast<int64_t>(fromAfterInstruction);
        return d >= std::numeric_limits<int32_t>::min() && d <= std::numeric_limits<int32_t>::max();
    }

    bool WriteBranch(uint8_t* site, uint8_t opcode, uintptr_t destination)
    {
        const uintptr_t next = reinterpret_cast<uintptr_t>(site + 5);
        if (!FitsRel32(next, destination))
            return false;
        const int32_t rel = static_cast<int32_t>(static_cast<int64_t>(destination) - static_cast<int64_t>(next));
        site[0] = opcode;
        std::memcpy(site + 1, &rel, sizeof(rel));
        return true;
    }

    extern "C" void __cdecl HL_CaptureRayCollisionRecord(const void* record)
    {
        if (!record)
        {
            g_lastRayHitValid = false;
            std::memset(g_lastRayHitRecord, 0, sizeof(g_lastRayHitRecord));
            return;
        }

        std::memcpy(g_lastRayHitRecord, record, sizeof(g_lastRayHitRecord));
        g_lastRayHitValid = true;
    }

    Vec3* __fastcall RenderCameraPositionHook(void* self, void*, Vec3* out)
    {
        Vec3* result = g_originalRenderCameraPosition ?
            g_originalRenderCameraPosition(self, out) : out;

        g_lastRenderCamera = nullptr;
        g_lastRenderCameraPositionValid = false;
        if (!self)
            return result;

        const uintptr_t state = *reinterpret_cast<const uintptr_t*>(
            reinterpret_cast<uintptr_t>(self) + 0x14);
        if (!state)
            return result;

        g_lastRenderCamera = *reinterpret_cast<void* const*>(state + 0x44);
        if (g_lastRenderCamera && out &&
            std::isfinite(out->x) && std::isfinite(out->y) && std::isfinite(out->z))
        {
            g_lastRenderCameraPosition = *out;
            g_lastRenderCameraPositionValid = true;
        }
        return result;
    }

    void RestoreRenderCameraHook()
    {
        if (!g_renderCameraTarget)
            return;
        DWORD oldProtect = 0;
        if (VirtualProtect(g_renderCameraTarget, sizeof(g_originalRenderCameraBytes),
                           PAGE_EXECUTE_READWRITE, &oldProtect))
        {
            std::memcpy(g_renderCameraTarget, g_originalRenderCameraBytes,
                        sizeof(g_originalRenderCameraBytes));
            DWORD ignored = 0;
            VirtualProtect(g_renderCameraTarget, sizeof(g_originalRenderCameraBytes),
                           oldProtect, &ignored);
            FlushInstructionCache(GetCurrentProcess(), g_renderCameraTarget,
                                  sizeof(g_originalRenderCameraBytes));
        }
        g_renderCameraTarget = nullptr;
        g_originalRenderCameraPosition = nullptr;
        g_lastRenderCamera = nullptr;
        g_lastRenderCameraPositionValid = false;
    }

    bool InstallRenderCameraHook(uintptr_t address)
    {
        auto target = reinterpret_cast<uint8_t*>(address);
        if (!target)
            return false;

        const uint8_t expected[5] = {0x8B, 0x41, 0x14, 0x85, 0xC0};
        if (std::memcmp(target, expected, sizeof(expected)) != 0)
        {
            Log("FAIL render-camera prologue validation");
            return false;
        }

        auto trampoline = reinterpret_cast<uint8_t*>(
            VirtualAlloc(nullptr, 16, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE));
        if (!trampoline)
        {
            Log("FAIL VirtualAlloc render-camera trampoline");
            return false;
        }

        std::memcpy(trampoline, target, 5);
        if (!WriteBranch(trampoline + 5, 0xE9, reinterpret_cast<uintptr_t>(target + 5)))
        {
            Log("FAIL render-camera trampoline rel32");
            VirtualFree(trampoline, 0, MEM_RELEASE);
            return false;
        }

        std::memcpy(g_originalRenderCameraBytes, target, sizeof(g_originalRenderCameraBytes));
        DWORD oldProtect = 0;
        if (!VirtualProtect(target, 5, PAGE_EXECUTE_READWRITE, &oldProtect))
        {
            Log("FAIL VirtualProtect render-camera target");
            VirtualFree(trampoline, 0, MEM_RELEASE);
            return false;
        }

        const bool ok = WriteBranch(target, 0xE9,
            reinterpret_cast<uintptr_t>(&RenderCameraPositionHook));

        DWORD ignored = 0;
        VirtualProtect(target, 5, oldProtect, &ignored);
        FlushInstructionCache(GetCurrentProcess(), target, 5);

        if (!ok)
        {
            Log("FAIL render-camera hook rel32");
            VirtualFree(trampoline, 0, MEM_RELEASE);
            return false;
        }

        g_renderCameraTarget = target;
        g_originalRenderCameraPosition =
            reinterpret_cast<RenderCameraPositionFn>(trampoline);
        Log("PASS render-camera capture hook RVA=0x%08X",
            static_cast<unsigned>(address - reinterpret_cast<uintptr_t>(g_engine)));
        return true;
    }

    void RestoreLineOfSightCaptureHook()
    {
        if (g_lineOfSightCaptureTarget)
        {
            DWORD oldProtect = 0;
            if (VirtualProtect(g_lineOfSightCaptureTarget,
                               sizeof(g_originalLineOfSightBytes),
                               PAGE_EXECUTE_READWRITE, &oldProtect))
            {
                std::memcpy(g_lineOfSightCaptureTarget, g_originalLineOfSightBytes,
                            sizeof(g_originalLineOfSightBytes));
                DWORD ignored = 0;
                VirtualProtect(g_lineOfSightCaptureTarget,
                               sizeof(g_originalLineOfSightBytes),
                               oldProtect, &ignored);
                FlushInstructionCache(GetCurrentProcess(), g_lineOfSightCaptureTarget,
                                      sizeof(g_originalLineOfSightBytes));
            }
        }
        if (g_lineOfSightCaptureStub)
            VirtualFree(g_lineOfSightCaptureStub, 0, MEM_RELEASE);

        g_lineOfSightCaptureTarget = nullptr;
        g_lineOfSightCaptureStub = nullptr;
        g_lastRayHitValid = false;
        std::memset(g_lastRayHitRecord, 0, sizeof(g_lastRayHitRecord));
    }

    bool InstallLineOfSightCaptureHook(uintptr_t address)
    {
        auto target = reinterpret_cast<uint8_t*>(address);
        if (!target)
            return false;

        const uint8_t expected[6] = {0x8B, 0x74, 0x24, 0x14, 0x6A, 0x00};
        if (std::memcmp(target, expected, sizeof(expected)) != 0)
        {
            Log("FAIL LOS capture-site validation");
            return false;
        }

        auto stub = reinterpret_cast<uint8_t*>(
            VirtualAlloc(nullptr, 64, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE));
        if (!stub)
        {
            Log("FAIL VirtualAlloc LOS capture stub");
            return false;
        }

        size_t p = 0;
        // Replay overwritten instructions:
        //   mov esi,[esp+14h]
        //   push 0
        const uint8_t replay[] = {0x8B,0x74,0x24,0x14,0x6A,0x00};
        std::memcpy(stub + p, replay, sizeof(replay)); p += sizeof(replay);

        // Preserve flags and GPRs around the C helper.
        stub[p++] = 0x9C; // pushfd
        stub[p++] = 0x60; // pushad
        stub[p++] = 0x56; // push esi

        const size_t callOffset = p;
        p += 5;
        const uint8_t addEsp4[] = {0x83,0xC4,0x04};
        std::memcpy(stub + p, addEsp4, sizeof(addEsp4)); p += sizeof(addEsp4);
        stub[p++] = 0x61; // popad
        stub[p++] = 0x9D; // popfd

        const size_t jumpOffset = p;
        p += 5;

        if (!WriteBranch(stub + callOffset, 0xE8,
                         reinterpret_cast<uintptr_t>(&HL_CaptureRayCollisionRecord)) ||
            !WriteBranch(stub + jumpOffset, 0xE9,
                         reinterpret_cast<uintptr_t>(target + 6)))
        {
            Log("FAIL LOS capture-stub rel32");
            VirtualFree(stub, 0, MEM_RELEASE);
            return false;
        }

        std::memcpy(g_originalLineOfSightBytes, target,
                    sizeof(g_originalLineOfSightBytes));
        DWORD oldProtect = 0;
        if (!VirtualProtect(target, 6, PAGE_EXECUTE_READWRITE, &oldProtect))
        {
            Log("FAIL VirtualProtect LOS capture target");
            VirtualFree(stub, 0, MEM_RELEASE);
            return false;
        }

        const bool ok = WriteBranch(target, 0xE9,
            reinterpret_cast<uintptr_t>(stub));
        if (ok)
            target[5] = 0x90;

        DWORD ignored = 0;
        VirtualProtect(target, 6, oldProtect, &ignored);
        FlushInstructionCache(GetCurrentProcess(), target, 6);

        if (!ok)
        {
            Log("FAIL LOS capture hook rel32");
            VirtualFree(stub, 0, MEM_RELEASE);
            return false;
        }

        g_lineOfSightCaptureTarget = target;
        g_lineOfSightCaptureStub = stub;
        Log("PASS LOS collision-record capture hook RVA=0x%08X",
            static_cast<unsigned>(address - reinterpret_cast<uintptr_t>(g_engine)));
        return true;
    }

    bool InstallGOMUpdateHook(uintptr_t address)
    {
        auto target = reinterpret_cast<uint8_t*>(address);
        if (!target)
            return false;

        // Signature guarantees: push ebx; push ebp; push esi; push edi; call rel32
        if (target[0] != 0x53 || target[1] != 0x55 || target[2] != 0x56 ||
            target[3] != 0x57 || target[4] != 0xE8)
        {
            Log("FAIL GOM prologue validation");
            return false;
        }

        std::memcpy(g_originalGOMBytes, target, sizeof(g_originalGOMBytes));

        int32_t originalCallRel = 0;
        std::memcpy(&originalCallRel, target + 5, sizeof(originalCallRel));
        const uintptr_t originalCallTarget =
            reinterpret_cast<uintptr_t>(target + 9) + originalCallRel;

        auto trampoline = reinterpret_cast<uint8_t*>(
            VirtualAlloc(nullptr, 32, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE));
        if (!trampoline)
        {
            Log("FAIL VirtualAlloc trampoline");
            return false;
        }

        std::memcpy(trampoline, target, 4);
        if (!WriteBranch(trampoline + 4, 0xE8, originalCallTarget) ||
            !WriteBranch(trampoline + 9, 0xE9, reinterpret_cast<uintptr_t>(target + 9)))
        {
            Log("FAIL trampoline rel32 range");
            VirtualFree(trampoline, 0, MEM_RELEASE);
            return false;
        }

        DWORD oldProtect = 0;
        if (!VirtualProtect(target, 9, PAGE_EXECUTE_READWRITE, &oldProtect))
        {
            Log("FAIL VirtualProtect GOM target");
            VirtualFree(trampoline, 0, MEM_RELEASE);
            return false;
        }

        const bool hookBranchOk = WriteBranch(target, 0xE9, reinterpret_cast<uintptr_t>(&GOMUpdateHook));
        if (hookBranchOk)
            std::memset(target + 5, 0x90, 4);

        DWORD ignored = 0;
        VirtualProtect(target, 9, oldProtect, &ignored);
        FlushInstructionCache(GetCurrentProcess(), target, 9);

        if (!hookBranchOk)
        {
            Log("FAIL hook rel32 range");
            VirtualFree(trampoline, 0, MEM_RELEASE);
            return false;
        }

        g_gomTarget = target;
        g_originalGOMUpdate = reinterpret_cast<GOMUpdateFn>(trampoline);
        Log("PASS GOM hook installed RVA=0x%08X", static_cast<unsigned>(address - reinterpret_cast<uintptr_t>(g_engine)));
        return true;
    }

    bool ResolveRuntime()
    {
        const uintptr_t pcall = RequireUnique("LuaPcall", kSigLuaPcall);
        const uintptr_t getfield = RequireUnique("LuaGetField", kSigLuaGetField);
        const uintptr_t settop = RequireUnique("LuaSetTop", kSigLuaSetTop);
        const uintptr_t gettop = RequireUnique("LuaGetTop", kSigLuaGetTop);
        const uintptr_t tolstring = RequireUnique("LuaToLString", kSigLuaToLString);
        const uintptr_t loadbuffer = RequireUnique("LuaLoadBuffer", kSigLuaLoadBuffer);
        const uintptr_t pushc = RequireUnique("LuaPushCClosure", kSigLuaPushCClosure);
        const uintptr_t pushls = RequireUnique("LuaPushLString", kSigLuaPushLString);
        const uintptr_t setfield = RequireUnique("LuaSetField", kSigLuaSetField);
        const uintptr_t pushgoh = RequireUnique("LuaPushGOH", kSigLuaPushGOH);
        const uintptr_t managerRef = RequireUnique("LuaManager", kSigLuaManager);
        const uintptr_t gom = RequireUnique("GOMUpdate", kSigGOMUpdate);
        const uintptr_t renderCamera =
            RequireUnique("RenderCameraPosition", kSigRenderCameraPosition);
        const uintptr_t losCapture =
            RequireUnique("LineOfSightCapture", kSigLineOfSightCapture);

        const uintptr_t luaToUserData =
            RequireUnique("LuaToUserData", kSigLuaToUserData);
        const uintptr_t luaToNumber =
            RequireUnique("LuaToNumber", kSigLuaToNumber);
        const uintptr_t luaPushBoolean =
            RequireUnique("LuaPushBoolean", kSigLuaPushBoolean);
        const uintptr_t nameCtor =
            RequireUnique("NameCtor", kSigNameCtor);
        const uintptr_t jointLocalToWorld =
            RequireUnique("JointLocalToWorld", kSigJointLocalToWorld);
        const uintptr_t laserShaderRoute =
            RequireUnique("LaserShaderRoute", kSigLaserShaderRoute);
        const uintptr_t laserEventCreate =
            RequireUnique("LaserEventCreate", kSigLaserEventCreate);
        const uintptr_t laserCleanupRoute =
            RequireUnique("LaserCleanupRoute", kSigLaserCleanupRoute);
        const uintptr_t laserSubmit =
            RequireUnique("LaserSubmit", kSigLaserSubmit);

        // These routines exist in multiple identical specializations. They are
        // accepted only when every match embeds the same absolute global.
        const uintptr_t physicsManagerGlobal =
            RequireConsistentImm32("PhysicsManager", kSigPhysicsManagerRef, 5);
        const uintptr_t gohTableGlobal =
            RequireConsistentImm32("GOHTable", kSigGOHTableRef, 11);

        if (!pcall || !getfield || !settop || !gettop || !tolstring || !loadbuffer ||
            !pushc || !pushls || !setfield || !pushgoh || !managerRef || !gom ||
            !renderCamera || !losCapture || !physicsManagerGlobal || !gohTableGlobal ||
            !luaToUserData || !luaToNumber || !luaPushBoolean || !nameCtor ||
            !jointLocalToWorld || !laserShaderRoute || !laserEventCreate ||
            !laserCleanupRoute || !laserSubmit)
            return false;

        LuaPcall = reinterpret_cast<LuaPcallFn>(pcall);
        LuaGetField = reinterpret_cast<LuaGetFieldFn>(getfield);
        LuaSetTop = reinterpret_cast<LuaSetTopFn>(settop);
        LuaGetTop = reinterpret_cast<LuaGetTopFn>(gettop);
        LuaToLString = reinterpret_cast<LuaToLStringFn>(tolstring);
        LuaLoadBuffer = reinterpret_cast<LuaLoadBufferFn>(loadbuffer);
        LuaPushCClosure = reinterpret_cast<LuaPushCClosureFn>(pushc);
        LuaPushLString = reinterpret_cast<LuaPushLStringFn>(pushls);
        LuaSetField = reinterpret_cast<LuaSetFieldFn>(setfield);
        LuaPushGOH = reinterpret_cast<LuaPushGOHFn>(pushgoh);
        LuaToUserData = reinterpret_cast<LuaToUserDataFn>(luaToUserData);
        LuaToNumber = reinterpret_cast<LuaToNumberFn>(luaToNumber);
        LuaPushBoolean = reinterpret_cast<LuaPushBooleanFn>(luaPushBoolean);
        NameCtor = reinterpret_cast<NameCtorFn>(nameCtor);
        JointLocalToWorld = reinterpret_cast<JointLocalToWorldFn>(jointLocalToWorld);

        // Derive every renderer primitive from unique LaserAction sequences.
        const uintptr_t shaderManagerSlotAddress =
            *reinterpret_cast<const uint32_t*>(laserShaderRoute + 5);
        const uintptr_t shaderLookupTarget =
            ResolveRel32Target(laserShaderRoute + 14);

        const uintptr_t laserCallback =
            *reinterpret_cast<const uint32_t*>(laserEventCreate + 2);
        const uintptr_t laserEventAllocTarget =
            ResolveRel32Target(laserEventCreate + 6);
        const uintptr_t laserHandleAllocTarget =
            ResolveRel32Target(laserEventCreate + 22);
        const uintptr_t renderContextTarget =
            ResolveRel32Target(laserEventCreate + 34);

        const uintptr_t laserHandleValidTarget =
            ResolveRel32Target(laserCleanupRoute + 5);
        const uintptr_t laserHandleReleaseTarget =
            ResolveRel32Target(laserCleanupRoute + 17);

        const uintptr_t renderEventGlobalA =
            *reinterpret_cast<const uint32_t*>(laserSubmit + 1);
        const uintptr_t renderEventGlobalB =
            *reinterpret_cast<const uint32_t*>(laserSubmit + 16);

        if (!shaderManagerSlotAddress || !shaderLookupTarget || !laserCallback ||
            !laserEventAllocTarget || !laserHandleAllocTarget || !renderContextTarget ||
            !laserHandleValidTarget || !laserHandleReleaseTarget ||
            !renderEventGlobalA || renderEventGlobalA != renderEventGlobalB)
        {
            Log("FAIL v006 derived LaserSight route is incomplete/inconsistent");
            return false;
        }

        g_shaderManagerSlot = reinterpret_cast<void**>(shaderManagerSlotAddress);
        g_renderEventGlobalSlot = reinterpret_cast<void**>(renderEventGlobalA);
        g_protoLitGlowNameGlobal = ResolveProtoLitGlowNameGlobal();
        g_eyePointNameGlobal = ResolveEyePointNameGlobal();
        g_laserSightCallback = reinterpret_cast<void*>(laserCallback);
        ShaderLookup = reinterpret_cast<ShaderLookupFn>(shaderLookupTarget);
        LaserEventAlloc = reinterpret_cast<LaserEventAllocFn>(laserEventAllocTarget);
        LaserHandleAlloc = reinterpret_cast<LaserHandleAllocFn>(laserHandleAllocTarget);
        LaserHandleValid = reinterpret_cast<LaserHandleValidFn>(laserHandleValidTarget);
        LaserHandleRelease = reinterpret_cast<LaserHandleReleaseFn>(laserHandleReleaseTarget);
        LaserSubmit = reinterpret_cast<LaserSubmitFn>(laserSubmit);
        RenderContext = reinterpret_cast<RenderContextFn>(renderContextTarget);

        Log("PASS v006 LaserSight route shaderSlot=0x%08X eventSlot=0x%08X callback=0x%08X",
            static_cast<unsigned>(shaderManagerSlotAddress - reinterpret_cast<uintptr_t>(g_engine)),
            static_cast<unsigned>(renderEventGlobalA - reinterpret_cast<uintptr_t>(g_engine)),
            static_cast<unsigned>(laserCallback - reinterpret_cast<uintptr_t>(g_engine)));

        // managerRef points at: 8B 0D <absolute address of global manager slot>
        const uintptr_t slotAddress = *reinterpret_cast<uintptr_t*>(managerRef + 2);
        g_luaScriptManagerSlot = reinterpret_cast<void**>(slotAddress);
        g_physicsManagerGlobal = reinterpret_cast<uintptr_t*>(physicsManagerGlobal);
        g_gohTableGlobal = reinterpret_cast<uintptr_t*>(gohTableGlobal);

        if (!g_luaScriptManagerSlot || !g_physicsManagerGlobal || !g_gohTableGlobal ||
            !g_shaderManagerSlot || !g_renderEventGlobalSlot ||
            !g_protoLitGlowNameGlobal || !g_eyePointNameGlobal ||
            !ShaderLookup || !LaserEventAlloc || !LaserHandleAlloc ||
            !LaserHandleValid || !LaserHandleRelease || !LaserSubmit || !RenderContext)
        {
            Log("FAIL one or more manager/global/native LaserSight slots are null");
            return false;
        }

        if (!InstallRenderCameraHook(renderCamera))
            return false;

        if (!InstallLineOfSightCaptureHook(losCapture))
        {
            RestoreRenderCameraHook();
            return false;
        }

        if (!InstallGOMUpdateHook(gom))
        {
            RestoreLineOfSightCaptureHook();
            RestoreRenderCameraHook();
            return false;
        }

        return true;
    }

    DWORD WINAPI SetupThread(void*)
    {
        g_root = SelfRoot();
        Log("starting; build=%s root=%s", kBuildId, g_root.c_str());

        while (!(g_engine = GetModuleHandleA("prototypeenginef.dll")))
            Sleep(50);

        Log("prototypeenginef.dll base=0x%08X", static_cast<unsigned>(reinterpret_cast<uintptr_t>(g_engine)));

        if (!ResolveRuntime())
        {
            Log("FATAL runtime resolution/hook failed; no gameplay mutation enabled");
            return 0;
        }

        Log("READY build=%s. F4=read-only math, F5=echo gate, F6=enable flight, F7=disable, F8=read-only target, F9=read-only free-aim LOS, F10=read-only target-local roundtrip, F11=read-only EYEPOINT, F12=legacy ai_Laser falsification, F13=read-only shader, F14=real one-shot LaserSight, F15=held LaserSight toggle", kBuildId);
        return 0;
    }
}

BOOL APIENTRY DllMain(HMODULE module, DWORD reason, LPVOID)
{
    if (reason == DLL_PROCESS_ATTACH)
    {
        hl::g_self = module;
        DisableThreadLibraryCalls(module);
        HANDLE thread = CreateThread(nullptr, 0, hl::SetupThread, nullptr, 0, nullptr);
        if (thread)
            CloseHandle(thread);
    }
    return TRUE;
}