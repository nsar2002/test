from __future__ import annotations

import hashlib
import importlib.util
import inspect
import itertools
import json
import sys
import time
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pyarrow.feather as feather

W = Path("v6_m5b3b_work")  # pinned MaleCNS sources (shared with the M5B3B re-execution)
B = Path("v6_m5b3b_out")   # outputs of the unchanged M5B3B re-execution
O = Path("v6_m5d0_out")
O.mkdir(exist_ok=True)

PROTOCOL_FREEZE_COMMIT = "de1cba0d62f5c0c2117628813fe3be5920c225a1"
PROTOCOL_PATH = "research/v6_m5d0_mbon_readout_conditioning_protocol.md"
PROTOCOL_SHA = "50d54b9abeaa6404ce4499f0dedc1e7cbd613916d227b960cacf1aeb5b6a2726"
M5C_SCRIPT = "fly_mnq/v6_m5c_dopamine_gated_plasticity_chronology.py"
M5C_RESULT = "research/results/v6_m5c_plasticity_chronology_result.json"
M5D0_FROZEN_FILES = {
    PROTOCOL_PATH: PROTOCOL_SHA,
    "research/v6_m5c_dopamine_gated_plasticity_chronology_protocol.md": "4590ab29cfba6fe9a559003286c94146cb96082bbe2f6c6d864437c5ce26eee6",
    M5C_SCRIPT: "57ba0542338588f1d0b27a24a9e91affd12209b32d8328726dd8b85503ad96a4",
    M5C_RESULT: "77b9c79a70bfc589b43a53c61df253aa908dd9052a3e5a1032a3f1df7d455d5c",
}
M5C_PASS = "PASS_M5C_DOPAMINE_GATED_KC_MBON_CHRONOLOGY_QUALIFIED"
MBON_STATUS_EXPECTED = {"single_compartment": 55, "multi_compartment": 40, "outside_fast_lobe_map": 2}

SEED = 20260927
L_SPACING = 32
N_TRIALS = 8
N_RANDOM_STATES = 16
RANDOM_STATE_GMAX = 2.0
READOUT_REL_TOL = 1e-12
OVERLAP_TOL = 1e-10
REFERENCE_POINT = {"eta_minus": 0.05, "eta_plus": 0.05, "lam_K": 0.5, "lam_D": 0.5, "g_max": 2.0}


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ReadoutWeights(NamedTuple):
    w: np.ndarray          # float64 raw aggregate synapse count per edge (structure edge order)
    mbon_ids: np.ndarray   # sorted unique MBON bodyIds
    edge_mbon: np.ndarray  # index of each edge's MBON in mbon_ids
    order: np.ndarray      # canonical summation order: by (MBON bodyId, KC bodyId)
    total: np.ndarray      # W_m = sum of w over E_m


def make_readout_weights(structure, w) -> ReadoutWeights:
    w = np.asarray(w, dtype=np.float64)
    mbon_ids, edge_mbon = np.unique(structure.edge_post, return_inverse=True)
    order = np.lexsort((structure.edge_pre, structure.edge_post))
    total = np.bincount(edge_mbon[order], weights=w[order], minlength=len(mbon_ids))
    return ReadoutWeights(w, mbon_ids, edge_mbon.astype(np.int64), order, total)


def raw_drive(structure, weights, gains, kc_event):
    z = np.asarray(kc_event, dtype=np.float64)[structure.edge_kc]
    contrib = weights.w * np.asarray(gains, dtype=np.float64) * z
    o = weights.order
    return np.bincount(weights.edge_mbon[o], weights=contrib[o], minlength=len(weights.mbon_ids))


def readout(structure, weights, gains, kc_event):
    """Frozen M5D0 readout: rho_m = sum_{e in E_m} w_e g_e z_k(e) / W_m (canonical summation order)."""
    return raw_drive(structure, weights, gains, kc_event) / weights.total


def readout_reduceat(structure, weights, gains, kc_event):
    """Independent implementation used only for criterion B."""
    z = np.asarray(kc_event, dtype=np.float64)[structure.edge_kc]
    contrib = weights.w * np.asarray(gains, dtype=np.float64) * z
    o = np.argsort(weights.edge_mbon, kind="stable")
    seg = weights.edge_mbon[o]
    starts = np.searchsorted(seg, np.arange(len(weights.mbon_ids)))
    return np.add.reduceat(contrib[o], starts) / weights.total


