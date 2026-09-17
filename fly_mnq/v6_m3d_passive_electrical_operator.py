from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.ipc as ipc
from scipy import sparse
from scipy.sparse.linalg import splu
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

WORK=Path("v6_m3d_work")
OUT=Path("v6_m3d_out")
WORK.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

EXPECTED={
    "brain":"cc9bd1ecd00bd703a6fa648bc6ad145c93c7c1ee53debdcc9ce0d1f4305e6aca",
    "annotations":"2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2",
    "syn_partners":"959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07",
    "swc_10540":"22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f",
    "swc_10977":"34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf",
}
APL_IDS=(10540,10977)
EXPECTED_KC_COUNT=4064
EXPECTED_RAW_APL_KC_ROWS=406552
VOXEL_M=8e-9
Q_MIN=0.40/2.64
Q_MAX=4.00/0.20
Q_GRID=np.exp(np.linspace(np.log(Q_MIN),np.log(Q_MAX),33))
PRIMARY=("CALYX","ALPHA","ALPHA_PRIME","BETA","BETA_PRIME","GAMMA")
ALL_ROI=PRIMARY+("PEDUNCLE","OTHER")

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def semantic_roi(x)->str:
    s="" if x is None else str(x)
    if s.startswith("CA("): return "CALYX"
    if s.startswith("PED("): return "PEDUNCLE"
    if s.startswith("aL("): return "ALPHA"
    if s.startswith("a'L("): return "ALPHA_PRIME"
    if s.startswith("bL("): return "BETA"
    if s.startswith("b'L("): return "BETA_PRIME"
    if s.startswith("gL("): return "GAMMA"
    return "OTHER"

def parse_swc(path:Path):
    rows=[]
    with path.open() as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith("#"): continue
            p=s.split()
            if len(p)<7: raise RuntimeError(f"{path.name}: malformed row")
            rows.append((int(p[0]),int(p[1]),float(p[2]),float(p[3]),float(p[4]),float(p[5]),int(p[6])))
    df=pd.DataFrame(rows,columns=["id","type","x","y","z","r","parent"])
    if len(df)<100: raise RuntimeError(f"{path.name}: too few nodes")
    if df.id.duplicated().any(): raise RuntimeError(f"{path.name}: duplicate IDs")
    if not np.isfinite(df[["x","y","z","r"]].to_numpy(float)).all(): raise RuntimeError(f"{path.name}: nonfinite geometry")
    if (df.r<=0).any(): raise RuntimeError(f"{path.name}: nonpositive radius")

    ids=df.id.to_numpy(np.int64)
    parent_ids=df.parent.to_numpy(np.int64)
    id_to_i={int(x):i for i,x in enumerate(ids)}
    rr=[]; cc=[]
    for i,p in enumerate(parent_ids):
        j=id_to_i.get(int(p))
        if j is not None:
            rr.extend((i,j)); cc.extend((j,i))
    G=sparse.csr_matrix((np.ones(len(rr),np.int8),(rr,cc)),shape=(len(ids),len(ids)))
    nc,labels=connected_components(G,directed=False,return_labels=True)
    sizes=np.bincount(labels,minlength=nc)
    winners=np.flatnonzero(sizes==sizes.max())
    if len(winners)!=1: raise RuntimeError(f"{path.name}: largest component not unique")
    main_label=int(winners[0])
    gidx=np.flatnonzero(labels==main_label)
    glob_to_local=np.full(len(ids),-1,np.int64)
    glob_to_local[gidx]=np.arange(len(gidx),dtype=np.int64)

    parent_local=np.full(len(gidx),-1,np.int64)
    for li,gi in enumerate(gidx):
        pj=id_to_i.get(int(parent_ids[gi]))
        if pj is not None and labels[pj]==main_label:
            parent_local[li]=glob_to_local[pj]
    roots=np.flatnonzero(parent_local<0)
    if len(roots)!=1: raise RuntimeError(f"{path.name}: main component roots={len(roots)}")

    xyz_all=df[["x","y","z"]].to_numpy(float)
    r_all=df.r.to_numpy(float)
    xyz=xyz_all[gidx]*VOXEL_M
    radii=r_all[gidx]*VOXEL_M

    row=[]; col=[]; dat=[]
    node_area=np.zeros(len(gidx),float)
    edge_count=0
    min_L=float("inf")
    max_L=0.0
    for child,p in enumerate(parent_local):
        if p<0: continue
        p=int(p)
        delta=xyz[child]-xyz[p]
        L=float(np.linalg.norm(delta))
        if not np.isfinite(L) or L<=0: raise RuntimeError(f"{path.name}: nonpositive edge length")
        r1=float(radii[p]); r2=float(radii[child])
        g0=math.pi*r1*r2/L
        row.extend((p,child,p,child))
        col.extend((p,child,child,p))
        dat.extend((g0,g0,-g0,-g0))
        slant=math.sqrt(L*L+(r1-r2)*(r1-r2))
        area=math.pi*(r1+r2)*slant
        node_area[p]+=0.5*area
        node_area[child]+=0.5*area
        edge_count+=1
        min_L=min(min_L,L); max_L=max(max_L,L)
    if edge_count!=len(gidx)-1: raise RuntimeError(f"{path.name}: main component edge count")
    if np.any(~np.isfinite(node_area)) or np.any(node_area<=0): raise RuntimeError(f"{path.name}: invalid node membrane area")
    L0=sparse.coo_matrix((dat,(row,col)),shape=(len(gidx),len(gidx))).tocsr()
    sym_err=(L0-L0.T)
    max_sym=float(np.max(np.abs(sym_err.data))) if sym_err.nnz else 0.0
    if max_sym>1e-18: raise RuntimeError(f"{path.name}: base operator asymmetry {max_sym}")
    return {
        "ids_all":ids,"xyz_all_source":xyz_all,"labels":labels,"main_label":main_label,
        "gidx":gidx,"glob_to_local":glob_to_local,
        "xyz_m":xyz,"radii_m":radii,"L0":L0,"node_area":node_area,
        "component_sizes":sizes.tolist(),"raw_roots":[int(ids[i]) for i,p in enumerate(parent_ids) if id_to_i.get(int(p)) is None],
        "main_root_id":int(ids[gidx[int(roots[0])]]),"main_nodes":int(len(gidx)),"total_nodes":int(len(ids)),
        "min_edge_m":min_L,"max_edge_m":max_L,"min_area_m2":float(node_area.min()),"max_area_m2":float(node_area.max()),
        "max_symmetry_error":max_sym,
    }

