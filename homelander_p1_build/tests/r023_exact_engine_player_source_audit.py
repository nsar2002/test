#!/usr/bin/env python3
"""R023: exact-file, READ-ONLY static engine marker audit; never executes the DLL.

Only an exact, NUL-terminated string hit is proven. A hit does not prove a
safe Lua ABI, return type, runtime availability, or player identity; a miss
does not prove that a non-exported internal implementation is absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

EXACT_SHA256 = "ed0870eb24ace5565a0245ade42114f0724b881d3d75b793f376e9bb184f8d51"
EXACT_SIZE = 20210960
# All strings below are selectors for investigation, NOT validated GOH getters.
NAMES = [
    "go_IsPlayer",  # public third-party catalog, NOT an exact game DLL export marker
    "go_GetGOHByName",  # likewise not on this build's observed string table
    "go_FindGOHByName", "go_FindTransientGOHByName", "go_FindGOHByUID",
    "go_GetPosition", "go_IsValid", "ai_GetPhysicsVelocity",
    "online_GetNumPlayers", "online_DeterminePlayerIndex",
    "PlutoConvertIndexToGOH", "PlutoConvertGOHToIndex",
    "cm_SetCameraAvatar", "cm_SetCameraAvatarByName", "cm_GetCameraAvatar",
    "cm_GetGameCamera", "MainCharacter", "ALEX_DEFAULT",
]


def offsets(data: bytes, needle: bytes) -> list[int]:
    # Do not silently misclassify a substring, e.g. go_IsPlayer in go_IsPlayerInVehicle.
    pat = b"(?<![A-Za-z0-9_])" + re.escape(needle) + b"\\x00"
    return [m.start() for m in re.finditer(pat, data)]


def pe_headers(data: bytes) -> tuple[int, list[dict]]:
    if len(data) < 0x100 or data[:2] != b"MZ":
        raise ValueError("not a PE image")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if pe + 24 > len(data) or data[pe:pe + 4] != b"PE\\x00\\x00":
        raise ValueError("PE header absent")
    machine, nsections = struct.unpack_from("<HH", data, pe + 4)
    size_opt = struct.unpack_from("<H", data, pe + 20)[0]
    if machine != 0x14C or not 0 < nsections <= 16:
        raise ValueError("not supported x86 PE image")
    o = pe + 24
    if struct.unpack_from("<H", data, o)[0] != 0x10B:
        raise ValueError("not PE32")
    imagebase = struct.unpack_from("<I", data, o + 28)[0]
    sections = []
    for i in range(nsections):
        p = o + size_opt + i * 40
        if p + 40 > len(data):
            raise ValueError("invalid section table")
        name = data[p:p + 8].split(b"\\x00")[0].decode("ascii", "replace")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, p + 8)
        if raw + rawsize > len(data):
            raise ValueError("section exceeds file size")
        sections.append({"name": name, "rva": va, "raw": raw, "raw_size": rawsize,
                         "virtual_size": vsize})
    return imagebase, sections


def inspect(data: bytes, *, pin: bool = True) -> dict:
    digest = hashlib.sha256(data).hexdigest()
    if pin and (digest != EXACT_SHA256 or len(data) != EXACT_SIZE):
        raise ValueError("not the exact prototypeenginef.dll in user's v003 evidence")
    base, sections = pe_headers(data)
    names = {}
    for key in NAMES:
        hits = offsets(data, key.encode("ascii"))
        locations = []
        for o in hits:
            s = next((x for x in sections
                      if x["raw"] <= o < x["raw"] + x["raw_size"]), None)
            if s is None:
                continue
            va = base + s["rva"] + o - s["raw"]
            # These are file-level byte references, NOT identified function bodies.
            marker = struct.pack("<I", va)
            ref_hits = []
            start = 0
            while len(ref_hits) < 12:
                found = data.find(marker, start)
                if found < 0:
                    break
                start = found + 1
                text = next((x for x in sections
                             if x["name"] == ".text" and
                             x["raw"] <= found < x["raw"] + x["raw_size"]), None)
                if text:
                    ref_hits.append("0x%08x" % (base + text["rva"] + found - text["raw"]))
            locations.append({"file_offset": "0x%08x" % o, "section": s["name"],
                              "rva": "0x%08x" % (va - base),
                              "text_reference_locations": ref_hits})
        names[key] = {"literal_exact_nul_marker": bool(hits),
                      "locations": locations}
    return {
        "schema": "p1-r023-offline-exact-engine-source-audit/1",
        "input_sha256": digest,
        "file_size": len(data),
        "pinned_real_evidence_dll": pin,
        "machine": "PE32 i386",
        "marker_semantics": "Only byte-level exact string marker; never a safe ABI or confirmed player GOH",
        "markers": names,
        "interpretation": {
            "no_authoritative_player_goh_identified": True,
            "go_IsPlayer": "Public catalog marker not confirmed in this exact game DLL; do not call.",
            "go_GetGOHByName": "Public catalog marker not confirmed; do not call.",
            "cm_SetCameraAvatar": "Setter registration only; never invoke as a read-only getter.",
            "PlutoConvertIndexToGOH": "Name visible, index semantics/ABI not validated; do not guess index zero.",
            "MainCharacter": "String is not proof of an in-game GOH name; do not promote to candidate.",
            "next_safe_step": "Trace genuine player GOH provenance from game source/native camera avatar assignment read-only; capture evidence before candidate runtime change.",
        },
    }


def selftest() -> None:
    # A bounded parser test: an approximate PE has synthetic .text/.rdata,
    # and false prefix lookups must not appear as independent API markers.
    b = bytearray(b"\\x00" * 0x600)
    b[:2] = b"MZ"
    struct.pack_into("<I", b, 0x3C, 0x80)
    b[0x80:0x84] = b"PE\\x00\\x00"
    struct.pack_into("<HH", b, 0x84, 0x14C, 2)
    struct.pack_into("<H", b, 0x94, 0xE0)
    struct.pack_into("<H", b, 0x98, 0x10B)
    struct.pack_into("<I", b, 0x98 + 28, 0x10000000)
    p = 0x80 + 24 + 0xE0
    b[p:p + 8] = b".text\\x00\\x00\\x00"
    struct.pack_into("<IIII", b, p + 8, 0x100, 0x1000, 0x100, 0x200)
    p += 40
    b[p:p + 8] = b".rdata\\x00\\x00"
    struct.pack_into("<IIII", b, p + 8, 0x100, 0x2000, 0x100, 0x300)
    b[0x320:0x320 + len(b"go_IsPlayerInVehicle\\x00")] = b"go_IsPlayerInVehicle\\x00"
    b[0x350:0x350 + len(b"go_FindGOHByName\\x00")] = b"go_FindGOHByName\\x00"
    struct.pack_into("<I", b, 0x240, 0x10002050)
    rep = inspect(bytes(b), pin=False)
    assert rep["markers"]["go_FindGOHByName"]["literal_exact_nul_marker"]
    assert not rep["markers"]["go_IsPlayer"]["literal_exact_nul_marker"]
    assert rep["markers"]["go_FindGOHByName"]["locations"][0]["text_reference_locations"] == ["0x10001040"]
    try:
        inspect(bytes(b), pin=True)
    except ValueError:
        pass
    else:
        raise AssertionError("synthetic data must never pass genuine game evidence pin")
    print("P1_R023_READONLY_EXACT_MARKER_PE32_XREF_AND_GAME_HASH_FAILCLOSED_SELFTEST_PASS")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", type=Path,
                    help="existing exact original prototypeenginef.dll (read-only); not an installer")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.engine is None:
        ap.error("--engine is required unless --selftest")
    data = args.engine.read_bytes()
    print(json.dumps(inspect(data), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
