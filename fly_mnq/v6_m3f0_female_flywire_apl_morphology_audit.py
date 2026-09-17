from __future__ import annotations
import hashlib, json, math, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

WORK=Path("v6_m3f0_work"); OUT=Path("v6_m3f0_out")
WORK.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)

ANNOT_COMMIT="8587524c1748ce5ef2080822a2fc890fc03bf597"
ANNOT_BLOB_SHA="afea3e15a5671f5da0b9f7dd2e932d328c3b57a0"
ANNOT_EXPECTED_SIZE=31718505
ANNOT_URL=f"https://raw.githubusercontent.com/flyconnectome/flywire_annotations/{ANNOT_COMMIT}/supplemental_files/Supplemental_file1_neuron_annotations.tsv"
SKEL_BASE="https://flyem.mrc-lmb.cam.ac.uk/flyconnectome/flywire_skeletons_783"

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def curl(url:str,p:Path):
    cp=subprocess.run(["curl","--fail","--location","--retry","5","--retry-delay","3","--max-time","300","-o",str(p),url],
                      text=True,capture_output=True)
    if cp.returncode:
        raise RuntimeError(f"curl failed {url}: {cp.stderr[-1000:]}")
    if not p.exists() or p.stat().st_size==0:
        raise RuntimeError(f"empty download {url}")

def side_norm(v):
    s=str(v).strip().lower()
    if s in {"left","l"}: return "left"
    if s in {"right","r"}: return "right"
    return s

def pyval(v):
    if pd.isna(v): return None
    if isinstance(v,(np.integer,)): return int(v)
    if isinstance(v,(np.floating,)): return float(v)
    return str(v)

def parse_precomputed(path:Path):
    raw=path.read_bytes()
    if len(raw)<8: raise RuntimeError(f"{path.name}: short skeleton")
    n=np.frombuffer(raw,dtype="<u4",count=1,offset=0)[0].item()
    e=np.frombuffer(raw,dtype="<u4",count=1,offset=4)[0].item()
    off=8
    xyz_bytes=12*n
    edge_bytes=8*e
    rad_bytes=4*n
    expected=off+xyz_bytes+edge_bytes+rad_bytes
    if len(raw)!=expected:
        raise RuntimeError(f"{path.name}: binary size {len(raw)} != expected {expected} for n={n},e={e}")
    xyz=np.frombuffer(raw,dtype="<f4",count=3*n,offset=off).reshape(n,3).astype(float)
    off+=xyz_bytes
    edges=np.frombuffer(raw,dtype="<u4",count=2*e,offset=off).reshape(e,2).astype(np.int64)
    off+=edge_bytes
    rad=np.frombuffer(raw,dtype="<f4",count=n,offset=off).astype(float)

    if n<100: raise RuntimeError(f"{path.name}: too few nodes {n}")
    if e!=n-1: raise RuntimeError(f"{path.name}: edges {e} != nodes-1 {n-1}")
    if not np.isfinite(xyz).all(): raise RuntimeError(f"{path.name}: nonfinite xyz")
    edge_index_ok=bool(not np.any(edges<0) and not np.any(edges>=n))
    self_edge_count=int(np.sum(edges[:,0]==edges[:,1])) if edge_index_ok else -1
    canon=np.sort(edges,axis=1) if edge_index_ok else np.empty((0,2),dtype=np.int64)
    duplicate_undirected_edges=int(len(canon)-len(np.unique(canon,axis=0))) if edge_index_ok else -1

    if edge_index_ok:
        rr=np.concatenate([edges[:,0],edges[:,1]])
        cc=np.concatenate([edges[:,1],edges[:,0]])
        G=sparse.csr_matrix((np.ones(len(rr),np.int8),(rr,cc)),shape=(n,n))
        nc,labels=connected_components(G,directed=False,return_labels=True)
        d=xyz[edges[:,0]]-xyz[edges[:,1]]
        L=np.linalg.norm(d,axis=1)
        invalid_edge_lengths=int(np.sum(~np.isfinite(L) | (L<=0)))
    else:
        nc=-1; L=np.array([],float); invalid_edge_lengths=-1

    finite_rad=np.isfinite(rad)
    nonfinite_radius_count=int(np.sum(~finite_rad))
    nonpositive_radius_count=int(np.sum(finite_rad & (rad<=0)))
    structure_pass=bool(
        n>=100 and e==n-1 and np.isfinite(xyz).all() and
        nonfinite_radius_count==0 and nonpositive_radius_count==0 and
        edge_index_ok and self_edge_count==0 and duplicate_undirected_edges==0 and
        nc==1 and invalid_edge_lengths==0
    )

    return {
        "n_nodes":int(n),"n_edges":int(e),"xyz":xyz,"radius":rad,"edges":edges,
        "coord_min_nm":[float(x) for x in xyz.min(axis=0)],
        "coord_max_nm":[float(x) for x in xyz.max(axis=0)],
        "radius_min_nm":float(np.nanmin(rad)),"radius_median_nm":float(np.nanmedian(rad)),"radius_max_nm":float(np.nanmax(rad)),
        "nonfinite_radius_count":nonfinite_radius_count,
        "nonpositive_radius_count":nonpositive_radius_count,
        "self_edge_count":self_edge_count,
        "duplicate_undirected_edge_count":duplicate_undirected_edges,
        "invalid_edge_length_count":invalid_edge_lengths,
        "total_cable_um":float(L.sum()/1000.0) if len(L) else None,
        "connected_components":int(nc),
        "root_semantics_unavailable":True,
        "structure_pass":structure_pass,
    }

