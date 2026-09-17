from __future__ import annotations
import hashlib, json, math
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

WORK=Path("v6_m3f0b_work"); OUT=Path("v6_m3f0b_out")
WORK.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)

PARQUET=WORK/"sk_lod1_783_healed_ds2.parquet"
EXPECTED_MD5="a4c104776f33ec539ef859064c4de3df"
ROOTS={
    720575940624547622:{"side":"left","soma_nm":[333408.0,188960.0,148040.0],
                       "fast_nodes":136848,"fast_cable_um":76043.50582675338,
                       "fast_soma_dist_um":0.3479653503005229},
    720575940613583001:{"side":"right","soma_nm":[717664.0,204160.0,120560.0],
                       "fast_nodes":141780,"fast_cable_um":79532.01355678483,
                       "fast_soma_dist_um":0.39195110786866344},
}

def digest(p:Path,algo:str)->str:
    h=hashlib.new(algo)
    with p.open("rb") as f:
        for b in iter(lambda:f.read(32<<20),b""): h.update(b)
    return h.hexdigest()

def jsonable(v):
    if isinstance(v,(np.integer,)): return int(v)
    if isinstance(v,(np.floating,)): return float(v)
    if pd.isna(v): return None
    return v

def schema_gate(path:Path):
    pf=pq.ParquetFile(path)
    names=pf.schema_arrow.names
    id_col="neuron" if "neuron" in names else ("fragment_id" if "fragment_id" in names else None)
    node_col="node_id" if "node_id" in names else ("sample_id" if "sample_id" in names else None)
    required_xyz=all(c in names for c in ("x","y","z"))
    radius="radius" if "radius" in names else None
    parent="parent_id" if "parent_id" in names else None
    ok=bool(id_col and node_col and required_xyz and radius and parent)
    return pf,names,id_col,node_col,radius,parent,ok

def audit_one(df:pd.DataFrame,root:int,node_col:str,radius_col:str,parent_col:str):
    rep={"root_id":int(root),"side":ROOTS[root]["side"]}
    n=int(len(df)); rep["n_nodes"]=n
    if n<100:
        rep["pass"]=False; rep["reason"]="too_few_nodes"; return rep

    ids=pd.to_numeric(df[node_col],errors="coerce").to_numpy()
    xyz=df[["x","y","z"]].apply(pd.to_numeric,errors="coerce").to_numpy(float)
    rad=pd.to_numeric(df[radius_col],errors="coerce").to_numpy(float)
    par=pd.to_numeric(df[parent_col],errors="coerce").to_numpy()

    finite_ids=np.isfinite(ids.astype(float))
    duplicate_nodes=int(n-len(np.unique(ids[finite_ids])))
    finite_xyz=bool(np.isfinite(xyz).all())
    nonfinite_radius=int(np.sum(~np.isfinite(rad)))
    nonpositive_radius=int(np.sum(np.isfinite(rad)&(rad<=0)))

    idset=set(int(x) for x in ids if np.isfinite(float(x)))
    roots=[]
    missing_parent=[]
    self_parent=0
    edges=[]
    for i,(nid,p) in enumerate(zip(ids,par)):
        if not np.isfinite(float(nid)): continue
        nid=int(nid)
        rootlike=False
        if pd.isna(p):
            rootlike=True
        else:
            pf=float(p)
            if not np.isfinite(pf):
                rootlike=True
            else:
                pid=int(pf)
                if pid<0:
                    rootlike=True
                elif pid==nid:
                    self_parent+=1
                elif pid not in idset:
                    missing_parent.append(pid)
                else:
                    edges.append((nid,pid))
        if rootlike: roots.append(nid)

    id_to_idx={int(x):i for i,x in enumerate(ids) if np.isfinite(float(x))}
    valid_edges=[(id_to_idx[a],id_to_idx[b]) for a,b in edges if a in id_to_idx and b in id_to_idx]
    edge_count=len(valid_edges)
    if valid_edges:
        arr=np.asarray(valid_edges,dtype=np.int64)
        canon=np.sort(arr,axis=1)
        duplicate_edges=int(len(canon)-len(np.unique(canon,axis=0)))
        rr=np.concatenate([arr[:,0],arr[:,1]])
        cc=np.concatenate([arr[:,1],arr[:,0]])
        G=sparse.csr_matrix((np.ones(len(rr),np.int8),(rr,cc)),shape=(n,n))
        nc,labels=connected_components(G,directed=False,return_labels=True)
        L=np.linalg.norm(xyz[arr[:,0]]-xyz[arr[:,1]],axis=1)
        invalid_edge_length=int(np.sum(~np.isfinite(L)|(L<=0)))
        cable_um=float(np.nansum(L)/1000.0)
    else:
        duplicate_edges=0; nc=n; labels=np.arange(n); invalid_edge_length=0; cable_um=0.0

    soma=np.asarray(ROOTS[root]["soma_nm"],float)
    soma_dist,soma_ix=cKDTree(xyz).query(soma,k=1) if finite_xyz else (float("nan"),-1)
    soma_ix=int(soma_ix) if soma_ix>=0 else -1
    soma_rad=float(rad[soma_ix]) if soma_ix>=0 and np.isfinite(rad[soma_ix]) else None

    pass_=bool(
        n>=100 and duplicate_nodes==0 and finite_xyz and
        nonfinite_radius==0 and nonpositive_radius==0 and
        len(roots)==1 and len(missing_parent)==0 and self_parent==0 and
        edge_count==n-1 and duplicate_edges==0 and nc==1 and invalid_edge_length==0
    )
    rep.update({
        "pass":pass_,
        "node_id_unique":duplicate_nodes==0,
        "duplicate_node_count":duplicate_nodes,
        "finite_xyz":finite_xyz,
        "nonfinite_radius_count":nonfinite_radius,
        "nonpositive_radius_count":nonpositive_radius,
        "radius_min_nm":float(np.nanmin(rad)),
        "radius_median_nm":float(np.nanmedian(rad)),
        "radius_max_nm":float(np.nanmax(rad)),
        "root_count":int(len(roots)),
        "tree_root_node_id":int(roots[0]) if len(roots)==1 else None,
        "missing_parent_count":int(len(missing_parent)),
        "self_parent_count":int(self_parent),
        "n_edges":int(edge_count),
        "duplicate_undirected_edge_count":int(duplicate_edges),
        "connected_components":int(nc),
        "invalid_edge_length_count":int(invalid_edge_length),
        "coord_min_nm":[float(x) for x in np.nanmin(xyz,axis=0)],
        "coord_max_nm":[float(x) for x in np.nanmax(xyz,axis=0)],
        "total_cable_um":cable_um,
        "soma_mapping":{
            "source_soma_nm":[float(x) for x in soma],
            "nearest_node_id":int(ids[soma_ix]) if soma_ix>=0 else None,
            "nearest_distance_nm":float(soma_dist),
            "nearest_distance_um":float(soma_dist/1000.0),
            "nearest_radius_nm":soma_rad,
        },
        "cross_representation":{
            "fast_precomputed_nodes":int(ROOTS[root]["fast_nodes"]),
            "node_count_ratio_zenodo_to_fast":float(n/ROOTS[root]["fast_nodes"]),
            "fast_precomputed_cable_um":float(ROOTS[root]["fast_cable_um"]),
            "cable_ratio_zenodo_to_fast":float(cable_um/ROOTS[root]["fast_cable_um"]),
            "fast_precomputed_soma_distance_um":float(ROOTS[root]["fast_soma_dist_um"]),
        }
    })
    return rep

