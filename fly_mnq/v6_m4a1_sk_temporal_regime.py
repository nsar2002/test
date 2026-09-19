#!/usr/bin/env python3
import bz2
import itertools
import json
import math
import os
import re
import struct
import sys
import tempfile
import time
import zlib
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pyabf
import requests
from scipy.ndimage import median_filter

RECORD_ID = 18644411
ARCHIVE_KEY = "Ephys_sparse coding.zip"
EXPECTED_MD5 = "c6d63ac25c504db4fc3ee45578d63169"
EXPECTED_SIZE = 2287477173
M4A0_PATH = "research/results/v6_m4a0_chen_ephys_schema_result.json"
OUT = "v6_m4a1_result.json"

COLLECTION = "Ephys_sparse coding/APL_SD_APL_SKRNAi_Fig4H-J/raw/"
CTRL = "APL_RNAi_ctrl_kk"
RNAI = "APL_SK_RNAi_kk"

EXPECTED_COUNTS = {
    (CTRL, "IC_fp"): 11,
    (RNAI, "IC_fp"): 8,
    (CTRL, "IC_AHP_2nA"): 6,
    (RNAI, "IC_AHP_2nA"): 5,
}

CLASSIFICATIONS = {
    "PASS_M4A1_SK_POST_ONLY_IDENTIFIED",
    "PASS_M4A1_SK_DURING_STIMULUS_EFFECT_IDENTIFIED",
    "NO_IDENTIFIABLE_M4A1_SK_TEMPORAL_EFFECT",
    "BLOCKED_M4A1_SOURCE_OR_PROTOCOL_PARITY",
    "BLOCKED_M4A1X_CHANNEL_MAPPING_PARITY",
}

class ChannelMappingParityError(ValueError):
    pass

def write_result(result):
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    print(json.dumps({
        "classification": result.get("classification"),
        "reason": result.get("reason"),
        "source_counts": result.get("source_counts"),
        "primary": result.get("primary"),
        "ic_fp": result.get("ic_fp"),
        "bump_diagnostic": result.get("bump_diagnostic"),
        "guardrails": result.get("guardrails"),
    }, indent=2, sort_keys=True))

def blocked(reason, **extra):
    r = {
        "classification": "BLOCKED_M4A1_SOURCE_OR_PROTOCOL_PARITY",
        "reason": reason,
        "guardrails": {
            "chen_selected_raw_payload_opened": True,
            "unselected_archive_member_opened": False,
            "m4v0_numeric_values_opened": False,
            "amin_loaded": False,
            "m3f4_residual_used_for_selection": False,
            "mnq_loaded": False,
            "active_conductance_fit": False,
            "spatial_parameter_fit": False,
        },
    }
    r.update(extra)
    write_result(r)
    return 0

def blocked_mapping(reason, **extra):
    r = {
        "classification": "BLOCKED_M4A1X_CHANNEL_MAPPING_PARITY",
        "reason": reason,
        "guardrails": {
            "chen_selected_raw_payload_opened": True,
            "unselected_archive_member_opened": False,
            "m4v0_numeric_values_opened": False,
            "amin_loaded": False,
            "m3f4_residual_used_for_selection": False,
            "mnq_loaded": False,
            "active_conductance_fit": False,
            "spatial_parameter_fit": False,
        },
    }
    r.update(extra)
    write_result(r)
    return 0

