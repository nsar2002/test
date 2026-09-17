from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.ipc as ipc
import pyarrow.parquet as pq

OUT = Path("v6_m0_out")
WORK = Path("v6_m0_work")
OUT.mkdir(exist_ok=True)

EXPECTED_BRAIN_SHA256 = "cc9bd1ecd00bd703a6fa648bc6ad145c93c7c1ee53debdcc9ce0d1f4305e6aca"
EXPECTED_APL_IDS = [10540, 10977]
MIN_RECIPROCAL_IDENTIFIABLE_PNS = 3


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def calyx_mask(primary_post: pa.Array) -> pa.Array:
    s = pc.cast(primary_post, pa.string())
    return pc.fill_null(pc.starts_with(s, pattern="CA("), False)


def main() -> None:
    brain_path = WORK / "brain.npz"
    ann_path = WORK / "body-annotations.feather"
    syn_path = WORK / "syn-partners.feather"
    for p in (brain_path, ann_path, syn_path):
        if not p.exists():
            raise RuntimeError(f"missing prerequisite: {p}")

    brain_sha = sha256(brain_path)
    if brain_sha != EXPECTED_BRAIN_SHA256:
        raise RuntimeError(f"brain hash mismatch: {brain_sha}")

    meta = np.load(brain_path, allow_pickle=False)
    ids = np.asarray(meta["ids"], dtype=np.int64)
    cell_type = np.asarray(meta["cell_type"]).astype(str)
    apl_ids = ids[cell_type == "APL"].tolist()
    if apl_ids != EXPECTED_APL_IDS:
        raise RuntimeError(f"APL identity mismatch: {apl_ids}")

    ann = feather.read_table(ann_path).to_pandas()
    required_ann = {"bodyId", "class", "flywireType"}
    missing_ann = sorted(required_ann - set(ann.columns))
    if missing_ann:
        raise RuntimeError(f"annotation schema missing {missing_ann}")
    ann = ann.drop_duplicates("bodyId").copy()
    alpn = ann.loc[ann["class"].fillna("").eq("ALPN"), ["bodyId", "flywireType"]].copy()
    alpn["bodyId"] = alpn["bodyId"].astype(np.int64)
    alpn["flywireType"] = alpn["flywireType"].fillna("").astype(str)
    pn_ids = np.sort(alpn["bodyId"].unique())
    if len(pn_ids) < MIN_RECIPROCAL_IDENTIFIABLE_PNS:
        raise RuntimeError(f"too few ALPN bodies in source: {len(pn_ids)}")

    source = pa.memory_map(str(syn_path), "r")
    reader = ipc.open_file(source)
    schema = reader.schema
    required_syn = [
        "x_pre", "y_pre", "z_pre", "body_pre", "conf_pre",
        "x_post", "y_post", "z_post", "body_post", "conf_post", "primary_post",
    ]
    missing_syn = [x for x in required_syn if schema.get_field_index(x) < 0]
    if missing_syn:
        raise RuntimeError(f"synapse schema missing {missing_syn}; schema={schema}")

    pn_values = pa.array(pn_ids)
    apl_values = pa.array(np.asarray(EXPECTED_APL_IDS, dtype=np.int64))
    kept_batches: list[pa.RecordBatch] = []
    total_partner_rows = 0
    total_calyx_rows = 0

    for bi in range(reader.num_record_batches):
        b = reader.get_batch(bi)
        pre = b.column(schema.get_field_index("body_pre"))
        post = b.column(schema.get_field_index("body_post"))
        pre_apl = pc.is_in(pre, value_set=apl_values)
        post_apl = pc.is_in(post, value_set=apl_values)
        pre_pn = pc.is_in(pre, value_set=pn_values)
        post_pn = pc.is_in(post, value_set=pn_values)
        pair_mask = pc.or_(pc.and_(pre_pn, post_apl), pc.and_(pre_apl, post_pn))
        pair = b.filter(pair_mask)
        total_partner_rows += pair.num_rows
        if pair.num_rows == 0:
            continue
        roi = pair.column(schema.get_field_index("primary_post"))
        pair = pair.filter(calyx_mask(roi))
        total_calyx_rows += pair.num_rows
        if pair.num_rows:
            kept_batches.append(pair)

    if not kept_batches:
        raise RuntimeError("no ALPN↔APL CALYX synapse rows found")

    table = pa.Table.from_batches(kept_batches)
    out_parquet = OUT / "malecns_alpn_apl_calyx_synapses.parquet"
    pq.write_table(table, out_parquet, compression="zstd")
    df = table.select(["body_pre", "body_post", "primary_post"]).to_pandas()
    apl_set = set(EXPECTED_APL_IDS)
    pn_set = set(map(int, pn_ids))

    pn_to_apl = df[df["body_pre"].isin(pn_set) & df["body_post"].isin(apl_set)]
    apl_to_pn = df[df["body_pre"].isin(apl_set) & df["body_post"].isin(pn_set)]
    p2a_ids = set(map(int, pn_to_apl["body_pre"].unique()))
    a2p_ids = set(map(int, apl_to_pn["body_post"].unique()))
    reciprocal_ids = sorted(p2a_ids & a2p_ids)

    type_map = alpn.set_index("bodyId")["flywireType"].to_dict()
    reciprocal_types = sorted({type_map.get(int(b), "") for b in reciprocal_ids if type_map.get(int(b), "")})
    per_pn = [
        {
            "bodyId": int(body),
            "flywireType": type_map.get(int(body), ""),
            "pn_to_apl_calyx_rows": int((pn_to_apl["body_pre"] == body).sum()),
            "apl_to_pn_calyx_rows": int((apl_to_pn["body_post"] == body).sum()),
        }
        for body in reciprocal_ids
    ]

    exact_roi_values = sorted(map(str, df["primary_post"].dropna().unique().tolist()))
    criteria = {
        "official_synapse_schema_has_direction_xyz_and_primary_post": len(missing_syn) == 0,
        "apl_identity_exact_10540_10977": apl_ids == EXPECTED_APL_IDS,
        "alpn_identity_source_defined": len(pn_ids) >= MIN_RECIPROCAL_IDENTIFIABLE_PNS,
        "calyx_pn_to_apl_nonzero": len(pn_to_apl) > 0,
        "calyx_apl_to_pn_nonzero": len(apl_to_pn) > 0,
        "reciprocal_identifiable_pns_ge_3": len(reciprocal_ids) >= MIN_RECIPROCAL_IDENTIFIABLE_PNS,
        "model_executed": False,
        "market_or_mnq_inspected": False,
    }
    passed = all(criteria[k] for k in [
        "official_synapse_schema_has_direction_xyz_and_primary_post",
        "apl_identity_exact_10540_10977",
        "alpn_identity_source_defined",
        "calyx_pn_to_apl_nonzero",
        "calyx_apl_to_pn_nonzero",
        "reciprocal_identifiable_pns_ge_3",
    ]) and not criteria["model_executed"] and not criteria["market_or_mnq_inspected"]

    report = {
        "gate": "V6-M0_MALECNS_PN_APL_CALYX_IMPLEMENTATION_SOURCE_AUDIT",
        "status": "PASS" if passed else "FAIL",
        "classification": "PASS_M0_MALECNS_PN_APL_SOURCE_GEOMETRY" if passed else "FAIL_M0_MALECNS_PN_APL_SOURCE_GEOMETRY",
        "frozen_min_reciprocal_identifiable_pns": MIN_RECIPROCAL_IDENTIFIABLE_PNS,
        "source": {
            "brain_sha256": brain_sha,
            "annotation_sha256": sha256(ann_path),
            "syn_partners_sha256": sha256(syn_path),
        },
        "counts": {
            "source_alpn_bodies": int(len(pn_ids)),
            "all_pn_apl_partner_rows_before_calyx_filter": int(total_partner_rows),
            "calyx_rows_total": int(total_calyx_rows),
            "pn_to_apl_calyx_rows": int(len(pn_to_apl)),
            "apl_to_pn_calyx_rows": int(len(apl_to_pn)),
            "pn_to_apl_unique_pns": int(len(p2a_ids)),
            "apl_to_pn_unique_pns": int(len(a2p_ids)),
            "reciprocal_unique_pns": int(len(reciprocal_ids)),
            "reciprocal_distinct_nonempty_types": int(len(reciprocal_types)),
        },
        "calyx_primary_post_values": exact_roi_values,
        "reciprocal_pn_types": reciprocal_types,
        "per_reciprocal_pn": per_pn,
        "criteria": criteria,
        "output": {"parquet": str(out_parquet), "parquet_sha256": sha256(out_parquet)},
        "guardrails": {
            "no_synapse_count_to_current_conversion": True,
            "no_coupling_parameter_selected": True,
            "no_v5_residual_used": True,
            "no_market_data": True,
        },
    }
    report_path = OUT / "v6_m0_malecns_pn_apl_source_audit.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "classification": report["classification"],
        "counts": report["counts"],
        "calyx_primary_post_values": report["calyx_primary_post_values"],
        "criteria": report["criteria"],
        "source": report["source"],
        "output": report["output"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
