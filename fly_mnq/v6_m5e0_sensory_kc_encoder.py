from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.feather as feather
import scipy.sparse as sp

W_DIR = Path("v6_m5b3b_work")  # pinned body annotations and connectome weights (shared convention)
O = Path("v6_m5e0_out")

PROTOCOL_PATH = "research/v6_m5e0_sensory_kc_encoder_protocol.md"
PROTOCOL_FREEZE_COMMIT = "ce8543e9add81f6114b2a0d42230e58dc1fd9a34"
PROTOCOL_SHA = "037704788249ac288324524ff2da426b59f6ad057c069fdd3e3ae7a49f32eb79"
M4B0_SCRIPT = "fly_mnq/v6_m4b0_functional_apl_sparsifier.py"
M4B0_SHA = "5927c88dbcbee6ae291d7d2c2dc70893e2c3c3f48ba1a28cb7c79eb1a328bac5"
ANN_SHA = "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
WEIGHTS_SHA = "e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1"

EXPECTED = {"KC": 4064, "KC_L": 2019, "KC_R": 2045, "PN_BODIES": 314, "PN_TYPES": 88, "PN_KC_EDGES": 22586,
            "PN_KC_SYNAPSES": 390928, "K_L": 202, "K_R": 205}
SCALE = 2 ** 20
CLIP = 3.0
F_MAX = 44
SHUFFLE_SEED = 20260929
SWAP_FACTOR = 10
STREAM_SEED = 20260930
T_STREAM = 2000
RETAIN_FACTOR = 1.25

PASS = "PASS_M5E0_SENSORY_KC_ENCODER_QUALIFIED"
FAIL = "FAIL_M5E0_SENSORY_KC_ENCODER"
BLOCKED = "BLOCKED_M5E0_PREREQUISITE_PARITY"


def sha256_file(path) -> str:
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


# ---------------------------------------------------------------- sources

def load_sources(ann_path, weights_path):
    ann = feather.read_table(ann_path, columns=["bodyId", "class", "type", "somaSide"]).to_pandas()
    kc = ann[ann["class"] == "Kenyon_Cell"].sort_values("bodyId")
    kc_ids = kc["bodyId"].to_numpy(np.int64)
    kc_sides = kc["somaSide"].astype(str).to_numpy()
    kc_type = kc["type"].astype(str).to_numpy()
    alpn = ann[ann["class"] == "ALPN"]
    alpn_ids = np.sort(alpn["bodyId"].to_numpy(np.int64))
    table = feather.read_table(weights_path, columns=["body_pre", "body_post", "weight"], memory_map=True)
    parts = ([], [], [])
    for batch in table.to_batches(max_chunksize=4_000_000):
        pre = batch.column(0).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        post = batch.column(1).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        take = np.isin(pre, alpn_ids) & np.isin(post, kc_ids)
        if take.any():
            parts[0].append(pre[take].copy())
            parts[1].append(post[take].copy())
            parts[2].append(batch.column(2).to_numpy(zero_copy_only=False)[take].astype(np.int64))
    pre, post, w = (np.concatenate(p) for p in parts)
    order = np.lexsort((post, pre))
    pre, post, w = pre[order], post[order], w[order]
    pn_ids = np.unique(pre)
    pn_type = dict(zip(alpn["bodyId"].astype(np.int64).tolist(), alpn["type"].astype(str).tolist()))
    edges = {"p": np.searchsorted(pn_ids, pre).astype(np.int64), "k": np.searchsorted(kc_ids, post).astype(np.int64),
             "w": w.astype(np.int64)}
    return kc_ids, kc_sides, kc_type, pn_ids, np.array([pn_type[int(b)] for b in pn_ids]), edges


def channel_ranking(pn_types, edges):
    syn = pd.Series(edges["w"]).groupby(pn_types[edges["p"]]).sum()
    ranked = sorted(syn.index.tolist(), key=lambda t: (-int(syn[t]), t))
    return ranked


# ---------------------------------------------------------------- encoder

