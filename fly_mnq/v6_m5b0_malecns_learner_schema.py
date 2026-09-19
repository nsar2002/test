from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.ipc as ipc

OUT = Path("v6_m5b0_out")
WORK = Path("v6_m5b0_work")
OUT.mkdir(exist_ok=True)

EXPECTED_BRAIN_SHA256 = "cc9bd1ecd00bd703a6fa648bc6ad145c93c7c1ee53debdcc9ce0d1f4305e6aca"
DISCOVERY_TOKENS = ("kenyon", "kc", "mbon", "dan", "dopamin", "mbin", "mushroom")
META_NAME_TOKENS = ("side", "hemi", "later", "soma")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def value_matches(text: str) -> list[str]:
    s = text.casefold()
    return [tok for tok in DISCOVERY_TOKENS if tok in s]


def is_stringish(t: pa.DataType) -> bool:
    return (
        pa.types.is_string(t)
        or pa.types.is_large_string(t)
        or pa.types.is_dictionary(t)
    )


def scalar_text(x) -> str:
    if x is None:
        return ""
    return str(x)


def main() -> None:
    ann_path = WORK / "body-annotations.feather"
    syn_path = WORK / "syn-partners.feather"
    brain_path = WORK / "brain.npz"
    for p in (ann_path, syn_path, brain_path):
        if not p.exists():
            raise RuntimeError(f"missing source: {p}")

    brain_sha = sha256(brain_path)
    if brain_sha != EXPECTED_BRAIN_SHA256:
        raise RuntimeError(f"brain.npz hash mismatch: {brain_sha}")

    ann = feather.read_table(ann_path)
    ann_schema = [{"name": f.name, "type": str(f.type)} for f in ann.schema]
    if "bodyId" not in ann.column_names:
        raise RuntimeError(f"official annotation missing bodyId; columns={ann.column_names}")
    body_ids = ann["bodyId"].to_numpy(zero_copy_only=False)
    unique_body = len(set(int(x) for x in body_ids if x is not None))
    body_id_unique = unique_body == ann.num_rows

    matched_values = {}
    token_body_sets = {tok: set() for tok in DISCOVERY_TOKENS}
    taxonomy_body_sets = {"KC_LIKE": set(), "MBON_LIKE": set(), "DAN_LIKE": set()}

    for field in ann.schema:
        if not is_stringish(field.type):
            continue
        name = field.name
        col = ann[name].to_pylist()
        counts = Counter()
        token_by_value = {}
        for i, raw in enumerate(col):
            text = scalar_text(raw).strip()
            if not text:
                continue
            toks = value_matches(text)
            if not toks:
                continue
            counts[text] += 1
            token_by_value.setdefault(text, set()).update(toks)
            bid = int(body_ids[i])
            for tok in toks:
                token_body_sets[tok].add(bid)
            low = text.casefold()
            if "kenyon" in low or re.search(r"(^|[^a-z])kc([^a-z]|$)", low):
                taxonomy_body_sets["KC_LIKE"].add(bid)
            if "mbon" in low:
                taxonomy_body_sets["MBON_LIKE"].add(bid)
            if "dan" in low or "dopamin" in low:
                taxonomy_body_sets["DAN_LIKE"].add(bid)
        if counts:
            matched_values[name] = [
                {
                    "value": v,
                    "body_count": int(n),
                    "matched_tokens": sorted(token_by_value[v]),
                }
                for v, n in sorted(counts.items(), key=lambda kv: kv[0])
            ]

    metadata_fields = {}
    for field in ann.schema:
        lname = field.name.casefold()
        if not any(tok in lname for tok in META_NAME_TOKENS):
            continue
        values = ann[field.name].to_pylist()
        nonempty = [scalar_text(x).strip() for x in values if scalar_text(x).strip()]
        metadata_fields[field.name] = {
            "type": str(field.type),
            "missing_or_empty_count": int(len(values) - len(nonempty)),
            "distinct_nonempty_values": sorted(set(nonempty)),
        }

    source = pa.memory_map(str(syn_path), "r")
    reader = ipc.open_file(source)
    syn_schema = [{"name": f.name, "type": str(f.type)} for f in reader.schema]
    required_syn = {
        "body_pre", "body_post",
        "x_pre", "y_pre", "z_pre",
        "x_post", "y_post", "z_post",
        "primary_post",
    }
    syn_required_present = required_syn.issubset(set(reader.schema.names))

    brain = np.load(brain_path, allow_pickle=False)
    brain_ids = set(int(x) for x in np.asarray(brain["ids"], dtype=np.int64))
    ann_id_set = set(int(x) for x in body_ids)
    cell_types = np.asarray(brain["cell_type"]).astype(str)
    brain_type_counts = Counter(cell_types.tolist())
    brain_matching_type_counts = {
        v: int(n)
        for v, n in sorted(brain_type_counts.items())
        if value_matches(v)
    }

    criteria = {
        "exact_sources_loaded": True,
        "bodyId_present": "bodyId" in ann.column_names,
        "bodyId_unique": bool(body_id_unique),
        "kc_like_source_taxonomy_discovered": bool(taxonomy_body_sets["KC_LIKE"]),
        "mbon_like_source_taxonomy_discovered": bool(taxonomy_body_sets["MBON_LIKE"]),
        "dan_like_source_taxonomy_discovered": bool(taxonomy_body_sets["DAN_LIKE"]),
        "directional_synapse_schema_present": bool(syn_required_present),
        "model_executed": False,
        "plasticity_executed": False,
        "market_or_reward_inspected": False,
        "amin_numeric_opened": False,
        "m4v0_numeric_opened": False,
    }
    passed = all(criteria[k] for k in (
        "exact_sources_loaded",
        "bodyId_present",
        "bodyId_unique",
        "kc_like_source_taxonomy_discovered",
        "mbon_like_source_taxonomy_discovered",
        "dan_like_source_taxonomy_discovered",
        "directional_synapse_schema_present",
    )) and not any(criteria[k] for k in (
        "model_executed",
        "plasticity_executed",
        "market_or_reward_inspected",
        "amin_numeric_opened",
        "m4v0_numeric_opened",
    ))

    report = {
        "gate": "V6-M5B0_MALECNS_LEARNER_SCHEMA",
        "status": "PASS" if passed else "BLOCKED",
        "classification": (
            "PASS_M5B0_MALECNS_LEARNER_SCHEMA_QUALIFIED"
            if passed else "BLOCKED_M5B0_MALECNS_LEARNER_SCHEMA"
        ),
        "sources": {
            "brain_npz_sha256": brain_sha,
            "annotations_sha256": sha256(ann_path),
            "syn_partners_sha256": sha256(syn_path),
        },
        "annotation_rows": int(ann.num_rows),
        "annotation_schema": ann_schema,
        "source_matched_taxonomy_values": matched_values,
        "candidate_body_counts": {
            k: int(len(v)) for k, v in taxonomy_body_sets.items()
        },
        "metadata_fields_by_frozen_name_tokens": metadata_fields,
        "synapse_schema": syn_schema,
        "brain_npz_parity": {
            "brain_ids": int(len(brain_ids)),
            "annotation_ids": int(len(ann_id_set)),
            "id_intersection": int(len(brain_ids & ann_id_set)),
            "brain_matching_cell_type_counts": brain_matching_type_counts,
        },
        "criteria": criteria,
        "guardrails": {
            "final_learner_subset_selected": False,
            "degree_or_synapse_count_used_for_selection": False,
            "model_executed": False,
            "learning_rule_executed": False,
            "market_data_loaded": False,
        },
    }
    out = OUT / "v6_m5b0_malecns_learner_schema.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "classification": report["classification"],
        "annotation_rows": report["annotation_rows"],
        "candidate_body_counts": report["candidate_body_counts"],
        "metadata_fields": report["metadata_fields_by_frozen_name_tokens"],
        "matched_taxonomy_fields": list(report["source_matched_taxonomy_values"]),
        "criteria": report["criteria"],
        "sources": report["sources"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
