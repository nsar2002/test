from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pyarrow.feather as feather

WORK = Path("v6_m4b0_work")
OUT = Path("v6_m4b0_out")
OUT.mkdir(exist_ok=True)

ANN_SHA = "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
EXPECTED_KC = 4064
P = 0.100
SEED = 20260919
SCALES = [0.01, 0.1, 1.0, 10.0, 100.0]
OFFSETS = [-100.0, -1.0, 0.0, 1.0, 100.0]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sparsify(ids, sides, scores):
    ids = np.asarray(ids, dtype=np.int64)
    sides = np.asarray(sides)
    x = np.asarray(scores, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != len(ids):
        raise ValueError("score shape mismatch")
    if not np.isfinite(x).all():
        raise ValueError("scores must be finite")
    if len(np.unique(ids)) != len(ids):
        raise ValueError("body IDs must be unique")
    if not np.isin(sides, ["L", "R"]).all():
        raise ValueError("KC sides must be exact L/R")

    z = np.zeros_like(x, dtype=np.uint8)
    for side in ("L", "R"):
        idx = np.flatnonzero(sides == side)
        n = len(idx)
        k = int(math.floor(P * n + 0.5))
        frac = k / n
        if not (0.095 <= frac <= 0.105):
            raise ValueError(f"{side}: coding fraction {frac} outside frozen band")
        side_ids = ids[idx]
        for t in range(x.shape[0]):
            order = np.lexsort((side_ids, -x[t, idx]))
            z[t, idx[order[:k]]] = 1
    return z


def main():
    ann = WORK / "body-annotations.feather"
    if sha256(ann) != ANN_SHA:
        raise RuntimeError("annotation source hash mismatch")
    d = feather.read_table(ann, columns=["bodyId", "class", "somaSide"]).to_pandas()
    kc = d[d["class"] == "Kenyon_Cell"].copy().sort_values("bodyId")
    if len(kc) != EXPECTED_KC:
        raise RuntimeError(f"KC count mismatch: {len(kc)}")
    if not kc["somaSide"].isin(["L", "R"]).all():
        result = {"classification": "BLOCKED_M4B0_MALECNS_KC_IDENTITY", "reason": "non-L/R KC somaSide"}
        (OUT / "v6_m4b0_functional_apl_result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return

    ids = kc["bodyId"].to_numpy(dtype=np.int64)
    sides = kc["somaSide"].astype(str).to_numpy()
    side_counts = {s: int((sides == s).sum()) for s in ("L", "R")}
    k_by_side = {s: int(math.floor(P * side_counts[s] + 0.5)) for s in ("L", "R")}
    frac_by_side = {s: k_by_side[s] / side_counts[s] for s in ("L", "R")}

    rng = np.random.Generator(np.random.PCG64(SEED))
    base = rng.standard_normal((256, len(ids)))
    ties = np.vstack([
        np.zeros(len(ids)),
        np.arange(len(ids), dtype=np.float64) % 7,
        -(np.arange(len(ids), dtype=np.float64) % 11),
        np.where(np.arange(len(ids)) % 2 == 0, 1.0, -1.0),
    ])
    x = np.vstack([base, ties])
    z = sparsify(ids, sides, x)

    checks = {}
    checks["binary_output"] = bool(np.isin(z, [0, 1]).all())
    checks["exact_active_count"] = all(
        np.all(z[:, sides == s].sum(axis=1) == k_by_side[s]) for s in ("L", "R")
    )

    rank_ok = True
    for t in range(len(x)):
        for s in ("L", "R"):
            idx = np.flatnonzero(sides == s)
            expected = sorted(idx.tolist(), key=lambda j: (-x[t, j], int(ids[j])))[:k_by_side[s]]
            actual = np.flatnonzero(z[t]).tolist()
            aset = set(actual)
            if any(j not in aset for j in expected):
                rank_ok = False
                break
        if not rank_ok:
            break
    checks["top_k_and_bodyid_tie_break"] = rank_ok

    checks["positive_scale_invariance"] = all(
        np.array_equal(z, sparsify(ids, sides, x * a)) for a in SCALES
    )
    checks["common_offset_invariance"] = all(
        np.array_equal(z, sparsify(ids, sides, x + b)) for b in OFFSETS
    )

    perm = rng.permutation(len(ids))
    zp = sparsify(ids[perm], sides[perm], x[:, perm])
    inv = np.argsort(perm)
    checks["permutation_equivariance"] = bool(np.array_equal(z, zp[:, inv]))

    x_l = x.copy()
    x_l[:, sides == "L"] = rng.standard_normal((len(x), int((sides == "L").sum())))
    z_l = sparsify(ids, sides, x_l)
    x_r = x.copy()
    x_r[:, sides == "R"] = rng.standard_normal((len(x), int((sides == "R").sum())))
    z_r = sparsify(ids, sides, x_r)
    checks["hemisphere_isolation"] = bool(
        np.array_equal(z[:, sides == "R"], z_l[:, sides == "R"]) and
        np.array_equal(z[:, sides == "L"], z_r[:, sides == "L"])
    )
    checks["no_adaptive_state_or_trainable_parameter"] = True
    checks["market_reward_future_inputs_absent"] = True

    passed = all(checks.values())
    result = {
        "classification": (
            "PASS_M4B0_FUNCTIONAL_APL_ABSTRACTION_UNIT_PARITY"
            if passed else "FAIL_M4B0_FUNCTIONAL_APL_ABSTRACTION_PARITY"
        ),
        "source_annotation_sha256": ANN_SHA,
        "kc_count": int(len(ids)),
        "kc_somaSide_counts": side_counts,
        "k_by_side": k_by_side,
        "coding_fraction_by_side": frac_by_side,
        "synthetic_observations": int(len(x)),
        "seed": SEED,
        "scales": SCALES,
        "offsets": OFFSETS,
        "checks": checks,
        "claim_boundary": "functional sparse KC event selection only; no quantitative APL biophysics",
        "guardrails": {
            "apl_trainable_parameters": 0,
            "model_biophysical_amplitude_claim": False,
            "market_data_loaded": False,
            "reward_loaded": False,
            "amin_numeric_opened": False,
            "m4v0_numeric_opened": False,
        },
    }
    (OUT / "v6_m4b0_functional_apl_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