def request_range(session, url, start, end):
    headers = {"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
    last = None
    for attempt in range(1, 5):
        try:
            with session.get(url, headers=headers, stream=True, timeout=(30, 180), allow_redirects=True) as resp:
                last = {
                    "attempt": attempt,
                    "status": resp.status_code,
                    "content_range": resp.headers.get("Content-Range"),
                    "content_length": resp.headers.get("Content-Length"),
                }
                if resp.status_code != 206:
                    raise RuntimeError(f"range status {resp.status_code}")
                cr = resp.headers.get("Content-Range", "")
                if not cr.endswith(f"/{EXPECTED_SIZE}"):
                    raise RuntimeError(f"unexpected Content-Range total: {cr}")
                n = end - start + 1
                data = resp.raw.read(n, decode_content=False)
                if len(data) != n:
                    raise RuntimeError(f"range bytes expected {n} got {len(data)}")
                return data
        except Exception as exc:
            last = {**(last or {}), "error": f"{type(exc).__name__}: {exc}"}
            if attempt < 4:
                time.sleep(2 ** (attempt - 1))
    raise RuntimeError(f"range request failed: {last}")

def member_kind(name):
    b = name.rsplit("/", 1)[-1].lower()
    if "ic_ahp_2na" in b:
        return "IC_AHP_2nA"
    if "ic_fp" in b:
        return "IC_fp"
    return None

def member_group(name):
    if not name.startswith(COLLECTION):
        return None
    tail = name[len(COLLECTION):]
    first = tail.split("/", 1)[0]
    return first if first in {CTRL, RNAI} else None

def select_members(meta):
    selected = []
    counts = {}
    for e in meta.get("members", []):
        name = e.get("name", "")
        g = member_group(name)
        k = member_kind(name)
        if g and k:
            selected.append(e)
            counts[(g, k)] = counts.get((g, k), 0) + 1
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"frozen source counts mismatch: {counts} != {EXPECTED_COUNTS}")
    if len(selected) != 30:
        raise ValueError(f"selected member total {len(selected)} != 30")
    return selected, counts

def decode_member(session, url, e, out_dir):
    off = int(e["local_header_offset"])
    hdr = request_range(session, url, off, off + 29)
    if hdr[:4] != b"PK\x03\x04":
        raise ValueError(f"bad local header signature for {e['name']}")
    sig, ver, flags, method, mt, md, crc_lh, comp_lh, uncomp_lh, fn_len, extra_len = struct.unpack(
        "<4s5H3L2H", hdr
    )
    var = request_range(session, url, off + 30, off + 30 + fn_len + extra_len - 1) if (fn_len + extra_len) else b""
    name_b = var[:fn_len]
    enc = "utf-8" if (flags & 0x800) else "cp437"
    local_name = name_b.decode(enc, errors="strict")
    if local_name != e["name"]:
        raise ValueError(f"local/central filename mismatch: {local_name!r} != {e['name']!r}")
    if method != int(e["compression_method"]):
        raise ValueError(f"compression method mismatch for {e['name']}")
    data_start = off + 30 + fn_len + extra_len
    comp_n = int(e["compressed_size"])
    comp = request_range(session, url, data_start, data_start + comp_n - 1)
    if method == 0:
        raw = comp
    elif method == 8:
        raw = zlib.decompress(comp, -15)
    elif method == 12:
        raw = bz2.decompress(comp)
    else:
        raise ValueError(f"unsupported ZIP compression method {method}")
    if len(raw) != int(e["uncompressed_size"]):
        raise ValueError(f"uncompressed size mismatch for {e['name']}")
    crc = zlib.crc32(raw) & 0xFFFFFFFF
    if f"{crc:08x}" != str(e["crc32"]).lower():
        raise ValueError(f"CRC mismatch for {e['name']}")
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", e["name"].rsplit("/", 1)[-1])
    path = Path(out_dir) / f"{crc:08x}_{safe}"
    path.write_bytes(raw)
    return path, f"{crc:08x}"

def to_mv(x, unit):
    u = unit.strip().replace("µ", "u").lower()
    if u == "mv":
        return np.asarray(x, dtype=float)
    if u == "v":
        return np.asarray(x, dtype=float) * 1000.0
    if u == "uv":
        return np.asarray(x, dtype=float) / 1000.0
    raise ValueError(f"unsupported voltage unit {unit!r}")

def to_pa(x, unit):
    u = unit.strip().replace("µ", "u").lower()
    if u == "pa":
        return np.asarray(x, dtype=float)
    if u == "na":
        return np.asarray(x, dtype=float) * 1000.0
    if u == "ua":
        return np.asarray(x, dtype=float) * 1e6
    if u == "a":
        return np.asarray(x, dtype=float) * 1e12
    raise ValueError(f"unsupported current unit {unit!r}")

