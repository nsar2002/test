from __future__ import annotations
import csv, hashlib, json, math
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu

WORK=Path("v6_m3e1_work"); OUT=Path("v6_m3e1_out")
WORK.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)

EXPECTED_SWC={
  10540:"22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f",
  10977:"34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf",
}
SOMA_NODE={10540:12,10977:10}
SOURCE_WORKBOOK_SHA="419644f8806d4189b032cdcc578320904c3c666770fae680ef126c4d511349b7"
RA_RANGE=(0.40,4.00)
RM_RANGE=(0.20,2.64)
VOXEL_M=8e-9

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def load_obs(path:Path):
    rows=list(csv.DictReader(path.open()))
    if len(rows)!=20: raise RuntimeError(f"expected 20 NS rows, got {len(rows)}")
    vals=[]
    parity=[]
    cells=[]
    for r in rows:
        if r["state"]!="NS": raise RuntimeError("non-NS row")
        if r["source_workbook_sha256"]!=SOURCE_WORKBOOK_SHA: raise RuntimeError("source workbook hash tag mismatch")
        dv=float(r["dV_mV_at_minus50pA"])
        calc=abs(dv)*1e-3/(50e-12)/1e6
        stored=float(r["derived_Rin_MOhm"])
        wb=float(r["workbook_Rin_numeric"])
        vals.append(calc); parity.append(max(abs(calc-stored),abs(calc-wb))); cells.append(r["cell"])
    vals=np.array(vals,float)
    if not np.all(np.isfinite(vals)) or np.any(vals<=0): raise RuntimeError("invalid observed resistance")
    if max(parity)>1e-9: raise RuntimeError(f"source parity mismatch {max(parity)}")
    return {
        "cells":cells,
        "values_MOhm":[float(x) for x in vals],
        "min_MOhm":float(vals.min()),
        "max_MOhm":float(vals.max()),
        "median_MOhm":float(np.median(vals)),
        "q25_MOhm":float(np.quantile(vals,0.25)),
        "q75_MOhm":float(np.quantile(vals,0.75)),
        "max_parity_abs_MOhm":float(max(parity)),
    }

def parse_tree(path:Path):
    rows=[]
    with path.open() as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith("#"): continue
            p=s.split()
            if len(p)<7: raise RuntimeError("malformed SWC")
            rows.append((int(p[0]),float(p[2]),float(p[3]),float(p[4]),float(p[5]),int(p[6])))
    ids=np.array([r[0] for r in rows],np.int64)
    xyz=np.array([[r[1],r[2],r[3]] for r in rows],float)
    rad=np.array([r[4] for r in rows],float)
    par=np.array([r[5] for r in rows],np.int64)
    if len(np.unique(ids))!=len(ids): raise RuntimeError("duplicate SWC ids")
    if not np.isfinite(xyz).all() or not np.isfinite(rad).all() or np.any(rad<=0): raise RuntimeError("invalid SWC geometry")
    imap={int(x):i for i,x in enumerate(ids)}
    rr=[];cc=[]
    for i,p in enumerate(par):
        j=imap.get(int(p))
        if j is not None:
            rr.extend([i,j]);cc.extend([j,i])
    G=sparse.csr_matrix((np.ones(len(rr),np.int8),(rr,cc)),shape=(len(ids),len(ids)))
    nc,lab=connected_components(G,directed=False,return_labels=True)
    sizes=np.bincount(lab,minlength=nc)
    win=np.flatnonzero(sizes==sizes.max())
    if len(win)!=1: raise RuntimeError("largest component not unique")
    ml=int(win[0]); gidx=np.flatnonzero(lab==ml)
    gl_to_local=np.full(len(ids),-1,np.int64); gl_to_local[gidx]=np.arange(len(gidx))
    parent_local=np.full(len(gidx),-1,np.int64)
    for li,gi in enumerate(gidx):
        pj=imap.get(int(par[gi]))
        if pj is not None and lab[pj]==ml: parent_local[li]=gl_to_local[pj]
    if np.sum(parent_local<0)!=1: raise RuntimeError("main component not single-root tree")
    xyz_m=xyz[gidx]*VOXEL_M
    rad_m=rad[gidx]*VOXEL_M

    # Geometry basis exactly matching M3D: axial g0 / Ra, lateral membrane area / Rm.
    er=[];ec=[];ev=[]
    area=np.zeros(len(gidx),float)
    edges=0
    for child,p in enumerate(parent_local):
        if p<0: continue
        p=int(p); L=float(np.linalg.norm(xyz_m[child]-xyz_m[p]))
        if L<=0 or not np.isfinite(L): raise RuntimeError("invalid edge length")
        r1=float(rad_m[p]); r2=float(rad_m[child])
        g0=math.pi*r1*r2/L
        er.extend([p,child,p,child]); ec.extend([p,child,child,p]); ev.extend([g0,g0,-g0,-g0])
        slant=math.sqrt(L*L+(r1-r2)*(r1-r2))
        A=math.pi*(r1+r2)*slant
        area[p]+=0.5*A; area[child]+=0.5*A
        edges+=1
    if edges!=len(gidx)-1: raise RuntimeError("tree edge mismatch")
    if np.any(area<=0): raise RuntimeError("nonpositive membrane area")
    L0=sparse.coo_matrix((ev,(er,ec)),shape=(len(gidx),len(gidx))).tocsr()

    return {"ids":ids,"gidx":gidx,"glob_to_local":gl_to_local,"L0":L0,"area":area,
            "component_sizes":[int(x) for x in sizes],"main_label":ml}