class Encoder:
    """Frozen M5E0 encoder: ON/OFF PN channels -> exact int64 KC drive -> frozen M4B0 top-k sparsifier."""

    def __init__(self, kc_ids, kc_sides, pn_types, ranking, edges, sparsify):
        self.kc_ids, self.kc_sides, self.sparsify = kc_ids, kc_sides, sparsify
        self.n_pn, self.n_kc = len(pn_types), len(kc_ids)
        self.wt = sp.csr_matrix((edges["w"], (edges["k"], edges["p"])), shape=(self.n_kc, self.n_pn), dtype=np.int64)
        self.w_dense = np.zeros((self.n_pn, self.n_kc), dtype=np.float64)
        np.add.at(self.w_dense, (edges["p"], edges["k"]), edges["w"].astype(np.float64))
        self.channel_pns = [np.flatnonzero(pn_types == t) for t in ranking]

    def activities(self, u):
        u = np.asarray(u, dtype=np.float64)
        if u.ndim != 2 or not (1 <= u.shape[1] <= F_MAX):
            raise ValueError(f"feature matrix must be (T, F) with 1 <= F <= {F_MAX}")
        if not np.isfinite(u).all():
            raise ValueError("features must be finite")
        a = np.zeros((u.shape[0], self.n_pn), dtype=np.int64)
        for j in range(u.shape[1]):
            on = np.rint(np.clip(u[:, j], 0.0, CLIP) * SCALE).astype(np.int64)
            off = np.rint(np.clip(-u[:, j], 0.0, CLIP) * SCALE).astype(np.int64)
            a[:, self.channel_pns[2 * j]] = on[:, None]
            a[:, self.channel_pns[2 * j + 1]] = off[:, None]
        return a

    def drive(self, a_q):
        return np.asarray((self.wt @ a_q.T).T, dtype=np.int64)

    def encode(self, u):
        a_q = self.activities(u)
        s = self.drive(a_q)
        return self.sparsify(self.kc_ids, self.kc_sides, s.astype(np.float64)), s, a_q


# ---------------------------------------------------------------- wiring control

def rewire(edges, seed=SHUFFLE_SEED, factor=SWAP_FACTOR):
    """Degree-preserving bipartite double-edge swaps; each edge's weight travels with its PN."""
    p, k, w = edges["p"].copy(), edges["k"].copy(), edges["w"].copy()
    n = len(p)
    present = set(zip(p.tolist(), k.tolist()))
    rng = np.random.Generator(np.random.PCG64(seed))
    draws = rng.integers(0, n, size=(factor * n, 2), dtype=np.int64)
    accepted = 0
    for i, j in draws.tolist():
        p1, k1, p2, k2 = int(p[i]), int(k[i]), int(p[j]), int(k[j])
        if p1 == p2 or k1 == k2 or (p1, k2) in present or (p2, k1) in present:
            continue
        present.discard((p1, k1))
        present.discard((p2, k2))
        present.add((p1, k2))
        present.add((p2, k1))
        k[i], k[j] = k2, k1
        accepted += 1
    return {"p": p, "k": k, "w": w}, accepted


def expected_retention(edges):
    dp = np.bincount(edges["p"])
    dk = np.bincount(edges["k"])
    e = len(edges["p"])
    return float((dp[edges["p"]].astype(np.float64) * dk[edges["k"]]).sum() / e / e)


def wiring_checks(orig, shuf):
    n_pn = int(max(orig["p"].max(), shuf["p"].max())) + 1
    n_kc = int(max(orig["k"].max(), shuf["k"].max())) + 1
    same_pn_deg = np.array_equal(np.bincount(orig["p"], minlength=n_pn), np.bincount(shuf["p"], minlength=n_pn))
    same_kc_deg = np.array_equal(np.bincount(orig["k"], minlength=n_kc), np.bincount(shuf["k"], minlength=n_kc))
    wo = pd.DataFrame({"p": orig["p"], "w": orig["w"]}).sort_values(["p", "w"], kind="mergesort")
    ws = pd.DataFrame({"p": shuf["p"], "w": shuf["w"]}).sort_values(["p", "w"], kind="mergesort")
    same_weights = bool(np.array_equal(wo.to_numpy(), ws.to_numpy()))
    pairs = shuf["p"] * n_kc + shuf["k"]
    no_dup = len(np.unique(pairs)) == len(pairs)
    retained = float(np.isin(pairs, orig["p"] * n_kc + orig["k"]).mean())
    return {"pn_out_degree_preserved": bool(same_pn_deg), "kc_in_degree_preserved": bool(same_kc_deg),
            "pn_out_weight_multisets_preserved": same_weights, "no_duplicate_edges": bool(no_dup),
            "retained_fraction": retained}


# ---------------------------------------------------------------- synthetic streams