def read_sources():
    paths={
        "brain":WORK/"brain.npz",
        "annotations":WORK/"body-annotations.feather",
        "syn_partners":WORK/"syn-partners.feather",
        "swc_10540":WORK/"10540.swc",
        "swc_10977":WORK/"10977.swc",
    }
    hashes={k:sha256(p) for k,p in paths.items()}
    bad={k:(hashes[k],EXPECTED[k]) for k in EXPECTED if hashes[k]!=EXPECTED[k]}
    if bad: raise RuntimeError(f"source hash mismatch {bad}")
    brain=np.load(paths["brain"],allow_pickle=False)
    ids=np.asarray(brain["ids"],dtype=np.int64)
    ct=np.asarray(brain["cell_type"]).astype(str)
    kc_ids=np.sort(ids[np.char.startswith(ct,"KC")])
    if len(kc_ids)!=EXPECTED_KC_COUNT: raise RuntimeError(f"KC count {len(kc_ids)}")
    ann=feather.read_table(paths["annotations"]).to_pandas()
    ann=ann.drop_duplicates("bodyId")
    pn_ids=np.sort(ann.loc[ann["class"].fillna("").eq("ALPN"),"bodyId"].astype(np.int64).unique())
    return paths,hashes,kc_ids,pn_ids

def extract_rows(syn_path:Path,kc_ids:np.ndarray,pn_ids:np.ndarray):
    source=pa.memory_map(str(syn_path),"r")
    reader=ipc.open_file(source)
    schema=reader.schema
    req=["body_pre","body_post","x_pre","y_pre","z_pre","x_post","y_post","z_post","primary_post"]
    miss=[x for x in req if schema.get_field_index(x)<0]
    if miss: raise RuntimeError(f"missing synapse columns {miss}")
    kcset=pa.array(kc_ids)
    pnset=pa.array(pn_ids)
    aplset=pa.array(np.array(APL_IDS,dtype=np.int64))
    aplkc=[]; pncalyx=[]
    for bi in range(reader.num_record_batches):
        b=reader.get_batch(bi)
        pre=b.column(schema.get_field_index("body_pre"))
        post=b.column(schema.get_field_index("body_post"))
        pre_kc=pc.is_in(pre,value_set=kcset); post_kc=pc.is_in(post,value_set=kcset)
        pre_pn=pc.is_in(pre,value_set=pnset)
        pre_apl=pc.is_in(pre,value_set=aplset); post_apl=pc.is_in(post,value_set=aplset)
        mask_kc=pc.or_(pc.and_(pre_kc,post_apl),pc.and_(pre_apl,post_kc))
        bb=b.filter(mask_kc)
        if bb.num_rows: aplkc.append(bb.select(req).to_pandas())
        mask_pn=pc.and_(pre_pn,post_apl)
        bp=b.filter(mask_pn)
        if bp.num_rows: pncalyx.append(bp.select(req).to_pandas())
    ak=pd.concat(aplkc,ignore_index=True)
    if len(ak)!=EXPECTED_RAW_APL_KC_ROWS: raise RuntimeError(f"APL-KC raw rows {len(ak)}")
    pn=pd.concat(pncalyx,ignore_index=True) if pncalyx else pd.DataFrame(columns=req)
    return ak,pn

