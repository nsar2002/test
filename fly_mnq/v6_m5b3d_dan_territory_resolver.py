from __future__ import annotations

import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.feather as feather
from scipy.spatial import cKDTree

W = Path("v6_m5b3b_work")  # pinned body annotations and connectome weights (shared convention)
O = Path("v6_m5b3d_out")

PROTOCOL_PATH = "research/v6_m5b3d_dan_territory_resolver_protocol.md"
PROTOCOL_FREEZE_COMMIT = "994a2b152b93188adeafa57196e726b9abd9628a"
PROTOCOL_SHA = "a9bea6d68c51b971e9ac3d666a429c7165cadbf57849c7c02b1089577de8651e"
M5B3C_SCRIPT = "fly_mnq/v6_m5b3c_synapse_compartment_resolver.py"  # frozen streaming/validation machinery
M5B3C_RESULT = "research/results/v6_m5b3c_resolver_result.json"
M5B3B_SCRIPT = "fly_mnq/v6_m5b3b_compartment_gating_mvp.py"
M5B3B_RESULT = "research/results/v6_m5b3b_compartment_gating_mvp_result.json"
C0_RESULT = "research/results/v6_m5b3c0_synapse_schema_result.json"
C1_RESULT = "research/results/v6_m5b3c1_roi_vocabulary_result.json"
C1_SCRIPT = "fly_mnq/v6_m5b3c1_roi_vocabulary_probe.py"
FROZEN_FILES = {
    M5B3C_SCRIPT: "7fc15e98a33f8f1f70a2a382aa7f6bd873b4c6462643849b0b3b66c61b5a4779",
    M5B3C_RESULT: "91e65addba9f6a080267aee1559a887ca11c0f5d869744fa572a0403bbd10d59",
    M5B3B_SCRIPT: "0a8d6c3fb61e7659fb885433dc0a93998dfa3b1b05397d8310274eb9fe14914b",
    M5B3B_RESULT: "1792a7f082cf951db76f98978236d3cc0eed828874922ebde79a98b88aadb1b2",
    C0_RESULT: "4c0f237cf8d270ec6abaebf3926e750e75c8079bda7c1a4da8f6138af7c12c7e",
    C1_RESULT: "4a3d73dac3fd87ed266a8e8003f1f345cf1b06aa0f5e5960d35f8be3e38b21b5",
    C1_SCRIPT: "6a88359ea4b0b90f2e615d48cfd21a51b7f188a24c34d51d7cdd0ee6c0419557",
}
ANN_SHA = "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
WEIGHTS_SHA = "e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1"

PARTNERS = "syn-partners-male-cns-v1.0-minconf-0.5.feather"
PIN = {"size": 6777179098, "etag": '"58efcf712f8c4d4de5f2ad51e97def76"', "generation": "1780494942562468",
       "md5": "58efcf712f8c4d4de5f2ad51e97def76", "record_batches": 4759, "footer_length": 116632,
       "sha256": "959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07"}
FIELDS = ["x_pre", "y_pre", "z_pre", "x_post", "y_post", "z_post", "body_pre", "body_post", "primary_post"]

EXPECTED = {"KC": 4064, "MBON": 97, "FAST_DAN": 328, "KC_MBON_EDGES": 61210, "SINGLE": 55, "MULTI": 40, "OUTSIDE": 2}
SYSTEMS = ("gamma", "alpha_beta", "alpha_prime_beta_prime")
SIDES = ("L", "R")
TIE_K = 16
VOXEL_NM = 8.0
SHUFFLE_SEED = 20260928  # diagnostic type-shuffle control only

BLOCKED = "BLOCKED_M5B3D_SOURCE"
FAIL = "FAIL_M5B3D_RESOLVER_VALIDATION"
PASS = "PASS_M5B3D_DAN_TERRITORY_RESOLVER_VALIDATED"

C = None  # frozen M5B3C module, loaded after its hash is verified


def load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def m5b3c():
    global C
    if C is None:
        C = load_module("v6_m5b3c_frozen", M5B3C_SCRIPT)
    return C


# ---------------------------------------------------------------- lobe systems

def comp_system(comp: str) -> str:
    return "gamma" if comp.startswith("y") else ("alpha_prime_beta_prime" if "'" in comp else "alpha_beta")


def kc_system(kc_type: str) -> str:
    if kc_type.startswith("KCg"):
        return "gamma"
    if kc_type.startswith("KCa'b'"):
        return "alpha_prime_beta_prime"
    if kc_type.startswith("KCab"):
        return "alpha_beta"
    return "unknown"