def synthetic_streams():
    rng = np.random.Generator(np.random.PCG64(STREAM_SEED))
    iid20 = rng.standard_normal((T_STREAM, 20))
    common = rng.standard_normal((T_STREAM, 1))
    idio = rng.standard_normal((T_STREAM, 20))
    corr20 = np.sqrt(0.8) * common + np.sqrt(0.2) * idio
    iid44 = rng.standard_normal((T_STREAM, 44))
    zero20 = np.zeros((T_STREAM, 20))
    imp = np.zeros((40, 20))
    for j in range(20):
        imp[2 * j, j] = 3.0
        imp[2 * j + 1, j] = -3.0
    return {"iid20": iid20, "corr20": corr20, "iid44": iid44, "zero20": zero20, "impulse20": imp}


# ---------------------------------------------------------------- formal execution

def build(ann_path, weights_path, sparsify):
    kc_ids, kc_sides, kc_type, pn_ids, pn_types, edges = load_sources(ann_path, weights_path)
    ranking = channel_ranking(pn_types, edges)
    shuffled, accepted = rewire(edges)
    enc = Encoder(kc_ids, kc_sides, pn_types, ranking, edges, sparsify)
    enc_s = Encoder(kc_ids, kc_sides, pn_types, ranking, shuffled, sparsify)
    return {"kc_ids": kc_ids, "kc_sides": kc_sides, "kc_type": kc_type, "pn_ids": pn_ids, "pn_types": pn_types,
            "edges": edges, "ranking": ranking, "shuffled": shuffled, "accepted": accepted, "enc": enc, "enc_s": enc_s}


def encode_all(world, streams):
    out = {}
    for arm, enc in (("connectome", world["enc"]), ("rewired", world["enc_s"])):
        for name, u in streams.items():
            z, s, a_q = enc.encode(u)
            out[(arm, name)] = {"z": z, "s": s, "a_q": a_q}
    return out


def kc_class(t):
    return "gamma" if t.startswith("KCg") else ("alpha_prime_beta_prime" if t.startswith("KCa'b'") else ("alpha_beta" if t.startswith("KCab") else "other"))


def chi_square(table):
    table = np.asarray(table, dtype=np.float64)
    table = table[table.sum(axis=1) > 0][:, table.sum(axis=0) > 0]
    exp = table.sum(axis=1, keepdims=True) * table.sum(axis=0, keepdims=True) / table.sum()
    return float(((table - exp) ** 2 / exp).sum())


def main():
    out = {}
    try:
        run(out)
    except Exception as exc:  # recorded, never silent
        finish(out, BLOCKED, f"execution error: {exc!r}")


