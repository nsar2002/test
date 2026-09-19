from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.feather as feather

W = Path("v6_m5b2_work")
O = Path("v6_m5b2_out")
O.mkdir(exist_ok=True)

ANN_SHA = "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
WEIGHTS_SHA = "e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1"
EXPECTED = {"KC": 4064, "DAN": 340, "MBON": 97}
EXPECTED_KC_SIDES = {"L": 2019, "R": 2045}
CLASS_TO_ROLE = {"Kenyon_Cell": "KC", "DAN": "DAN", "MBON": "MBON"}
ROLES = ("KC", "DAN", "MBON")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()

def idx_in(sorted_ids, values):
    pos = np.searchsorted(sorted_ids, values)
    ok = pos < len(sorted_ids)
    safe = np.minimum(pos, len(sorted_ids) - 1)
    ok &= sorted_ids[safe] == values
    return safe, ok

def qsummary(values):
    x = np.asarray(values)
    if len(x) == 0:
        return {"min": None, "median": None, "max": None}
    return {
        "min": float(np.min(x)),
        "median": float(np.median(x)),
        "max": float(np.max(x)),
    }

def degree_summary(pre, post):
    if len(pre) == 0:
        return {
            "pre_out_degree": {"min": None, "median": None, "max": None},
            "post_in_degree": {"min": None, "median": None, "max": None},
        }
    _, outdeg = np.unique(pre, return_counts=True)
    _, indeg = np.unique(post, return_counts=True)
    return {
        "pre_out_degree": qsummary(outdeg),
        "post_in_degree": qsummary(indeg),
    }