def type_compartment_by_system(dan_map, lobe15):
    """{dan type: {system: LOBE15 index}}; each type names at most one lobe compartment per system."""
    out = {}
    for t, comps in dan_map.items():
        per = {}
        for c in comps:
            if c in lobe15:
                s = comp_system(c)
                if s in per:
                    raise ValueError(f"{t} names two lobe compartments in {s}")
                per[s] = lobe15.index(c)
        out[t] = per
    return out


# ---------------------------------------------------------------- territory assignment (pure)

def build_candidates(dk_pre_xyz, dk_dan_type, dk_kc_system, dk_kc_side, type_comp):
    """Candidate DAN release sites per (system, side): unique DAN->KC T-bar locations whose DAN type names a lobe
    compartment in the postsynaptic KC's system. Returns {(system, side): (xyz int64 (n,3), comp int64 (n,))}."""
    out = {}
    comp_of = np.array([type_comp[t].get(s, -1) for t, s in zip(dk_dan_type, dk_kc_system)], dtype=np.int64)
    for s in SYSTEMS:
        for side in SIDES:
            sel = (dk_kc_system == s) & (dk_kc_side == side) & (comp_of >= 0)
            if not sel.any():
                out[(s, side)] = (np.zeros((0, 3), dtype=np.int64), np.zeros(0, dtype=np.int64))
                continue
            df = pd.DataFrame({"x": dk_pre_xyz[sel, 0], "y": dk_pre_xyz[sel, 1], "z": dk_pre_xyz[sel, 2], "c": comp_of[sel]})
            df = df.drop_duplicates().sort_values(["x", "y", "z", "c"], kind="mergesort")
            out[(s, side)] = (df[["x", "y", "z"]].to_numpy(np.int64), df["c"].to_numpy(np.int64))
    return out


def assign_nearest(query_xyz, cand_xyz, cand_comp, k=TIE_K):
    """Compartment of the exactly nearest candidate; -1 if the exact nearest set spans >1 compartment or may exceed k.

    Returns (comp, nearest squared distance in voxels^2 (int64), neighbor index array (n, k)).
    """
    n = len(query_xyz)
    if n == 0 or len(cand_xyz) == 0:
        return np.full(n, -1, dtype=np.int64), np.full(n, -1, dtype=np.int64), np.zeros((n, 0), dtype=np.int64)
    kk = min(k, len(cand_xyz))
    tree = cKDTree(cand_xyz.astype(np.float64))
    _, idx = tree.query(query_xyz.astype(np.float64), k=kk)
    idx = np.asarray(idx, dtype=np.int64).reshape(n, kk)
    d2 = ((cand_xyz[idx] - query_xyz[:, None, :]) ** 2).sum(axis=2)  # exact int64
    dmin = d2.min(axis=1)
    tied = d2 == dmin[:, None]
    comps = np.where(tied, cand_comp[idx], -1)
    first = cand_comp[idx[np.arange(n), tied.argmax(axis=1)]]
    same = np.all((comps == first[:, None]) | ~tied, axis=1)
    overflow = tied[:, -1] & (kk < len(cand_xyz))  # ties may continue beyond the k returned neighbours
    comp = np.where(same & ~overflow, first, -1)
    return comp, dmin, idx


def labels_for_ties(idx, d2min, cand_xyz, query_xyz, labels):
    """Re-evaluate the tie rule on the same neighbour sets with alternative candidate labels (shuffle control)."""
    n, kk = idx.shape
    if kk == 0:
        return np.full(n, -1, dtype=np.int64)
    d2 = ((cand_xyz[idx] - query_xyz[:, None, :]) ** 2).sum(axis=2)
    tied = d2 == d2min[:, None]
    comps = np.where(tied, labels[idx], -1)
    first = labels[idx[np.arange(n), tied.argmax(axis=1)]]
    same = np.all((comps == first[:, None]) | ~tied, axis=1)
    overflow = tied[:, -1] & (kk < len(cand_xyz))
    return np.where(same & ~overflow, first, -1)