def robust_sigma(v):
    v = np.asarray(v, dtype=float)
    med = np.median(v)
    return float(1.4826 * np.median(np.abs(v - med)))

def smooth20(v, rate):
    n = max(3, int(round(rate * 0.020)))
    if n % 2 == 0:
        n += 1
    if n >= len(v):
        n = max(3, len(v) // 2 * 2 - 1)
    return median_filter(np.asarray(v, dtype=float), size=n, mode="nearest")

def stable_segments(cmd, rate):
    cmd = np.asarray(cmd, dtype=float)
    if not np.all(np.isfinite(cmd)):
        raise ValueError("nonfinite command waveform")
    span = float(np.ptp(cmd))
    tol = max(1e-6, 1e-9 * max(1.0, span))
    changes = np.flatnonzero(np.abs(np.diff(cmd)) > tol) + 1
    bounds = np.r_[0, changes, len(cmd)]
    segs = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        if b <= a:
            continue
        level = float(np.median(cmd[a:b]))
        segs.append((int(a), int(b), level))
    return segs, tol

def pulse_metrics(v_mv, c_pa, rate):
    segs, tol = stable_segments(c_pa, rate)
    pre_n = int(round(rate * 0.100))
    min_pulse_n = int(round(rate * 0.100))
    out = []
    sm = smooth20(v_mv, rate)
    for idx, (a, b, level) in enumerate(segs):
        if b - a < min_pulse_n or a < pre_n:
            continue
        pre_cmd = c_pa[a-pre_n:a]
        pre_level = float(np.median(pre_cmd))
        if np.ptp(pre_cmd) > max(tol * 2, 1e-5):
            continue
        delta_i = level - pre_level
        if delta_i <= max(tol * 2, 0.1):
            continue
        base = float(np.median(v_mv[a-pre_n:a]))
        sigma = robust_sigma(v_mv[a-pre_n:a])
        charging = float(np.max(sm[a:b]) - base)
        late_n = min(pre_n, b-a)
        late = float(np.median(v_mv[b-late_n:b]) - base)

        # post window: until next command transition, max 2 s
        next_end = len(v_mv)
        if idx + 1 < len(segs):
            next_end = segs[idx+1][1]
        post_end = min(len(v_mv), b + int(round(rate * 2.0)))
        # stop at the next change after b if earlier
        if idx + 1 < len(segs):
            post_end = min(post_end, segs[idx+1][1])
        if post_end <= b + max(3, int(rate * 0.020)):
            continue
        post = sm[b:post_end]
        min_rel = int(np.argmin(post))
        min_v = float(post[min_rel])
        ahp = float(base - min_v)

        decay = None
        if ahp > max(2.0 * sigma, 1e-9):
            d = base - post[min_rel:]
            # recovery from peak toward baseline
            i70 = np.flatnonzero(d <= 0.70 * ahp)
            if len(i70):
                j70 = int(i70[0])
                i30 = np.flatnonzero(d[j70:] <= 0.30 * ahp)
                if len(i30):
                    j30 = j70 + int(i30[0])
                    decay = float((j30 - j70) / rate)

        residual = v_mv[a:b] - sm[a:b]
        bump = bool(np.max(residual) > 5.0 * max(sigma, 1e-12))
        out.append({
            "current_pA": float(delta_i),
            "current_key_pA": float(round(delta_i, 3)),
            "duration_ms": float((b-a) / rate * 1000.0),
            "baseline_mV": base,
            "sigma_baseline_mV": sigma,
            "charging_mV": charging,
            "late_mV": late,
            "ahp_mV": ahp,
            "ahp_decay_70_30_s": decay,
            "bump_gt_5sigma": bump,
        })
    return out

def read_abf(path, source_name, group, kind, crc):
    abf = pyabf.ABF(str(path))
    adc_names = [str(x) for x in abf.adcNames]
    adc_units = [str(x) for x in abf.adcUnits]
    in0_channels = [
        i for i, name in enumerate(adc_names)
        if name.strip().casefold() == "in 0"
    ]
    if len(in0_channels) != 1:
        raise ChannelMappingParityError(
            f"{source_name}: exact IN 0 ADC count {len(in0_channels)} != 1; "
            f"adc_names={adc_names!r}, adc_units={adc_units!r}"
        )
    ch = in0_channels[0]
    try:
        to_mv([0.0], adc_units[ch])
    except Exception as exc:
        raise ChannelMappingParityError(
            f"{source_name}: IN 0 is not voltage-convertible; "
            f"unit={adc_units[ch]!r}"
        ) from exc
    pulses = []
    sweep_meta = []
    for sw in abf.sweepList:
        abf.setSweep(int(sw), channel=ch)
        rate = float(abf.dataRate)
        y_unit = str(abf.sweepUnitsY)
        c_unit = str(abf.sweepUnitsC)
        y = to_mv(abf.sweepY, y_unit)
        c = to_pa(abf.sweepC, c_unit)
        if len(y) != len(c):
            raise ValueError(f"{source_name}: voltage/command length mismatch")
        pp = pulse_metrics(y, c, rate)
        pulses.extend([{**x, "sweep": int(sw)} for x in pp])
        sweep_meta.append({
            "sweep": int(sw),
            "sample_rate_hz": rate,
            "voltage_unit_raw": y_unit,
            "command_unit_raw": c_unit,
            "command_min_pA": float(np.min(c)),
            "command_max_pA": float(np.max(c)),
            "positive_pulses_detected": len(pp),
        })
    if not pulses:
        raise ValueError(f"{source_name}: no qualifying positive command pulse detected")
    return {
        "source_name": source_name,
        "group": group,
        "kind": kind,
        "crc32": crc,
        "abf_version": str(abf.abfVersionString),
        "adc_names": adc_names,
        "adc_units": adc_units,
        "selected_voltage_channel_index": int(ch),
        "selected_voltage_channel_name": adc_names[ch],
        "selected_voltage_channel_unit": adc_units[ch],
        "channel_count": int(abf.channelCount),
        "sweep_count": int(abf.sweepCount),
        "sweeps": sweep_meta,
        "pulses": pulses,
    }

def aggregate_file(rec):
    by_current = {}
    for p in rec["pulses"]:
        by_current.setdefault(p["current_key_pA"], []).append(p)
    agg = {}
    for k, rows in sorted(by_current.items()):
        def med(field):
            vals = [x[field] for x in rows if x[field] is not None and math.isfinite(float(x[field]))]
            return float(np.median(vals)) if vals else None
        agg[str(k)] = {
            "n_pulses": len(rows),
            "duration_ms_median": med("duration_ms"),
            "sigma_baseline_mV": med("sigma_baseline_mV"),
            "charging_mV": med("charging_mV"),
            "late_mV": med("late_mV"),
            "ahp_mV": med("ahp_mV"),
            "ahp_decay_70_30_s": med("ahp_decay_70_30_s"),
            "bump_pulses": int(sum(bool(x["bump_gt_5sigma"]) for x in rows)),
        }
    return {
        "source_name": rec["source_name"],
        "group": rec["group"],
        "kind": rec["kind"],
        "crc32": rec["crc32"],
        "abf_version": rec["abf_version"],
        "adc_names": rec["adc_names"],
        "adc_units": rec["adc_units"],
        "channel_count": rec["channel_count"],
        "sweep_count": rec["sweep_count"],
        "sweeps": rec["sweeps"],
        "by_current": agg,
    }

def exact_perm_p(control, rnai):
    x = np.asarray(control, dtype=float)
    y = np.asarray(rnai, dtype=float)
    pooled = np.r_[x, y]
    n = len(x)
    obs = float(np.median(x) - np.median(y))
    vals = []
    for inds in itertools.combinations(range(len(pooled)), n):
        mask = np.zeros(len(pooled), dtype=bool)
        mask[list(inds)] = True
        vals.append(float(np.median(pooled[mask]) - np.median(pooled[~mask])))
    vals = np.asarray(vals)
    p = float(np.mean(np.abs(vals) >= abs(obs) - 1e-12))
    return obs, p, int(len(vals))

def bootstrap_diff(control, rnai, seed, nboot=100000):
    x = np.asarray(control, dtype=float)
    y = np.asarray(rnai, dtype=float)
    rng = np.random.Generator(np.random.PCG64(seed))
    ix = rng.integers(0, len(x), size=(nboot, len(x)))
    iy = rng.integers(0, len(y), size=(nboot, len(y)))
    diffs = np.median(x[ix], axis=1) - np.median(y[iy], axis=1)
    return {
        "estimate": float(np.median(x) - np.median(y)),
        "ci95": [float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))],
        "n_boot": nboot,
        "seed": seed,
    }