def run_learner(structure, weights, theta, kc_events, dan_events):
    """Streams (rho(t), g(t)); rho(t) is read from g(t-1) before the step-t update (read-before-write)."""
    g_prev = np.ones(len(structure.edge_comp), dtype=np.float64)
    for t, g in enumerate(M5C.run_chronology(structure, theta, kc_events, dan_events)):
        rho = readout(structure, weights, g_prev, kc_events[t])
        yield rho, g
        g_prev = g


def final_gains(structure, theta, Z, A, keep_steps=()):
    kept = {}
    g = np.ones(len(structure.edge_comp), dtype=np.float64)
    for t, g in enumerate(M5C.run_chronology(structure, theta, Z, A)):
        if t in keep_steps:
            kept[t] = g
    return g, kept


M5C = None  # frozen M5C module, loaded in main() after its hash is verified


def main():
    global M5C
    started = time.time()
    prereq = {}
    for path, want in M5D0_FROZEN_FILES.items():
        prereq["sha256:" + path] = Path(path).is_file() and sha256(path) == want

    def blocked(reason, extra=None):
        result = {
            "classification": "BLOCKED_M5D0_PREREQUISITE_PARITY",
            "reason": reason,
            "protocol_freeze_commit": PROTOCOL_FREEZE_COMMIT,
            "prerequisite_parity": prereq,
            "diagnostics": extra or {},
        }
        write_result(result)

    if not all(prereq.values()):
        blocked("M5D0 frozen file anchors failed")
        return
    M5C = load_module("v6_m5c_frozen", M5C_SCRIPT)
    m5c_result = json.loads(Path(M5C_RESULT).read_text(encoding="utf-8"))
    prereq["m5c_classification_pass"] = m5c_result.get("classification") == M5C_PASS
    for path, want in M5C.FROZEN_FILES.items():
        prereq["m5c_frozen_sha256:" + path] = Path(path).is_file() and sha256(path) == want
    prereq["source_annotations_sha256"] = sha256(W / "body-annotations.feather") == M5C.ANN_SHA
    prereq["source_weights_sha256"] = sha256(W / "connectome-weights.feather") == M5C.WEIGHTS_SHA
    for path, want in M5C.M5B3B_RERUN_SHA.items():
        prereq["m5b3b_rerun_sha256:" + path] = Path(path).is_file() and sha256(path) == want
    npz_ok = M5C.M5B3B_RERUN_EDGES.is_file()
    edges_npz = np.load(M5C.M5B3B_RERUN_EDGES) if npz_ok else None
    prereq["m5b3b_rerun_eligible_edge_content_digest"] = (
        npz_ok and M5C.edge_content_digest(edges_npz) == M5C.EDGE_CONTENT_DIGEST
    )
    if not all(prereq.values()):
        blocked("M5C/M5B3B/source prerequisite anchors failed")
        return

    m4b0 = M5C.load_module("v6_m4b0_frozen", M5C.M4B0_SCRIPT)
    m5b3b = M5C.load_module("v6_m5b3b_frozen", M5C.M5B3B_SCRIPT)
    gate_pop = json.loads(M5C.M5B3B_RERUN_GATES.read_text(encoding="utf-8"))
    m5b3b_result = json.loads(M5C.M5B3B_RERUN_RESULT.read_text(encoding="utf-8"))

    ann = feather.read_table(
        W / "body-annotations.feather", columns=["bodyId", "class", "type", "somaSide"]
    ).to_pandas()
    kc = ann[ann["class"] == "Kenyon_Cell"].sort_values("bodyId")
    dan = ann[ann["class"] == "DAN"].sort_values("bodyId")
    mbon = ann[ann["class"] == "MBON"].sort_values("bodyId")
    kc_ids = kc["bodyId"].to_numpy(dtype=np.int64)
    kc_sides = kc["somaSide"].astype(str).to_numpy()
    dan_ids = dan["bodyId"].to_numpy(dtype=np.int64)
    mbon_ids = mbon["bodyId"].to_numpy(dtype=np.int64)
    mbon_side = {int(b): m5b3b.norm(s) for b, s in zip(mbon["bodyId"], mbon["somaSide"])}
    fast_set = set(int(b) for ids in gate_pop.values() for b in ids)
    typed_fast = set(int(b) for b, t in zip(dan["bodyId"], dan["type"].map(m5b3b.norm)) if t in m5b3b.DAN_MAP)

    table = feather.read_table(
        W / "connectome-weights.feather", columns=["body_pre", "body_post", "weight"], memory_map=True
    )
    pre_parts, post_parts, w_parts = [], [], []
    for batch in table.to_batches(max_chunksize=4_000_000):
        p = batch.column(0).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        q = batch.column(1).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        wt = batch.column(2).to_numpy(zero_copy_only=False).astype(np.float64, copy=False)
        _, p_ok = M5C.idx_in(kc_ids, p)
        _, q_ok = M5C.idx_in(mbon_ids, q)
        take = p_ok & q_ok
        if take.any():
            pre_parts.append(p[take].copy())
            post_parts.append(q[take].copy())
            w_parts.append(wt[take].copy())
    edge_pre = np.concatenate(pre_parts)
    edge_post = np.concatenate(post_parts)
    edge_w = np.concatenate(w_parts)
    eligible = {
        (int(a), int(b)): str(c)
        for a, b, c in zip(edges_npz["body_pre"], edges_npz["body_post"], edges_npz["compartment"])
    }
    edge_label = [eligible.get((int(a), int(b)), "") for a, b in zip(edge_pre, edge_post)]
    n_plastic = sum(1 for c in edge_label if c)

    per_body = {int(r["bodyId"]): r for r in m5b3b_result["mbon_mapping"]["per_body"]}
    status_counts = {}
    for r in per_body.values():
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    single_by_comp = {}
    for bid, r in per_body.items():
        if r["status"] == "single_compartment":
            single_by_comp.setdefault(r["compartments"][0], []).append(bid)

    counts = {
        "KC": int(len(kc_ids)),
        "KC_L": int((kc_sides == "L").sum()),
        "KC_R": int((kc_sides == "R").sum()),
        "DAN": int(len(dan_ids)),
        "MBON": int(len(mbon_ids)),
        "FAST_DAN": int(len(fast_set)),
        "NONFAST_DAN": int(len(dan_ids) - len(fast_set)),
        "KC_MBON_EDGES": int(len(edge_pre)),
        "ELIGIBLE_EDGES": int(n_plastic),
        "NONPLASTIC_EDGES": int(len(edge_pre) - n_plastic),
        "GATE_COMPARTMENTS": int(len(gate_pop)),
    }
    prereq.update({
        "structure_counts_exact": counts == M5C.EXPECTED,
        "eligible_edges_all_found_in_exact_kc_mbon": n_plastic == len(eligible),
        "kc_mbon_pairs_unique": len(set(zip(edge_pre.tolist(), edge_post.tolist()))) == len(edge_pre),
        "fast_dan_set_equals_frozen_type_rule": fast_set == typed_fast,
        "mbon_status_counts_exact": status_counts == MBON_STATUS_EXPECTED,
        "every_mbon_has_kc_input": len(np.unique(edge_post)) == counts["MBON"],
        "every_eligible_compartment_has_single_compartment_mbon": all(
            len(single_by_comp.get(c, [])) > 0 for c in M5C.ELIGIBLE_COMPARTMENTS
        ),
        "weights_finite_positive": bool(np.isfinite(edge_w).all() and (edge_w > 0).all()),
    })
    if not all(prereq.values()):
        blocked("frozen structure parity failed", {"counts": counts, "mbon_status_counts": status_counts})
        return

    S0 = M5C.build_structure(kc_ids, dan_ids, edge_pre, edge_post, edge_label, gate_pop)
    RW0 = make_readout_weights(S0, edge_w)
    n_kc, n_dan, n_edge = len(kc_ids), len(dan_ids), len(edge_pre)
    mpos = {int(b): i for i, b in enumerate(RW0.mbon_ids)}
    comps = M5C.ELIGIBLE_COMPARTMENTS
    shared = {c: sorted(c2 for c2, ids in gate_pop.items() if set(ids) & set(gate_pop[c])) for c in comps}
    single_idx = {c: np.array(sorted(mpos[b] for b in single_by_comp[c]), dtype=np.int64) for c in comps}
    nonplastic_mbons = np.array(
        sorted(mpos[b] for b, r in per_body.items() if r["status"] != "single_compartment"), dtype=np.int64
    )
    untouched = {}
    for c in comps:
        idx = [single_idx[c2] for c2 in comps if c2 not in shared[c]] + [nonplastic_mbons]
        untouched[c] = np.unique(np.concatenate(idx))

    # Frozen synthetic streams (PCG64 seed 20260927); draw order fixed by the protocol.
    rng = np.random.Generator(np.random.PCG64(SEED))
    odors = {}
    for c in comps:
        z2 = m4b0.sparsify(kc_ids, kc_sides, rng.standard_normal((2, n_kc)))
        odors[c] = (z2[0].copy(), z2[1].copy())
    plastic = S0.edge_comp >= 0
    random_states = []
    for _ in range(N_RANDOM_STATES):
        g = np.ones(n_edge, dtype=np.float64)
        g[plastic] = rng.uniform(0.0, RANDOM_STATE_GMAX, int(plastic.sum()))
        z = m4b0.sparsify(kc_ids, kc_sides, rng.standard_normal((1, n_kc)))[0]
        random_states.append((g, z))
    perm_kc = rng.permutation(n_kc)
    perm_dan = rng.permutation(n_dan)
    perm_edge = rng.permutation(n_edge)
    S_perm = M5C.build_structure(
        kc_ids[perm_kc], dan_ids[perm_dan], edge_pre[perm_edge], edge_post[perm_edge],
        [edge_label[i] for i in perm_edge], gate_pop,
    )
    RW_perm = make_readout_weights(S_perm, edge_w[perm_edge])

    rec = M5C.Recorder()
    gi = "grid_independent"

    # B (theta-independent part): two independent readout implementations.
    worst = 0.0
    for g, z in random_states:
        a = readout(S0, RW0, g, z)
        b = readout_reduceat(S0, RW0, g, z)
        scale = np.maximum(np.maximum(np.abs(a), np.abs(b)), np.finfo(np.float64).tiny)
        worst = max(worst, float(np.max(np.abs(a - b) / scale)))
    rec.check("B_readout_exactness_and_bounds", worst <= READOUT_REL_TOL, gi, {"max_relative_difference": worst})

    # K: interface firewall.
    rec.check("K_interface_firewall", list(inspect.signature(readout).parameters) == ["structure", "weights", "gains", "kc_event"], gi, "readout signature")
    rec.check("K_interface_firewall", list(inspect.signature(run_learner).parameters) == ["structure", "weights", "theta", "kc_events", "dan_events"], gi, "learner signature")

    # Per-compartment static quantities.
    kc_col = {c: None for c in comps}
    omega = {}
    naive = {}
    tested = {}
    a_edges = {}
    for c in comps:
        zA, zB = odors[c]
        naive[c] = (raw_drive(S0, RW0, np.ones(n_edge), zA), raw_drive(S0, RW0, np.ones(n_edge), zB))
        tested[c] = np.array([m for m in single_idx[c] if naive[c][0][m] > 0], dtype=np.int64)
        zAB = (zA & zB).astype(np.uint8)
        num = raw_drive(S0, RW0, np.ones(n_edge), zAB)
        den = naive[c][1]
        omega[c] = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
        a_edges[c] = np.flatnonzero((S0.edge_comp == S0.comps.index(c)) & (zA[S0.edge_kc] == 1))
        kc_col[c] = np.flatnonzero(S0.gate_members[S0.comps.index(c)])

    def paradigm_streams(c):
        zA = odors[c][0]
        cols = kc_col[c]
        T = L_SPACING * N_TRIALS
        Zf = np.zeros((T, n_kc), dtype=np.uint8)
        Af = np.zeros((T, n_dan), dtype=np.uint8)
        steps = np.arange(N_TRIALS) * L_SPACING
        Zf[steps] = zA
        Af[np.ix_(steps, cols)] = 1
        Zb = np.zeros((T, n_kc), dtype=np.uint8)
        Ab = np.zeros((T, n_dan), dtype=np.uint8)
        Ab[np.ix_(steps, cols)] = 1
        Zb[steps + 1] = zA
        Zr = np.vstack([Zf, Zb])
        Ar = np.vstack([Af, Ab])
        return (Zf, Af), (Zb, Ab), (Zr, Ar)

    streams = {c: paradigm_streams(c) for c in comps}
    diagnostics = {
        "tested_mbons_by_compartment_and_side": {
            c: {s: int(sum(1 for m in tested[c] if mbon_side[int(RW0.mbon_ids[m])] == s)) for s in ("L", "R")}
            for c in comps
        },
        "odor_overlap_kcs": {c: int((odors[c][0] & odors[c][1]).sum()) for c in comps},
        "shared_dan_compartments": shared,
        "naive_rho_A_summary": {
            c: {"min": float((naive[c][0] / RW0.total).min()), "max": float((naive[c][0] / RW0.total).max())}
            for c in comps
        },
    }

    def check_bounds(rho, th, P, label):
        return rec.check("B_readout_exactness_and_bounds", bool(rho.min() >= 0.0 and rho.max() <= th.g_max), P, label)

    points = [dict(zip(M5C.GRID, v)) for v in itertools.product(*M5C.GRID.values())]
    for pt in points:
        th = M5C.Theta(**pt)
        P = pt
        ref = pt == REFERENCE_POINT
        ref_summary = {}
        for c in comps:
            zA, zB = odors[c]
            (Zf, Af), (Zb, Ab), (Zr, Ar) = streams[c]
            nA, nB = naive[c]
            T_A = tested[c]

            # FWD with streaming readout (C), then D, G, H.
            g_hist = {}
            rho_hist = {}
            g_f = None
            for t, (rho, g) in enumerate(run_learner(S0, RW0, th, Zf, Af)):
                check_bounds(rho, th, P, f"stream {c} t={t}")
                if t in (0, 32):
                    rho_hist[t] = rho
                if t in (31, 32):
                    g_hist[t] = g
                g_f = g
            c_ok = np.array_equal(rho_hist[0], readout(S0, RW0, np.ones(n_edge), zA))
            c_ok &= np.array_equal(rho_hist[32], readout(S0, RW0, g_hist[31], zA))
            post = readout(S0, RW0, g_hist[32], zA)
            c_ok &= bool(len(T_A) > 0 and np.any(post[T_A] != rho_hist[32][T_A]))
            rec.check("C_read_before_write", c_ok, P, {"compartment": c})

            g_b, _ = final_gains(S0, th, Zb, Ab)
            g_r, kept = final_gains(S0, th, Zr, Ar, keep_steps=(L_SPACING * N_TRIALS - 1,))
            g_mid = kept[L_SPACING * N_TRIALS - 1]

            results = {}
            for name, g in (("FWD", g_f), ("BWD", g_b), ("REV", g_r), ("REV_MID", g_mid)):
                rA = raw_drive(S0, RW0, g, zA)
                rB = raw_drive(S0, RW0, g, zB)
                check_bounds(rA / RW0.total, th, P, f"{name} {c} A")
                check_bounds(rB / RW0.total, th, P, f"{name} {c} B")
                RA = np.divide(rA, nA, out=np.full_like(rA, np.nan), where=nA > 0)
                RB = np.divide(rB, nB, out=np.full_like(rB, np.nan), where=nB > 0)
                results[name] = (g, rA, rB, RA, RB)

            rec.check("D_forward_depression", len(T_A) > 0 and bool(np.all(results["FWD"][3][T_A] < 1.0)), P, {"compartment": c})
            rec.check("E_backward_potentiation", len(T_A) > 0 and bool(np.all(results["BWD"][3][T_A] > 1.0)), P, {"compartment": c})
            rec.check("F_reversal", len(T_A) > 0 and bool(np.all(results["REV"][3][T_A] > results["REV_MID"][3][T_A])), P, {"compartment": c})

            for name in ("FWD", "BWD", "REV"):
                g, rA, rB, RA, RB = results[name]
                ga = g[a_edges[c]]
                uniform = len(ga) > 0 and bool(np.all(ga == ga[0]))
                ok = uniform
                err = None
                if uniform:
                    a_c = float(ga[0])
                    mb = np.array([m for m in single_idx[c] if nB[m] > 0], dtype=np.int64)
                    dev = np.abs((RB[mb] - 1.0) - omega[c][mb] * (a_c - 1.0))
                    err = float(dev.max()) if len(mb) else 0.0
                    ok = err <= OVERLAP_TOL
                rec.check("G_overlap_only_specificity", ok, P, {"compartment": c, "paradigm": name, "max_abs_error": err, "uniform_a_c": uniform})
                u = untouched[c]
                h_ok = bool(np.array_equal(rA[u], nA[u]) and np.array_equal(rB[u], nB[u]))
                rec.check("H_compartment_locality", h_ok, P, {"compartment": c, "paradigm": name})

            # I: determinism.
            g_f2, _ = final_gains(S0, th, Zf, Af)
            i_ok = np.array_equal(g_f2, g_f) and np.array_equal(
                readout(S0, RW0, g_f2, zA), readout(S0, RW0, g_f, zA)
            )
            rec.check("I_determinism", i_ok, P, {"compartment": c})

            # J: permutation equivariance of FWD test readouts keyed by MBON bodyId.
            g_p, _ = final_gains(S_perm, th, Zf[:, perm_kc], Af[:, perm_dan])
            j_ok = np.array_equal(RW_perm.mbon_ids, RW0.mbon_ids) and np.array_equal(
                readout(S_perm, RW_perm, g_p, zA[perm_kc]), readout(S0, RW0, g_f, zA)
            ) and np.array_equal(
                readout(S_perm, RW_perm, g_p, zB[perm_kc]), readout(S0, RW0, g_f, zB)
            )
            rec.check("J_permutation_equivariance", j_ok, P, {"compartment": c})

            if ref:
                ref_summary[c] = {
                    name: {
                        "R_A_mean_tested": float(np.mean(results[name][3][T_A])) if len(T_A) else None,
                        "R_B_mean_single": float(np.nanmean(results[name][4][single_idx[c]])),
                    }
                    for name in ("FWD", "BWD", "REV_MID", "REV")
                }
        if ref:
            diagnostics["reference_point_R_summary"] = ref_summary

    crit_names = [
        "B_readout_exactness_and_bounds", "C_read_before_write", "D_forward_depression", "E_backward_potentiation",
        "F_reversal", "G_overlap_only_specificity", "H_compartment_locality", "I_determinism",
        "J_permutation_equivariance", "K_interface_firewall",
    ]
    criteria = {"A_prerequisite_parity": True}
    for name in crit_names:
        cc = rec.counts.get(name, {"checks": 0, "failures": 0})
        criteria[name] = cc["checks"] > 0 and cc["failures"] == 0
    passed = all(criteria.values())
    result = {
        "classification": "PASS_M5D0_MBON_READOUT_CONDITIONING_QUALIFIED" if passed else "FAIL_M5D0_MBON_READOUT_CONDITIONING",
        "reason": (
            "all frozen readout and conditioning criteria held at all 72 grid points"
            if passed else
            "prerequisites held but at least one frozen readout/conditioning criterion failed"
        ),
        "protocol_freeze_commit": PROTOCOL_FREEZE_COMMIT,
        "protocol_sha256": PROTOCOL_SHA,
        "prerequisite_parity": prereq,
        "structure_counts": counts,
        "mbon_status_counts": status_counts,
        "grid_points": len(points),
        "seed": SEED,
        "criteria": criteria,
        "check_counts": {k: rec.counts[k] for k in sorted(rec.counts)},
        "failure_records": rec.records,
        "diagnostics": diagnostics,
        "readout_definition": "rho_m = sum_{e in E_m} w_e g_e z_k(e) / W_m; read-before-write; canonical (MBON,KC) summation order",
        "guardrails": {
            "parameter_values_selected": False,
            "valence_assigned": False,
            "action_mapping_defined": False,
            "synapse_coordinates_opened": False,
            "market_reward_pnl_opened": False,
            "amin_numeric_opened": False,
            "m4v0_numeric_opened": False,
        },
    }
    write_result(result)
    print(f"runtime_seconds={time.time() - started:.1f}", file=sys.stderr)


def write_result(result):
    (O / "v6_m5d0_mbon_readout_conditioning_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result.get(k) for k in ("classification", "reason", "criteria", "check_counts", "structure_counts")},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