def resolve(syn_pre_xyz, syn_kc_system, syn_kc_side, candidates, shuffle_rng=None):
    """Assign every KC->MBON synapse. Returns code (LOBE15 index or -1), nearest distance (nm, -1 if none) and,
    if shuffle_rng is given, the codes under a within-(system, side) permutation of candidate labels."""
    n = len(syn_pre_xyz)
    code = np.full(n, -1, dtype=np.int64)
    dist = np.full(n, -1.0)
    shuffled = np.full(n, -1, dtype=np.int64) if shuffle_rng is not None else None
    for s in SYSTEMS:
        for side in SIDES:
            sel = np.flatnonzero((syn_kc_system == s) & (syn_kc_side == side))
            if len(sel) == 0:
                continue
            cxyz, ccomp = candidates[(s, side)]
            comp, d2, idx = assign_nearest(syn_pre_xyz[sel], cxyz, ccomp)
            code[sel] = comp
            dist[sel] = np.where(d2 >= 0, np.sqrt(np.maximum(d2, 0).astype(np.float64)) * VOXEL_NM, -1.0)
            if shuffle_rng is not None and len(ccomp):
                shuffled[sel] = labels_for_ties(idx, d2, cxyz, syn_pre_xyz[sel], shuffle_rng.permutation(ccomp))
    return code, dist, shuffled


# ---------------------------------------------------------------- self-test (synthetic data only)

def selftest_territory():
    cases = {}
    lobe = ("a1", "a2", "a3", "a'1", "a'2", "a'3", "B1", "B2", "B'1", "B'2", "y1", "y2", "y3", "y4", "y5")
    dan_map = {"PAMg4": ("y4",), "PAMg5": ("y5",), "PPLx": ("y2", "a'1"), "PPLp": ("y1", "pedc")}
    tc = type_compartment_by_system(dan_map, lobe)
    cases["type_map"] = tc == {"PAMg4": {"gamma": 13}, "PAMg5": {"gamma": 14}, "PPLx": {"gamma": 11, "alpha_prime_beta_prime": 3},
                               "PPLp": {"gamma": 10}}
    try:
        type_compartment_by_system({"bad": ("y1", "y2")}, lobe)
        cases["type_map_rejects_two_per_system"] = False
    except ValueError:
        cases["type_map_rejects_two_per_system"] = True
    xyz = np.array([[0, 0, 0], [0, 0, 0], [100, 0, 0], [10, 0, 0], [50, 0, 0], [60, 0, 0]], dtype=np.int64)
    types = np.array(["PAMg4", "PAMg4", "PAMg5", "PPLx", "PPLx", "PAMg4"])
    ksys = np.array(["gamma", "gamma", "gamma", "alpha_prime_beta_prime", "gamma", "alpha_beta"])
    kside = np.array(["L", "L", "L", "L", "R", "L"])
    cand = build_candidates(xyz, types, ksys, kside, tc)
    g_l = cand[("gamma", "L")]
    cases["candidates"] = (g_l[0].tolist() == [[0, 0, 0], [100, 0, 0]] and g_l[1].tolist() == [13, 14]
                           and cand[("alpha_prime_beta_prime", "L")][1].tolist() == [3]
                           and cand[("gamma", "R")][1].tolist() == [11] and len(cand[("alpha_beta", "L")][1]) == 0)
    q = np.array([[10, 0, 0], [90, 0, 0], [50, 0, 0], [50, 0, 0], [5, 0, 0], [0, 0, 0]], dtype=np.int64)
    qs = np.array(["gamma", "gamma", "gamma", "gamma", "alpha_prime_beta_prime", "unknown"])
    qside = np.array(["L", "L", "L", "R", "L", "L"])
    code, dist, _ = resolve(q, qs, qside, cand)
    cases["assignment"] = code.tolist() == [13, 14, -1, 11, 3, -1] and abs(dist[0] - 80.0) < 1e-9 and dist[5] == -1.0
    same_tie = build_candidates(np.array([[0, 0, 0], [20, 0, 0]], dtype=np.int64), np.array(["PAMg4", "PAMg4"]),
                                np.array(["gamma", "gamma"]), np.array(["L", "L"]), tc)
    c2, _, _ = resolve(np.array([[10, 0, 0]], dtype=np.int64), np.array(["gamma"]), np.array(["L"]), same_tie)
    cases["tie_same_compartment_assigned"] = c2.tolist() == [13]
    many = np.array([[i, 0, 0] for i in range(40)], dtype=np.int64)
    c3, _, _ = resolve(np.array([[0, 5, 0]], dtype=np.int64), np.array(["gamma"]), np.array(["L"]),
                       {("gamma", "L"): (np.vstack([many[:1], np.array([[0, 10, 0]] * 1)]), np.array([13, 14]))} | {
                           (s, sd): (np.zeros((0, 3), dtype=np.int64), np.zeros(0, dtype=np.int64))
                           for s in SYSTEMS for sd in SIDES if (s, sd) != ("gamma", "L")})
    cases["equidistant_different_compartments_unresolved"] = c3.tolist() == [-1]
    ring = np.array([[int(round(100 * np.cos(a))), int(round(100 * np.sin(a))), 0] for a in np.linspace(0, 2 * np.pi, 4, endpoint=False)] * 5,
                    dtype=np.int64)
    ring_c = np.array([13] * len(ring))
    c4, _, _ = resolve(np.array([[0, 0, 0]], dtype=np.int64), np.array(["gamma"]), np.array(["L"]),
                       {("gamma", "L"): (ring, ring_c)} | {(s, sd): (np.zeros((0, 3), dtype=np.int64), np.zeros(0, dtype=np.int64))
                                                          for s in SYSTEMS for sd in SIDES if (s, sd) != ("gamma", "L")})
    cases["tie_overflow_unresolved"] = c4.tolist() == [-1]
    rng = np.random.default_rng(3)
    big = rng.integers(0, 10000, size=(5000, 3)).astype(np.int64)
    bigc = rng.integers(10, 15, size=5000).astype(np.int64)
    qq = rng.integers(0, 10000, size=(300, 3)).astype(np.int64)
    got, _, _ = assign_nearest(qq, big, bigc)
    d2 = ((big[None, :, :] - qq[:, None, :]) ** 2).sum(axis=2)
    brute = np.array([bigc[np.flatnonzero(r == r.min())[0]] if len(set(bigc[r == r.min()])) == 1 else -1 for r in d2])
    cases["kdtree_equals_bruteforce"] = bool(np.array_equal(got, brute))
    return {k: bool(v) for k, v in cases.items()}


