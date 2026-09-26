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
O = Path("v6_m5c_out")
O.mkdir(exist_ok=True)

PROTOCOL_FREEZE_COMMIT = "5fcce75f15360ca6795926217b6bcb21129cba1f"
PROTOCOL_PATH = "research/v6_m5c_dopamine_gated_plasticity_chronology_protocol.md"
PROTOCOL_SHA = "4590ab29cfba6fe9a559003286c94146cb96082bbe2f6c6d864437c5ce26eee6"

ANN_SHA = "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
WEIGHTS_SHA = "e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1"

M5B3B_SCRIPT = "fly_mnq/v6_m5b3b_compartment_gating_mvp.py"
M4B0_SCRIPT = "fly_mnq/v6_m4b0_functional_apl_sparsifier.py"
FROZEN_FILES = {
    PROTOCOL_PATH: PROTOCOL_SHA,
    M5B3B_SCRIPT: "0a8d6c3fb61e7659fb885433dc0a93998dfa3b1b05397d8310274eb9fe14914b",
    M4B0_SCRIPT: "5927c88dbcbee6ae291d7d2c2dc70893e2c3c3f48ba1a28cb7c79eb1a328bac5",
    "research/results/v6_m5b2_exact_learner_topology_result.json": "9f05cd3f87759299396133c9c7aeda9e55bebaf4b60d9887573b17a47075b733",
    "research/results/v6_m5b3a_compartment_label_schema_result.json": "dbf3844742d551910f642b05207c3d5b6d155a5fe9a9c89297aa9282bc439f58",
    "research/results/v6_m5b3b_compartment_gating_mvp_result.json": "1792a7f082cf951db76f98978236d3cc0eed828874922ebde79a98b88aadb1b2",
}
M5B3B_RERUN_RESULT = B / "v6_m5b3b_compartment_gating_mvp_result.json"
M5B3B_RERUN_GATES = B / "v6_m5b3b_gate_population_by_compartment.json"
M5B3B_RERUN_EDGES = B / "v6_m5b3b_eligible_kc_mbon_edges.npz"
M5B3B_RERUN_SHA = {
    str(M5B3B_RERUN_RESULT): "1792a7f082cf951db76f98978236d3cc0eed828874922ebde79a98b88aadb1b2",
    str(M5B3B_RERUN_GATES): "8ca690aacb7ebde862f4a37279549206011857eed3d6b6d49ecc146fdfa979ca",
}
EDGE_CONTENT_DIGEST = "b2567b0107378c25297f3571397be7bdf470ce04daed9cf846bd6c5d1062b637"
EDGE_FILE_SHA_DIAGNOSTIC = "cc347569347e3332ead93eeb94411641d542818953cc6a5e9db8565b9711cf01"
EDGE_ARRAYS = ("body_pre", "body_post", "raw_weight", "compartment", "gate_dan_count")

INPUT_MANIFEST = sorted(
    list(FROZEN_FILES)
    + [str(W / "body-annotations.feather"), str(W / "connectome-weights.feather")]
    + [str(M5B3B_RERUN_RESULT), str(M5B3B_RERUN_GATES), str(M5B3B_RERUN_EDGES)]
)

EXPECTED = {
    "KC": 4064, "KC_L": 2019, "KC_R": 2045, "DAN": 340, "MBON": 97,
    "FAST_DAN": 328, "NONFAST_DAN": 12,
    "KC_MBON_EDGES": 61210, "ELIGIBLE_EDGES": 26532, "NONPLASTIC_EDGES": 34678,
    "GATE_COMPARTMENTS": 16,
}
ELIGIBLE_COMPARTMENTS = ("B'1", "B'2", "B1", "a'1", "a'2", "a'3", "a1", "a2", "a3", "y2", "y4", "y5")
K_BY_SIDE = {"L": 202, "R": 205}

GRID = {
    "eta_minus": (0.05, 0.5),
    "eta_plus": (0.05, 0.5),
    "lam_K": (0.0, 0.5, 0.9),
    "lam_D": (0.0, 0.5, 0.9),
    "g_max": (1.5, 2.0),
}
REFERENCE_POINT = {"eta_minus": 0.05, "eta_plus": 0.05, "lam_K": 0.5, "lam_D": 0.5, "g_max": 2.0}
SEED = 20260926
T_RANDOM = 64
P_DAN = 0.05
KERNEL_KC_STEP = 3
KERNEL_T = 7
KERNEL_DELTAS = tuple(range(-3, 4))
SAT_T = 2048
SAT_SPACING = 64
SAT_PAIRS = 32
CUTS = (8, 16, 32, 48)
TOL = 1e-12
MAX_FAILURE_RECORDS = 200


