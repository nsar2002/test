from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.ipc as ipc
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

WORK=Path("v6_m3f0_work"); OUT=Path("v6_m3f0_out")
WORK.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)

EXPECTED={
    "brain":"cc9bd1ecd00bd703a6fa648bc6ad145c93c7c1ee53debdcc9ce0d1f4305e6aca",
    "syn":"959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07",
    "swc_10540":"22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f",
    "swc_10977":"34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf",
}
APL_IDS=(10540,10977)
VOXEL_M=8e-9
QMIN=0.40/2.64
QMAX=4.00/0.20
QGRID=np.exp(np.linspace(np.log(QMIN),np.log(QMAX),33))
GROUPS=("C","V","H")

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def group_from_roi(v):
    s="" if v is None else str(v)
    if s.startswith("CA("): return "C"
    if s.startswith("aL(") or s.startswith("a'L("): return "V"
    if s.startswith("bL(") or s.startswith("b'L(") or s.startswith("gL("): return "H"
    return None

def parse_tree(path):
    rows=[]
    for line in open(path):
        s=line.strip()
        if not s or s.startswith("#"): continue
        p=s.split()
        rows.append((int(p[0]),float(p[2]),float(p[3]),float(p[4]),float(p[5]),int(p[6])))
    ids=np.array([x[0] for x in rows],np.int64)
    xyz=np.array([[x[1],x[2],x[3]] for x in rows],float)
    rad=np.array([x[4] for x in rows],float)
    par=np.array([x[5] for x in rows],np.int64)
    imap={int(x):i for i,x in enumerate(ids)}
    rr=[];cc=[]
    for i,p in enumerate(par):
        j=imap.get(int(p))
        if j is not None:
            rr.extend([i,j]);cc.extend([j,i])
    G=sparse.csr_matrix((np.ones(len(rr),np.int8),(rr,cc)),shape=(len(ids),len(ids)))
    nc,lab=connected_components(G,directed=False,return_labels=True)
    sizes=np.bincount(lab,minlength=nc)
    wins=np.flatnonzero(sizes==sizes.max())
    if len(wins)!=1: raise RuntimeError("largest component not unique")
    ml=int(wins[0]); gidx=np.flatnonzero(lab==ml)
    gl2loc=np.full(len(ids),-1,np.int64); gl2loc[gidx]=np.arange(len(gidx))
    parent=np.full(len(gidx),-1,np.int64)
    for li,gi in enumerate(gidx):
        pj=imap.get(int(par[gi]))
        if pj is not None and lab[pj]==ml: parent[li]=gl2loc[pj]
    if np.sum(parent<0)!=1: raise RuntimeError("main component roots !=1")
    xyz_m=xyz[gidx]*VOXEL_M
    rad_m=rad[gidx]*VOXEL_M
    er=[];ec=[];ev=[]; area=np.zeros(len(gidx),float); edges=0
    for c,p in enumerate(parent):
        if p<0: continue
        p=int(p); L=float(np.linalg.norm(xyz_m[c]-xyz_m[p]))
        if L<=0: raise RuntimeError("nonpositive edge")
        r1=float(rad_m[p]); r2=float(rad_m[c])
        g0=math.pi*r1*r2/L
        er.extend([p,c,p,c]);ec.extend([p,c,c,p]);ev.extend([g0,g0,-g0,-g0])
        slant=math.sqrt(L*L+(r1-r2)*(r1-r2))
        A=math.pi*(r1+r2)*slant
        area[p]+=0.5*A;area[c]+=0.5*A;edges+=1
    if edges!=len(gidx)-1 or np.any(area<=0): raise RuntimeError("tree geometry failure")
    L0=sparse.coo_matrix((ev,(er,ec)),shape=(len(gidx),len(gidx))).tocsr()
    return {"ids":ids,"xyz_all":xyz,"labels":lab,"main_label":ml,"gidx":gidx,"gl2loc":gl2loc,
            "xyz_main":xyz[gidx],"L0":L0,"area":area,"component_sizes":[int(x) for x in sizes]}

def map_sites(tree,pts):
    kd=cKDTree(tree["xyz_all"])
    dist,gi=kd.query(np.asarray(pts,float),k=1,workers=-1)
    if not np.all(tree["labels"][gi]==tree["main_label"]):
        raise RuntimeError("site outside main component")
    li=tree["gl2loc"][gi]
    if np.any(li<0): raise RuntimeError("local mapping failure")
    return li.astype(np.int64),np.asarray(dist,float)

