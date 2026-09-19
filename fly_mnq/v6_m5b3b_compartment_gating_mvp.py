from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.feather as feather

W = Path("v6_m5b3b_work")
O = Path("v6_m5b3b_out")
O.mkdir(exist_ok=True)

ANN_SHA = "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
WEIGHTS_SHA = "e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1"
PRIVATE_PROTOCOL_COMMIT = "9fc5b987d0c897dc9b3285b33c955cf003def9bd"

EXPECTED = {"KC": 4064, "DAN": 340, "MBON": 97}
ROLE_CLASS = {"KC": "Kenyon_Cell", "DAN": "DAN", "MBON": "MBON"}

DAN_MAP = {
    "PPL101": ("y1", "pedc"),
    "PPL102": ("y1",),
    "PPL103": ("y2", "a'1"),
    "PPL104": ("a'3",),
    "PPL105": ("a'2", "a2"),
    "PPL106": ("a3",),
    "PAM01": ("y5",),
    "PAM02": ("B'2",),
    "PAM03": ("B2", "B'2"),
    "PAM04": ("B2",),
    "PAM05": ("B'2",),
    "PAM06": ("B'2",),
    "PAM07": ("y4",),
    "PAM08": ("y4",),
    "PAM09": ("B1",),
    "PAM10": ("B1",),
    "PAM11": ("a1",),
    "PAM12": ("y3",),
    "PAM13": ("B'1",),
    "PAM14": ("B'1",),
    "PAM15": ("y5", "B'2"),
}

MBON_MAP = {
    "MBON01": ("y5", "B'2"),
    "MBON02": ("B2", "B'2"),
    "MBON03": ("B'2",),
    "MBON04": ("B'2",),
    "MBON05": ("y4",),
    "MBON06": ("B1",),
    "MBON07": ("a1",),
    "MBON09": ("y3", "B'1"),
    "MBON10": ("B'1",),
    "MBON11": ("y1", "pedc"),
    "MBON12": ("y2", "a'1"),
    "MBON13": ("a'2",),
    "MBON14": ("a3",),
    "MBON15": ("a'1",),
    "MBON15-like": ("a'1", "a'2"),
    "MBON16": ("a'3",),
    "MBON17": ("a'3",),
    "MBON17-like": ("a'2", "a'3"),
    "MBON18": ("a2",),
    "MBON19": ("a2", "a3"),
    "MBON20": ("y1", "y2"),
    "MBON21": ("y4", "y5"),
    "MBON22": (),
    "MBON23": ("a2",),
    "MBON24": ("B2", "y5"),
    "MBON25": ("y1", "y2"),
    "MBON26": ("B'2",),
    "MBON27": ("y5",),
    "MBON28": ("a'3",),
    "MBON29": ("y4", "y5"),
    "MBON30": ("y1", "y2", "y3"),
    "MBON31": ("a'1",),
    "MBON32": ("y2",),
    "MBON33": ("y2", "y3"),
    "MBON34": ("y2",),
    "MBON35": ("y2",),
}

GAMMA = {"y1", "y2", "y3", "y4", "y5"}
ALPHA_BETA = {"a1", "a2", "a3", "B1", "B2"}
PRIME = {"a'1", "a'2", "a'3", "B'1", "B'2"}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()

def norm(v):
    if v is None or pd.isna(v):
        return ""
    return str(v).strip()

def idx_in(sorted_ids: np.ndarray, values: np.ndarray):
    pos = np.searchsorted(sorted_ids, values)
    ok = pos < len(sorted_ids)
    safe = np.minimum(pos, len(sorted_ids) - 1)
    ok &= sorted_ids[safe] == values
    return safe, ok

def mbon_compartments(type_name: str, instance: str):
    if type_name == "MBON25-like":
        if "(y2)" in instance and "(y1y2)" not in instance:
            return ("y2",)
        if "(y1y2)" in instance:
            return ("y1", "y2")
        raise ValueError(f"MBON25-like instance not covered by frozen body-specific rule: {instance!r}")
    if type_name not in MBON_MAP:
        raise KeyError(type_name)
    return MBON_MAP[type_name]

