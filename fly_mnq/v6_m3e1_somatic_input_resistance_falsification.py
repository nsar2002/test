from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.feather as feather
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

WORK=Path("v6_m3e1_work")
OUT=Path("v6_m3e1_out")
WORK.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

EXPECTED_ANN="2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
EXPECTED_SWC={
  10540:"22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f",
  10977:"34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf",
}
EXPECTED_SOMA_NODE={10540:12,10977:10}
VOXEL_M=8e-9
EMP=(0.0809216,0.1987428)
RA=(0.40,4.00)
RM=(0.20,2.64)

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
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

def build_tree(path:Path):
    rows=[]
    with path.open() as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith("#"): continue
            p=s.split()
            if len(p)<7: raise RuntimeError(f"{path.name}: malformed SWC row")
            rows.append((int(p[0]),float(p[2]),float(p[3]),float(p[4]),float(p[5]),int(p[6])))
    ids=np.array([r[0] for r in rows],np.int64)
    xyz_source=np.array([[r[1],r[2],r[3]] for r in rows],float)
    rad_source=np.array([r[4] for r in rows],float)
    parent_ids=np.array([r[5] for r in rows],np.int64)
    if len(np.unique(ids))!=len(ids): raise RuntimeError("duplicate SWC node ids")
    if not np.isfinite(xyz_source).all() or not np.isfinite(rad_source).all() or np.any(rad_source<=0):
        raise RuntimeError("invalid SWC geometry")

    imap={int(x):i for i,x in enumerate(ids)}
    rr=[]; cc=[]
    for i,p in enumerate(parent_ids):
        j=imap.get(int(p))
        if j is not None:
            rr.extend((i,j)); cc.extend((j,i))
    G=sparse.csr_matrix((np.ones(len(rr),np.int8),(rr,cc)),shape=(len(ids),len(ids)))
    nc,labels=connected_components(G,directed=False,return_labels=True)
    sizes=np.bincount(labels,minlength=nc)
    winners=np.flatnonzero(sizes==sizes.max())
    if len(winners)!=1: raise RuntimeError("largest component not unique")
    mainlab=int(winners[0])
    gidx=np.flatnonzero(labels==mainlab)
    glob2loc=np.full(len(ids),-1,np.int64)
    glob2loc[gidx]=np.arange(len(gidx),dtype=np.int64)

    parent=np.full(len(gidx),-1,np.int64)
    for li,gi in enumerate(gidx):
        pj=imap.get(int(parent_ids[gi]))
        if pj is not None and labels[pj]==mainlab:
            parent[li]=glob2loc[pj]
    roots=np.flatnonzero(parent<0)
    if len(roots)!=1: raise RuntimeError(f"main component roots={len(roots)}")

    xyz=xyz_source[gidx]*VOXEL_M
    rad=rad_source[gidx]*VOXEL_M
    row=[]; col=[]; dat=[]
    node_area=np.zeros(len(gidx),float)
    edge_count=0
    for child,p in enumerate(parent):
        if p<0: continue
        p=int(p)
        L=float(np.linalg.norm(xyz[child]-xyz[p]))
        if not np.isfinite(L) or L<=0: raise RuntimeError("invalid edge length")
        r1=float(rad[p]); r2=float(rad[child])
        g0=math.pi*r1*r2/L
        row.extend((p,child,p,child))
        col.extend((p,child,child,p))
        dat.extend((g0,g0,-g0,-g0))
        slant=math.sqrt(L*L+(r1-r2)*(r1-r2))
        area=math.pi*(r1+r2)*slant
        node_area[p]+=0.5*area
        node_area[child]+=0.5*area
        edge_count+=1
    if edge_count!=len(gidx)-1: raise RuntimeError("main component not a tree")
    if np.any(node_area<=0) or not np.isfinite(node_area).all(): raise RuntimeError("invalid membrane area")
    L0=sparse.coo_matrix((dat,(row,col)),shape=(len(gidx),len(gidx))).tocsr()
    return {
      "ids_all":ids,"xyz_source":xyz_source,"labels":labels,"mainlab":mainlab,
      "gidx":gidx,"glob2loc":glob2loc,"L0":L0,"node_area":node_area,
      "component_sizes":[int(x) for x in sizes],
      "main_nodes":int(len(gidx)),"total_nodes":int(len(ids)),
    }

def reconstruct_soma(ann:pd.DataFrame,tree,body:int):
    rows=ann[ann.bodyId.astype("int64")==body]
    if len(rows)!=1: raise RuntimeError(f"{body}: annotation row count {len(rows)}")
    loc=parse_loc(rows.iloc[0]["somaLocation"])
    if loc is None: raise RuntimeError(f"{body}: invalid somaLocation")
    dist,gi=cKDTree(tree["xyz_source"]).query(loc,k=1)
    gi=int(gi)
    if tree["labels"][gi]!=tree["mainlab"]:
        raise RuntimeError(f"{body}: soma nearest node outside main component")
    node_id=int(tree["ids_all"][gi])
    if node_id!=EXPECTED_SOMA_NODE[body]:
        raise RuntimeError(f"{body}: soma node parity {node_id} != {EXPECTED_SOMA_NODE[body]}")
    li=int(tree["glob2loc"][gi])
    if li<0: raise RuntimeError("invalid local soma index")
    return {
      "loc":[float(x) for x in loc],
      "nearest_node_id":node_id,
      "distance_source_units":float(dist),
      "distance_um":float(dist*0.008),
      "local_index":li
    }