def map_sites(tree, pts_source):
    pts=np.asarray(pts_source,float)
    kd=cKDTree(tree["xyz_all_source"])
    dist,gi=kd.query(pts,k=1,workers=-1)
    labels=tree["labels"][gi]
    if not np.all(labels==tree["main_label"]):
        raise RuntimeError("raw site outside historical main component")
    li=tree["glob_to_local"][gi]
    if np.any(li<0): raise RuntimeError("main-component local mapping failure")
    return li.astype(np.int64),np.asarray(dist,float)

def build_ensembles(tree,rows:pd.DataFrame,apl:int):
    rin=rows[(rows.body_post==apl)].copy()
    rout=rows[(rows.body_pre==apl)].copy()
    rin["semantic_roi"]=rin["primary_post"].map(semantic_roi)
    rout["semantic_roi"]=rout["primary_post"].map(semantic_roi)
    source_nodes={}
    target_nodes={}
    mapping={}
    for roi in ALL_ROI:
        a=rin[rin.semantic_roi.eq(roi)]
        b=rout[rout.semantic_roi.eq(roi)]
        if len(a):
            nd,dd=map_sites(tree,a[["x_post","y_post","z_post"]].to_numpy(float))
            source_nodes[roi]=nd
            mapping[f"in_{roi}"]={"n":int(len(nd)),"max_nearest_source_units":float(dd.max())}
        else:
            source_nodes[roi]=np.array([],np.int64)
            mapping[f"in_{roi}"]={"n":0,"max_nearest_source_units":None}
        if len(b):
            nd,dd=map_sites(tree,b[["x_pre","y_pre","z_pre"]].to_numpy(float))
            target_nodes[roi]=nd
            mapping[f"out_{roi}"]={"n":int(len(nd)),"max_nearest_source_units":float(dd.max())}
        else:
            target_nodes[roi]=np.array([],np.int64)
            mapping[f"out_{roi}"]={"n":0,"max_nearest_source_units":None}
    for roi in PRIMARY:
        if len(source_nodes[roi])==0 or len(target_nodes[roi])==0:
            raise RuntimeError(f"APL {apl}: empty primary source/readout {roi}")
    return source_nodes,target_nodes,mapping

def build_pn_calyx(tree,pnrows:pd.DataFrame,apl:int):
    d=pnrows[(pnrows.body_post==apl)].copy()
    d=d[d.primary_post.astype(str).str.startswith("CA(",na=False)]
    if len(d)==0: raise RuntimeError(f"APL {apl}: no PN->APL calyx sites")
    nd,dist=map_sites(tree,d[["x_post","y_post","z_post"]].to_numpy(float))
    return nd,{"n":int(len(nd)),"max_nearest_source_units":float(dist.max())}

def rhs_from_nodes(n_nodes:int,nodes:np.ndarray):
    counts=np.bincount(nodes,minlength=n_nodes).astype(float)
    total=float(counts.sum())
    if total<=0: raise RuntimeError("empty source")
    return counts/total

def target_mean(V:np.ndarray,nodes:np.ndarray)->float:
    return float(np.mean(V[nodes]))

