from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.ipc as ipc
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

WORK=Path("v6_m3a2_work")
OUT=Path("v6_m3a2_out")
WORK.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

EXPECTED_SWC={
    10540:"22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f",
    10977:"34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf",
}
EXPECTED_BRAIN="cc9bd1ecd00bd703a6fa648bc6ad145c93c7c1ee53debdcc9ce0d1f4305e6aca"
EXPECTED_KC_COUNT=4064
EXPECTED_RAW_ROWS=406552
APL_IDS=np.array(sorted(EXPECTED_SWC),dtype=np.int64)
VOXEL_UM=0.008

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def parse_swc(path:Path)->dict:
    rows=[]
    with path.open() as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith("#"): continue
            p=s.split()
            if len(p)<7: raise RuntimeError(f"{path.name}: malformed row")
            rows.append((int(p[0]),int(p[1]),float(p[2]),float(p[3]),float(p[4]),float(p[5]),int(p[6])))
    if not rows: raise RuntimeError(f"{path.name}: empty")
    arr=np.array(rows,dtype=object)
    ids=arr[:,0].astype(np.int64)
    typ=arr[:,1].astype(np.int64)
    xyz=np.column_stack([arr[:,2].astype(float),arr[:,3].astype(float),arr[:,4].astype(float)])
    rad=arr[:,5].astype(float)
    parent_ids=arr[:,6].astype(np.int64)
    if len(np.unique(ids))!=len(ids): raise RuntimeError(f"{path.name}: duplicate ids")
    if not np.all(np.isfinite(xyz)): raise RuntimeError(f"{path.name}: nonfinite xyz")
    if not np.all(np.isfinite(rad)) or np.any(rad<=0): raise RuntimeError(f"{path.name}: invalid radius")
    id_to_i={int(x):i for i,x in enumerate(ids)}
    rows_i=[]; cols_i=[]
    for i,pid in enumerate(parent_ids):
        j=id_to_i.get(int(pid))
        if j is not None:
            rows_i.extend((i,j)); cols_i.extend((j,i))
    G=sparse.csr_matrix((np.ones(len(rows_i),np.int8),(rows_i,cols_i)),shape=(len(ids),len(ids)))
    nc,lab=connected_components(G,directed=False,return_labels=True)
    sizes=np.bincount(lab,minlength=nc)
    maxsize=int(sizes.max())
    winners=np.flatnonzero(sizes==maxsize)
    if len(winners)!=1:
        return {"classification":"FAIL_M3A2_MAIN_COMPONENT_NOT_UNIQUE","ids":ids,"xyz":xyz,"rad":rad,"parent_ids":parent_ids,
                "labels":lab,"component_sizes":sizes.tolist(),"raw_roots":ids[[id_to_i.get(int(p),None) is None for p in parent_ids]].tolist()}
    mainlab=int(winners[0])
    gidx=np.flatnonzero(lab==mainlab)
    gl_to_local={int(g):i for i,g in enumerate(gidx)}
    parent=np.full(len(gidx),-1,np.int64)
    edge_count=0
    main_cable=0.0
    total_cable=0.0
    component_cable=np.zeros(nc,dtype=float)
    for i,pid in enumerate(parent_ids):
        j=id_to_i.get(int(pid))
        if j is None: continue
        d=float(np.linalg.norm(xyz[i]-xyz[j]))
        total_cable+=d
        if lab[i]==lab[j]:
            component_cable[lab[i]]+=d
        if i in gl_to_local and j in gl_to_local:
            parent[gl_to_local[i]]=gl_to_local[j]
            edge_count+=1
            main_cable+=d
    roots=np.flatnonzero(parent<0)
    if len(roots)!=1:
        return {"classification":"FAIL_M3A2_MAIN_COMPONENT_NOT_TREE","ids":ids,"xyz":xyz,"rad":rad,"parent_ids":parent_ids,
                "labels":lab,"component_sizes":sizes.tolist(),"main_label":mainlab,"main_indices":gidx,
                "main_roots":ids[gidx[roots]].tolist(),"raw_roots":ids[[id_to_i.get(int(p),None) is None for p in parent_ids]].tolist()}
    children=[[] for _ in range(len(gidx))]
    for c,p in enumerate(parent):
        if p>=0: children[int(p)].append(c)
    seen=[]
    stack=[int(roots[0])]
    while stack:
        v=stack.pop()
        seen.append(v)
        for ch in reversed(children[v]): stack.append(ch)
    if len(seen)!=len(gidx) or edge_count!=len(gidx)-1:
        return {"classification":"FAIL_M3A2_MAIN_COMPONENT_NOT_TREE","ids":ids,"xyz":xyz,"rad":rad,"parent_ids":parent_ids,
                "labels":lab,"component_sizes":sizes.tolist(),"main_label":mainlab,"main_indices":gidx}
    raw_roots=ids[np.array([id_to_i.get(int(p),None) is None for p in parent_ids],dtype=bool)].tolist()
    return {
        "classification":"STRUCTURE_OK",
        "ids":ids,"xyz":xyz,"rad":rad,"parent_ids":parent_ids,"labels":lab,
        "component_sizes":sizes.tolist(),"component_cable_source_units":component_cable.tolist(),
        "main_label":mainlab,"main_indices":gidx,"main_root_id":int(ids[gidx[int(roots[0])]]),
        "raw_roots":[int(x) for x in raw_roots],
        "total_nodes":int(len(ids)),"main_nodes":int(len(gidx)),
        "node_fraction_retained":float(len(gidx)/len(ids)),
        "main_edges":int(edge_count),
        "total_cable_source_units":float(total_cable),
        "main_cable_source_units":float(main_cable),
        "discarded_cable_source_units":float(total_cable-main_cable),
        "main_cable_um":float(main_cable*VOXEL_UM),
        "discarded_component_sizes":[int(sizes[i]) for i in range(nc) if i!=mainlab],
        "type_counts":{str(int(t)):int(np.sum(typ==t)) for t in np.unique(typ)},
    }