class Theta(NamedTuple):
    eta_minus: float
    eta_plus: float
    lam_K: float
    lam_D: float
    g_max: float


class Structure(NamedTuple):
    kc_ids: np.ndarray       # KC bodyIds, any order; KC event columns follow this order
    dan_ids: np.ndarray      # all exact DAN bodyIds, any order; DAN event columns follow this order
    edge_pre: np.ndarray     # KC bodyId of each exact KC->MBON edge
    edge_post: np.ndarray    # MBON bodyId of each exact KC->MBON edge
    edge_kc: np.ndarray      # index of edge_pre in kc_ids
    edge_comp: np.ndarray    # index into comps for plastic edges, -1 for nonplastic
    comps: tuple             # gate compartment labels
    gate_members: np.ndarray # int64 (n_comp, n_dan) 0/1 frozen M5B3B gate membership
    gate_size: np.ndarray    # int64 (n_comp,) |G_c|


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def edge_content_digest(npz) -> str:
    h = hashlib.sha256()
    for name in EDGE_ARRAYS:
        a = np.ascontiguousarray(npz[name])
        h.update(name.encode() + b"\0" + a.dtype.str.encode() + b"\0" + repr(a.shape).encode() + b"\0")
        h.update(a.tobytes())
    return h.hexdigest()


def load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def idx_in(sorted_ids: np.ndarray, values: np.ndarray):
    pos = np.searchsorted(sorted_ids, values)
    ok = pos < len(sorted_ids)
    safe = np.minimum(pos, len(sorted_ids) - 1)
    ok &= sorted_ids[safe] == values
    return safe, ok


def build_structure(kc_ids, dan_ids, edge_pre, edge_post, edge_label, gate_pop) -> Structure:
    kc_ids = np.asarray(kc_ids, dtype=np.int64)
    dan_ids = np.asarray(dan_ids, dtype=np.int64)
    edge_pre = np.asarray(edge_pre, dtype=np.int64)
    edge_post = np.asarray(edge_post, dtype=np.int64)
    if len(np.unique(kc_ids)) != len(kc_ids) or len(np.unique(dan_ids)) != len(dan_ids):
        raise ValueError("body IDs must be unique")
    sorter = np.argsort(kc_ids, kind="stable")
    pos = np.searchsorted(kc_ids, edge_pre, sorter=sorter)
    pos = np.minimum(pos, len(kc_ids) - 1)
    edge_kc = sorter[pos].astype(np.int64)
    if not np.array_equal(kc_ids[edge_kc], edge_pre):
        raise ValueError("edge presynaptic body not in KC set")
    comps = tuple(sorted(gate_pop))
    comp_index = {c: i for i, c in enumerate(comps)}
    edge_comp = np.array([comp_index[c] if c else -1 for c in edge_label], dtype=np.int64)
    dan_pos = {int(b): i for i, b in enumerate(dan_ids)}
    members = np.zeros((len(comps), len(dan_ids)), dtype=np.int64)
    for c, ids in gate_pop.items():
        for b in ids:
            members[comp_index[c], dan_pos[int(b)]] = 1
    size = members.sum(axis=1).astype(np.int64)
    if (size <= 0).any():
        raise ValueError("empty gate population")
    return Structure(kc_ids, dan_ids, edge_pre, edge_post, edge_kc, edge_comp, comps, members, size)


