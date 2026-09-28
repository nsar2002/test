from __future__ import annotations

import hashlib
import importlib.util
import inspect
import itertools
import json
import time
from pathlib import Path

import numpy as np
import pyarrow.feather as feather

W = Path("v6_m5b3b_work")  # pinned MaleCNS sources (shared with the M5B3B re-execution)
O = Path("v6_m5f0_out")

PROTOCOL_PATH = "research/v6_m5f0_dan_teaching_semantics_protocol.md"
PROTOCOL_FREEZE_COMMIT = "6f2de871b9ac9597a34cd2fa5075006fb632493e"
PROTOCOL_SHA = "771d730c7b28fbf7fb530d7907cd75e517518937ed7b42db5307a8d74a461738"
M5C_SCRIPT = "fly_mnq/v6_m5c_dopamine_gated_plasticity_chronology.py"
M5C_RESULT = "research/results/v6_m5c_plasticity_chronology_result.json"
M5D0_SCRIPT = "fly_mnq/v6_m5d0_mbon_readout_conditioning.py"
M5D0_RESULT = "research/results/v6_m5d0_mbon_readout_conditioning_result.json"
M5E0_SCRIPT = "fly_mnq/v6_m5e0_sensory_kc_encoder.py"
M5E0_RESULT = "research/results/v6_m5e0_encoder_result.json"
M5E0_WIRING = "research/results/v6_m5e0_wiring.npz"
M5D1B_RESULT = "research/results/v6_m5d1b_valence_extension_result.json"
M5D1C_RECORD = "research/v6_m5d1c_type_number_bridge_result.md"
FROZEN_FILES = {
    PROTOCOL_PATH: PROTOCOL_SHA,
    M5C_SCRIPT: "57ba0542338588f1d0b27a24a9e91affd12209b32d8328726dd8b85503ad96a4",
    M5C_RESULT: "77b9c79a70bfc589b43a53c61df253aa908dd9052a3e5a1032a3f1df7d455d5c",
    M5D0_SCRIPT: "fa40e79552488c6d47fe653ffc086d1f33f321c39e71d79c58bb25a19eac9f5c",
    M5D0_RESULT: "30063194b47253503b937ee9939e96dcfbfeb711001eccdad9d8000f2fa1b182",
    M5E0_SCRIPT: "35c3181380d9647a06a2fb0a47f6a1f924ee1f38531d90846090e20e82cf1a47",
    M5E0_RESULT: "a778a02d5efef468b4860a020d3985fbfb664fb1ae8e3758cea941807c0a451f",
    M5E0_WIRING: "e31c8e0ed9636c629e7088a053064bd399324b73aac298d6698aab3f84ecd31b",
    M5D1B_RESULT: "4ab95b21738fbeb61dbcebe4e647644c02b9d281c01d29ec4f78bb4a3cd38bad",
    M5D1C_RECORD: "364b5629ca4dcd85825b7118130c31d94c90fb9276047ae1542a644ff35ac201",
}
PASSES = {
    M5C_RESULT: "PASS_M5C_DOPAMINE_GATED_KC_MBON_CHRONOLOGY_QUALIFIED",
    M5D0_RESULT: "PASS_M5D0_MBON_READOUT_CONDITIONING_QUALIFIED",
    M5E0_RESULT: "PASS_M5E0_SENSORY_KC_ENCODER_QUALIFIED",
}
MBON_STATUS_EXPECTED = {"single_compartment": 55, "multi_compartment": 40, "outside_fast_lobe_map": 2}

APPETITIVE = ("PAM01", "PAM02", "PAM11")
AVERSIVE = ("PPL101", "PPL103", "PPL104", "PPL106")
APP_EXPECTED = ("B'2", "a1", "y5")
AV_EXPECTED = ("a'1", "a'3", "a3", "y2")
SEED = 20261001
T_BARS = 4000
HALF = 2000
N_FEATURES = 20
F_THRESHOLD = 0.0691
PHIS = (-0.3, 0.0, 0.3)
T_CAUSAL = 3000

PASS = "PASS_M5F0_TEACHING_SEMANTICS_QUALIFIED"
FAIL = "FAIL_M5F0_TEACHING_SEMANTICS"
BLOCKED = "BLOCKED_M5F0_PREREQUISITE_PARITY"