def run(out):
    O.mkdir(exist_ok=True)
    ann_path, w_path = W_DIR / "body-annotations.feather", W_DIR / "connectome-weights.feather"
    prereq = {
        "protocol_sha256": Path(PROTOCOL_PATH).is_file() and sha256_file(PROTOCOL_PATH) == PROTOCOL_SHA,
        "m4b0_sha256": Path(M4B0_SCRIPT).is_file() and sha256_file(M4B0_SCRIPT) == M4B0_SHA,
        "annotations_sha256": ann_path.is_file() and sha256_file(ann_path) == ANN_SHA,
        "weights_sha256": w_path.is_file() and sha256_file(w_path) == WEIGHTS_SHA,
    }
    out.update({"protocol": {"path": PROTOCOL_PATH, "sha256": PROTOCOL_SHA, "freeze_commit": PROTOCOL_FREEZE_COMMIT}})
    if not all(prereq.values()):
        out["prerequisites"] = prereq
        return finish(out, BLOCKED, "pinned file hash mismatch")
    m4b0 = load_module("v6_m4b0_frozen", M4B0_SCRIPT)
    world = build(ann_path, w_path, m4b0.sparsify)
    e = world["edges"]
    anchors = {
        "KC": int(len(world["kc_ids"])), "KC_L": int((world["kc_sides"] == "L").sum()), "KC_R": int((world["kc_sides"] == "R").sum()),
        "PN_BODIES": int(len(world["pn_ids"])), "PN_TYPES": int(len(world["ranking"])), "PN_KC_EDGES": int(len(e["p"])),
        "PN_KC_SYNAPSES": int(e["w"].sum()),
    }
    prereq["identity_anchors_exact"] = all(anchors[k] == EXPECTED[k] for k in anchors)
    prereq["kc_sides_exact_LR"] = bool(np.isin(world["kc_sides"], ["L", "R"]).all())
    out.update({"prerequisites": prereq, "identity": anchors})
    if not all(prereq.values()):
        return finish(out, BLOCKED, "identity anchors or KC sides failed")

    streams = synthetic_streams()
    res = encode_all(world, streams)
    left = world["kc_sides"] == "L"
    crit = {}
    crit["B_exact_arithmetic"] = all(
        np.array_equal(r["s"].astype(np.float64), r["a_q"].astype(np.float64) @ (world["enc"] if arm == "connectome" else world["enc_s"]).w_dense)
        for (arm, _), r in res.items())
    crit["C_exact_sparsity"] = all(
        bool((r["z"][:, left].sum(axis=1) == EXPECTED["K_L"]).all() and (r["z"][:, ~left].sum(axis=1) == EXPECTED["K_R"]).all())
        for r in res.values())
    u = streams["iid20"]
    rng = np.random.Generator(np.random.PCG64(STREAM_SEED + 1))
    u_a = u.copy()
    u_a[1000:] = rng.standard_normal(u_a[1000:].shape)
    u_b = u.copy()
    u_b[:1000] = rng.standard_normal(u_b[:1000].shape)
    z0 = res[("connectome", "iid20")]["z"]
    za, zb = world["enc"].encode(u_a)[0], world["enc"].encode(u_b)[0]
    crit["D_memoryless"] = bool(np.array_equal(za[:1000], z0[:1000]) and np.array_equal(zb[1000:], z0[1000:]))
    raised = []
    for bad in (np.zeros((3, 0)), np.zeros((3, 45)), np.array([[np.nan] * 5]), np.array([[np.inf] * 5])):
        try:
            world["enc"].activities(bad)
            raised.append(False)
        except ValueError:
            raised.append(True)
    ranking2 = channel_ranking(world["pn_types"], e)
    types44 = {world["ranking"][c] for c in range(2 * F_MAX)}
    crit["E_channel_map"] = bool(ranking2 == world["ranking"] and len(types44) == 2 * F_MAX and all(raised))
    wc = wiring_checks(e, world["shuffled"])
    r0 = expected_retention(e)
    shuffled2, _ = rewire(e)
    wc.update({"expected_retention_R0": r0, "retention_bound": RETAIN_FACTOR * r0, "accepted_swaps": int(world["accepted"]),
               "attempted_swaps": int(SWAP_FACTOR * len(e["p"])),
               "regeneration_identical": bool(all(np.array_equal(world["shuffled"][x], shuffled2[x]) for x in ("p", "k", "w")))})
    crit["F_wiring_control"] = bool(wc["pn_out_degree_preserved"] and wc["kc_in_degree_preserved"]
                                    and wc["pn_out_weight_multisets_preserved"] and wc["no_duplicate_edges"]
                                    and wc["retained_fraction"] <= wc["retention_bound"] and wc["regeneration_identical"])
    digests = {
        "W": digest(e["p"], e["k"], e["w"]), "W_rewired": digest(world["shuffled"]["p"], world["shuffled"]["k"], world["shuffled"]["w"]),
        **{f"z:{arm}:{name}": digest(r["z"]) for (arm, name), r in res.items()},
    }
    world2 = build(ann_path, w_path, m4b0.sparsify)
    res2 = encode_all(world2, synthetic_streams())
    digests2 = {
        "W": digest(world2["edges"]["p"], world2["edges"]["k"], world2["edges"]["w"]),
        "W_rewired": digest(world2["shuffled"]["p"], world2["shuffled"]["k"], world2["shuffled"]["w"]),
        **{f"z:{arm}:{name}": digest(r["z"]) for (arm, name), r in res2.items()},
    }
    crit["G_determinism"] = digests == digests2
    crit = {"A_prerequisite_parity": True, **crit}
    out.update({"criteria": crit, "wiring_control": wc, "digests": digests,
                "channel_ranking": world["ranking"]})
    out["diagnostics"] = diagnostics(world, res)
    np.savez_compressed(O / "v6_m5e0_wiring.npz", pn_ids=world["pn_ids"], pn_types=world["pn_types"].astype("U32"),
                        kc_ids=world["kc_ids"], ranking=np.array(world["ranking"], dtype="U32"),
                        p=e["p"], k=e["k"], w=e["w"], k_rewired=world["shuffled"]["k"])
    out["wiring_file"] = {"file": "v6_m5e0_wiring.npz", "content_digest": digest(world["pn_ids"], world["kc_ids"], e["p"], e["k"], e["w"],
                                                                                   world["shuffled"]["k"])}
    if all(crit.values()):
        return finish(out, PASS, "all frozen encoder criteria passed")
    return finish(out, FAIL, "failed: " + ", ".join(k for k, v in crit.items() if not v))