def load_kc_ids():
    b=np.load(WORK/"brain.npz",allow_pickle=False)
    ids=np.asarray(b["ids"],dtype=np.int64); ct=np.asarray(b["cell_type"]).astype(str)
    return np.sort(ids[np.char.startswith(ct,"KC")])

def extract_rows(kc_ids):
    source=pa.memory_map(str(WORK/"syn-partners.feather"),"r")
    rd=ipc.open_file(source); sc=rd.schema
    req=["body_pre","body_post","x_pre","y_pre","z_pre","x_post","y_post","z_post","primary_post"]
    for c in req:
        if sc.get_field_index(c)<0: raise RuntimeError(f"missing {c}")
    kcset=pa.array(kc_ids); aplset=pa.array(np.array(APL_IDS,np.int64))
    chunks=[]
    for bi in range(rd.num_record_batches):
        b=rd.get_batch(bi)
        pre=b.column(sc.get_field_index("body_pre")); post=b.column(sc.get_field_index("body_post"))
        pk=pc.is_in(pre,value_set=kcset); qk=pc.is_in(post,value_set=kcset)
        pa_=pc.is_in(pre,value_set=aplset); qa=pc.is_in(post,value_set=aplset)
        mask=pc.or_(pc.and_(pk,qa),pc.and_(pa_,qk))
        bb=b.filter(mask)
        if bb.num_rows: chunks.append(bb.select(req).to_pandas())
    d=pd.concat(chunks,ignore_index=True)
    if len(d)!=406552: raise RuntimeError(f"APL-KC row count {len(d)}")
    return d

def build_for_apl(tree,d,apl):
    rin=d[(d.body_post==apl)].copy()
    rout=d[(d.body_pre==apl)].copy()
    # All C/H/V anchors from both directions.
    anchor_xyz=[]; anchor_group=[]
    for df,cols in ((rin,["x_post","y_post","z_post"]),(rout,["x_pre","y_pre","z_pre"])):
        for _,r in df.iterrows():
            g=group_from_roi(r["primary_post"])
            if g is None: continue
            anchor_xyz.append([r[cols[0]],r[cols[1]],r[cols[2]]]); anchor_group.append(g)
    anchor_xyz=np.asarray(anchor_xyz,float)
    anchor_group=np.asarray(anchor_group,object)
    if len(anchor_xyz)==0: raise RuntimeError("no anchors")
    akd=cKDTree(anchor_xyz)
    k=min(8,len(anchor_xyz))
    dist,ix=akd.query(tree["xyz_main"],k=k,workers=-1)
    if k==1:
        dist=dist[:,None]; ix=ix[:,None]
    labels=np.empty(len(tree["xyz_main"]),object)
    ambiguous=np.zeros(len(labels),bool)
    nearest=np.asarray(dist[:,0],float)
    for i in range(len(labels)):
        d0=float(dist[i,0]); lab0=anchor_group[int(ix[i,0])]
        labels[i]=lab0
        for jj in range(1,k):
            if abs(float(dist[i,jj])-d0)<=1e-12 and anchor_group[int(ix[i,jj])]!=lab0:
                ambiguous[i]=True; break
    part={g:np.flatnonzero((labels==g)&(~ambiguous)) for g in GROUPS}
    counts={g:int(len(part[g])) for g in GROUPS}
    if any(v==0 for v in counts.values()): raise RuntimeError(f"empty partition {counts}")

    # Readout weights from raw APL->KC output sites.
    W=np.zeros((tree["L0"].shape[0],3),float)
    out_counts={}
    out_map_max={}
    for gi,g in enumerate(GROUPS):
        sub=rout[rout["primary_post"].map(group_from_roi).eq(g)]
        if len(sub)==0: raise RuntimeError(f"no output group {g}")
        nodes,md=map_sites(tree,sub[["x_pre","y_pre","z_pre"]].to_numpy(float))
        cnt=np.bincount(nodes,minlength=W.shape[0]).astype(float)
        W[:,gi]=cnt/cnt.sum()
        out_counts[g]=int(len(nodes)); out_map_max[g]=float(md.max())
    return {
        "partition_labels":labels,"ambiguous":ambiguous,"partition":part,
        "partition_counts":counts,
        "nearest_anchor_max_source_units":float(nearest.max()),
        "nearest_anchor_median_source_units":float(np.median(nearest)),
        "ambiguous_count":int(ambiguous.sum()),
        "W":W,"output_site_counts":out_counts,"output_map_max_source_units":out_map_max,
        "anchor_count":int(len(anchor_xyz)),
        "anchor_group_counts":{g:int(np.sum(anchor_group==g)) for g in GROUPS},
    }