M5C = None
M5D0 = None


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


def digest(*arrays) -> str:
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(a)
        h.update(a.dtype.str.encode() + b"\0" + repr(a.shape).encode() + b"\0")
        h.update(a.tobytes())
    return h.hexdigest()


# ---------------------------------------------------------------- frozen teaching semantics and readout

class Teacher:
    """Frozen M5F0 teaching semantics: the sign of one outcome selects the signed DAN body set."""

    def __init__(self, dan_ids, dan_types):
        self.n = len(dan_ids)
        self.app = np.isin(np.asarray(dan_types), APPETITIVE)
        self.av = np.isin(np.asarray(dan_types), AVERSIVE)

    def dan_event(self, o):
        v = np.zeros(self.n, dtype=np.uint8)
        if o > 0:
            v[self.app] = 1
        elif o < 0:
            v[self.av] = 1
        return v


def score(structure, weights, gains, kc_event, naive, app_idx, av_idx):
    """Compartment-valence readout s = mean_AV R_m - mean_APP R_m, R_m = r_m(g, z) / r_m(1, z) for r_m(1, z) > 0."""
    r = M5D0.raw_drive(structure, weights, gains, kc_event)
    valid = naive > 0
    rel = np.zeros_like(r)
    rel[valid] = r[valid] / naive[valid]
    va, vp = valid[av_idx], valid[app_idx]
    if not va.any() or not vp.any():
        return 0.0, rel, False
    return float(rel[av_idx][va].mean() - rel[app_idx][vp].mean()), rel, True


def run_learner(structure, weights, theta, codes, teach, teacher, naive, app_idx, av_idx, track=False):
    """Two chronology steps per bar: I(t) (z(t), no DAN; read before write) and T(t) (z(t), D(o(t)))."""
    n_bars = len(codes)
    Z = np.repeat(codes, 2, axis=0)
    A = np.zeros((2 * n_bars, len(structure.dan_ids)), dtype=np.uint8)
    for t in range(n_bars):
        A[2 * t + 1] = teacher.dan_event(teach[t])
    s = np.zeros(n_bars)
    zero_steps = 0
    g_prev = np.ones(len(structure.edge_comp), dtype=np.float64)
    lo, hi, finite_nonneg = np.inf, -np.inf, True
    for step, g in enumerate(M5C.run_chronology(structure, theta, Z, A)):
        if step % 2 == 0:
            t = step // 2
            s[t], rel, ok = score(structure, weights, g_prev, codes[t], naive[t], app_idx, av_idx)
            zero_steps += 0 if ok else 1
            finite_nonneg &= bool(np.isfinite(rel).all() and (rel >= 0).all())
        if track:
            lo, hi = min(lo, float(g.min())), max(hi, float(g.max()))
        g_prev = g
    return {"s": s, "g": g_prev, "zero_steps": zero_steps, "g_min": lo, "g_max_seen": hi, "rel_ok": finite_nonneg}


def rho_os(s, o):
    a, b = s[HALF:], o[HALF:]
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


# ---------------------------------------------------------------- synthetic tasks

def synthetic_tasks():
    rng = np.random.Generator(np.random.PCG64(SEED))
    u = rng.standard_normal((T_BARS, N_FEATURES))
    eps = rng.standard_normal(T_BARS)
    o = u[:, 0] + 0.5 * eps
    perm = rng.permutation(T_BARS)
    tasks = {"PLANTED": {"u": u, "o": o, "teach": o}, "SHUFFLED": {"u": u, "o": o, "teach": o[perm]}}
    for phi in PHIS:
        r = np.zeros(T_BARS + 1)
        r[0] = rng.standard_normal()
        innov = rng.standard_normal(T_BARS)
        for t in range(1, T_BARS + 1):
            r[t] = phi * r[t - 1] + np.sqrt(1.0 - phi * phi) * innov[t - 1]
        noise = rng.standard_normal((T_BARS, N_FEATURES - 1))
        uu = np.column_stack([r[:T_BARS], noise])
        tasks[f"AR({phi:+.1f})"] = {"u": uu, "o": r[1:], "teach": r[1:]}
    return tasks


# ---------------------------------------------------------------- formal execution