def solve_rin(tree,soma_li:int,ra:float,rm:float):
    A=((1.0/ra)*tree["L0"] + sparse.diags(tree["node_area"]/rm,format="csr")).tocsc()
    rhs=np.zeros(tree["main_nodes"],float)
    rhs[soma_li]=1.0
    lu=splu(A,permc_spec="COLAMD")
    V=lu.solve(rhs)
    resid=A@V-rhs
    max_resid=float(np.max(np.abs(resid)))
    v=float(V[soma_li])
    if not np.isfinite(v) or v<=0: raise RuntimeError("nonpositive/nonfinite Rin")
    return {
      "Ra_ohm_m":float(ra),"Rm_ohm_m2":float(rm),
      "Rin_ohm":v,"Rin_GOhm":v/1e9,
      "max_abs_linear_residual_A":max_resid,
      "min_voltage_V_per_A":float(np.min(V)),
      "max_voltage_V_per_A":float(np.max(V))
    }

def overlap(a,b):
    return max(a[0],b[0]) <= min(a[1],b[1])

def main():
    annp=WORK/"body-annotations.feather"
    if sha256(annp)!=EXPECTED_ANN: raise RuntimeError("annotation hash mismatch")
    ann=feather.read_table(annp).to_pandas()
    need={"bodyId","somaLocation","flywireType"}
    if not need.issubset(ann.columns): raise RuntimeError(f"annotation schema missing {need-set(ann.columns)}")

    reports={}
    all_overlap=True
    source_hashes={"annotations":sha256(annp)}
    for body in (10540,10977):
        swcp=WORK/f"{body}.swc"
        got=sha256(swcp); source_hashes[f"swc_{body}"]=got
        if got!=EXPECTED_SWC[body]: raise RuntimeError(f"{body}: swc hash mismatch")
        tree=build_tree(swcp)
        soma=reconstruct_soma(ann,tree,body)
        corners={}
        for ra in RA:
            for rm in RM:
                key=f"Ra={ra:.2f}|Rm={rm:.2f}"
                corners[key]=solve_rin(tree,soma["local_index"],ra,rm)
        rmin=corners[f"Ra={RA[0]:.2f}|Rm={RM[0]:.2f}"]["Rin_GOhm"]
        rmax=corners[f"Ra={RA[1]:.2f}|Rm={RM[1]:.2f}"]["Rin_GOhm"]
        allvals=[x["Rin_GOhm"] for x in corners.values()]
        tol=1e-12*max(1.0,rmax)
        mono=(rmin <= min(allvals)+tol and rmax >= max(allvals)-tol and
              corners[f"Ra={RA[0]:.2f}|Rm={RM[1]:.2f}"]["Rin_GOhm"] >= rmin-tol and
              corners[f"Ra={RA[1]:.2f}|Rm={RM[0]:.2f}"]["Rin_GOhm"] >= rmin-tol and
              corners[f"Ra={RA[0]:.2f}|Rm={RM[1]:.2f}"]["Rin_GOhm"] <= rmax+tol and
              corners[f"Ra={RA[1]:.2f}|Rm={RM[0]:.2f}"]["Rin_GOhm"] <= rmax+tol)
        if not mono: raise RuntimeError(f"{body}: corner monotonicity parity failed")
        model=(float(rmin),float(rmax))
        ov=overlap(model,EMP)
        all_overlap=all_overlap and ov
        reports[str(body)]={
          "structure":{"total_nodes":tree["total_nodes"],"main_nodes":tree["main_nodes"],"component_sizes":tree["component_sizes"]},
          "soma_mapping":soma,
          "corners":corners,
          "continuous_model_interval_GOhm":[model[0],model[1]],
          "experimental_interval_GOhm":[EMP[0],EMP[1]],
          "overlap":bool(ov),
          "overlap_interval_GOhm":[max(model[0],EMP[0]),min(model[1],EMP[1])] if ov else None,
          "monotonicity_basis":"Rayleigh monotonicity; corners evaluated for implementation parity"
        }
    cls="PASS_M3E1_GROSS_INPUT_RESISTANCE_COMPATIBILITY" if all_overlap else "FAIL_M3E1_CURRENT_PASSIVE_MORPHOLOGY_GROSSLY_INCOMPATIBLE"
    report={
      "gate":"V6-M3E1_CROSS_SEX_SOMATIC_INPUT_RESISTANCE_GROSS_FALSIFICATION",
      "classification":cls,
      "source_hashes":source_hashes,
      "experimental_source":{
        "workbook_sha256":"419644f8806d4189b032cdcc578320904c3c666770fae680ef126c4d511349b7",
        "n_NS":20,
        "workbook_Rin_GOhm":{"min":0.0809216,"q25":0.1148641,"median":0.1264146,"q75":0.13307865,"max":0.1987428},
        "raw_D4_reextraction_GOhm":{"min":0.07712698129507203,"max":0.1958723097581131},
        "unit_note":"Workbook displayed 80-199-style numerics are MOhm-scale; canonical D4 normalized /1000 to GOhm."
      },
      "frozen_passive_rectangle":{"Ra_ohm_m":[RA[0],RA[1]],"Rm_ohm_m2":[RM[0],RM[1]]},
      "reports":reports,
      "guardrails":{
        "ra_rm_fit":False,
        "envelope_truncated_from_overlap":False,
        "m3d_locality_crossing_used":False,
        "invented_soma_area":False,
        "amin_loaded":False,
        "mnq_loaded":False
      }
    }
    (OUT/"v6_m3e1_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
