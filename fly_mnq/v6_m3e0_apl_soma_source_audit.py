from __future__ import annotations
import hashlib, json, re
from pathlib import Path
import numpy as np, pandas as pd
import pyarrow.feather as feather
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

WORK=Path("v6_m3e0_work"); OUT=Path("v6_m3e0_out")
WORK.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
EXPECTED_ANN="2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
EXPECTED_SWC={10540:"22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f",
              10977:"34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf"}
VOXEL_UM=0.008

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def parse_loc(v):
    if v is None: return None
    if isinstance(v,float) and np.isnan(v): return None
    if isinstance(v,(list,tuple,np.ndarray)):
        a=np.asarray(v,dtype=float).ravel()
        return a[:3] if len(a)>=3 and np.isfinite(a[:3]).all() else None
    if isinstance(v,dict):
        for keys in (("x","y","z"),("X","Y","Z")):
            if all(k in v for k in keys):
                a=np.array([v[k] for k in keys],float)
                return a if np.isfinite(a).all() else None
    nums=re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",str(v))
    if len(nums)>=3:
        a=np.array(list(map(float,nums[:3])))
        return a if np.isfinite(a).all() else None
    return None

def swc_component(path):
    rows=[]
    for line in open(path):
        s=line.strip()
        if not s or s.startswith("#"): continue
        p=s.split()
        rows.append((int(p[0]),float(p[2]),float(p[3]),float(p[4]),int(p[6])))
    ids=np.array([r[0] for r in rows],np.int64)
    xyz=np.array([[r[1],r[2],r[3]] for r in rows],float)
    parent=np.array([r[4] for r in rows],np.int64)
    imap={int(x):i for i,x in enumerate(ids)}
    rr=[]; cc=[]
    for i,p in enumerate(parent):
        j=imap.get(int(p))
        if j is not None:
            rr += [i,j]; cc += [j,i]
    G=sparse.csr_matrix((np.ones(len(rr),np.int8),(rr,cc)),shape=(len(ids),len(ids)))
    nc,labels=connected_components(G,directed=False,return_labels=True)
    sizes=np.bincount(labels,minlength=nc)
    win=np.flatnonzero(sizes==sizes.max())
    if len(win)!=1: raise RuntimeError(f"{path}: largest component not unique")
    return ids,xyz,labels,int(win[0]),sizes

def clean(v):
    if v is None: return None
    if isinstance(v,float) and np.isnan(v): return None
    if isinstance(v,(list,tuple,np.ndarray,dict)): return json.loads(json.dumps(v,default=lambda x:x.tolist() if hasattr(x,'tolist') else str(x)))
    return str(v)

def main():
    annp=WORK/"body-annotations.feather"
    if sha256(annp)!=EXPECTED_ANN: raise RuntimeError("annotation hash mismatch")
    ann=feather.read_table(annp).to_pandas()
    if "bodyId" not in ann.columns or "somaLocation" not in ann.columns or "flywireType" not in ann.columns:
        raise RuntimeError(f"missing required columns; columns={list(ann.columns)}")
    out={}
    all_ok=True
    for body in (10540,10977):
        swcp=WORK/f"{body}.swc"
        got=sha256(swcp)
        if got!=EXPECTED_SWC[body]: raise RuntimeError(f"{body} SWC hash mismatch")
        rows=ann[ann.bodyId.astype("int64")==body]
        if len(rows)!=1:
            out[str(body)]={"row_count":int(len(rows)),"criteria_pass":False}
            all_ok=False; continue
        row=rows.iloc[0]
        loc=parse_loc(row["somaLocation"])
        flywire=clean(row.get("flywireType"))
        ids,xyz,labels,mainlab,sizes=swc_component(swcp)
        nearest=None
        onmain=False
        if loc is not None:
            dist,idx=cKDTree(xyz).query(loc,k=1)
            nearest={"node_id":int(ids[int(idx)]),
                     "distance_source_units":float(dist),
                     "distance_um":float(dist*VOXEL_UM),
                     "component_label":int(labels[int(idx)]),
                     "main_component_label":mainlab}
            onmain=bool(labels[int(idx)]==mainlab)
        criteria={
            "exactly_one_annotation_row":len(rows)==1,
            "somaLocation_finite_xyz":loc is not None,
            "flywireType_nonempty":bool(flywire and flywire.lower() not in {"nan","none",""}),
            "nearest_swc_node_on_historical_main_component":onmain,
        }
        ok=all(criteria.values())
        all_ok=all_ok and ok
        out[str(body)]={
            "criteria_pass":ok,
            "criteria":criteria,
            "somaLocation_source_units":None if loc is None else [float(x) for x in loc],
            "nearest_swc_node":nearest,
            "component_sizes":[int(x) for x in sizes],
            "annotation_fields":{k:clean(row.get(k)) for k in
                ["type","instance","superclass","class","subclass","somaSide","rootSide","somaNeuromere","flywireType","mancType","mancBodyid","status"]
                if k in ann.columns}
        }
    cls="PASS_M3E0_SOURCE_DEFINED_APL_SOMA_MAPPING" if all_ok else "FAIL_M3E0_APL_SOMA_MAPPING_SOURCE"
    report={"gate":"V6-M3E0_APL_SOMA_CROSS_SEX_SOURCE_AUDIT","classification":cls,
            "source_hashes":{"annotations":sha256(annp),**{f"swc_{b}":sha256(WORK/f"{b}.swc") for b in (10540,10977)}},
            "apl":out,
            "interpretation":{"female_whole_cell_vs_male_morphology":"falsification_only_unless_future_cross_sex_quantitative_mapping",
                              "flywireType_is_correspondence_not_geometry_identity":True},
            "guardrails":{"input_resistance_values_loaded":False,"ra_rm_fit":False,"amin_loaded":False,"mnq_loaded":False}}
    (OUT/"v6_m3e0_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