def main():
    out = {}
    try:
        run(out)
    except Exception as exc:  # recorded, never silent
        finish(out, BLOCKED, f"execution error: {exc!r}")


def build(out):
    """Frozen prerequisite chain and learner structure (mirrors M5D0 exactly)."""
    global M5C, M5D0
    prereq = {f"sha256:{p}": Path(p).is_file() and sha256(p) == want for p, want in FROZEN_FILES.items()}
    out["prerequisites"] = prereq
    if not all(prereq.values()):
        return None
    for p, want in PASSES.items():
        prereq[f"pass:{p}"] = json.loads(Path(p).read_text(encoding="utf-8")).get("classification") == want
    M5C = load_module("v6_m5c_frozen", M5C_SCRIPT)
    M5D0 = load_module("v6_m5d0_frozen", M5D0_SCRIPT)
    for p, want in M5C.FROZEN_FILES.items():
        prereq[f"m5c_frozen_sha256:{p}"] = Path(p).is_file() and sha256(p) == want
    prereq["source_annotations_sha256"] = sha256(W / "body-annotations.feather") == M5C.ANN_SHA
    prereq["source_weights_sha256"] = sha256(W / "connectome-weights.feather") == M5C.WEIGHTS_SHA
    for p, want in M5C.M5B3B_RERUN_SHA.items():
        prereq[f"m5b3b_rerun_sha256:{p}"] = Path(p).is_file() and sha256(p) == want
    npz_ok = M5C.M5B3B_RERUN_EDGES.is_file()
    edges_npz = np.load(M5C.M5B3B_RERUN_EDGES) if npz_ok else None
    prereq["m5b3b_rerun_eligible_edge_content_digest"] = npz_ok and M5C.edge_content_digest(edges_npz) == M5C.EDGE_CONTENT_DIGEST
    counts_d1b = json.loads(Path(M5D1B_RESULT).read_text(encoding="utf-8"))["merged_label_counts"]["DAN"]
    prereq["dan_sign_counts_3_app_4_av"] = counts_d1b.get("APPETITIVE") == len(APPETITIVE) and counts_d1b.get("AVERSIVE") == len(AVERSIVE)
    if not all(prereq.values()):
        return None

    m4b0 = M5C.load_module("v6_m4b0_frozen", M5C.M4B0_SCRIPT)
    m5b3b = M5C.load_module("v6_m5b3b_frozen", M5C.M5B3B_SCRIPT)
    m5e0 = load_module("v6_m5e0_frozen", M5E0_SCRIPT)
    gate_pop = json.loads(M5C.M5B3B_RERUN_GATES.read_text(encoding="utf-8"))
    m5b3b_result = json.loads(M5C.M5B3B_RERUN_RESULT.read_text(encoding="utf-8"))
    ann = feather.read_table(W / "body-annotations.feather", columns=["bodyId", "class", "type", "somaSide"]).to_pandas()
    kc = ann[ann["class"] == "Kenyon_Cell"].sort_values("bodyId")
    dan = ann[ann["class"] == "DAN"].sort_values("bodyId")
    mbon = ann[ann["class"] == "MBON"].sort_values("bodyId")
    kc_ids = kc["bodyId"].to_numpy(dtype=np.int64)
    kc_sides = kc["somaSide"].astype(str).to_numpy()
    dan_ids = dan["bodyId"].to_numpy(dtype=np.int64)
    dan_types = dan["type"].map(m5b3b.norm).to_numpy()
    mbon_ids = mbon["bodyId"].to_numpy(dtype=np.int64)
    fast_set = set(int(b) for ids in gate_pop.values() for b in ids)
    typed_fast = set(int(b) for b, t in zip(dan["bodyId"], dan_types) if t in m5b3b.DAN_MAP)
    table = feather.read_table(W / "connectome-weights.feather", columns=["body_pre", "body_post", "weight"], memory_map=True)
    pre_parts, post_parts, w_parts = [], [], []
    for batch in table.to_batches(max_chunksize=4_000_000):
        p = batch.column(0).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        q = batch.column(1).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        wt = batch.column(2).to_numpy(zero_copy_only=False).astype(np.float64, copy=False)
        take = M5C.idx_in(kc_ids, p)[1] & M5C.idx_in(mbon_ids, q)[1]
        if take.any():
            pre_parts.append(p[take].copy())
            post_parts.append(q[take].copy())
            w_parts.append(wt[take].copy())
    edge_pre, edge_post, edge_w = (np.concatenate(x) for x in (pre_parts, post_parts, w_parts))
    eligible = {(int(a), int(b)): str(c) for a, b, c in zip(edges_npz["body_pre"], edges_npz["body_post"], edges_npz["compartment"])}
    edge_label = [eligible.get((int(a), int(b)), "") for a, b in zip(edge_pre, edge_post)]
    n_plastic = sum(1 for c in edge_label if c)
    per_body = {int(r["bodyId"]): r for r in m5b3b_result["mbon_mapping"]["per_body"]}
    status_counts = {}
    for r in per_body.values():
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    counts = {
        "KC": int(len(kc_ids)), "KC_L": int((kc_sides == "L").sum()), "KC_R": int((kc_sides == "R").sum()),
        "DAN": int(len(dan_ids)), "MBON": int(len(mbon_ids)), "FAST_DAN": int(len(fast_set)),
        "NONFAST_DAN": int(len(dan_ids) - len(fast_set)), "KC_MBON_EDGES": int(len(edge_pre)),
        "ELIGIBLE_EDGES": int(n_plastic), "NONPLASTIC_EDGES": int(len(edge_pre) - n_plastic),
        "GATE_COMPARTMENTS": int(len(gate_pop)),
    }
    type_of = dict(zip(dan["bodyId"].astype(np.int64).tolist(), dan_types.tolist()))
    app = tuple(sorted(c for c in M5C.ELIGIBLE_COMPARTMENTS if any(type_of.get(int(b)) in APPETITIVE for b in gate_pop.get(c, []))))
    av = tuple(sorted(c for c in M5C.ELIGIBLE_COMPARTMENTS if any(type_of.get(int(b)) in AVERSIVE for b in gate_pop.get(c, []))))
    prereq.update({
        "structure_counts_exact": counts == M5C.EXPECTED,
        "eligible_edges_all_found": n_plastic == len(eligible),
        "fast_dan_set_equals_frozen_type_rule": fast_set == typed_fast,
        "mbon_status_counts_exact": status_counts == MBON_STATUS_EXPECTED,
        "app_compartments_as_frozen": app == APP_EXPECTED,
        "av_compartments_as_frozen": av == AV_EXPECTED,
    })
    out["identity"] = {"counts": counts, "app_compartments": list(app), "av_compartments": list(av)}
    if not all(prereq.values()):
        return None

    S = M5C.build_structure(kc_ids, dan_ids, edge_pre, edge_post, edge_label, gate_pop)
    RW = M5D0.make_readout_weights(S, edge_w)
    mpos = {int(b): i for i, b in enumerate(RW.mbon_ids)}
    app_idx = np.array(sorted(mpos[b] for b, r in per_body.items() if r["status"] == "single_compartment" and r["compartments"][0] in app), dtype=np.int64)
    av_idx = np.array(sorted(mpos[b] for b, r in per_body.items() if r["status"] == "single_compartment" and r["compartments"][0] in av), dtype=np.int64)
    e_kc, e_sides, _, pn_ids, pn_types, pn_edges = m5e0.load_sources(W / "body-annotations.feather", W / "connectome-weights.feather")
    ranking = m5e0.channel_ranking(pn_types, pn_edges)
    wiring = np.load(M5E0_WIRING)
    m5e0_result = json.loads(Path(M5E0_RESULT).read_text(encoding="utf-8"))
    rewired = {"p": pn_edges["p"], "k": wiring["k_rewired"].astype(np.int64), "w": pn_edges["w"]}
    prereq["m5e0_wiring_content_digest"] = m5e0.digest(pn_ids, e_kc, pn_edges["p"], pn_edges["k"], pn_edges["w"], wiring["k_rewired"]) == m5e0_result["wiring_file"]["content_digest"]
    prereq["encoder_kc_order_equals_structure"] = bool(np.array_equal(e_kc, kc_ids))
    if not all(prereq.values()):
        return None
    encoders = {"connectome": m5e0.Encoder(e_kc, e_sides, pn_types, ranking, pn_edges, m4b0.sparsify),
                "rewired": m5e0.Encoder(e_kc, e_sides, pn_types, ranking, rewired, m4b0.sparsify)}
    teacher = Teacher(dan_ids, dan_types)
    return {"S": S, "RW": RW, "app_idx": app_idx, "av_idx": av_idx, "encoders": encoders, "teacher": teacher,
            "dan_ids": dan_ids, "dan_types": dan_types, "per_body": per_body, "mpos": mpos}