def evaluate(tree,geo):
    idx={g:i for i,g in enumerate(GROUPS)}
    all_pass=True
    worst={g:{"min_local_minus_best_distant":float("inf"),"q":None,"node_local_index":None,"best_distant":None} for g in ("H","V")}
    violations={g:0 for g in ("H","V")}
    by_q=[]
    for q in QGRID:
        A=(tree["L0"]+sparse.diags(q*tree["area"],format="csr")).tocsc()
        lu=splu(A,permc_spec="COLAMD")
        phi=lu.solve(geo["W"])  # columns C,V,H
        rec={"q":float(q)}
        for g,others in (("H",("C","V")),("V",("C","H"))):
            nodes=geo["partition"][g]
            local=phi[nodes,idx[g]]
            o1=phi[nodes,idx[others[0]]]; o2=phi[nodes,idx[others[1]]]
            best=np.maximum(o1,o2)
            margin=local-best
            bad=margin<=0
            nbad=int(np.sum(bad)); violations[g]+=nbad
            if nbad: all_pass=False
            mi=int(np.argmin(margin)); m=float(margin[mi])
            which=others[0] if o1[mi]>=o2[mi] else others[1]
            if m<worst[g]["min_local_minus_best_distant"]:
                worst[g]={"min_local_minus_best_distant":m,"q":float(q),
                          "node_local_index":int(nodes[mi]),"best_distant":which,
                          "local_value":float(local[mi]),"best_distant_value":float(best[mi])}
            rec[g]={"min_margin":m,"violating_nodes":nbad,"source_nodes":int(len(nodes))}
        by_q.append(rec)
    return {"all_pointwise_pass":bool(all_pass),"violations_total":violations,"worst":worst,"by_q":by_q}

def main():
    for key,p in [("brain",WORK/"brain.npz"),("syn",WORK/"syn-partners.feather"),
                  ("swc_10540",WORK/"10540.swc"),("swc_10977",WORK/"10977.swc")]:
        got=sha256(p)
        if got!=EXPECTED[key]: raise RuntimeError(f"{key} hash {got}")
    kc=load_kc_ids()
    if len(kc)!=4064: raise RuntimeError(f"KC count {len(kc)}")
    d=extract_rows(kc)
    reps={}; pass_all=True
    for apl in APL_IDS:
        tree=parse_tree(WORK/f"{apl}.swc")
        geo=build_for_apl(tree,d,apl)
        ev=evaluate(tree,geo)
        eligible=(geo["ambiguous_count"]==0 and ev["all_pointwise_pass"])
        pass_all=pass_all and eligible
        reps[str(apl)]={
            "component_sizes":tree["component_sizes"],
            "anchor_count":geo["anchor_count"],
            "anchor_group_counts":geo["anchor_group_counts"],
            "partition_counts":geo["partition_counts"],
            "ambiguous_count":geo["ambiguous_count"],
            "nearest_anchor_max_source_units":geo["nearest_anchor_max_source_units"],
            "nearest_anchor_median_source_units":geo["nearest_anchor_median_source_units"],
            "output_site_counts":geo["output_site_counts"],
            "output_map_max_source_units":geo["output_map_max_source_units"],
            "evaluation":ev,
            "eligible":eligible,
        }
    cls="PASS_M3F0_HV_DIRECT_STIM_ORDINAL_PREDICTION_ELIGIBLE" if pass_all else "NO_ROBUST_M3F0_HV_DIRECT_STIM_ORDINAL_PREDICTION"
    report={
        "gate":"V6-M3F0_ROBUST_DIRECT_APL_STIM_ORDINAL_ELIGIBILITY",
        "classification":cls,
        "q_grid":[float(x) for x in QGRID],
        "region_aggregation":{"C":["CALYX"],"V":["ALPHA","ALPHA_PRIME"],"H":["BETA","BETA_PRIME","GAMMA"]},
        "reports":reps,
        "guardrails":{"amin_response_loaded":False,"amin_fitted_length_used":False,
                      "q_restricted":False,"optical_mapping_fit":False,"mnq_loaded":False},
    }
    (OUT/"v6_m3f0_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":cls,
        "summary":{k:{
            "eligible":v["eligible"],"ambiguous_count":v["ambiguous_count"],
            "partition_counts":v["partition_counts"],
            "violations_total":v["evaluation"]["violations_total"],
            "worst":v["evaluation"]["worst"],
        } for k,v in reps.items()},
        "guardrails":report["guardrails"],
    },indent=2,sort_keys=True))

if __name__=="__main__": main()