def selftest():
    cases = {}
    try:
        st = m5b3c().selftest()
        cases["m5b3c_machinery"] = bool(st["passed"])
    except Exception as exc:
        cases["m5b3c_machinery"] = repr(exc)
    try:
        cases.update(selftest_territory())
    except Exception as exc:
        cases["territory_exception"] = repr(exc)
    return {"passed": all(v is True for v in cases.values()) and len(cases) == 9, "cases": cases}


# ---------------------------------------------------------------- formal execution

TRANSPORT = {}


def partner_keep(kc_sorted, mbon_sorted, dan_sorted):
    """Keep KC->MBON rows and fast-DAN->KC rows."""
    def keep(c, batch):
        pre, post = batch.column("body_pre"), batch.column("body_post")
        c.key_nulls += pre.null_count + post.null_count
        p, q = C.filled(pre, -1), C.filled(post, -1)
        return ((C.idx_in(kc_sorted, p)[1] & C.idx_in(mbon_sorted, q)[1])
                | (C.idx_in(dan_sorted, p)[1] & C.idx_in(kc_sorted, q)[1]))
    return keep


def main():
    out = {}
    try:
        run(out)
    except Exception as exc:  # any execution error prevents evaluation: recorded, never silent
        finish(out, BLOCKED, f"execution error: {exc!r}")