def rin_for(tree,soma_node,Ra,Rm):
    ids=tree["ids"]
    hit=np.flatnonzero(ids==int(soma_node))
    if len(hit)!=1: raise RuntimeError(f"soma node {soma_node} absent")
    gi=int(hit[0]); li=int(tree["glob_to_local"][gi])
    if li<0: raise RuntimeError("soma node not on historical main component")
    A=((1.0/Ra)*tree["L0"] + sparse.diags(tree["area"]/Rm,format="csr")).tocsc()
    lu=splu(A,permc_spec="COLAMD")
    b=np.zeros(A.shape[0],float); b[li]=1.0
    v=lu.solve(b)
    resid=float(np.max(np.abs(A@v-b)))
    if resid>1e-8: raise RuntimeError(f"solve residual {resid}")
    R=float(v[li])
    if not np.isfinite(R) or R<=0: raise RuntimeError("invalid Rin")
    return R,resid,li

def main():
    obs=load_obs(Path("research/sources/v6_m3e1_female_ns_rin_snapshot.csv"))
    reports={}
    all_overlap=True
    for body in (10540,10977):
        p=WORK/f"{body}.swc"
        got=sha256(p)
        if got!=EXPECTED_SWC[body]: raise RuntimeError(f"{body} SWC hash mismatch")
        tree=parse_tree(p)
        corners=[]
        for Ra in RA_RANGE:
            for Rm in RM_RANGE:
                R,resid,li=rin_for(tree,SOMA_NODE[body],Ra,Rm)
                corners.append({"Ra_Ohm_m":Ra,"Rm_Ohm_m2":Rm,"Rin_Ohm":R,"Rin_MOhm":R/1e6,"residual":resid})
        # Rayleigh extrema must be the lower/lower and upper/upper corners.
        low=next(x for x in corners if x["Ra_Ohm_m"]==RA_RANGE[0] and x["Rm_Ohm_m2"]==RM_RANGE[0])
        high=next(x for x in corners if x["Ra_Ohm_m"]==RA_RANGE[1] and x["Rm_Ohm_m2"]==RM_RANGE[1])
        numeric_min=min(x["Rin_MOhm"] for x in corners)
        numeric_max=max(x["Rin_MOhm"] for x in corners)
        if abs(low["Rin_MOhm"]-numeric_min)>1e-9 or abs(high["Rin_MOhm"]-numeric_max)>1e-9:
            raise RuntimeError("corner monotonicity diagnostic failed")
        overlap=max(low["Rin_MOhm"],obs["min_MOhm"]) <= min(high["Rin_MOhm"],obs["max_MOhm"])
        all_overlap=all_overlap and overlap
        reports[str(body)]={
            "soma_node_id":SOMA_NODE[body],
            "component_sizes":tree["component_sizes"],
            "corners":corners,
            "model_interval_MOhm":[low["Rin_MOhm"],high["Rin_MOhm"]],
            "female_empirical_hull_MOhm":[obs["min_MOhm"],obs["max_MOhm"]],
            "nonempty_intersection":bool(overlap),
            "intersection_MOhm":None if not overlap else [max(low["Rin_MOhm"],obs["min_MOhm"]),min(high["Rin_MOhm"],obs["max_MOhm"])],
        }
    cls="PASS_M3E1_CROSS_SEX_RIN_NOT_FALSIFIED" if all_overlap else "FAIL_M3E1_CROSS_SEX_RIN_INCOMPATIBLE"
    report={
        "gate":"V6-M3E1_CROSS_SEX_SOMATIC_INPUT_RESISTANCE_FALSIFICATION",
        "classification":cls,
        "physiology":obs,
        "model_reports":reports,
        "frozen_passive_rectangle":{"Ra_Ohm_m":list(RA_RANGE),"Rm_Ohm_m2":list(RM_RANGE)},
        "interpretation":{
            "calibration_allowed":False,
            "ra_rm_truncation_allowed":False,
            "cross_sex_equivalence_claimed":False,
            "known_m3d_locality_crossing_used":False,
        },
        "guardrails":{"amin_loaded":False,"optical_bridge_used":False,"mnq_loaded":False},
    }
    (OUT/"v6_m3e1_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