def solve_tree(tree,source_nodes,target_nodes,pn_nodes):
    n=tree["main_nodes"]
    B=np.column_stack([rhs_from_nodes(n,source_nodes[r]) for r in PRIMARY]+[rhs_from_nodes(n,pn_nodes)])
    results=[]
    local_all={r:True for r in PRIMARY}
    worst={r:{"ratio":-np.inf,"target":None,"q":None} for r in PRIMARY}
    max_resid=0.0
    min_voltage=float("inf")
    matrices=[]
    pn_diag=[]
    for qi,q in enumerate(Q_GRID):
        A=(tree["L0"] + sparse.diags(q*tree["node_area"],format="csr")).tocsc()
        lu=splu(A,permc_spec="COLAMD")
        V=lu.solve(B)
        resid=A@V-B
        denom=np.maximum(1.0,np.max(np.abs(B),axis=0))
        max_resid=max(max_resid,float(np.max(np.abs(resid))/denom))
        min_voltage=min(min_voltage,float(np.min(V)))
        mat={}
        for si,r in enumerate(PRIMARY):
            raw={s:target_mean(V[:,si],target_nodes[s]) for s in ALL_ROI}
            d=raw[r]
            if not np.isfinite(d) or d<=0: raise RuntimeError(f"invalid normalization {r} q={q}")
            norm={s:float(raw[s]/d) for s in ALL_ROI}
            if abs(norm[r]-1)>1e-10: raise RuntimeError("self normalization")
            mat[r]=norm
            for s in PRIMARY:
                if s==r: continue
                ratio=norm[s]
                if ratio>=1.0:
                    local_all[r]=False
                if ratio>worst[r]["ratio"]:
                    worst[r]={"ratio":float(ratio),"target":s,"q":float(q)}
        matrices.append({"q":float(q),"T":mat})

        pv=V[:,-1]
        raw={s:target_mean(pv,target_nodes[s]) for s in ALL_ROI}
        d=raw["CALYX"]
        if not np.isfinite(d) or d<=0: raise RuntimeError("invalid PN calyx normalization")
        pn_diag.append({"q":float(q),"T":{s:float(raw[s]/d) for s in ALL_ROI}})
    return {
        "q_grid":[float(x) for x in Q_GRID],
        "matrices":matrices,
        "local_dominance_all_grid":local_all,
        "worst_nonlocal":worst,
        "pn_calyx_diagnostic":pn_diag,
        "numerics":{"max_linear_residual":max_resid,"minimum_solved_voltage":min_voltage},
    }

def main():
    paths,hashes,kc_ids,pn_ids=read_sources()
    aplkc,pnrows=extract_rows(paths["syn_partners"],kc_ids,pn_ids)
    trees={}
    reports={}
    all_local=True
    for apl in APL_IDS:
        tree=parse_swc(paths[f"swc_{apl}"])
        trees[apl]=tree
        src,tgt,mapping=build_ensembles(tree,aplkc,apl)
        pn,pnmap=build_pn_calyx(tree,pnrows,apl)
        sol=solve_tree(tree,src,tgt,pn)
        if sol["numerics"]["max_linear_residual"]>1e-8: raise RuntimeError(f"APL {apl}: solve residual too large")
        if sol["numerics"]["minimum_solved_voltage"] < -1e-12: raise RuntimeError(f"APL {apl}: negative passive voltage")
        local_ok=all(sol["local_dominance_all_grid"].values())
        all_local=all_local and local_ok
        reports[str(apl)]={
            "structure":{
                "total_nodes":tree["total_nodes"],"main_nodes":tree["main_nodes"],
                "component_sizes":tree["component_sizes"],"raw_roots":tree["raw_roots"],
                "main_root_id":tree["main_root_id"],"min_edge_m":tree["min_edge_m"],
                "max_edge_m":tree["max_edge_m"],"min_area_m2":tree["min_area_m2"],
                "max_area_m2":tree["max_area_m2"],"max_symmetry_error":tree["max_symmetry_error"],
            },
            "mapping":mapping,"pn_calyx_mapping":pnmap,"operator":sol,
        }
    classification="PASS_M3D_PASSIVE_OPERATOR_AND_GRID_LOCAL_DOMINANCE" if all_local else "PASS_M3D_PASSIVE_OPERATOR_LOCAL_DOMINANCE_NOT_ROBUST"
    report={
        "gate":"V6-M3D_SET_VALUED_3D_PASSIVE_APL_ELECTRICAL_OPERATOR",
        "classification":classification,
        "source_hashes":hashes,
        "kc_count":int(len(kc_ids)),"alpn_count":int(len(pn_ids)),
        "apl_kc_raw_rows":int(len(aplkc)),
        "q_interval_1_per_m":[Q_MIN,Q_MAX],
        "q_grid_count":len(Q_GRID),
        "primary_rois":list(PRIMARY),
        "reports":reports,
        "guardrails":{
            "amin_response_loaded":False,"amin_fitted_length_used":False,"v5_lambda50_used":False,
            "ra_rm_point_fit":False,"optical_bridge_used":False,"release_gain_used":False,
            "mnq_or_market_loaded":False,
        }
    }
    out=OUT/"v6_m3d_passive_electrical_operator.json"
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":classification,
        "source_hashes":hashes,
        "q_interval_1_per_m":[Q_MIN,Q_MAX],
        "q_grid_count":len(Q_GRID),
        "summary":{a:{
            "local_dominance_all_grid":r["operator"]["local_dominance_all_grid"],
            "worst_nonlocal":r["operator"]["worst_nonlocal"],
            "numerics":r["operator"]["numerics"],
            "pn_calyx_endpoints":[r["operator"]["pn_calyx_diagnostic"][0],r["operator"]["pn_calyx_diagnostic"][-1]],
        } for a,r in reports.items()},
        "guardrails":report["guardrails"],
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
