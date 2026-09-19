#!/usr/bin/env python3
import json, re, struct, sys, time
from pathlib import PurePosixPath
import requests

RECORD_ID = 18644411
EXPECTED_KEY = "Ephys_sparse coding.zip"
EXPECTED_MD5 = "c6d63ac25c504db4fc3ee45578d63169"
API = f"https://zenodo.org/api/records/{RECORD_ID}"
OUT = "v6_m4a0_result.json"
RAW_EXTS = {
    ".abf", ".atf", ".dat", ".ibw", ".h5", ".hdf5", ".mat", ".nwb",
    ".smr", ".wcp", ".edr", ".tdms"
}
APL_RE = re.compile(r"(^|[^a-z0-9])apl([^a-z0-9]|$)", re.I)

def fail(cls, reason, **extra):
    r = {
        "classification": cls,
        "reason": reason,
        "guardrails": {
            "archive_member_payload_opened": False,
            "archive_member_decompressed": False,
            "amin_loaded": False,
            "m3f4_residual_used": False,
            "mnq_loaded": False,
            "model_fit": False,
        },
    }
    r.update(extra)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(r, f, indent=2, sort_keys=True)
    print(json.dumps(r, indent=2, sort_keys=True))
    return 0

def range_get(url, start, end):
    headers = {"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
    with requests.get(url, headers=headers, stream=True, timeout=(30, 120), allow_redirects=True) as resp:
        if resp.status_code != 206:
            return None, {"status": resp.status_code, "content_range": resp.headers.get("Content-Range"), "final_url": resp.url}
        cr = resp.headers.get("Content-Range", "")
        data = resp.raw.read(end - start + 1, decode_content=False)
        if len(data) != end - start + 1:
            raise RuntimeError(f"range length mismatch: expected {end-start+1}, got {len(data)}")
        return data, {"status": resp.status_code, "content_range": cr, "final_url": resp.url}

def parse_zip64_extra(extra, need_uncomp, need_comp, need_offset, need_disk):
    vals = {}
    p = 0
    while p + 4 <= len(extra):
        xid, xlen = struct.unpack_from("<HH", extra, p)
        p += 4
        payload = extra[p:p+xlen]
        p += xlen
        if xid != 0x0001:
            continue
        q = 0
        if need_uncomp:
            vals["uncomp"] = struct.unpack_from("<Q", payload, q)[0]; q += 8
        if need_comp:
            vals["comp"] = struct.unpack_from("<Q", payload, q)[0]; q += 8
        if need_offset:
            vals["offset"] = struct.unpack_from("<Q", payload, q)[0]; q += 8
        if need_disk:
            vals["disk"] = struct.unpack_from("<I", payload, q)[0]; q += 4
        return vals
    return vals

def safe_path(name):
    if "\\" in name or name.startswith("/"):
        return False
    p = PurePosixPath(name)
    return not any(part == ".." for part in p.parts)

def main():
    s = requests.Session()
    s.headers.update({
        "Accept": "application/json",
        "User-Agent": "fly-mnq-v6-m4a0-source-audit/1.0"
    })
    meta = None
    meta_diag = []
    for attempt in range(1, 5):
        try:
            resp = s.get(API, timeout=(30, 60))
            diag = {
                "attempt": attempt,
                "status": resp.status_code,
                "content_type": resp.headers.get("Content-Type"),
                "content_length_header": resp.headers.get("Content-Length"),
                "received_bytes": len(resp.content),
            }
            meta_diag.append(diag)
            if resp.status_code == 200 and resp.content:
                try:
                    meta = resp.json()
                    break
                except ValueError:
                    pass
        except requests.RequestException as exc:
            meta_diag.append({"attempt": attempt, "transport_exception": type(exc).__name__})
        if attempt < 4:
            time.sleep(2 ** (attempt - 1))
    if meta is None:
        return fail(
            "BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA",
            "Zenodo record API did not yield valid JSON after frozen bounded retries",
            metadata_transport=meta_diag,
        )
    files = meta.get("files", [])
    matches = [f for f in files if f.get("key") == EXPECTED_KEY]
    if len(matches) != 1:
        return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "exact archive key not uniquely present", zenodo_file_count=len(files), exact_matches=len(matches))
    f = matches[0]
    checksum = f.get("checksum", "")
    if checksum.lower() != f"md5:{EXPECTED_MD5}":
        return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "provider MD5 mismatch", provider_checksum=checksum)
    size = int(f.get("size", 0))
    url = (f.get("links") or {}).get("content")
    if not url or size <= 0:
        return fail(
            "BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA",
            "missing provider content URL or byte size",
            provider_size=size,
            file_object_keys=sorted(f.keys()),
            available_link_keys=sorted((f.get("links") or {}).keys()),
        )

    tail_len = min(size, 1024 * 1024)
    tail_start = size - tail_len
    tail, tmeta = range_get(url, tail_start, size - 1)
    if tail is None:
        return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "provider did not honor value-opaque range request", provider_size=size, range_probe=tmeta)

    eocd_sig = b"PK\x05\x06"
    pos = tail.rfind(eocd_sig)
    if pos < 0 or pos + 22 > len(tail):
        return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "EOCD not found in bounded tail", provider_size=size)
    eocd = struct.unpack_from("<4s4H2LH", tail, pos)
    _, disk_no, cd_disk, disk_entries, total_entries, cd_size32, cd_off32, comment_len = eocd
    if disk_no != 0 or cd_disk != 0:
        return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "multi-disk ZIP is outside frozen gate")

    total = total_entries
    cd_size = cd_size32
    cd_off = cd_off32
    zip64 = (total_entries == 0xFFFF or cd_size32 == 0xFFFFFFFF or cd_off32 == 0xFFFFFFFF)
    if zip64:
        loc_sig = b"PK\x06\x07"
        loc_pos = tail.rfind(loc_sig, 0, pos)
        if loc_pos < 0 or loc_pos + 20 > len(tail):
            return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "ZIP64 locator missing")
        _, loc_disk, z64_off, ndisks = struct.unpack_from("<4sLQL", tail, loc_pos)
        if loc_disk != 0 or ndisks != 1:
            return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "ZIP64 multi-disk archive outside frozen gate")
        z64, _ = range_get(url, z64_off, z64_off + 55)
        if z64 is None or z64[:4] != b"PK\x06\x06":
            return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "ZIP64 EOCD unreadable")
        vals = struct.unpack_from("<4sQ2H2L4Q", z64, 0)
        _, _, _, _, z_disk, z_cd_disk, z_disk_entries, z_total, z_cd_size, z_cd_off = vals
        if z_disk != 0 or z_cd_disk != 0:
            return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "ZIP64 central directory is multi-disk")
        total, cd_size, cd_off = int(z_total), int(z_cd_size), int(z_cd_off)

    if total <= 0 or cd_size <= 0 or cd_off < 0 or cd_off + cd_size > size:
        return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "central-directory bounds invalid", entries=total, cd_size=cd_size, cd_offset=cd_off, provider_size=size)

    cd, cdmeta = range_get(url, cd_off, cd_off + cd_size - 1)
    if cd is None:
        return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "central-directory range request not honored", central_directory_range=cdmeta)

    entries = []
    p = 0
    for idx in range(total):
        if p + 46 > len(cd) or cd[p:p+4] != b"PK\x01\x02":
            return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "central-directory entry parse failed", parsed_entries=len(entries), expected_entries=total)
        h = struct.unpack_from("<4s6H3L5H2L", cd, p)
        (_, ver_made, ver_need, flags, method, mtime, mdate, crc32, comp32, uncomp32,
         fn_len, extra_len, comment_len, disk_start, int_attr, ext_attr, local_off32) = h
        p += 46
        name_b = cd[p:p+fn_len]; p += fn_len
        extra = cd[p:p+extra_len]; p += extra_len
        p += comment_len
        enc = "utf-8" if (flags & 0x800) else "cp437"
        name = name_b.decode(enc, errors="strict")
        need_uncomp = uncomp32 == 0xFFFFFFFF
        need_comp = comp32 == 0xFFFFFFFF
        need_off = local_off32 == 0xFFFFFFFF
        need_disk = disk_start == 0xFFFF
        zvals = parse_zip64_extra(extra, need_uncomp, need_comp, need_off, need_disk)
        uncomp = zvals.get("uncomp", uncomp32)
        comp = zvals.get("comp", comp32)
        local_off = zvals.get("offset", local_off32)
        dstart = zvals.get("disk", disk_start)
        if dstart != 0:
            return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "member starts on nonzero disk", member=name)
        entries.append({
            "name": name,
            "compressed_size": int(comp),
            "uncompressed_size": int(uncomp),
            "crc32": f"{crc32:08x}",
            "compression_method": int(method),
            "local_header_offset": int(local_off),
            "is_safe_path": safe_path(name),
            "extension": PurePosixPath(name).suffix.lower(),
        })

    if p != len(cd):
        return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "central-directory trailing bytes under strict parser", parsed_bytes=p, central_directory_bytes=len(cd))
    if any(not e["is_safe_path"] for e in entries):
        return fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", "unsafe path entry present", unsafe_count=sum(not e["is_safe_path"] for e in entries))

    raw_candidates = [e for e in entries if e["extension"] in RAW_EXTS and APL_RE.search(e["name"])]
    ext_counts = {}
    for e in entries:
        ext_counts[e["extension"]] = ext_counts.get(e["extension"], 0) + 1

    if not raw_candidates:
        cls = "BLOCKED_M4A0_CHEN_EPHYS_SCHEMA_NOT_SELF_DESCRIBING"
        reason = "no central-directory member has both an exact APL token and a preregistered raw-electrophysiology extension"
    else:
        cls = "PASS_M4A0_CHEN_EPHYS_ARCHIVE_SCHEMA_QUALIFIED"
        reason = "provider identity, bounded ZIP schema, safe paths, and deterministic APL raw-recording candidates all passed"

    result = {
        "classification": cls,
        "reason": reason,
        "provider": {
            "record_id": RECORD_ID,
            "archive_key": EXPECTED_KEY,
            "provider_size": size,
            "provider_checksum": checksum,
            "range_status_tail": tmeta.get("status"),
            "range_status_central_directory": cdmeta.get("status"),
        },
        "zip": {
            "zip64": zip64,
            "entries_expected": total,
            "entries_parsed": len(entries),
            "central_directory_size": cd_size,
            "central_directory_offset": cd_off,
            "extensions": dict(sorted(ext_counts.items())),
        },
        "discoverability": {
            "rule": "case-insensitive exact APL token in member path AND extension in frozen raw-ephys extension set",
            "raw_extensions": sorted(RAW_EXTS),
            "candidate_count": len(raw_candidates),
            "candidate_members": raw_candidates,
        },
        "members": entries,
        "guardrails": {
            "archive_member_payload_opened": False,
            "archive_member_decompressed": False,
            "amin_loaded": False,
            "m3f4_residual_used": False,
            "mnq_loaded": False,
            "model_fit": False,
        },
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
    print(json.dumps({
        "classification": cls,
        "provider_size": size,
        "entries_parsed": len(entries),
        "candidate_count": len(raw_candidates),
        "extensions": dict(sorted(ext_counts.items())),
        "candidate_names": [e["name"] for e in raw_candidates],
        "guardrails": result["guardrails"],
    }, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        sys.exit(fail("BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA", f"exception: {type(exc).__name__}: {exc}"))