def run_chronology(structure, theta, kc_events, dan_events):
    """Frozen M5C chronology. Yields a fresh gain vector g(t) after each step t.

    D_c(t) = n_c(t)/|G_c|; x_k(t) = lam_K*x_k(t-1) + z_k(t);
    dg_e(t) = -eta_minus*x_k(t)*D_c(t) + eta_plus*y_c(t-1)*z_k(t);
    g_e(t) = min(max(g_e(t-1) + dg_e(t), 0), g_max); y_c(t) = lam_D*y_c(t-1) + D_c(t).
    Nonplastic edges keep g = 1.
    """
    Z = np.asarray(kc_events)
    A = np.asarray(dan_events)
    if Z.ndim != 2 or A.ndim != 2 or Z.shape[0] != A.shape[0]:
        raise ValueError("event arrays must be (T, n) with equal T")
    if Z.shape[1] != len(structure.kc_ids) or A.shape[1] != len(structure.dan_ids):
        raise ValueError("event columns must match structure body order")
    if not (np.isin(Z, (0, 1)).all() and np.isin(A, (0, 1)).all()):
        raise ValueError("events must be binary")
    plastic = np.flatnonzero(structure.edge_comp >= 0)
    p_kc = structure.edge_kc[plastic]
    p_comp = structure.edge_comp[plastic]
    g = np.ones(len(structure.edge_comp), dtype=np.float64)
    x = np.zeros(len(structure.kc_ids), dtype=np.float64)
    y = np.zeros(len(structure.comps), dtype=np.float64)
    for t in range(Z.shape[0]):
        z = Z[t].astype(np.float64)
        n = structure.gate_members @ A[t].astype(np.int64)
        d = n / structure.gate_size
        x = theta.lam_K * x + z
        dg = -theta.eta_minus * x[p_kc] * d[p_comp] + theta.eta_plus * y[p_comp] * z[p_kc]
        g_new = g.copy()
        g_new[plastic] = np.minimum(np.maximum(g[plastic] + dg, 0.0), theta.g_max)
        y = theta.lam_D * y + d
        g = g_new
        yield g


class Recorder:
    def __init__(self):
        self.counts = {}
        self.records = []

    def check(self, criterion, ok, point, detail):
        ok = bool(ok)
        c = self.counts.setdefault(criterion, {"checks": 0, "failures": 0})
        c["checks"] += 1
        if not ok:
            c["failures"] += 1
            if len(self.records) < MAX_FAILURE_RECORDS:
                self.records.append({"criterion": criterion, "grid_point": point, "detail": detail})
        return ok


def consume(structure, theta, Z, A, rec, point, label, nonplastic, keep=False):
    """Run a stream, enforcing F (nonplastic invariance) and G bounds at every step."""
    traj = [] if keep else None
    g = np.ones(len(structure.edge_comp), dtype=np.float64)
    np_ok = True
    lo_ok = True
    hi_ok = True
    for g in run_chronology(structure, theta, Z, A):
        np_ok &= bool(np.all(g[nonplastic] == 1.0))
        lo_ok &= bool(g.min() >= 0.0)
        hi_ok &= bool(g.max() <= theta.g_max)
        if keep:
            traj.append(g)
    rec.check("F_nonplastic_invariance", np_ok, point, label)
    rec.check("G_bounds", lo_ok and hi_ok, point, label)
    return g, (np.vstack(traj) if keep else None)