def values_at(files, current, field):
    out = {CTRL: [], RNAI: []}
    key = str(current)
    for f in files:
        row = f["by_current"].get(key)
        if row is None or row.get(field) is None:
            continue
        out[f["group"]].append(float(row[field]))
    return out

def common_currents(files):
    sets = []
    for f in files:
        sets.append(set(float(k) for k in f["by_current"].keys()))
    return sorted(set.intersection(*sets)) if sets else []

def main():
    with open(M4A0_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
    if meta.get("classification") != "PASS_M4A0_CHEN_EPHYS_ARCHIVE_SCHEMA_QUALIFIED":
        return blocked("M4A0 prerequisite is not PASS", m4a0_classification=meta.get("classification"))
    provider = meta.get("provider", {})
    if provider.get("record_id") != RECORD_ID or provider.get("archive_key") != ARCHIVE_KEY:
        return blocked("M4A0 provider identity mismatch", provider=provider)
    if provider.get("provider_checksum") != f"md5:{EXPECTED_MD5}" or int(provider.get("provider_size", -1)) != EXPECTED_SIZE:
        return blocked("M4A0 checksum/size identity mismatch", provider=provider)

    try:
        selected, counts = select_members(meta)
    except Exception as exc:
        return blocked(f"source selection failed: {type(exc).__name__}: {exc}")

    url = f"https://zenodo.org/records/{RECORD_ID}/files/{quote(ARCHIVE_KEY)}?download=1"
    s = requests.Session()
    s.headers.update({"User-Agent": "fly-mnq-v6-m4a1-causal-sk-audit/1.0", "Accept-Encoding": "identity"})

    raw_records = []
    extracted_names = []
    try:
        with tempfile.TemporaryDirectory(prefix="v6_m4a1_") as td:
            for i, e in enumerate(sorted(selected, key=lambda x: x["name"]), start=1):
                name = e["name"]
                g = member_group(name)
                k = member_kind(name)
                p, crc = decode_member(s, url, e, td)
                extracted_names.append(name)
                rec = read_abf(p, name, g, k, crc)
                raw_records.append(rec)
                print(f"READ {i:02d}/30 {g} {k} {name.rsplit('/',1)[-1]} sweeps={rec['sweep_count']} pulses={len(rec['pulses'])}")
    except ChannelMappingParityError as exc:
        return blocked_mapping(
            f"frozen M4A1X IN 0 rule failed: {exc}",
            source_counts={f"{g}:{k}": n for (g,k),n in sorted(counts.items())},
            selected_members=extracted_names,
        )
    except Exception as exc:
        return blocked(
            f"raw extraction/ABF parity failed: {type(exc).__name__}: {exc}",
            source_counts={f"{g}:{k}": n for (g,k),n in sorted(counts.items())},
            selected_members=extracted_names,
        )

    files = [aggregate_file(r) for r in raw_records]
    ahp_files = [f for f in files if f["kind"] == "IC_AHP_2nA"]
    fp_files = [f for f in files if f["kind"] == "IC_fp"]

    # Strict AHP protocol parity.
    ahp_common = common_currents(ahp_files)
    all_sets = [set(float(k) for k in f["by_current"]) for f in ahp_files]
    if not ahp_common:
        return blocked("no exact common AHP current level across all files", file_summaries=files)
    # Require every AHP file to expose the same current-level set.
    if any(sset != all_sets[0] for sset in all_sets[1:]):
        return blocked(
            "AHP command current-level sets differ between files",
            ahp_current_sets=[sorted(x) for x in all_sets],
            file_summaries=files,
        )
    primary_current = float(max(ahp_common))

    # Duration parity at primary level: <= 1 ms total spread.
    durations = []
    for f in ahp_files:
        d = f["by_current"][str(primary_current)]["duration_ms_median"]
        durations.append(float(d))
    if max(durations) - min(durations) > 1.0:
        return blocked(
            "AHP primary pulse duration differs by >1 ms across files",
            primary_current_pA=primary_current,
            durations_ms=durations,
            file_summaries=files,
        )

    # Primary AHP contrast.
    ahp_vals = values_at(ahp_files, primary_current, "ahp_mV")
    if len(ahp_vals[CTRL]) != 6 or len(ahp_vals[RNAI]) != 5:
        return blocked("AHP file-level primary values incomplete", counts={k:len(v) for k,v in ahp_vals.items()})
    ahp_boot = bootstrap_diff(ahp_vals[CTRL], ahp_vals[RNAI], 2026091901)
    ahp_obs, ahp_perm_p, ahp_perm_n = exact_perm_p(ahp_vals[CTRL], ahp_vals[RNAI])

    # Noise-derived equivalence band.
    sigmas = []
    for f in ahp_files:
        row = f["by_current"][str(primary_current)]
        sigmas.append(float(row["sigma_baseline_mV"]))
    equivalence_E = float(2.0 * np.median(sigmas))

    during = {}
    during_outside = False
    all_equiv = True
    for current in ahp_common:
        ckey = str(float(current))
        during[ckey] = {}
        for field, seed in [("charging_mV", 2026091902), ("late_mV", 2026091903)]:
            vals = values_at(ahp_files, float(current), field)
            if len(vals[CTRL]) != 6 or len(vals[RNAI]) != 5:
                return blocked(f"incomplete primary during values at {current} {field}")
            st = bootstrap_diff(vals[CTRL], vals[RNAI], seed + int(round(abs(current)*10)))
            lo, hi = st["ci95"]
            inside = bool(lo >= -equivalence_E and hi <= equivalence_E)
            outside = bool(lo > equivalence_E or hi < -equivalence_E)
            st["equivalence_halfwidth_mV"] = equivalence_E
            st["ci_entirely_inside_equivalence"] = inside
            st["ci_wholly_outside_equivalence"] = outside
            during[ckey][field] = st
            all_equiv = all_equiv and inside
            during_outside = during_outside or outside

    # Corroborative IC_fp curves at current levels common to every IC_fp file.
    fp_common = common_currents(fp_files)
    fp_stats = {"common_currents_pA": fp_common, "levels": {}}
    for current in fp_common:
        k = str(float(current))
        fp_stats["levels"][k] = {}
        for field, seed in [("charging_mV", 2026091912), ("late_mV", 2026091913)]:
            vals = values_at(fp_files, float(current), field)
            if len(vals[CTRL]) == 11 and len(vals[RNAI]) == 8:
                fp_stats["levels"][k][field] = bootstrap_diff(
                    vals[CTRL], vals[RNAI], seed + int(round(abs(current)*10))
                )

    # Overlap corroboration requirement only when exact common current overlap exists.
    overlaps = sorted(set(ahp_common).intersection(fp_common))
    corroborated = None
    if during_outside and overlaps:
        corroborated = False
        for current in overlaps:
            arow = during[str(float(current))]
            frow = fp_stats["levels"].get(str(float(current)), {})
            for field in ("charging_mV", "late_mV"):
                if not arow[field]["ci_wholly_outside_equivalence"]:
                    continue
                fp = frow.get(field)
                if not fp:
                    continue
                # Direction reproduced when point estimates have same nonzero sign.
                if arow[field]["estimate"] * fp["estimate"] > 0:
                    corroborated = True

    ahp_positive = bool(ahp_boot["estimate"] > 0 and ahp_boot["ci95"][0] > 0)
    if during_outside and (corroborated is True or corroborated is None):
        classification = "PASS_M4A1_SK_DURING_STIMULUS_EFFECT_IDENTIFIED"
        reason = "at least one primary during-stimulus SK-RNAi contrast lies wholly outside the measurement-derived equivalence band"
    elif ahp_positive and all_equiv:
        classification = "PASS_M4A1_SK_POST_ONLY_IDENTIFIED"
        reason = "post-stimulus AHP SK effect identified while all primary during-stimulus contrasts are practically equivalent to zero at measurement sensitivity"
    else:
        classification = "NO_IDENTIFIABLE_M4A1_SK_TEMPORAL_EFFECT"
        reason = "frozen criteria identify neither a robust post-only pattern nor a corroborated during-stimulus SK effect"

    # Bump diagnostic from IC_fp only.
    total_fp_pulses = 0
    bump_fp_pulses = 0
    files_with_bump = {CTRL: 0, RNAI: 0}
    for r in raw_records:
        if r["kind"] != "IC_fp":
            continue
        bs = sum(bool(p["bump_gt_5sigma"]) for p in r["pulses"])
        total_fp_pulses += len(r["pulses"])
        bump_fp_pulses += bs
        if bs:
            files_with_bump[r["group"]] += 1

    result = {
        "classification": classification,
        "reason": reason,
        "source_counts": {f"{g}:{k}": n for (g,k),n in sorted(counts.items())},
        "source": {
            "record_id": RECORD_ID,
            "archive_key": ARCHIVE_KEY,
            "provider_md5": EXPECTED_MD5,
            "provider_size": EXPECTED_SIZE,
            "collection": COLLECTION,
            "selected_members": sorted(extracted_names),
        },
        "primary": {
            "ahp_common_currents_pA": ahp_common,
            "primary_current_pA": primary_current,
            "primary_duration_ms_range": [min(durations), max(durations)],
            "baseline_sigma_mV": sigmas,
            "equivalence_halfwidth_mV": equivalence_E,
            "ahp_control_mV": ahp_vals[CTRL],
            "ahp_sk_rnai_mV": ahp_vals[RNAI],
            "ahp_median_difference_control_minus_rnai": ahp_boot,
            "ahp_exact_permutation": {
                "observed_median_difference_mV": ahp_obs,
                "two_sided_p": ahp_perm_p,
                "enumerated_partitions": ahp_perm_n,
            },
            "during": during,
            "all_primary_during_ci_inside_equivalence": all_equiv,
            "any_primary_during_ci_wholly_outside_equivalence": during_outside,
            "exact_fp_overlap_currents_pA": overlaps,
            "fp_direction_corroborated_if_required": corroborated,
        },
        "ic_fp": fp_stats,
        "bump_diagnostic": {
            "definition": "within-pulse voltage above 20-ms rolling-median trajectory > 5 * pre-pulse robust sigma",
            "total_positive_pulses": total_fp_pulses,
            "bump_positive_pulses": bump_fp_pulses,
            "files_with_bump": files_with_bump,
            "classification_effect": "diagnostic_only",
        },
        "file_summaries": files,
        "guardrails": {
            "chen_selected_raw_payload_opened": True,
            "unselected_archive_member_opened": False,
            "m4v0_numeric_values_opened": False,
            "amin_loaded": False,
            "m3f4_residual_used_for_selection": False,
            "mnq_loaded": False,
            "active_conductance_fit": False,
            "spatial_parameter_fit": False,
        },
    }
    if classification not in CLASSIFICATIONS:
        raise AssertionError(classification)
    write_result(result)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        sys.exit(blocked(f"unhandled exception: {type(exc).__name__}: {exc}"))
