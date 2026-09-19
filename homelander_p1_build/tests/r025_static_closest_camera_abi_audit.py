#!/usr/bin/env python3
"""R025: read-only exact-game machine-code fingerprint for one candidate Lua API.

Never imports/executes the engine DLL. Registry byte fingerprints and a thunk
prove a candidate registration relationship in ONE pinned game build, not an
ABI contract, player identity or permission to mutate the running game.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

GAME_SHA = "ed0870eb24ace5565a0245ade42114f0724b881d3d75b793f376e9bb184f8d51"
GAME_SIZE = 20210960
IMAGE_BASE = 0x10000000
REG_VA = 0x1037A4CC
REG_BYTES = bytes.fromhex("68 e7 7a 03 10 68 24 6e df 10 8b ce e8 ff 92 c9 ff")
THUNK_VA = 0x10037AE7
THUNK_BYTES = bytes.fromhex("e9 64 e2 33 00")
IMPL_VA = 0x10375D50
IMPL_PROLOGUE = bytes.fromhex("55 8b ec 83 e4 f8 83 ec 34")
OUTPUT_VA = 0x10375EBA
OUTPUT_BYTES = bytes.fromhex("8b 4c 24 18 8b 75 08 51 56 e8 08 59 46 00")
SELECT_VA = 0x10375E76
SELECT_BYTES = bytes.fromhex("f3 0f 10 4c 24 14 0f 2f c8 76 1a")
NAME_VA = 0x10DF6E24
NAME = b"ai_GetClosestCharacterToCamera\x00"


def audit(blob: bytes, *, pin: bool = True) -> dict:
    digest = hashlib.sha256(blob).hexdigest()
    if pin and (digest != GAME_SHA or len(blob) != GAME_SIZE):
        raise ValueError("not the exact first-live v003 user's engine DLL")
    if blob[:2] != b"MZ":
        raise ValueError("not MZ")
    pe_offset = struct.unpack_from("<I", blob, 0x3C)[0]
    if blob[pe_offset:pe_offset + 4] != b"PE\x00\x00":
        raise ValueError("not PE32")
    machine, num_sections = struct.unpack_from("<HH", blob, pe_offset + 4)
    optsize = struct.unpack_from("<H", blob, pe_offset + 20)[0]
    if machine != 0x14C or blob[pe_offset + 24:pe_offset + 26] != b"\x0b\x01":
        raise ValueError("not x86 PE32")
    opt = pe_offset + 24
    real_base = struct.unpack_from("<I", blob, opt + 28)[0]
    if real_base != IMAGE_BASE:
        raise ValueError("unexpected original DLL preferred imagebase")
    raw_sections = []
    for i in range(num_sections):
        p = opt + optsize + i * 40
        if p + 40 > len(blob):
            raise ValueError("truncated sections")
        label = blob[p:p+8].split(b"\x00", 1)[0].decode("ascii","replace")
        rawsize, raw = struct.unpack_from("<II", blob, p + 16)
        va = struct.unpack_from("<I", blob, p + 12)[0]
        if raw + rawsize > len(blob):
            raise ValueError("section extends beyond file")
        raw_sections.append((label, IMAGE_BASE + va, raw, rawsize))
    def bytes_at(va: int, n: int) -> bytes:
        for label, virtual, raw, size in raw_sections:
            off = va - virtual
            if 0 <= off and off+n <= size:
                return blob[raw+off:raw+off+n]
        raise ValueError("VA is not backed by file section: 0x%08x" % va)
    expectations = ((REG_VA, REG_BYTES), (THUNK_VA, THUNK_BYTES),
                    (IMPL_VA, IMPL_PROLOGUE), (OUTPUT_VA, OUTPUT_BYTES),
                    (SELECT_VA, SELECT_BYTES), (NAME_VA, NAME))
    for address, expected in expectations:
        if bytes_at(address, len(expected)) != expected:
            raise ValueError("original engine function fingerprint mismatch 0x%08x" % address)
    displacement = struct.unpack("<i", THUNK_BYTES[1:5])[0]
    destination = THUNK_VA + 5 + displacement
    if destination != IMPL_VA:
        raise ValueError("registered thunk no longer jumps to inspected implementation")
    return {
        "schema": "p1-r025-exact-engine-closest-camera-candidate-static/1",
        "game_sha256": digest,
        "game_size": len(blob),
        "exact_user_engine_pinned": pin,
        "lua_api_name": "ai_GetClosestCharacterToCamera",
        "registration_va": hex(REG_VA),
        "registration_thunk_va": hex(THUNK_VA),
        "thunk_jump_destination_va": hex(destination),
        "character_search_implementation_va": hex(IMPL_VA),
        "closest_selection_va": hex(SELECT_VA),
        "result_output_va": hex(OUTPUT_VA),
        "source_evidence_level": "exact engine code byte fingerprints, not authenticated runtime GOH",
        "return_may_be_NPC": True,
        "lua_GOH_return_type_tested_in_real_game": False,
        "current_player_identified": False,
        "original_v003_GATE_PASS": False,
        "real_game_execution_performed": False,
        "original_game_files_changed": False,
        "safety": "only a separately authorized read-only Lua observation could test real candidate and online player index; never set HOMELANDER_PLAYER from camera proximity alone",
    }


def selftest():
    b = bytearray(0x400000)
    b[:2] = b"MZ"
    struct.pack_into("<I", b, 0x3C, 0x80)
    b[0x80:0x84] = b"PE\x00\x00"
    struct.pack_into("<HH", b, 0x84, 0x14C, 2)
    struct.pack_into("<H", b, 0x94, 0xE0)
    b[0x98:0x9A] = b"\x0b\x01"
    struct.pack_into("<I", b, 0x98+28, IMAGE_BASE)
    p = 0x80 + 24 + 0xE0
    b[p:p+8] = b".text\x00\x00\x00"
    struct.pack_into("<III", b, p+12, 0x1000, 0x380000, 0x1000)
    p += 40
    b[p:p+8] = b".rdata\x00\x00"
    struct.pack_into("<III", b, p+12, 0xDF0000, 0x7E000, 0x381000)
    # Fixture mappings deliberately use explicit VA->file section offset.
    def map_va(va):
        if va >= 0x10DF0000:\n            return 0x381000 + va - 0x10DF0000\n        return va - IMAGE_BASE
    for va, expected in ((REG_VA, REG_BYTES), (THUNK_VA, THUNK_BYTES),
                         (IMPL_VA, IMPL_PROLOGUE), (OUTPUT_VA, OUTPUT_BYTES),
                         (SELECT_VA, SELECT_BYTES), (NAME_VA, NAME)):
        pos = map_va(va)
        b[pos:pos+len(expected)] = expected
    out = audit(bytes(b), pin=False)
    assert out["lua_api_name"] == "ai_GetClosestCharacterToCamera"
    assert out["thunk_jump_destination_va"] == hex(IMPL_VA)
    assert out["current_player_identified"] is False
    try:
        audit(bytes(b), pin=True)
    except ValueError:
        pass
    else:
        raise AssertionError("synthetic data must not pass genuine user DLL sha256 pin")
    b[map_va(THUNK_VA)] = 0x90
    try:
        audit(bytes(b), pin=False)
    except ValueError:
        pass
    else:
        raise AssertionError("registration trampoline mismatch must fail closed")
    print("P1_R025_STATIC_EXACT_ENGINE_NATIVE_REGISTRATION_TRAMPOLINE_AND_NEGATIVE_FINGERPRINT_PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", type=Path)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.engine is None:
        ap.error("read-only --engine path required unless --selftest")
    print(json.dumps(audit(args.engine.read_bytes()),sort_keys=True,indent=2))


if __name__ == "__main__":
    main()