def main():
    annot=WORK/"Supplemental_file1_neuron_annotations.tsv"
    if not annot.exists():
        curl(ANNOT_URL,annot)
    if annot.stat().st_size!=ANNOT_EXPECTED_SIZE:
        raise RuntimeError(f"annotation size {annot.stat().st_size} != {ANNOT_EXPECTED_SIZE}")
    ann_sha=sha256(annot)
    df=pd.read_csv(annot,sep="\t",low_memory=False)
    required={"root_id","cell_type","side","soma_x","soma_y","soma_z","status"}
    miss=required-set(df.columns)
    if miss: raise RuntimeError(f"annotation schema missing {sorted(miss)}")

    exact=df[df["cell_type"].astype("string").str.strip().eq("APL")].copy()
    if len(exact)!=2:
        report={
          "gate":"V6-M3F0_FEMALE_FLYWIRE_APL_MORPHOLOGY_SOURCE",
          "classification":"BLOCKED_M3F0_FEMALE_APL_IDENTITY_AMBIGUOUS",
          "annotation":{"commit":ANNOT_COMMIT,"blob_sha":ANNOT_BLOB_SHA,"sha256":ann_sha,
                        "size":annot.stat().st_size,"exact_APL_row_count":int(len(exact))},
          "guardrails":{"fuzzy_search":False,"morphology_selected":False,"rin_loaded":False,"amin_loaded":False,"mnq_loaded":False}
        }
        (OUT/"v6_m3f0_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
        return

    exact["root_id"]=pd.to_numeric(exact["root_id"],errors="raise").astype("int64")
    if exact.root_id.nunique()!=2:
        raise RuntimeError("APL root IDs not distinct")
    exact["_side_norm"]=exact["side"].map(side_norm)
    if sorted(exact["_side_norm"].tolist())!=["left","right"]:
        report={
          "gate":"V6-M3F0_FEMALE_FLYWIRE_APL_MORPHOLOGY_SOURCE",
          "classification":"BLOCKED_M3F0_FEMALE_APL_IDENTITY_AMBIGUOUS",
          "annotation":{"commit":ANNOT_COMMIT,"blob_sha":ANNOT_BLOB_SHA,"sha256":ann_sha,
                        "size":annot.stat().st_size,"exact_APL_row_count":2,
                        "sides":exact["_side_norm"].tolist()},
          "guardrails":{"fuzzy_search":False,"morphology_selected":False,"rin_loaded":False,"amin_loaded":False,"mnq_loaded":False}
        }
        (OUT/"v6_m3f0_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
        return

    for c in ["soma_x","soma_y","soma_z"]:
        exact[c]=pd.to_numeric(exact[c],errors="coerce")
    if not np.isfinite(exact[["soma_x","soma_y","soma_z"]].to_numpy(float)).all():
        raise RuntimeError("nonfinite APL soma coordinates")
    bad_status=exact["status"].astype("string").fillna("").str.strip().eq("outlier_seg")
    if bad_status.any(): raise RuntimeError("APL annotation includes outlier_seg")

    rows=[]
    sk_reports={}
    for _,r in exact.sort_values("_side_norm").iterrows():
        root=int(r.root_id); side=r["_side_norm"]
        skp=WORK/f"{root}.precomputed"
        curl(f"{SKEL_BASE}/{root}",skp)
        sk=parse_precomputed(skp)
        soma_nm=np.array([float(r.soma_x)*4.0,float(r.soma_y)*4.0,float(r.soma_z)*40.0])
        dist,ix=cKDTree(sk["xyz"]).query(soma_nm,k=1)
        ix=int(ix)
        if not np.isfinite(dist): raise RuntimeError(f"{root}: nonfinite soma mapping")
        fields={}
        for k in ["root_id","side","cell_type","cell_class","super_class","cell_sub_class","top_nt",
                  "status","dimorphism","matching_notes","supertype","synonyms","hemibrain_type",
                  "soma_x","soma_y","soma_z","fbbt_id","vfb_id"]:
            if k in exact.columns:
                fields[k]=pyval(r.get(k))
        fields["side_normalized"]=side
        fields["soma_nm"]=[float(x) for x in soma_nm]
        fields["nearest_skeleton_node_index"]=ix
        fields["nearest_soma_distance_nm"]=float(dist)
        fields["nearest_soma_distance_um"]=float(dist/1000.0)
        fields["nearest_skeleton_radius_nm"]=float(sk["radius"][ix])
        rows.append(fields)
        sk_reports[str(root)]={
          "side":side,
          "raw_precomputed_sha256":sha256(skp),
          "raw_precomputed_bytes":skp.stat().st_size,
          "structure":{k:v for k,v in sk.items() if k not in {"xyz","radius","edges"}},
          "soma_mapping":{"source_soma_nm":[float(x) for x in soma_nm],
                          "nearest_node_index":ix,
                          "distance_nm":float(dist),
                          "distance_um":float(dist/1000.0),
                          "nearest_radius_nm":float(sk["radius"][ix])}
        }

    all_structure=all(v["structure"]["structure_pass"] for v in sk_reports.values())
    classification="PASS_M3F0_FEMALE_FLYWIRE_APL_MORPHOLOGY_SOURCE" if all_structure else "FAIL_M3F0_FEMALE_PRECOMPUTED_SKELETON_STRUCTURE"
    report={
      "gate":"V6-M3F0_FEMALE_FLYWIRE_APL_MORPHOLOGY_SOURCE",
      "classification":classification,
      "dataset":{"name":"FlyWire FAFB","materialization":783,"sex":"female adult fly brain"},
      "annotation":{"commit":ANNOT_COMMIT,"blob_sha":ANNOT_BLOB_SHA,"sha256":ann_sha,
                    "size":annot.stat().st_size,"exact_APL_row_count":2,
                    "rows":rows},
      "skeleton_source":{"base_url":SKEL_BASE,"format":"neuroglancer_precomputed_skeleton",
                         "units":"1 nm","radius_vertex_attribute":"float32"},
      "skeletons":sk_reports,
      "guardrails":{"exact_cell_type_only":True,"fuzzy_search":False,"community_label_used":False,
                    "morphology_similarity_used":False,"rin_loaded":False,"ra_rm_fit":False,
                    "amin_loaded":False,"mnq_loaded":False}
    }
    (OUT/"v6_m3f0_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    pd.DataFrame(rows).to_csv(OUT/"v6_m3f0_apl_rows.csv",index=False)
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