def main():
    if not PARQUET.exists(): raise RuntimeError(f"missing {PARQUET}")
    md5=digest(PARQUET,"md5")
    sha=digest(PARQUET,"sha256")
    size=PARQUET.stat().st_size
    if md5!=EXPECTED_MD5:
        raise RuntimeError(f"Zenodo MD5 mismatch {md5} != {EXPECTED_MD5}")

    pf,names,id_col,node_col,radius_col,parent_col,schema_ok=schema_gate(PARQUET)
    base={
      "gate":"V6-M3F0B_FEMALE_FLYWIRE_ZENODO_SWC",
      "source":{"doi":"10.5281/zenodo.10877326","version":"v2",
                "filename":PARQUET.name,"md5":md5,"sha256":sha,"bytes":int(size)},
      "schema":{"names":names,"id_column":id_col,"node_column":node_col,
                "radius_column":radius_col,"parent_column":parent_col,
                "schema_ok":schema_ok,
                "num_row_groups":int(pf.metadata.num_row_groups),
                "num_rows":int(pf.metadata.num_rows)},
      "immutable_root_ids":[int(x) for x in ROOTS],
      "guardrails":{"radius_imputation":False,"mesh_reskeletonization":False,
                    "alternate_root":False,"rin_loaded":False,"ra_rm_fit":False,
                    "amin_loaded":False,"mnq_loaded":False}
    }
    if not schema_ok:
        base["classification"]="BLOCKED_M3F0B_ZENODO_SWC_SCHEMA"
        (OUT/"v6_m3f0b_result.json").write_text(json.dumps(base,indent=2,sort_keys=True)+"\n")
        print(json.dumps(base,indent=2,sort_keys=True))
        return

    ids=[int(x) for x in ROOTS]
    table=pq.read_table(PARQUET,filters=[(id_col,"in",ids)])
    df=table.to_pandas()
    got=set(int(x) for x in pd.to_numeric(df[id_col],errors="coerce").dropna().unique())
    if got!=set(ids):
        base["classification"]="BLOCKED_M3F0B_ZENODO_SWC_SCHEMA"
        base["observed_root_ids"]=sorted(got)
        (OUT/"v6_m3f0b_result.json").write_text(json.dumps(base,indent=2,sort_keys=True)+"\n")
        print(json.dumps(base,indent=2,sort_keys=True))
        return

    reports={}
    for root in ids:
        sub=df[pd.to_numeric(df[id_col],errors="coerce").eq(root)].copy()
        reports[str(root)]=audit_one(sub,root,node_col,radius_col,parent_col)

    allpass=all(v["pass"] for v in reports.values())
    base["classification"]="PASS_M3F0B_FEMALE_ZENODO_SWC_CABLE_GEOMETRY" if allpass else "FAIL_M3F0B_FEMALE_ZENODO_SWC_CABLE_GEOMETRY"
    base["reports"]=reports
    (OUT/"v6_m3f0b_result.json").write_text(json.dumps(base,indent=2,sort_keys=True)+"\n")
    # Save only the two immutable APL rows as a compact provenance artifact.
    keep=[c for c in [id_col,node_col,"x","y","z",radius_col,parent_col,"label"] if c in df.columns]
    df[keep].to_parquet(OUT/"v6_m3f0b_selected_apl_swc.parquet",index=False)
    print(json.dumps(base,indent=2,sort_keys=True))

if __name__=="__main__": main()