def diagnostics(world, res):
    d = {}
    e = world["edges"]
    pt = world["pn_types"]
    table = []
    for r, t in enumerate(world["ranking"]):
        sel = pt[e["p"]] == t
        table.append({"rank": r, "type": t, "bodies": int((pt == t).sum()), "edges": int(sel.sum()),
                      "synapses": int(e["w"][sel].sum()), "kcs_reached": int(len(np.unique(e["k"][sel])))})
    d["channel_table"] = table
    left = world["kc_sides"] == "L"
    cls = np.array([kc_class(t) for t in world["kc_type"]])
    per = {}
    for (arm, name), r in res.items():
        z, s = r["z"].astype(bool), r["s"]
        zero_in_code = ((s == 0) & z)
        comp = {c: float(z[:, cls == c].sum() / z.sum()) for c in ("gamma", "alpha_beta", "alpha_prime_beta_prime", "other")}
        per[f"{arm}:{name}"] = {
            "mean_positive_drive_kcs_L": float((s[:, left] > 0).sum(axis=1).mean()),
            "mean_positive_drive_kcs_R": float((s[:, ~left] > 0).sum(axis=1).mean()),
            "steps_with_zero_drive_kc_in_code": float(zero_in_code.any(axis=1).mean()),
            "code_class_composition": comp,
        }
    d["per_stream"] = per
    rng = np.random.Generator(np.random.PCG64(STREAM_SEED + 2))
    pairs = rng.integers(0, T_STREAM, size=(2000, 2))
    pairs = pairs[pairs[:, 0] != pairs[:, 1]]
    streams = synthetic_streams()
    dec = {}
    for name in ("iid20", "corr20"):
        u = streams[name]
        z = res[("connectome", name)]["z"].astype(bool)
        cos = np.array([float(u[i] @ u[j] / np.sqrt((u[i] @ u[i]) * (u[j] @ u[j]))) for i, j in pairs])
        ov = np.array([(z[i] & z[j]).sum() / z[i].sum() for i, j in pairs])
        dec[name] = {"mean_input_cosine": float(cos.mean()), "mean_abs_input_cosine": float(np.abs(cos).mean()),
                     "mean_code_overlap": float(ov.mean()),
                     "code_overlap_vs_input_cosine_correlation": float(np.corrcoef(cos, ov)[0, 1]),
                     "mean_code_overlap_input_cosine_gt_0.5": float(ov[cos > 0.5].mean()) if (cos > 0.5).any() else None,
                     "mean_code_overlap_input_cosine_lt_-0.5": float(ov[cos < -0.5].mean()) if (cos < -0.5).any() else None}
    d["decorrelation"] = dec
    kcls = cls[e["k"]]
    classes = ("gamma", "alpha_beta", "alpha_prime_beta_prime", "other")
    def contingency(k_idx):
        c = cls[k_idx]
        return np.array([[int(((pt[e["p"]] == t) & (c == q)).sum()) for q in classes] for t in world["ranking"]])
    d["pn_type_by_kc_class_chi_square"] = {"connectome": chi_square(contingency(e["k"])),
                                           "rewired": chi_square(contingency(world["shuffled"]["k"]))}
    za = res[("connectome", "iid20")]["z"].astype(bool)
    zb = res[("rewired", "iid20")]["z"].astype(bool)
    d["connectome_vs_rewired_code_overlap_iid20"] = float(((za & zb).sum(axis=1) / za.sum(axis=1)).mean())
    return d


def finish(out, classification, reason):
    out.update({"classification": classification, "reason": reason})
    O.mkdir(exist_ok=True)
    (O / "v6_m5e0_encoder_result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out.get(k) for k in ("classification", "reason", "criteria", "identity", "wiring_control")},
                     indent=2, sort_keys=True))
    dg = out.get("diagnostics") or {}
    for k in ("decorrelation", "pn_type_by_kc_class_chi_square", "connectome_vs_rewired_code_overlap_iid20"):
        if k in dg:
            print(k, dg[k])


if __name__ == "__main__":
    main()