def main():
    started = time.time()
    prereq = {}
    for path, want in FROZEN_FILES.items():
        prereq["sha256:" + path] = Path(path).is_file() and sha256(path) == want
    prereq["source_annotations_sha256"] = sha256(W / "body-annotations.feather") == ANN_SHA
    prereq["source_weights_sha256"] = sha256(W / "connectome-weights.feather") == WEIGHTS_SHA
    for path, want in M5B3B_RERUN_SHA.items():
        prereq["m5b3b_rerun_sha256:" + path] = Path(path).is_file() and sha256(path) == want
    edges_npz = np.load(M5B3B_RERUN_EDGES) if M5B3B_RERUN_EDGES.is_file() else None
    content_digest = edge_content_digest(edges_npz) if edges_npz is not None else None
    prereq["m5b3b_rerun_eligible_edge_content_digest"] = content_digest == EDGE_CONTENT_DIGEST
    edge_file_sha = sha256(M5B3B_RERUN_EDGES) if edges_npz is not None else None

    def blocked(reason, extra=None):
        result = {
            "classification": "BLOCKED_M5C_PREREQUISITE_PARITY",
            "reason": reason,
            "protocol_freeze_commit": PROTOCOL_FREEZE_COMMIT,
            "prerequisite_parity": prereq,
            "diagnostics": {"eligible_edge_npz_file_sha256": edge_file_sha, **(extra or {})},
            "input_manifest": INPUT_MANIFEST,
        }
        write_result(result)

    if not all(prereq.values()):
        blocked("one or more frozen file/source/M5B3B re-execution anchors failed")
        return

    m4b0 = load_module("v6_m4b0_frozen", M4B0_SCRIPT)
    m5b3b = load_module("v6_m5b3b_frozen", M5B3B_SCRIPT)
    gate_pop = json.loads(M5B3B_RERUN_GATES.read_text(encoding="utf-8"))

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
    fast_set = set(int(b) for ids in gate_pop.values() for b in ids)
    typed_fast = set(int(b) for b, t in zip(dan["bodyId"], dan["type"].map(m5b3b.norm)) if t in m5b3b.DAN_MAP)
    nonfast_ids = np.array(sorted(set(dan_ids.tolist()) - fast_set), dtype=np.int64)

    table = feather.read_table(W / "connectome-weights.feather", columns=["body_pre", "body_post"], memory_map=True)
    pre_parts, post_parts = [], []
    for batch in table.to_batches(max_chunksize=4_000_000):
        p = batch.column(0).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        q = batch.column(1).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        _, p_ok = idx_in(kc_ids, p)
        _, q_ok = idx_in(mbon_ids, q)
        take = p_ok & q_ok
        if take.any():
            pre_parts.append(p[take].copy())
            post_parts.append(q[take].copy())
    edge_pre = np.concatenate(pre_parts)
    edge_post = np.concatenate(post_parts)
    eligible = {
        (int(a), int(b)): str(c)
        for a, b, c in zip(edges_npz["body_pre"], edges_npz["body_post"], edges_npz["compartment"])
    }
    edge_label = [eligible.get((int(a), int(b)), "") for a, b in zip(edge_pre, edge_post)]
    n_plastic = sum(1 for c in edge_label if c)
    pairs_unique = len(set(zip(edge_pre.tolist(), edge_post.tolist()))) == len(edge_pre)

    counts = {
        "KC": int(len(kc_ids)),
        "KC_L": int((kc_sides == "L").sum()),
        "KC_R": int((kc_sides == "R").sum()),
        "DAN": int(len(dan_ids)),
        "MBON": int(len(mbon_ids)),
        "FAST_DAN": int(len(fast_set)),
        "NONFAST_DAN": int(len(nonfast_ids)),
        "KC_MBON_EDGES": int(len(edge_pre)),
        "ELIGIBLE_EDGES": int(n_plastic),
        "NONPLASTIC_EDGES": int(len(edge_pre) - n_plastic),
        "GATE_COMPARTMENTS": int(len(gate_pop)),
    }
    eligible_comps = tuple(sorted(set(c for c in edge_label if c)))
    prereq.update({
        "structure_counts_exact": counts == EXPECTED,
        "eligible_edges_all_found_in_exact_kc_mbon": n_plastic == len(eligible),
        "kc_mbon_pairs_unique": pairs_unique,
        "fast_dan_set_equals_frozen_type_rule": fast_set == typed_fast,
        "eligible_compartments_exact": eligible_comps == ELIGIBLE_COMPARTMENTS,
        "kc_somaSide_exact_LR": bool(np.isin(kc_sides, ["L", "R"]).all()),
    })
    if not all(prereq.values()):
        blocked("frozen structure parity failed", {"counts": counts, "eligible_compartments": list(eligible_comps)})
        return

    S0 = build_structure(kc_ids, dan_ids, edge_pre, edge_post, edge_label, gate_pop)
    nonplastic = np.flatnonzero(S0.edge_comp < 0)
    comp_edges = {c: np.flatnonzero(S0.edge_comp == S0.comps.index(c)) for c in ELIGIBLE_COMPARTMENTS}
    dan_col = {int(b): i for i, b in enumerate(dan_ids)}
    fast_cols = np.array(sorted(dan_col[b] for b in fast_set), dtype=np.int64)
    nonfast_cols = np.array(sorted(dan_col[int(b)] for b in nonfast_ids), dtype=np.int64)
    n_kc, n_dan, n_edge = len(kc_ids), len(dan_ids), len(edge_pre)

    # Frozen synthetic streams (PCG64 seed 20260926); draw order is fixed.
    rng = np.random.Generator(np.random.PCG64(SEED))
    Z_int = m4b0.sparsify(kc_ids, kc_sides, rng.standard_normal((T_RANDOM, n_kc)))
    A_int = (rng.random((T_RANDOM, n_dan)) < P_DAN).astype(np.uint8)
    alt = {}
    for tau in CUTS:
        Za = Z_int.copy()
        Aa = A_int.copy()
        Za[tau + 1:] = m4b0.sparsify(kc_ids, kc_sides, rng.standard_normal((T_RANDOM - tau - 1, n_kc)))
        Aa[tau + 1:] = (rng.random((T_RANDOM - tau - 1, n_dan)) < P_DAN).astype(np.uint8)
        alt[tau] = (Za, Aa)
    perm_kc = rng.permutation(n_kc)
    perm_dan = rng.permutation(n_dan)
    perm_edge = rng.permutation(n_edge)

    rec = Recorder()
    grid_free = "grid_independent"

    # L (grid-independent part): exact sparsifier counts per hemisphere per step.
    l_counts_ok = True
    for Zs in [Z_int] + [alt[t][0] for t in CUTS]:
        for side in ("L", "R"):
            l_counts_ok &= bool(np.all(Zs[:, kc_sides == side].sum(axis=1) == K_BY_SIDE[side]))
    rec.check("L_m4b0_integration", l_counts_ok, grid_free, "exact 202 L / 205 R active KCs per step")

    # M: interface firewall.
    params = list(inspect.signature(run_chronology).parameters)
    rec.check("M_interface_firewall", params == ["structure", "theta", "kc_events", "dan_events"], grid_free, params)
    rec.check("M_interface_firewall", all(p in INPUT_MANIFEST for p in list(FROZEN_FILES)), grid_free, "manifest")
    rec.check("K_valence_agnostic_shared_rule", len(Theta._fields) == 5, grid_free, list(Theta._fields))

    # J structure (built once): joint permutation of KC, DAN and edge order.
    S_perm = build_structure(
        kc_ids[perm_kc], dan_ids[perm_dan], edge_pre[perm_edge], edge_post[perm_edge],
        [edge_label[i] for i in perm_edge], gate_pop,
    )

    ones_kc = np.ones(n_kc, dtype=np.uint8)
    diagnostics = {}
    points = [dict(zip(GRID, v)) for v in itertools.product(*GRID.values())]
    for pt in points:
        th = Theta(**pt)
        P = pt

        # B, C, K: pairing kernel per eligible compartment.
        kernel = {}
        for c in ELIGIBLE_COMPARTMENTS:
            members = np.flatnonzero(S0.gate_members[S0.comps.index(c)])
            for delta in KERNEL_DELTAS:
                Z = np.zeros((KERNEL_T, n_kc), dtype=np.uint8)
                A = np.zeros((KERNEL_T, n_dan), dtype=np.uint8)
                Z[KERNEL_KC_STEP] = 1
                A[KERNEL_KC_STEP + delta, members] = 1
                g, _ = consume(S0, th, Z, A, rec, P, f"kernel {c} delta={delta}", nonplastic)
                ge = g[comp_edges[c]]
                if delta >= 0:
                    factor = th.lam_K ** delta
                    expected = 1.0 - th.eta_minus * factor
                    sign_ok = bool(np.all(ge <= 1.0)) and (bool(np.all(ge < 1.0)) if factor > 0 else bool(np.all(ge == 1.0)))
                else:
                    factor = th.lam_D ** (abs(delta) - 1)
                    expected = 1.0 + th.eta_plus * factor
                    sign_ok = bool(np.all(ge >= 1.0)) and (bool(np.all(ge > 1.0)) if factor > 0 else bool(np.all(ge == 1.0)))
                err = float(np.max(np.abs(ge - expected)))
                rec.check("B_pairing_kernel_exact", err <= TOL, P, {"compartment": c, "delta": delta, "max_abs_error": err})
                rec.check("C_order_sign_rule", sign_ok, P, {"compartment": c, "delta": delta})
                uniq = np.unique(ge)
                rec.check("K_valence_agnostic_shared_rule", len(uniq) == 1, P, {"compartment": c, "delta": delta, "distinct_values": int(len(uniq))})
                kernel.setdefault(delta, []).append(float(ge[0]))
        for delta, vals in kernel.items():
            rec.check("K_valence_agnostic_shared_rule", len(set(vals)) == 1, P, {"delta": delta, "cross_compartment_values": sorted(set(vals))})
        if pt == REFERENCE_POINT:
            diagnostics["kernel_reference_point"] = {str(d): kernel[d][0] - 1.0 for d in KERNEL_DELTAS}

        # D1 KC-only, D2 DAN-only, D3 KC specificity.
        g, _ = consume(S0, th, Z_int, np.zeros_like(A_int), rec, P, "D1 KC-only", nonplastic)
        rec.check("D_coincidence_requirement", np.all(g == 1.0), P, "D1 KC-only stream changed a gain")
        g, _ = consume(S0, th, np.zeros_like(Z_int), A_int, rec, P, "D2 DAN-only", nonplastic)
        rec.check("D_coincidence_requirement", np.all(g == 1.0), P, "D2 DAN-only stream changed a gain")
        A1 = np.zeros((1, n_dan), dtype=np.uint8)
        A1[0, fast_cols] = 1
        g, _ = consume(S0, th, Z_int[:1], A1, rec, P, "D3 KC specificity", nonplastic)
        expect = np.zeros(n_edge, dtype=bool)
        expect[S0.edge_comp >= 0] = Z_int[0][S0.edge_kc[S0.edge_comp >= 0]] == 1
        rec.check("D_coincidence_requirement", np.array_equal(g != 1.0, expect), P, "D3 changed set != eligible edges of active KCs")

        # E: compartment locality for every single DAN body.
        e_ok = True
        e_detail = None
        for b in dan_ids:
            col = dan_col[int(b)]
            A1 = np.zeros((1, n_dan), dtype=np.uint8)
            A1[0, col] = 1
            g, _ = consume(S0, th, ones_kc[None, :], A1, rec, P, f"E single DAN {int(b)}", nonplastic)
            mapped = set(np.flatnonzero(S0.gate_members[:, col]).tolist())
            expect = np.isin(S0.edge_comp, list(mapped)) if mapped else np.zeros(n_edge, dtype=bool)
            if not np.array_equal(g != 1.0, expect):
                e_ok = False
                e_detail = {"dan_bodyId": int(b), "fast": int(b) in fast_set}
                break
        rec.check("E_compartment_locality", e_ok, P, e_detail)

        # G: saturation streams.
        Zs = np.zeros((SAT_T, n_kc), dtype=np.uint8)
        As = np.zeros((SAT_T, n_dan), dtype=np.uint8)
        steps = np.arange(SAT_PAIRS) * SAT_SPACING
        Zs[steps] = 1
        As[np.ix_(steps, fast_cols)] = 1
        g, _ = consume(S0, th, Zs, As, rec, P, "G depression saturation", nonplastic)
        rec.check("G_saturation", np.all(g[S0.edge_comp >= 0] == 0.0), P, "depression saturation did not reach exactly 0")
        Zs = np.zeros((SAT_T, n_kc), dtype=np.uint8)
        Zs[steps + 1] = 1
        g, _ = consume(S0, th, Zs, As, rec, P, "G potentiation saturation", nonplastic)
        rec.check("G_saturation", np.all(g[S0.edge_comp >= 0] == th.g_max), P, "potentiation saturation did not reach exactly G_MAX")

        # H, I, L: sparsifier-driven random stream.
        g_base, traj = consume(S0, th, Z_int, A_int, rec, P, "L/H/I base stream", nonplastic, keep=True)
        for tau in CUTS:
            Za, Aa = alt[tau]
            prefix = []
            for t, ga in enumerate(run_chronology(S0, th, Za, Aa)):
                prefix.append(ga)
                if t == tau:
                    break
            rec.check("H_causality_no_lookahead", np.array_equal(np.vstack(prefix), traj[: tau + 1]), P, {"tau": tau})
            _, _ = consume(S0, th, Za, Aa, rec, P, f"L alternative stream tau={tau}", nonplastic)
        g2, traj2 = consume(S0, th, Z_int, A_int, rec, P, "I repeat", nonplastic, keep=True)
        h1 = hashlib.sha256(np.ascontiguousarray(traj).tobytes()).hexdigest()
        h2 = hashlib.sha256(np.ascontiguousarray(traj2).tobytes()).hexdigest()
        rec.check("I_determinism", np.array_equal(traj, traj2) and h1 == h2, P, "repeat run differs")
        A_zero_nonfast = A_int.copy()
        A_zero_nonfast[:, nonfast_cols] = 0
        g3, _ = consume(S0, th, Z_int, A_zero_nonfast, rec, P, "L zero non-fast", nonplastic)
        rec.check("L_m4b0_integration", np.array_equal(g3, g_base), P, "non-fast DAN channels changed gains")

        # J: permutation equivariance.
        nonplastic_perm = np.flatnonzero(S_perm.edge_comp < 0)
        gp, _ = consume(S_perm, th, Z_int[:, perm_kc], A_int[:, perm_dan], rec, P, "J permuted", nonplastic_perm)
        restored = np.empty_like(gp)
        restored[perm_edge] = gp
        rec.check("J_permutation_equivariance", np.array_equal(restored, g_base), P, "restored gains differ")

        if pt == REFERENCE_POINT:
            plastic_mask = S0.edge_comp >= 0
            diagnostics["integration_reference_point"] = {
                "trajectory_sha256": h1,
                "fraction_eligible_edges_changed": float(np.mean(g_base[plastic_mask] != 1.0)),
                "mean_gain_by_compartment": {c: float(np.mean(g_base[comp_edges[c]])) for c in ELIGIBLE_COMPARTMENTS},
            }

    crit_names = {
        "B_pairing_kernel_exact", "C_order_sign_rule", "D_coincidence_requirement", "E_compartment_locality",
        "F_nonplastic_invariance", "G_bounds", "G_saturation", "H_causality_no_lookahead", "I_determinism",
        "J_permutation_equivariance", "K_valence_agnostic_shared_rule", "L_m4b0_integration", "M_interface_firewall",
    }
    criteria = {"A_prerequisite_parity": True}
    for name in sorted(crit_names):
        c = rec.counts.get(name, {"checks": 0, "failures": 0})
        criteria[name] = c["checks"] > 0 and c["failures"] == 0
    passed = all(criteria.values())
    result = {
        "classification": (
            "PASS_M5C_DOPAMINE_GATED_KC_MBON_CHRONOLOGY_QUALIFIED" if passed else "FAIL_M5C_PLASTICITY_CHRONOLOGY"
        ),
        "reason": (
            "all frozen chronology criteria held at all 72 grid points"
            if passed else
            "prerequisites held but at least one frozen chronology criterion failed"
        ),
        "protocol_freeze_commit": PROTOCOL_FREEZE_COMMIT,
        "protocol_sha256": PROTOCOL_SHA,
        "prerequisite_parity": prereq,
        "structure_counts": counts,
        "grid": {k: list(v) for k, v in GRID.items()},
        "grid_points": len(points),
        "seed": SEED,
        "criteria": criteria,
        "check_counts": {k: rec.counts[k] for k in sorted(rec.counts)},
        "failure_records": rec.records,
        "diagnostics": {"eligible_edge_npz_file_sha256": edge_file_sha,
                        "eligible_edge_npz_file_sha256_matches_recorded": edge_file_sha == EDGE_FILE_SHA_DIAGNOSTIC,
                        **diagnostics},
        "input_manifest": INPUT_MANIFEST,
        "declared_limitations": [
            "hemisphere-pooled gate populations (M5B3B not side-resolved)",
            "single shared rule across compartments",
            "abstract discrete time steps",
            "aggregate KC->MBON body-pair plasticity",
            "synthetic binary DAN activity; no DAN dynamics, feedback or valence",
        ],
        "guardrails": {
            "parameter_values_selected": False,
            "reward_valence_assigned": False,
            "mbon_readout_defined": False,
            "synapse_coordinates_opened": False,
            "multi_compartment_mbon_edges_plastic": False,
            "market_reward_pnl_opened": False,
            "amin_numeric_opened": False,
            "m4v0_numeric_opened": False,
        },
    }
    write_result(result)
    print(f"runtime_seconds={time.time() - started:.1f}", file=sys.stderr)


def write_result(result):
    (O / "v6_m5c_plasticity_chronology_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result.get(k) for k in ("classification", "reason", "criteria", "check_counts", "structure_counts")},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
