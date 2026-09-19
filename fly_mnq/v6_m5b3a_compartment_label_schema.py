from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd
import pyarrow.feather as feather

W=Path("v6_m5b3a_work")
O=Path("v6_m5b3a_out")
O.mkdir(exist_ok=True)

ANN_SHA="2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
EXPECTED={"DAN":340,"MBON":97}
CANDIDATE_FIELDS=("type","flywireType","hemibrainType")
FROZEN_FIELDS=("bodyId","class","somaSide","rootSide","instance","type","flywireType","hemibrainType","systematicType","systematic_type","subclass")

def h(p):
    x=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): x.update(b)
    return x.hexdigest()

def clean(v):
    if v is None or pd.isna(v):
        return None
    s=str(v).strip()
    return s if s else None

def main():
    p=W/"body-annotations.feather"
    got=h(p)
    d=feather.read_table(p).to_pandas()
    if "bodyId" not in d or "class" not in d:
        raise RuntimeError("required bodyId/class absent")
    sub=d[d["class"].isin(EXPECTED)].copy().sort_values("bodyId")
    counts={k:int((sub["class"]==k).sum()) for k in EXPECTED}
    body_unique=not bool(sub["bodyId"].duplicated().any())

    available=[f for f in FROZEN_FIELDS if f in sub.columns]
    records=[]
    coverage={}
    unique_values={}
    for role in EXPECTED:
        x=sub[sub["class"]==role]
        coverage[role]={}
        for f in available:
            coverage[role][f]=int(sum(clean(v) is not None for v in x[f]))
        unique_values[role]={}
        for f in CANDIDATE_FIELDS:
            if f in x:
                unique_values[role][f]=sorted({clean(v) for v in x[f] if clean(v) is not None})
            else:
                unique_values[role][f]=[]

    missing_type={"DAN":0,"MBON":0}
    disagreement={"DAN":0,"MBON":0}
    literal_tokens={"DAN":set(),"MBON":set()}
    token_re=re.compile(r"\(([^()]*)\)")

    for _,row in sub.iterrows():
        role=str(row["class"])
        vals={f:(clean(row[f]) if f in row else None) for f in available}
        tvals={f:clean(row[f]) if f in row else None for f in CANDIDATE_FIELDS}
        nonempty=[v for v in tvals.values() if v is not None]
        if not nonempty:
            missing_type[role]+=1
        if len(set(nonempty))>1:
            disagreement[role]+=1
        tokens=[]
        for v in nonempty:
            tokens.extend(m.group(1) for m in token_re.finditer(v))
        literal_tokens[role].update(tokens)
        rec={k:vals.get(k) for k in available}
        rec["type_field_values"]=tvals
        rec["type_fields_disagree"]=len(set(nonempty))>1
        rec["literal_parenthesized_tokens"]=sorted(set(tokens))
        records.append(rec)

    criteria={
        "annotation_hash_match":got==ANN_SHA,
        "exact_counts":counts==EXPECTED,
        "body_ids_unique":body_unique,
        "every_dan_has_type_field":missing_type["DAN"]==0,
        "every_mbon_has_type_field":missing_type["MBON"]==0,
    }
    passed=all(criteria.values())
    result={
        "classification":"PASS_M5B3A_COMPARTMENT_LABEL_SCHEMA_QUALIFIED" if passed else "BLOCKED_M5B3A_COMPARTMENT_LABEL_SCHEMA",
        "canonical_private_protocol_commit":"82e6b699e789710975a7c21cfa3f9c8e68c2fafa",
        "annotation_sha256":got,
        "counts":counts,
        "available_frozen_fields":available,
        "coverage_nonempty":coverage,
        "unique_type_values":unique_values,
        "literal_parenthesized_tokens":{k:sorted(v) for k,v in literal_tokens.items()},
        "type_field_disagreement_body_counts":disagreement,
        "missing_all_type_fields_body_counts":missing_type,
        "records":records,
        "criteria":criteria,
        "guardrails":{
            "connectivity_opened":False,
            "synapse_coordinates_opened":False,
            "compartment_translation_applied":False,
            "plasticity_executed":False,
            "market_reward_pnl_opened":False,
            "amin_numeric_opened":False,
            "m4v0_numeric_opened":False,
        }
    }
    (O/"v6_m5b3a_compartment_label_schema_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":result["classification"],
        "counts":counts,
        "coverage_nonempty":coverage,
        "unique_type_values":unique_values,
        "literal_parenthesized_tokens":result["literal_parenthesized_tokens"],
        "type_field_disagreement_body_counts":disagreement,
        "missing_all_type_fields_body_counts":missing_type,
        "criteria":criteria,
        "guardrails":result["guardrails"],
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