def run(out):
    O.mkdir(exist_ok=True)
    out.update({"protocol": {"path": PROTOCOL_PATH, "expected_sha256": PROTOCOL_SHA, "freeze_commit": PROTOCOL_FREEZE_COMMIT,
                             "sha256": None}, "pin": PIN, "tie_k": TIE_K, "voxel_nm": VOXEL_NM})
    prereq = {}
    for path, want in FROZEN_FILES.items():
        prereq[f"sha256:{path}"] = Path(path).is_file() and _sha(path) == want
    if not prereq[f"sha256:{M5B3C_SCRIPT}"]:
        out["prerequisites"] = prereq
        return finish(out, BLOCKED, "frozen M5B3C machinery hash mismatch")
    m5b3c()
    out["protocol"]["sha256"] = C.sha256_file(PROTOCOL_PATH) if Path(PROTOCOL_PATH).is_file() else None
    st = selftest()
    out["selftest"] = st
    if not st["passed"]:
        return finish(out, BLOCKED, "self-test failed on synthetic data")
    prereq["protocol_sha256"] = out["protocol"]["sha256"] == PROTOCOL_SHA
    ann_path, w_path = W / "body-annotations.feather", W / "connectome-weights.feather"
    prereq["annotations_sha256"] = ann_path.is_file() and C.sha256_file(ann_path) == ANN_SHA
    prereq["weights_sha256"] = w_path.is_file() and C.sha256_file(w_path) == WEIGHTS_SHA
    out["prerequisites"] = prereq
    if not all(prereq.values()):
        return finish(out, BLOCKED, "frozen file or pinned source hash mismatch")

    m5b3b = load_module("v6_m5b3b_frozen", M5B3B_SCRIPT)
    ref = json.loads(Path(M5B3B_RESULT).read_text(encoding="utf-8"))
    ann = feather.read_table(ann_path, columns=["bodyId", "class", "type", "instance", "somaSide"]).to_pandas()
    kc = ann[ann["class"] == "Kenyon_Cell"]
    mb = ann[ann["class"] == "MBON"]
    dn = ann[ann["class"] == "DAN"]
    fast = dn[dn["type"].map(m5b3b.norm).isin(m5b3b.DAN_MAP)]
    kc_sorted = np.sort(kc["bodyId"].to_numpy(np.int64))
    mbon_sorted = np.sort(mb["bodyId"].to_numpy(np.int64))
    dan_sorted = np.sort(fast["bodyId"].to_numpy(np.int64))
    kc_sys = dict(zip(kc["bodyId"].astype(np.int64).tolist(), kc["type"].map(m5b3b.norm).map(kc_system).tolist()))
    kc_side = dict(zip(kc["bodyId"].astype(np.int64).tolist(), kc["somaSide"].map(m5b3b.norm).tolist()))
    dan_type = dict(zip(fast["bodyId"].astype(np.int64).tolist(), fast["type"].map(m5b3b.norm).tolist()))
    ref_body = {int(r["bodyId"]): r for r in ref["mbon_mapping"]["per_body"]}
    mbon_status, mbon_named, mbon_type, map_mismatch = {}, {}, {}, []
    for _, row in mb.sort_values("bodyId").iterrows():
        bid, typ, inst = int(row["bodyId"]), m5b3b.norm(row["type"]), m5b3b.norm(row["instance"])
        comps = tuple(m5b3b.mbon_compartments(typ, inst))
        status = ("outside_fast_lobe_map" if not comps else "single_compartment" if len(comps) == 1 else "multi_compartment")
        r = ref_body.get(bid)
        if r is None or list(comps) != r["compartments"] or status != r["status"]:
            map_mismatch.append(bid)
        mbon_status[bid], mbon_type[bid] = status, typ
        mbon_named[bid] = tuple(C.LOBE15.index(c) for c in comps if c in C.LOBE15)
    type_comp = type_compartment_by_system(m5b3b.DAN_MAP, C.LOBE15)
    gate_pop = {c: len(v) for c, v in ref["fast_dan"]["gate_population_by_compartment"].items()}
    gated = {i for i, c in enumerate(C.LOBE15) if gate_pop.get(c, 0) > 0}
    single_nominal = {b: mbon_named[b][0] for b, s in mbon_status.items() if s == "single_compartment"}
    wpre, wpost, ww = C.kc_mbon_weights(w_path, kc_sorted, mbon_sorted)
    counts = {s: sum(v == s for v in mbon_status.values()) for s in ("single_compartment", "multi_compartment", "outside_fast_lobe_map")}
    kc_sys_counts = {s: sum(v == s for v in kc_sys.values()) for s in SYSTEMS + ("unknown",)}
    identity = {
        "KC": int(len(kc_sorted)), "MBON": int(len(mbon_sorted)), "FAST_DAN": int(len(dan_sorted)),
        "kc_mbon_edges": int(len(wpre)), "status_counts": counts, "m5b3b_map_mismatches": map_mismatch,
        "kc_system_counts": kc_sys_counts, "kc_side_counts": {s: sum(v == s for v in kc_side.values()) for s in SIDES},
        "single_bodies_with_one_lobe_compartment": all(len(mbon_named[b]) == 1 for b in single_nominal),
    }
    out["identity"] = identity
    ident_ok = (identity["KC"] == EXPECTED["KC"] and identity["MBON"] == EXPECTED["MBON"]
                and identity["FAST_DAN"] == EXPECTED["FAST_DAN"] and identity["kc_mbon_edges"] == EXPECTED["KC_MBON_EDGES"]
                and not map_mismatch and identity["single_bodies_with_one_lobe_compartment"]
                and counts == {"single_compartment": EXPECTED["SINGLE"], "multi_compartment": EXPECTED["MULTI"],
                               "outside_fast_lobe_map": EXPECTED["OUTSIDE"]}
                and sum(identity["kc_side_counts"].values()) == EXPECTED["KC"])
    if not ident_ok:
        return finish(out, BLOCKED, "identity or M5B3B map reproduction failed")

    c0 = {p["file"]: [c["name"] for c in p["schema"]] for p in json.loads(Path(C0_RESULT).read_text())["probes"]}
    c1 = json.loads(Path(C1_RESULT).read_text())["sources"]
    vocab = {"primary_post": c1[PARTNERS]["vocabularies"]["primary_post"]["values"]}
    try:
        col = C.Collector(FIELDS, vocab, partner_keep(kc_sorted, mbon_sorted, dan_sorted))
        raw = C.PinnedHttpStream(C.BASE + PARTNERS, PIN, ctx=C.ssl_context())
        t0 = time.time()
        tail = C.stream_file(raw, PIN, sorted(c0[PARTNERS].index(f) for f in FIELDS), col, C.footer_reader())
        TRANSPORT[PARTNERS] = {"seconds": round(time.time() - t0, 1), "reconnects": raw.reconnects, "connect_offsets": raw.connect_offsets}
        print(PARTNERS, "streamed", raw.pos, "bytes in", TRANSPORT[PARTNERS]["seconds"], "s; reconnects", raw.reconnects, flush=True)
    except Exception as exc:
        return finish(out, BLOCKED, f"stream failure: {exc!r}")
    src = {
        "bytes": raw.pos, "sha256": raw.sha256.hexdigest(), "md5": raw.md5.hexdigest(),
        "bytes_match_pin": raw.pos == PIN["size"], "sha256_matches_pin": raw.sha256.hexdigest() == PIN["sha256"],
        "md5_matches_pin": raw.md5.hexdigest() == PIN["md5"], "record_batches_parsed": col.batches,
        "rows_total": col.rows, "rows_kept": col.kept, "dictionary_mismatch_batches": col.dictionary_mismatch_batches,
        "kept_row_nulls": col.kept_nulls, "key_column_nulls": col.key_nulls, "tail": tail, "tail_ok": C.tail_ok(tail, PIN),
    }
    src["integrity_ok"] = bool(src["bytes_match_pin"] and src["sha256_matches_pin"] and src["md5_matches_pin"]
                               and col.batches == PIN["record_batches"] and col.dictionary_mismatch_batches == 0
                               and col.kept_nulls == 0 and src["tail_ok"])
    out["source"] = src
    if not src["integrity_ok"]:
        return finish(out, BLOCKED, "source integrity check failed")

    P = col.arrays()
    pre, post = P["body_pre"], P["body_post"]
    is_km = C.idx_in(kc_sorted, pre)[1] & C.idx_in(mbon_sorted, post)[1]
    is_dk = C.idx_in(dan_sorted, pre)[1] & C.idx_in(kc_sorted, post)[1]
    xyz_pre = np.stack([P["x_pre"], P["y_pre"], P["z_pre"]], axis=1).astype(np.int64)
    xyz_post = np.stack([P["x_post"], P["y_post"], P["z_post"]], axis=1).astype(np.int64)
    km_pre, km_post, km_xyz = pre[is_km], post[is_km], xyz_pre[is_km]
    km_sys = np.array([kc_sys[int(b)] for b in km_pre])
    km_side = np.array([kc_side[int(b)] for b in km_pre])
    dk_xyz = xyz_pre[is_dk]
    dk_type = np.array([dan_type[int(b)] for b in pre[is_dk]])
    dk_sys = np.array([kc_sys[int(b)] for b in post[is_dk]])
    dk_side = np.array([kc_side[int(b)] for b in post[is_dk]])

    parity = C.aggregate_parity(km_pre, km_post, wpre, wpost, ww)
    candidates = build_candidates(dk_xyz, dk_type, dk_sys, dk_side, type_comp)
    coverage = {}
    for i, c in enumerate(C.LOBE15):
        for side in SIDES:
            coverage[f"{c}({side})"] = int((candidates[(comp_system(c), side)][1] == i).sum())
    coverage_ok = all(v > 0 for v in coverage.values())
    code, dist_nm, shuffled = resolve(km_xyz, km_sys, km_side, candidates, np.random.default_rng(SHUFFLE_SEED))
    val = C.validate_semantics(km_post, code, single_nominal)
    edges = C.build_learner_edges(km_pre, km_post, code, mbon_status, mbon_named, gated)

    single_mask = np.isin(edges["plastic_post"], np.array(sorted(single_nominal), dtype=np.int64))
    repro = {}
    for c in sorted(set(edges["plastic_comp"][single_mask].tolist()) | set(ref["plastic_edges"]["per_compartment"])):
        sel = single_mask & (edges["plastic_comp"] == c)
        want = ref["plastic_edges"]["per_compartment"].get(c, {})
        repro[c] = {"edges": int(sel.sum()), "weight": int(edges["plastic_weight"][sel].sum()),
                    "m5b3b_edges": want.get("edge_count"), "m5b3b_weight": want.get("raw_weight")}
    repro_ok = all(v["edges"] == v["m5b3b_edges"] and v["weight"] == v["m5b3b_weight"] for v in repro.values())

    crit = {
        "A_prerequisites_exact": True,
        "B_source_integrity": True,
        "C_aggregate_parity_exact": bool(parity["exact"] and repro_ok),
        "D_territory_coverage": bool(coverage_ok),
        "E1_pooled_single_compartment_agreement": bool(val["pooled_pass"]),
        "E2_every_single_compartment_body_plurality": bool(val["every_body_plurality_matches"]),
        "F_no_market_valence_theta_criterion": True,
    }
    out.update({"criteria": crit, "aggregate_parity": parity, "m5b3b_single_reproduction": repro,
                "territory_coverage": coverage, "validation": val})
    out["diagnostics"] = diagnostics(km_pre, km_post, km_xyz, xyz_post[is_km], km_sys, code, dist_nm, shuffled, candidates,
                                     dk_xyz, single_nominal, mbon_status, mbon_named, mbon_type, edges, ref, gate_pop, m5b3b)
    arrays = dict(edges)
    out["learner_edges"] = {"file": "v6_m5b3d_learner_edges.npz", "content_digest": C.array_digest(arrays),
                            "plastic_rows": int(len(edges["plastic_pre"])), "nonplastic_rows": int(len(edges["nonplastic_pre"])),
                            "plastic_weight": int(edges["plastic_weight"].sum()), "nonplastic_weight": int(edges["nonplastic_weight"].sum())}
    np.savez_compressed(O / "v6_m5b3d_learner_edges.npz", **arrays)
    syn = {"body_pre": km_pre, "body_post": km_post, "x_pre": km_xyz[:, 0], "y_pre": km_xyz[:, 1], "z_pre": km_xyz[:, 2],
           "lobe_code": code, "nearest_nm": dist_nm}
    out["synapse_table"] = {"file": "v6_m5b3d_kc_mbon_synapses.npz (artifact only)", "content_digest": C.array_digest(syn),
                            "rows": int(len(km_pre))}
    np.savez_compressed(O / "v6_m5b3d_kc_mbon_synapses.npz", **syn)
    if all(crit.values()):
        return finish(out, PASS, "all frozen resolver criteria passed")
    return finish(out, FAIL, "failed: " + ", ".join(k for k, v in crit.items() if not v))


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pct(a, qs=(50, 90, 99, 100)):
    return {f"p{q}": float(np.percentile(a, q)) for q in qs} if len(a) else {}