def theta_of(pt):
    return M5C.Theta(pt["eta_minus"], pt["eta_plus"], pt["lam_K"], pt["lam_D"], pt["g_max"])


def prepare(world, arm, task):
    codes = world["encoders"][arm].encode(task["u"])[0]
    ones = np.ones(len(world["S"].edge_comp), dtype=np.float64)
    naive = np.stack([M5D0.raw_drive(world["S"], world["RW"], ones, codes[t]) for t in range(len(codes))])
    return codes, naive


def run(out):
    O.mkdir(exist_ok=True)
    out.update({"protocol": {"path": PROTOCOL_PATH, "sha256": PROTOCOL_SHA, "freeze_commit": PROTOCOL_FREEZE_COMMIT},
                "seed": SEED, "t_bars": T_BARS, "f_threshold": F_THRESHOLD})
    t0 = time.time()
    world = build(out)
    if world is None:
        return finish(out, BLOCKED, "prerequisite parity failed")
    S, RW, teacher = world["S"], world["RW"], world["teacher"]
    app_idx, av_idx = world["app_idx"], world["av_idx"]
    out["identity"].update({"app_mbons": int(len(app_idx)), "av_mbons": int(len(av_idx)),
                            "appetitive_dan_bodies": int(teacher.app.sum()), "aversive_dan_bodies": int(teacher.av.sum())})
    crit = {"A_prerequisites": True}

    rng = np.random.Generator(np.random.PCG64(SEED + 1))
    outs = rng.standard_normal(1000)
    outs[rng.choice(1000, size=100, replace=False)] = 0.0
    sem_ok = True
    for o in outs:
        v = teacher.dan_event(float(o))
        want = teacher.app if o > 0 else (teacher.av if o < 0 else np.zeros_like(teacher.app))
        sem_ok &= bool(np.array_equal(v.astype(bool), want) and v.dtype == np.uint8)
    crit["B_teaching_semantics_exact"] = sem_ok and not teacher.dan_event(0.0).any()

    tasks = synthetic_tasks()
    ref = theta_of(M5C.REFERENCE_POINT)
    prepared = {("connectome", name): prepare(world, "connectome", task) for name, task in tasks.items() if name != "SHUFFLED"}
    prepared[("connectome", "SHUFFLED")] = prepared[("connectome", "PLANTED")]
    prepared[("rewired", "PLANTED")] = prepare(world, "rewired", tasks["PLANTED"])

    def go(arm, name, theta, teach=None, codes=None, naive=None, track=False):
        c, n = prepared[(arm, name)]
        return run_learner(S, RW, theta, c if codes is None else codes, tasks[name]["teach"] if teach is None else teach,
                           teacher, n if naive is None else naive, app_idx, av_idx, track=track)

    base = go("connectome", "PLANTED", ref, track=True)
    again = go("connectome", "PLANTED", ref)
    crit["D_determinism"] = bool(np.array_equal(base["s"], again["s"]) and np.array_equal(base["g"], again["g"]))
    rngc = np.random.Generator(np.random.PCG64(SEED + 2))
    u_pert = tasks["PLANTED"]["u"].copy()
    u_pert[T_CAUSAL:] = rngc.standard_normal(u_pert[T_CAUSAL:].shape)
    teach_pert = tasks["PLANTED"]["teach"].copy()
    teach_pert[T_CAUSAL:] = rngc.standard_normal(T_BARS - T_CAUSAL)
    codes_pert = world["encoders"]["connectome"].encode(u_pert)[0]
    ones = np.ones(len(S.edge_comp), dtype=np.float64)
    naive_pert = prepared[("connectome", "PLANTED")][1].copy()
    for t in range(T_CAUSAL, T_BARS):
        naive_pert[t] = M5D0.raw_drive(S, RW, ones, codes_pert[t])
    both = go("connectome", "PLANTED", ref, teach=teach_pert, codes=codes_pert, naive=naive_pert)
    only_o = go("connectome", "PLANTED", ref, teach=teach_pert)
    crit["C_causality"] = bool(np.array_equal(both["s"][:T_CAUSAL], base["s"][:T_CAUSAL])
                               and np.array_equal(only_o["s"][:T_CAUSAL + 1], base["s"][:T_CAUSAL + 1]))
    planted_ref = rho_os(base["s"], tasks["PLANTED"]["o"])
    shuffled = go("connectome", "SHUFFLED", ref)
    shuffled_ref = rho_os(shuffled["s"], tasks["SHUFFLED"]["o"])
    crit["F_learning_planted_rule"] = planted_ref > F_THRESHOLD
    crit["G_shuffled_teaching_control"] = abs(shuffled_ref) <= F_THRESHOLD
    params = lambda f: list(inspect.signature(f).parameters)  # noqa: E731
    crit["H_interface_firewall"] = (params(M5C.run_chronology) == ["structure", "theta", "kc_events", "dan_events"]
                                    and params(Teacher.dan_event) == ["self", "o"]
                                    and not any("o" == p or "outcome" in p for p in params(score)))

    grid = [dict(zip(M5C.GRID, v)) for v in itertools.product(*M5C.GRID.values())]
    bounds_ok = base["g_min"] >= 0.0 and base["g_max_seen"] <= ref.g_max and base["rel_ok"]
    diag_grid = {"PLANTED:connectome": [], "PLANTED:rewired": [], **{f"{n}:connectome": [] for n in tasks if n.startswith("AR(")}}
    for pt in grid:
        th = theta_of(pt)
        key = {k: pt[k] for k in M5C.GRID}
        for arm in ("connectome", "rewired"):
            r = go(arm, "PLANTED", th, track=True)
            bounds_ok &= r["g_min"] >= 0.0 and r["g_max_seen"] <= th.g_max and r["rel_ok"]
            diag_grid[f"PLANTED:{arm}"].append({**key, "rho_os": rho_os(r["s"], tasks["PLANTED"]["o"]), "zero_steps": r["zero_steps"]})
        for name in tasks:
            if name.startswith("AR("):
                r = go("connectome", name, th, track=True)
                bounds_ok &= r["g_min"] >= 0.0 and r["g_max_seen"] <= th.g_max and r["rel_ok"]
                diag_grid[f"{name}:connectome"].append({**key, "rho_os": rho_os(r["s"], tasks[name]["o"]), "zero_steps": r["zero_steps"]})
    crit["E_bounds"] = bool(bounds_ok)
    ordered = ["A_prerequisites", "B_teaching_semantics_exact", "C_causality", "D_determinism", "E_bounds",
               "F_learning_planted_rule", "G_shuffled_teaching_control", "H_interface_firewall"]
    crit = {k: bool(crit[k]) for k in ordered}
    plastic = S.edge_comp >= 0
    gp = base["g"][plastic]
    ar_ref = {}
    for name in tasks:
        if name.startswith("AR("):
            r = go("connectome", name, ref)
            ar_ref[name] = rho_os(r["s"], tasks[name]["o"])
    out.update({
        "criteria": crit,
        "reference": {"theta": M5C.REFERENCE_POINT, "planted_rho_os": planted_ref, "shuffled_rho_os": shuffled_ref,
                      "planted_zero_steps": base["zero_steps"], "ar_rho_os": ar_ref,
                      "final_gain_fractions": {"at_0": float((gp == 0).mean()), "at_gmax": float((gp == ref.g_max).mean()),
                                               "within_1pm0.01": float((np.abs(gp - 1.0) <= 0.01).mean())}},
        "diagnostics": {"grid": diag_grid},
        "digests": {"s_planted_ref": digest(base["s"]), "g_planted_ref": digest(base["g"])},
    })
    print("elapsed", round(time.time() - t0, 1), "s", flush=True)
    if all(crit.values()):
        return finish(out, PASS, "all frozen teaching-semantics criteria passed")
    return finish(out, FAIL, "failed: " + ", ".join(k for k, v in crit.items() if not v))


def finish(out, classification, reason):
    out.update({"classification": classification, "reason": reason})
    O.mkdir(exist_ok=True)
    (O / "v6_m5f0_teaching_result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out.get(k) for k in ("classification", "reason", "criteria", "reference", "identity")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
