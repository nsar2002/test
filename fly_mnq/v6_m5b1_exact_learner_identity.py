import hashlib,json
from pathlib import Path
import pyarrow.feather as feather

W=Path("v6_m5b1_work")
O=Path("v6_m5b1_out")
O.mkdir(exist_ok=True)
ANN_SHA="2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
EXPECTED={"KC":4064,"DAN":340,"MBON":97}
RULE={"Kenyon_Cell":"KC","DAN":"DAN","MBON":"MBON"}

def h(p):
    x=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): x.update(b)
    return x.hexdigest()

def main():
    p=W/"body-annotations.feather"
    if h(p)!=ANN_SHA:
        r={"classification":"BLOCKED_M5B1_SOURCE_PARITY","reason":"annotation hash mismatch"}
    else:
        t=feather.read_table(p,columns=["bodyId","class","somaSide"])
        d=t.to_pandas()
        if d["bodyId"].duplicated().any():
            r={"classification":"BLOCKED_M5B1_SOURCE_PARITY","reason":"bodyId not unique"}
        else:
            x=d[d["class"].isin(RULE)].copy()
            x["role"]=x["class"].map(RULE)
            counts={q:int((x["role"]==q).sum()) for q in EXPECTED}
            kc=x[x["role"]=="KC"]
            sides={str(k):int(v) for k,v in kc["somaSide"].fillna("<MISSING>").value_counts().sort_index().items()}
            if counts!=EXPECTED:
                r={"classification":"BLOCKED_M5B1_SOURCE_PARITY","reason":"exact class counts mismatch","counts":counts}
            elif not kc["somaSide"].isin(["L","R"]).all():
                r={"classification":"BLOCKED_M5B1_KC_HEMISPHERE_IDENTITY","counts":counts,"kc_somaSide_counts":sides}
            else:
                r={
                  "classification":"PASS_M5B1_EXACT_LEARNER_IDENTITIES_FROZEN",
                  "source_annotation_sha256":ANN_SHA,
                  "counts":counts,
                  "kc_somaSide_counts":sides,
                  "identity_rule":{"KC":"class == Kenyon_Cell","DAN":"class == DAN","MBON":"class == MBON","KC_hemisphere":"somaSide exact L/R"},
                  "guardrails":{"synapse_table_opened":False,"degree_used":False,"model_executed":False,"plasticity_executed":False,"market_or_reward_inspected":False}
                }
    (O/"v6_m5b1_exact_learner_identity_result.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,indent=2,sort_keys=True))

if __name__=="__main__": main()