def diagnostics(km_pre, km_post, km_xyz, km_post_xyz, km_sys, code, dist_nm, shuffled, candidates, dk_xyz,
                single_nominal, mbon_status, mbon_named, mbon_type, edges, ref, gate_pop, m5b3b):
    d = {}
    res = code >= 0
    d["resolved"] = int(res.sum())
    d["unresolved_unknown_kc_class"] = int((km_sys == "unknown").sum())
    d["unresolved_tie"] = int(((km_sys != "unknown") & ~res).sum())
    d["nearest_release_site_nm"] = pct(dist_nm[res])
    d["pre_post_distance_nm"] = pct(np.sqrt(((km_xyz - km_post_xyz) ** 2).sum(axis=1).astype(np.float64)) * VOXEL_NM)
    d["dan_kc_rows"] = int(len(dk_xyz))
    d["candidate_release_sites"] = {f"{s}({side})": int(len(candidates[(s, side)][1])) for s in SYSTEMS for side in SIDES}
    single_ids = np.array(sorted(single_nominal), dtype=np.int64)
    sel = np.isin(km_post, single_ids)
    nom = np.array([single_nominal[int(b)] for b in km_post[sel]], dtype=np.int64)
    d["type_shuffle_control_pooled_agreement"] = float((shuffled[sel] == nom).mean()) if sel.any() else None
    d["pooled_agreement_resolved_only"] = float((code[sel][code[sel] >= 0] == nom[code[sel] >= 0]).mean()) if sel.any() else None
    m5b3c_ref = json.loads(Path(M5B3C_RESULT).read_text(encoding="utf-8"))["validation"]["per_body"]
    roi_plural = {int(r["bodyId"]): r["plurality"] for r in m5b3c_ref}
    val_bodies = []
    for b in sorted(single_nominal):
        c = code[km_post == b]
        counts = np.bincount(c[c >= 0], minlength=len(C.LOBE15))
        top = int(counts.max()) if (c >= 0).any() else 0
        plural = C.LOBE15[int(np.argmax(counts))] if top > 0 and int((counts == top).sum()) == 1 else None
        val_bodies.append({"bodyId": int(b), "type": mbon_type[b], "nominal": C.LOBE15[single_nominal[b]],
                           "territory_plurality": plural, "roi_plurality_m5b3c": roi_plural.get(int(b))})
    d["plurality_territory_vs_roi"] = val_bodies
    per_multi = []
    for b in sorted(k for k, s in mbon_status.items() if s == "multi_compartment"):
        c = code[km_post == b]
        named = mbon_named[b]
        per_multi.append({
            "bodyId": int(b), "type": mbon_type[b], "named": [C.LOBE15[i] for i in named], "kc_synapses": int(len(c)),
            "in_map": {C.LOBE15[i]: int((c == i).sum()) for i in named},
            "offmap": {C.LOBE15[i]: int(v) for i, v in enumerate(np.bincount(c[c >= 0], minlength=15)) if v and i not in named},
            "unresolved": int((c < 0).sum()),
        })
    d["multi_compartment_bodies"] = per_multi
    per_comp = {}
    for cname in C.LOBE15:
        s = edges["plastic_comp"] == cname
        s1 = s & np.isin(edges["plastic_post"], single_ids)
        s2 = s & ~np.isin(edges["plastic_post"], single_ids)
        per_comp[cname] = {"gate_dan_bodies": int(gate_pop.get(cname, 0)),
                           "single_edges": int(s1.sum()), "single_weight": int(edges["plastic_weight"][s1].sum()),
                           "resolved_subedges": int(s2.sum()), "resolved_weight": int(edges["plastic_weight"][s2].sum()),
                           "resolved_mbon_bodies": int(len(np.unique(edges["plastic_post"][s2])))}
    d["plastic_by_compartment"] = per_comp
    eligible_before = set(ref["plastic_edges"]["per_compartment"])
    d["newly_plastic_compartments"] = [c for c in C.LOBE15 if c not in eligible_before and per_comp[c]["resolved_weight"] > 0]
    d["nonplastic_by_reason"] = {r: int(edges["nonplastic_weight"][edges["nonplastic_reason"] == r].sum())
                                 for r in sorted(set(edges["nonplastic_reason"].tolist()))}
    loops = []
    for cname in C.LOBE15:
        dans = sorted(t for t, comps in m5b3b.DAN_MAP.items() if cname in comps and t in C.SIGNED_DAN)
        if not dans:
            continue
        s = edges["plastic_comp"] == cname
        for mt in sorted(set(mbon_type[int(b)] for b in np.unique(edges["plastic_post"][s]))):
            if mt not in C.SIGNED_MBON:
                continue
            ids = np.array([b for b, t in mbon_type.items() if t == mt], dtype=np.int64)
            w = int(edges["plastic_weight"][s & np.isin(edges["plastic_post"], ids)].sum())
            for dt in dans:
                loops.append({"compartment": cname, "mbon_type": mt, "mbon_sign": C.SIGNED_MBON[mt], "dan_type": dt,
                              "dan_sign": C.SIGNED_DAN[dt], "plastic_weight": w,
                              "model_consistent": (C.SIGNED_DAN[dt], C.SIGNED_MBON[mt]) in C.MODEL_CONSISTENT})
    d["signed_loops"] = loops
    return d


def finish(out, classification, reason):
    out.update({"classification": classification, "reason": reason})
    O.mkdir(exist_ok=True)
    (O / "v6_m5b3d_resolver_result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (O / "v6_m5b3d_transport_log.json").write_text(json.dumps(TRANSPORT, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out.get(k) for k in ("classification", "reason", "criteria", "aggregate_parity")}, indent=2, sort_keys=True))
    v = out.get("validation")
    if v:
        print("pooled agreement", round(v["pooled_agreement"], 6), "=", v["pooled_agree"], "/", v["pooled_n"])
    dg = out.get("diagnostics") or {}
    for k in ("type_shuffle_control_pooled_agreement", "pooled_agreement_resolved_only", "nearest_release_site_nm"):
        if k in dg:
            print(k, dg[k])
    for r in dg.get("signed_loops", []):
        print("loop", r)


if __name__ == "__main__":
    main()