def major_system(comp: str):
    if comp in GAMMA:
        return "gamma"
    if comp in ALPHA_BETA:
        return "alpha_beta"
    if comp in PRIME:
        return "alpha_prime_beta_prime"
    return "other"

def write_result(result):
    (O / "v6_m5b3b_compartment_gating_mvp_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "classification": result.get("classification"),
        "reason": result.get("reason"),
        "identity": result.get("identity"),
        "fast_dan": result.get("fast_dan"),
        "mbon_mapping": result.get("mbon_mapping"),
        "plastic_edges": result.get("plastic_edges"),
        "criteria": result.get("criteria"),
        "guardrails": result.get("guardrails"),
    }, indent=2, sort_keys=True))

def main():
    with open("research/results/v6_m5b2_exact_learner_topology_result.json", "r", encoding="utf-8") as f:
        m5b2 = json.load(f)
    with open("research/results/v6_m5b3a_compartment_label_schema_result.json", "r", encoding="utf-8") as f:
        m5b3a = json.load(f)

    prereq = {
        "m5b2_pass": m5b2.get("classification") == "PASS_M5B2_EXACT_LEARNER_TOPOLOGY_QUALIFIED",
        "m5b3a_pass": m5b3a.get("classification") == "PASS_M5B3A_COMPARTMENT_LABEL_SCHEMA_QUALIFIED",
    }

    ann_path = W / "body-annotations.feather"
    weights_path = W / "connectome-weights.feather"
    source_sha = {
        "annotations": sha256(ann_path),
        "weights": sha256(weights_path),
    }

    ann = feather.read_table(
        ann_path,
        columns=["bodyId", "class", "type", "instance", "somaSide"]
    ).to_pandas()
    if ann["bodyId"].duplicated().any():
        prereq["body_ids_unique"] = False
    else:
        prereq["body_ids_unique"] = True

    counts = {
        role: int((ann["class"] == cls).sum())
        for role, cls in ROLE_CLASS.items()
    }
    prereq.update({
        "annotation_hash_match": source_sha["annotations"] == ANN_SHA,
        "weights_hash_match": source_sha["weights"] == WEIGHTS_SHA,
        "identity_counts_exact": counts == EXPECTED,
    })

    if not all(prereq.values()):
        result = {
            "classification": "BLOCKED_M5B3B_SOURCE_PARITY",
            "reason": "one or more frozen source/prerequisite parity anchors failed",
            "canonical_private_protocol_commit": PRIVATE_PROTOCOL_COMMIT,
            "prerequisite_parity": prereq,
            "source_sha256": source_sha,
            "identity": {"counts": counts},
            "guardrails": {
                "edge_weight_threshold_applied": False,
                "synapse_coordinates_opened": False,
                "reward_valence_assigned": False,
                "learning_rate_selected": False,
                "market_reward_pnl_opened": False,
                "amin_numeric_opened": False,
                "m4v0_numeric_opened": False,
            },
        }
        write_result(result)
        return

    kcs = ann.loc[ann["class"] == "Kenyon_Cell", "bodyId"].astype(np.int64).to_numpy()
    mb = ann.loc[ann["class"] == "MBON", ["bodyId", "type", "instance", "somaSide"]].copy()
    dn = ann.loc[ann["class"] == "DAN", ["bodyId", "type", "instance", "somaSide"]].copy()

    # Exact fast-MB DAN inclusion is by frozen type list only.
    fast = dn[dn["type"].map(norm).isin(DAN_MAP)].copy()
    fast["type_clean"] = fast["type"].map(norm)
    fast_by_comp = defaultdict(list)
    fast_body_records = []
    for _, row in fast.sort_values("bodyId").iterrows():
        typ = row["type_clean"]
        comps = tuple(DAN_MAP[typ])
        bid = int(row["bodyId"])
        for c in comps:
            fast_by_comp[c].append(bid)
        fast_body_records.append({
            "bodyId": bid,
            "type": typ,
            "instance": norm(row["instance"]),
            "somaSide": norm(row["somaSide"]),
            "compartments": list(comps),
        })
    for c in list(fast_by_comp):
        fast_by_comp[c] = sorted(set(fast_by_comp[c]))

    # Map every exact MBON body prospectively.
    mbon_body_map = {}
    unknown_mbon_types = []
    body_rule_errors = []
    type_counts = defaultdict(int)
    single_count = 0
    multi_count = 0
    unmapped_count = 0
    for _, row in mb.sort_values("bodyId").iterrows():
        bid = int(row["bodyId"])
        typ = norm(row["type"])
        inst = norm(row["instance"])
        type_counts[typ] += 1
        try:
            comps = tuple(mbon_compartments(typ, inst))
        except KeyError:
            unknown_mbon_types.append(typ)
            comps = None
        except Exception as exc:
            body_rule_errors.append({"bodyId": bid, "type": typ, "instance": inst, "error": str(exc)})
            comps = None
        if comps is None:
            status = "unresolved"
            unmapped_count += 1
        elif len(comps) == 0:
            status = "outside_fast_lobe_map"
        elif len(comps) == 1:
            status = "single_compartment"
            single_count += 1
        else:
            status = "multi_compartment"
            multi_count += 1
        mbon_body_map[bid] = {
            "bodyId": bid,
            "type": typ,
            "instance": inst,
            "somaSide": norm(row["somaSide"]),
            "compartments": None if comps is None else list(comps),
            "status": status,
        }

    included_types = sorted(set(x["type"] for x in fast_body_records))
    included_dan_mapping_ok = all(x["type"] in DAN_MAP for x in fast_body_records)
    every_mbon_mapped = not unknown_mbon_types and not body_rule_errors and len(mbon_body_map) == EXPECTED["MBON"]

    single_with_no_gate = []
    for bid, rec in sorted(mbon_body_map.items()):
        comps = rec["compartments"]
        if comps is not None and len(comps) == 1:
            comp = comps[0]
            if len(fast_by_comp.get(comp, [])) == 0:
                single_with_no_gate.append({"bodyId": bid, "type": rec["type"], "compartment": comp})

    if not included_dan_mapping_ok or not every_mbon_mapped:
        result = {
            "classification": "BLOCKED_M5B3B_SOURCE_PARITY",
            "reason": "frozen DAN/MBON mapping could not be applied exactly to source identities",
            "canonical_private_protocol_commit": PRIVATE_PROTOCOL_COMMIT,
            "prerequisite_parity": prereq,
            "source_sha256": source_sha,
            "identity": {"counts": counts},
            "fast_dan": {
                "body_count": int(len(fast_body_records)),
                "type_count": int(len(included_types)),
                "types_present": included_types,
                "body_records": fast_body_records,
                "gate_population_by_compartment": dict(sorted(fast_by_comp.items())),
            },
            "mbon_mapping": {
                "body_count": int(len(mbon_body_map)),
                "type_counts": dict(sorted(type_counts.items())),
                "unknown_types": sorted(set(unknown_mbon_types)),
                "body_rule_errors": body_rule_errors,
            },
            "guardrails": {
                "edge_weight_threshold_applied": False,
                "synapse_coordinates_opened": False,
                "reward_valence_assigned": False,
                "learning_rate_selected": False,
                "market_reward_pnl_opened": False,
                "amin_numeric_opened": False,
                "m4v0_numeric_opened": False,
            },
        }
        write_result(result)
        return

    # Reconstruct exact aggregate KC->MBON edge set, no threshold.
    kc_ids = np.sort(kcs)
    mbon_ids = np.sort(mb["bodyId"].astype(np.int64).to_numpy())
    table = feather.read_table(weights_path, columns=["body_pre", "body_post", "weight"], memory_map=True)

    all_pre = []
    all_post = []
    all_w = []
    rows_scanned = 0
    for batch in table.to_batches(max_chunksize=4_000_000):
        pre = batch.column(0).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        post = batch.column(1).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        wt = batch.column(2).to_numpy(zero_copy_only=False).astype(np.float64, copy=False)
        rows_scanned += len(pre)
        _, pre_ok = idx_in(kc_ids, pre)
        _, post_ok = idx_in(mbon_ids, post)
        take = pre_ok & post_ok
        if take.any():
            all_pre.append(pre[take].copy())
            all_post.append(post[take].copy())
            all_w.append(wt[take].copy())

    pre = np.concatenate(all_pre) if all_pre else np.array([], dtype=np.int64)
    post = np.concatenate(all_post) if all_post else np.array([], dtype=np.int64)
    wt = np.concatenate(all_w) if all_w else np.array([], dtype=np.float64)

    all_weights_valid = bool(len(wt) > 0 and np.isfinite(wt).all() and (wt > 0).all())
    expected_kc_mbon = int(m5b2.get("families", {}).get("KC->MBON", {}).get("edge_count", -1))
    exact_edge_count_parity = len(pre) == expected_kc_mbon

    elig = np.zeros(len(pre), dtype=bool)
    comp_arr = np.empty(len(pre), dtype=object)
    comp_arr[:] = ""
    gate_count_arr = np.zeros(len(pre), dtype=np.int32)

    per_comp = defaultdict(lambda: {"edge_count": 0, "raw_weight": 0.0, "mbon_bodies": set(), "kc_bodies": set()})
    per_mbon = defaultdict(lambda: {"eligible_edges": 0, "eligible_weight": 0.0})

    for i, (a, b, w) in enumerate(zip(pre, post, wt)):
        rec = mbon_body_map[int(b)]
        comps = rec["compartments"]
        if comps is not None and len(comps) == 1:
            comp = comps[0]
            gates = fast_by_comp.get(comp, [])
            if gates:
                elig[i] = True
                comp_arr[i] = comp
                gate_count_arr[i] = len(gates)
                per_comp[comp]["edge_count"] += 1
                per_comp[comp]["raw_weight"] += float(w)
                per_comp[comp]["mbon_bodies"].add(int(b))
                per_comp[comp]["kc_bodies"].add(int(a))
                per_mbon[int(b)]["eligible_edges"] += 1
                per_mbon[int(b)]["eligible_weight"] += float(w)

    ep = pre[elig]
    eq = post[elig]
    ew = wt[elig]
    ec = comp_arr[elig].astype(str)
    egc = gate_count_arr[elig]

    system_counts = {"gamma": 0, "alpha_beta": 0, "alpha_prime_beta_prime": 0, "other": 0}
    for c in ec:
        system_counts[major_system(c)] += 1

    per_comp_serial = {}
    for c, d in sorted(per_comp.items()):
        per_comp_serial[c] = {
            "edge_count": int(d["edge_count"]),
            "raw_weight": float(d["raw_weight"]),
            "unique_mbon_bodies": int(len(d["mbon_bodies"])),
            "unique_kc_bodies": int(len(d["kc_bodies"])),
            "gate_dan_body_count": int(len(fast_by_comp[c])),
            "gate_dan_body_ids": list(fast_by_comp[c]),
        }

    per_mbon_serial = []
    for bid in sorted(mbon_body_map):
        rec = dict(mbon_body_map[bid])
        rec.update({
            "eligible_edges": int(per_mbon[bid]["eligible_edges"]),
            "eligible_raw_weight": float(per_mbon[bid]["eligible_weight"]),
        })
        per_mbon_serial.append(rec)

    strict_subset = bool(0 < int(elig.sum()) < len(pre))
    criteria = {
        "A_exact_prerequisites": bool(all(prereq.values()) and exact_edge_count_parity and all_weights_valid),
        "B_every_included_fast_dan_body_mapped": bool(included_dan_mapping_ok),
        "C_every_exact_mbon_body_mapped": bool(every_mbon_mapped),
        "D_every_single_compartment_mbon_has_gate": len(single_with_no_gate) == 0,
        "E_gamma_has_eligible_edge": system_counts["gamma"] > 0,
        "E_alpha_beta_has_eligible_edge": system_counts["alpha_beta"] > 0,
        "E_alpha_prime_beta_prime_has_eligible_edge": system_counts["alpha_prime_beta_prime"] > 0,
        "F_eligible_is_strict_subset_of_exact_kc_mbon": strict_subset,
        "G_no_weight_performance_market_criterion": True,
    }
    passed = all(criteria.values())
    classification = (
        "PASS_M5B3B_COMPARTMENT_GATING_MVP_QUALIFIED"
        if passed else
        "FAIL_M5B3B_COMPARTMENT_GATING_MVP"
    )

    # Artifact-only exact eligible edge/gate manifest.
    np.savez_compressed(
        O / "v6_m5b3b_eligible_kc_mbon_edges.npz",
        body_pre=ep.astype(np.int64),
        body_post=eq.astype(np.int64),
        raw_weight=ew.astype(np.float64),
        compartment=ec.astype("U8"),
        gate_dan_count=egc.astype(np.int32),
    )
    with open(O / "v6_m5b3b_gate_population_by_compartment.json", "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in sorted(fast_by_comp.items())}, f, indent=2, sort_keys=True)

    result = {
        "classification": classification,
        "reason": (
            "all frozen source, mapping and eligible-edge criteria passed"
            if passed else
            "source parity was valid but at least one frozen compartment-gating criterion failed"
        ),
        "canonical_private_protocol_commit": PRIVATE_PROTOCOL_COMMIT,
        "source_sha256": source_sha,
        "prerequisite_parity": prereq,
        "identity": {
            "counts": counts,
            "exact_kc_mbon_edges_reconstructed": int(len(pre)),
            "m5b2_expected_kc_mbon_edges": expected_kc_mbon,
            "exact_kc_mbon_edge_count_parity": exact_edge_count_parity,
            "all_kc_mbon_weights_finite_positive": all_weights_valid,
        },
        "fast_dan": {
            "body_count": int(len(fast_body_records)),
            "type_count": int(len(included_types)),
            "types_present": included_types,
            "gate_population_by_compartment": {k: v for k, v in sorted(fast_by_comp.items())},
        },
        "mbon_mapping": {
            "body_count": int(len(mbon_body_map)),
            "single_compartment_bodies": int(single_count),
            "multi_compartment_bodies": int(multi_count),
            "outside_fast_lobe_map_bodies": int(sum(r["status"] == "outside_fast_lobe_map" for r in mbon_body_map.values())),
            "unresolved_bodies": int(unmapped_count),
            "single_compartment_without_gate": single_with_no_gate,
            "per_body": per_mbon_serial,
        },
        "plastic_edges": {
            "eligible_edge_count": int(elig.sum()),
            "eligible_raw_weight": float(np.sum(ew)) if len(ew) else 0.0,
            "total_kc_mbon_edge_count": int(len(pre)),
            "eligible_fraction_of_kc_mbon_edges": float(elig.mean()) if len(elig) else 0.0,
            "eligible_unique_kcs": int(len(np.unique(ep))) if len(ep) else 0,
            "eligible_unique_mbons": int(len(np.unique(eq))) if len(eq) else 0,
            "major_system_edge_counts": system_counts,
            "per_compartment": per_comp_serial,
        },
        "criteria": criteria,
        "guardrails": {
            "edge_weight_threshold_applied": False,
            "direct_dan_mbon_required_for_gate": False,
            "synapse_coordinates_opened": False,
            "multi_compartment_mbon_edges_plastic": False,
            "reward_valence_assigned": False,
            "learning_rate_selected": False,
            "plasticity_executed": False,
            "market_reward_pnl_opened": False,
            "amin_numeric_opened": False,
            "m4v0_numeric_opened": False,
        },
    }
    write_result(result)

if __name__ == "__main__":
    main()