def main():
    brain=WORK/"brain.npz"
    syn=WORK/"syn-partners.feather"
    if sha256(brain)!=EXPECTED_BRAIN: raise RuntimeError("brain hash mismatch")
    meta=np.load(brain,allow_pickle=False)
    ids=np.asarray(meta["ids"],dtype=np.int64)
    ct=np.asarray(meta["cell_type"]).astype(str)
    kc_ids=np.sort(ids[np.char.startswith(ct,"KC")])
    if len(kc_ids)!=EXPECTED_KC_COUNT: raise RuntimeError(f"KC count {len(kc_ids)}")

    swc={}
    source_hashes={"brain":sha256(brain),"syn_partners":sha256(syn)}
    for apl in APL_IDS:
        p=WORK/f"{int(apl)}.swc"
        got=sha256(p)
        source_hashes[f"swc_{int(apl)}"]=got
        if got!=EXPECTED_SWC[int(apl)]: raise RuntimeError(f"{apl} swc hash mismatch {got}")
        swc[int(apl)]=parse_swc(p)

    structural_fail=[v["classification"] for v in swc.values() if v["classification"]!="STRUCTURE_OK"]
    if structural_fail:
        report={"gate":"V6-M3A2_PREEXISTING_MAIN_COMPONENT_MORPHOLOGY","classification":structural_fail[0],
                "source_hashes":source_hashes,"skeletons":{str(k):{kk:vv for kk,vv in v.items() if kk not in {"ids","xyz","rad","parent_ids","labels","main_indices"}} for k,v in swc.items()},
                "guardrails":{"amin_response_loaded":False,"mnq_or_market_loaded":False,"morphology_parameter_fit":False}}
        (OUT/"v6_m3a2_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
        return

    source=pa.memory_map(str(syn),"r")
    reader=ipc.open_file(source)
    schema=reader.schema
    req=["body_pre","body_post","x_pre","y_pre","z_pre","x_post","y_post","z_post"]
    miss=[x for x in req if schema.get_field_index(x)<0]
    if miss: raise RuntimeError(f"syn schema missing {miss}")
    kcset=pa.array(kc_ids)
    aplset=pa.array(APL_IDS)

    sites={int(a):{"in":[],"out":[]} for a in APL_IDS}
    raw_rows=0
    per_dir={int(a):{"kc_to_apl":0,"apl_to_kc":0} for a in APL_IDS}
    for bi in range(reader.num_record_batches):
        b=reader.get_batch(bi)
        pre=b.column(schema.get_field_index("body_pre"))
        post=b.column(schema.get_field_index("body_post"))
        pre_kc=pc.is_in(pre,value_set=kcset); post_kc=pc.is_in(post,value_set=kcset)
        pre_apl=pc.is_in(pre,value_set=aplset); post_apl=pc.is_in(post,value_set=aplset)
        mask=pc.or_(pc.and_(pre_kc,post_apl),pc.and_(pre_apl,post_kc))
        bb=b.filter(mask)
        if bb.num_rows==0: continue
        d=bb.select(req).to_pandas()
        raw_rows+=len(d)
        for apl in APL_IDS:
            aa=int(apl)
            rin=d[(d.body_post==aa) & d.body_pre.isin(kc_ids)]
            rout=d[(d.body_pre==aa) & d.body_post.isin(kc_ids)]
            if len(rin):
                sites[aa]["in"].append(rin[["x_post","y_post","z_post"]].to_numpy(float))
                per_dir[aa]["kc_to_apl"]+=len(rin)
            if len(rout):
                sites[aa]["out"].append(rout[["x_pre","y_pre","z_pre"]].to_numpy(float))
                per_dir[aa]["apl_to_kc"]+=len(rout)
    if raw_rows!=EXPECTED_RAW_ROWS:
        raise RuntimeError(f"raw APL-KC row count {raw_rows} expected {EXPECTED_RAW_ROWS}")

    coverage={}
    for apl in APL_IDS:
        aa=int(apl); s=swc[aa]
        tree=cKDTree(s["xyz"])
        total=0; main=0; max_dist=0.0
        for direction in ("in","out"):
            if not sites[aa][direction]: continue
            pts=np.vstack(sites[aa][direction])
            dist,ix=tree.query(pts,k=1,workers=-1)
            total+=len(ix)
            main+=int(np.sum(s["labels"][ix]==s["main_label"]))
            if len(dist): max_dist=max(max_dist,float(np.max(dist)))
        cov=main/total if total else float("nan")
        coverage[aa]={"relevant_sites":int(total),"sites_on_main_component":int(main),
                      "coverage":float(cov),"max_nearest_node_distance_source_units":max_dist,
                      "direction_counts":per_dir[aa]}
    pass_cov=all(np.isclose(coverage[int(a)]["coverage"],1.0,rtol=0,atol=0) for a in APL_IDS)
    classification="PASS_M3A2_PREEXISTING_MAIN_COMPONENT_MORPHOLOGY" if pass_cov else "FAIL_M3A2_RAW_SITE_COVERAGE"
    report={
        "gate":"V6-M3A2_PREEXISTING_MAIN_COMPONENT_MORPHOLOGY",
        "classification":classification,
        "source_hashes":source_hashes,
        "frozen_expected_raw_rows":EXPECTED_RAW_ROWS,
        "observed_raw_rows":int(raw_rows),
        "kc_count":int(len(kc_ids)),
        "skeletons":{str(k):{kk:vv for kk,vv in v.items() if kk not in {"ids","xyz","rad","parent_ids","labels","main_indices"}} for k,v in swc.items()},
        "raw_site_coverage":{str(k):v for k,v in coverage.items()},
        "historical_rule":{"source_file":"fly_mnq/v5_m4b_calibrate_kappa.py","git_blob_sha":"b973c50c775e97fe0fe1564994e58570ed900bc7","selection":"unique largest connected component by node count"},
        "guardrails":{"manual_component_selection":False,"amin_response_loaded":False,"mnq_or_market_loaded":False,"morphology_parameter_fit":False}
    }
    (OUT/"v6_m3a2_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