def main():
    ann_path = W / "body-annotations.feather"
    weights_path = W / "connectome-weights.feather"
    source_hash = {
        "annotations": sha256(ann_path),
        "weights": sha256(weights_path),
    }

    ann = feather.read_table(ann_path).to_pandas()
    if "bodyId" not in ann or "class" not in ann:
        raise RuntimeError("required annotation fields absent")
    if ann["bodyId"].duplicated().any():
        raise RuntimeError("bodyId not unique")

    ids_df = ann[ann["class"].isin(CLASS_TO_ROLE)].copy()
    ids_df["role"] = ids_df["class"].map(CLASS_TO_ROLE)
    ids_df = ids_df.sort_values("bodyId").reset_index(drop=True)
    counts = {r: int((ids_df["role"] == r).sum()) for r in ROLES}

    kc = ids_df[ids_df["role"] == "KC"]
    kc_sides = {
        str(k): int(v)
        for k, v in kc["somaSide"].fillna("<MISSING>").value_counts().sort_index().items()
    } if "somaSide" in kc.columns else {"<MISSING_FIELD>": int(len(kc))}

    parity = {
        "annotation_hash_match": source_hash["annotations"] == ANN_SHA,
        "weights_hash_match": source_hash["weights"] == WEIGHTS_SHA,
        "identity_counts_exact": counts == EXPECTED,
        "kc_sides_exact": kc_sides == EXPECTED_KC_SIDES,
    }

    if not all(parity.values()):
        result = {
            "classification": "BLOCKED_M5B2_SOURCE_OR_IDENTITY_PARITY",
            "source_sha256": source_hash,
            "counts": counts,
            "kc_somaSide_counts": kc_sides,
            "parity": parity,
            "guardrails": {
                "performance_selection": False,
                "synapse_coordinates_opened": False,
                "market_reward_pnl_opened": False,
                "amin_numeric_opened": False,
                "m4v0_numeric_opened": False,
            },
        }
        (O / "v6_m5b2_exact_learner_topology_result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    learner_ids = ids_df["bodyId"].to_numpy(np.int64)
    roles_by_sorted = ids_df["role"].to_numpy(str)
    role_by_id = dict(zip(learner_ids.tolist(), roles_by_sorted.tolist()))

    side_by_id = {}
    if "somaSide" in ids_df.columns:
        for bid, side in zip(ids_df["bodyId"], ids_df["somaSide"]):
            s = "" if pd.isna(side) else str(side)
            side_by_id[int(bid)] = s
    else:
        side_by_id = {int(b): "" for b in learner_ids}

    pres = []
    posts = []
    weights = []
    table = feather.read_table(weights_path, columns=["body_pre", "body_post", "weight"], memory_map=True)
    rows_scanned = 0
    for batch in table.to_batches(max_chunksize=4_000_000):
        pre = batch.column(0).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        post = batch.column(1).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        wt = batch.column(2).to_numpy(zero_copy_only=False).astype(np.float64, copy=False)
        rows_scanned += len(pre)
        _, pre_ok = idx_in(learner_ids, pre)
        _, post_ok = idx_in(learner_ids, post)
        keep = pre_ok & post_ok
        if keep.any():
            pres.append(pre[keep].copy())
            posts.append(post[keep].copy())
            weights.append(wt[keep].copy())

    pre = np.concatenate(pres) if pres else np.array([], np.int64)
    post = np.concatenate(posts) if posts else np.array([], np.int64)
    wt = np.concatenate(weights) if weights else np.array([], np.float64)

    all_weights_valid = bool(len(wt) > 0 and np.isfinite(wt).all() and (wt > 0).all())

    pre_role = np.asarray([role_by_id[int(x)] for x in pre], dtype=object)
    post_role = np.asarray([role_by_id[int(x)] for x in post], dtype=object)

    families = {}
    family_edges = {}
    for a in ROLES:
        for b in ROLES:
            key = f"{a}->{b}"
            m = (pre_role == a) & (post_role == b)
            fp, fq, fw = pre[m], post[m], wt[m]
            family_edges[key] = (fp, fq, fw)
            ds = degree_summary(fp, fq)
            side_counts = defaultdict(int)
            for x, y in zip(fp, fq):
                sx, sy = side_by_id.get(int(x), ""), side_by_id.get(int(y), "")
                rel = f"{sx}->{sy}" if sx in ("L", "R") and sy in ("L", "R") else "unresolved"
                side_counts[rel] += 1
            families[key] = {
                "edge_count": int(len(fp)),
                "total_raw_weight": float(np.sum(fw)) if len(fw) else 0.0,
                "unique_pre": int(len(np.unique(fp))),
                "unique_post": int(len(np.unique(fq))),
                "edge_weight": qsummary(fw),
                **ds,
                "side_relation_edge_counts": dict(sorted(side_counts.items())),
            }

    kc_mbon_pre, kc_mbon_post, kc_mbon_w = family_edges["KC->MBON"]
    dan_mbon_pre, dan_mbon_post, dan_mbon_w = family_edges["DAN->MBON"]
    mbon_dan_pre, mbon_dan_post, mbon_dan_w = family_edges["MBON->DAN"]
    kc_dan_pre, kc_dan_post, _ = family_edges["KC->DAN"]
    dan_kc_pre, dan_kc_post, _ = family_edges["DAN->KC"]

    mbons = ids_df[ids_df["role"] == "MBON"].copy().sort_values("bodyId")
    mb_diag = []
    for bid in mbons["bodyId"].astype(np.int64):
        km = kc_mbon_post == bid
        dm = dan_mbon_post == bid
        md = mbon_dan_pre == bid
        mb_diag.append({
            "bodyId": int(bid),
            "somaSide": side_by_id.get(int(bid), ""),
            "kc_partner_count": int(len(np.unique(kc_mbon_pre[km]))),
            "kc_total_raw_weight": float(np.sum(kc_mbon_w[km])) if km.any() else 0.0,
            "direct_dan_to_mbon": bool(dm.any()),
            "direct_mbon_to_dan": bool(md.any()),
        })

    optional_label_cols = [
        c for c in ("cell_type", "cellType", "type", "flywireType", "hemibrainType",
                    "hemibrain_type", "systematicType", "systematic_type", "subclass", "instance")
        if c in ids_df.columns
    ]
    ann_index = ann.set_index("bodyId", drop=False)
    dans = ids_df[ids_df["role"] == "DAN"].copy().sort_values("bodyId")
    dan_diag = []
    for bid in dans["bodyId"].astype(np.int64):
        d = {
            "bodyId": int(bid),
            "somaSide": side_by_id.get(int(bid), ""),
            "kc_to_dan_partner_count": int(len(np.unique(kc_dan_pre[kc_dan_post == bid]))),
            "dan_to_kc_partner_count": int(len(np.unique(dan_kc_post[dan_kc_pre == bid]))),
            "dan_to_mbon_count": int(len(np.unique(dan_mbon_post[dan_mbon_pre == bid]))),
            "mbon_to_dan_count": int(len(np.unique(mbon_dan_pre[mbon_dan_post == bid]))),
        }
        row = ann_index.loc[int(bid)]
        for col in optional_label_cols:
            val = row[col]
            d[col] = None if pd.isna(val) else str(val)
        dan_diag.append(d)

    # Source-only two-step path counts, counting distinct edge combinations through each middle MBON.
    kc_in_by_mbon = defaultdict(set)
    dan_in_by_mbon = defaultdict(set)
    dan_out_by_mbon = defaultdict(set)
    for x, y in zip(kc_mbon_pre, kc_mbon_post):
        kc_in_by_mbon[int(y)].add(int(x))
    for x, y in zip(dan_mbon_pre, dan_mbon_post):
        dan_in_by_mbon[int(y)].add(int(x))
    for x, y in zip(mbon_dan_pre, mbon_dan_post):
        dan_out_by_mbon[int(x)].add(int(y))

    kc_mbon_dan_paths = 0
    dan_mbon_dan_paths = 0
    kc_mbon_dan_middle = 0
    dan_mbon_dan_middle = 0
    for bid in mbons["bodyId"].astype(np.int64):
        a = len(kc_in_by_mbon[int(bid)])
        b = len(dan_out_by_mbon[int(bid)])
        c = len(dan_in_by_mbon[int(bid)])
        if a and b:
            kc_mbon_dan_middle += 1
            kc_mbon_dan_paths += a * b
        if c and b:
            dan_mbon_dan_middle += 1
            dan_mbon_dan_paths += c * b

    dan_recurrent = set(int(x) for x in dan_mbon_pre) | set(int(x) for x in mbon_dan_post)
    mbons_with_kc = set(int(x) for x in kc_mbon_post)

    criteria = {
        "A_source_hashes_match": all((parity["annotation_hash_match"], parity["weights_hash_match"])),
        "B_m5b1_identity_parity": bool(parity["identity_counts_exact"] and parity["kc_sides_exact"]),
        "C_all_induced_weights_finite_positive": all_weights_valid,
        "D_kc_to_mbon_nonempty": families["KC->MBON"]["edge_count"] > 0,
        "E_mbon_to_dan_nonempty": families["MBON->DAN"]["edge_count"] > 0,
        "F_dan_to_mbon_nonempty": families["DAN->MBON"]["edge_count"] > 0,
        "G_no_performance_or_market_selection": True,
    }
    passed = all(criteria.values())
    classification = (
        "PASS_M5B2_EXACT_LEARNER_TOPOLOGY_QUALIFIED"
        if passed else "FAIL_M5B2_REQUIRED_TOPOLOGY_MISSING"
    )

    result = {
        "classification": classification,
        "canonical_private_protocol_commit": "249c1d5a972d411c06f473e6442f2044aae3f6e0",
        "source_sha256": source_hash,
        "rows_scanned": int(rows_scanned),
        "identity": {"counts": counts, "kc_somaSide_counts": kc_sides},
        "induced_edge_count": int(len(pre)),
        "induced_total_raw_weight": float(np.sum(wt)) if len(wt) else 0.0,
        "all_induced_weights_finite_positive": all_weights_valid,
        "families": families,
        "mbon_diagnostics": mb_diag,
        "dan_diagnostics": dan_diag,
        "motif_availability": {
            "dans_with_any_mbon_edge_either_direction": int(len(dan_recurrent)),
            "mbons_with_direct_kc_input": int(len(mbons_with_kc)),
            "kc_to_mbon_to_dan_distinct_edge_combination_paths": int(kc_mbon_dan_paths),
            "kc_to_mbon_to_dan_middle_mbons": int(kc_mbon_dan_middle),
            "dan_to_mbon_to_dan_distinct_edge_combination_paths": int(dan_mbon_dan_paths),
            "dan_to_mbon_to_dan_middle_mbons": int(dan_mbon_dan_middle),
        },
        "criteria": criteria,
        "guardrails": {
            "edge_weight_threshold_applied": False,
            "final_dan_subset_selected": False,
            "synapse_coordinates_opened": False,
            "roi_placement_opened": False,
            "model_or_plasticity_executed": False,
            "market_reward_pnl_opened": False,
            "amin_numeric_opened": False,
            "m4v0_numeric_opened": False,
        },
    }
    (O / "v6_m5b2_exact_learner_topology_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "classification": classification,
        "source_sha256": source_hash,
        "identity": result["identity"],
        "induced_edge_count": result["induced_edge_count"],
        "families": families,
        "motif_availability": result["motif_availability"],
        "criteria": criteria,
        "guardrails": result["guardrails"],
    }, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
