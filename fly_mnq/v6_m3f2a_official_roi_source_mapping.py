from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.ipc as ipc
import requests
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from cloudvolume import CloudVolume

WORK=Path("v6_m3f2a_work"); OUT=Path("v6_m3f2a_out")
WORK.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)

BASE_HTTP="https://storage.googleapis.com/flyem-male-cns/rois/fullbrain-roi-v4"
BASE_CV="precomputed://gs://flyem-male-cns/rois/fullbrain-roi-v4"
EXPECTED={
    "brain":"cc9bd1ecd00bd703a6fa648bc6ad145c93c7c1ee53debdcc9ce0d1f4305e6aca",
    "syn":"959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07",
    "swc_10540":"22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f",
    "swc_10977":"34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf",
}
APL_IDS=(10540,10977)
VOXEL_NM=8.0

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def emit_blocked(classification,meta,reason):
    report={"gate":"V6-M3F2A_OFFICIAL_ROI_SOURCE_MAPPING","classification":classification,
            "reason":reason,"metadata":meta,
            "guardrails":{"amin_loaded":False,"electrical_transfer_loaded":False,
                          "nearest_synapse_roi_assignment":False,"mnq_loaded":False}}
    (OUT/"v6_m3f2a_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    raise SystemExit(0)

def fetch_metadata():
    r=requests.get(BASE_HTTP+"/info",timeout=60); r.raise_for_status()
    root_bytes=r.content; info=r.json()
    meta={"root_info_sha256":sha_bytes(root_bytes),"root_info":info}
    rel=info.get("segment_properties")
    if not rel:
        return meta,None,None
    if rel.startswith("gs://"):
        # Translate only the source-referenced GCS URL.
        m=re.match(r"gs://([^/]+)/(.+)",rel)
        sp_base=f"https://storage.googleapis.com/{m.group(1)}/{m.group(2)}"
    elif rel.startswith("http://") or rel.startswith("https://"):
        sp_base=rel.rstrip("/")
    else:
        sp_base=BASE_HTTP.rstrip("/")+"/"+rel.strip("/")
    rr=requests.get(sp_base+"/info",timeout=60); rr.raise_for_status()
    sp_bytes=rr.content; sp=rr.json()
    meta["segment_properties_ref"]=rel
    meta["segment_properties_info_url"]=sp_base+"/info"
    meta["segment_properties_info_sha256"]=sha_bytes(sp_bytes)
    return meta,sp,sp_bytes

def parse_label_map(sp):
    if not isinstance(sp,dict): return None
    inline=sp.get("inline")
    if not isinstance(inline,dict): return None
    ids=inline.get("ids")
    props=inline.get("properties")
    if not isinstance(ids,list) or not isinstance(props,list): return None
    label_props=[p for p in props if isinstance(p,dict) and p.get("type")=="label" and isinstance(p.get("values"),list)]
    if len(label_props)!=1: return None
    vals=label_props[0]["values"]
    if len(vals)!=len(ids): return None
    return {int(i):str(v) for i,v in zip(ids,vals)}

def semantic_group(name):
    if name is None: return None
    s=str(name).strip()
    u=s.upper().replace(" ","")
    # Same source-name semantics previously used for primary_post, plus spelled-out forms.
    if s.startswith("CA(") or u=="CA" or "CALYX" in u: return "C"
    if s.startswith("aL(") or s.startswith("a'L(") or "ALPHAPRIMELOBE" in u or "ALPHALOBE" in u: return "V"
    if s.startswith("bL(") or s.startswith("b'L(") or s.startswith("gL(") or "BETAPRIMELOBE" in u or "BETALOBE" in u or "GAMMALOBE" in u: return "H"
    return None

def parse_main(path):
    rows=[]
    for line in open(path):
        s=line.strip()
        if not s or s.startswith("#"): continue
        p=s.split()
        rows.append((int(p[0]),float(p[2]),float(p[3]),float(p[4]),int(p[6])))
    ids=np.array([r[0] for r in rows],np.int64)
    xyz=np.array([[r[1],r[2],r[3]] for r in rows],float)
    par=np.array([r[4] for r in rows],np.int64)
    imap={int(x):i for i,x in enumerate(ids)}
    rr=[];cc=[]
    for i,p in enumerate(par):
        j=imap.get(int(p))
        if j is not None: rr.extend([i,j]);cc.extend([j,i])
    G=sparse.csr_matrix((np.ones(len(rr),np.int8),(rr,cc)),shape=(len(ids),len(ids)))
    nc,lab=connected_components(G,directed=False,return_labels=True)
    sizes=np.bincount(lab,minlength=nc)
    wins=np.flatnonzero(sizes==sizes.max())
    if len(wins)!=1: raise RuntimeError("largest component not unique")
    ml=int(wins[0]); gidx=np.flatnonzero(lab==ml)
    return {"ids":ids[gidx],"xyz_source":xyz[gidx],"component_sizes":[int(x) for x in sizes]}

def physical_to_roi_vox(xyz_source,res_nm):
    nm=np.asarray(xyz_source,float)*VOXEL_NM
    return np.floor(nm/np.asarray(res_nm,float)).astype(np.int64)

def sample_labels(cv,pts,batch=20000):
    pts=np.asarray(pts,np.int64)
    lo=np.asarray(cv.bounds.minpt[:3],np.int64); hi=np.asarray(cv.bounds.maxpt[:3],np.int64)
    inside=np.all((pts>=lo)&(pts<hi),axis=1)
    labels=np.full(len(pts),-1,np.int64)
    if not np.all(inside):
        return labels,inside
    uniq,inv=np.unique(pts,axis=0,return_inverse=True)
    ulab=np.empty(len(uniq),np.int64)
    for a in range(0,len(uniq),batch):
        part=uniq[a:a+batch]
        keys=[tuple(map(int,x)) for x in part]
        got=cv.scattered_points(keys,mip=0)
        for j,k in enumerate(keys):
            ulab[a+j]=int(got[k])
    labels=ulab[inv]
    return labels,inside

def load_kc():
    b=np.load(WORK/"brain.npz",allow_pickle=False)
    ids=np.asarray(b["ids"],np.int64); ct=np.asarray(b["cell_type"]).astype(str)
    kc=np.sort(ids[np.char.startswith(ct,"KC")])
    if len(kc)!=4064: raise RuntimeError(f"KC count {len(kc)}")
    return kc

def extract_aplkc(kc):
    src=pa.memory_map(str(WORK/"syn-partners.feather"),"r")
    rd=ipc.open_file(src); sc=rd.schema
    req=["body_pre","body_post","x_pre","y_pre","z_pre","x_post","y_post","z_post","primary_post"]
    kcset=pa.array(kc); aplset=pa.array(np.array(APL_IDS,np.int64))
    chunks=[]
    for bi in range(rd.num_record_batches):
        b=rd.get_batch(bi)
        pre=b.column(sc.get_field_index("body_pre"));post=b.column(sc.get_field_index("body_post"))
        pk=pc.is_in(pre,value_set=kcset);qk=pc.is_in(post,value_set=kcset)
        pa_=pc.is_in(pre,value_set=aplset);qa=pc.is_in(post,value_set=aplset)
        mask=pc.or_(pc.and_(pk,qa),pc.and_(pa_,qk))
        bb=b.filter(mask)
        if bb.num_rows: chunks.append(bb.select(req).to_pandas())
    import pandas as pd
    d=pd.concat(chunks,ignore_index=True)
    if len(d)!=406552: raise RuntimeError(f"APL-KC rows {len(d)}")
    return d

def exact_name_counts(labels,labelmap):
    out={}
    for x in labels:
        name="BACKGROUND" if int(x)==0 else labelmap.get(int(x),f"UNMAPPED_ID_{int(x)}")
        out[name]=out.get(name,0)+1
    return dict(sorted(out.items(),key=lambda kv:(-kv[1],kv[0])))

def aggregate_counts(labels,labelmap):
    out={"C":0,"V":0,"H":0,"OUTSIDE":0}
    unknown_ids=set()
    for x in labels:
        xi=int(x)
        if xi==0: out["OUTSIDE"]+=1; continue
        name=labelmap.get(xi)
        if name is None:
            unknown_ids.add(xi);out["OUTSIDE"]+=1;continue
        g=semantic_group(name)
        out[g if g else "OUTSIDE"]+=1
    return out,sorted(map(int,unknown_ids))

def main():
    for k,p in [("brain",WORK/"brain.npz"),("syn",WORK/"syn-partners.feather"),
                ("swc_10540",WORK/"10540.swc"),("swc_10977",WORK/"10977.swc")]:
        got=sha_file(p)
        if got!=EXPECTED[k]: raise RuntimeError(f"{k} hash mismatch {got}")

    meta,sp,_=fetch_metadata()
    labelmap=parse_label_map(sp)
    if labelmap is None:
        emit_blocked("BLOCKED_M3F2A_ROI_LABEL_METADATA",meta,"No unique official inline label property resolved from source-referenced segment_properties metadata")

    name_to_group={name:semantic_group(name) for _,name in sorted(labelmap.items()) if semantic_group(name) is not None}
    meta["resolved_label_count"]=len(labelmap)
    meta["resolved_cvh_label_mapping"]=name_to_group
    if not any(v=="C" for v in name_to_group.values()) or not any(v=="V" for v in name_to_group.values()) or not any(v=="H" for v in name_to_group.values()):
        emit_blocked("BLOCKED_M3F2A_ROI_LABEL_METADATA",meta,"Official label metadata did not expose all C/V/H groups under frozen name semantics")

    cv=CloudVolume(BASE_CV,use_https=True,bounded=True,fill_missing=False,progress=False,mip=0)
    res=[float(x) for x in cv.resolution]
    meta["cloudvolume_resolution_nm"]=res
    meta["cloudvolume_voxel_offset"]=[int(x) for x in cv.bounds.minpt[:3]]
    meta["cloudvolume_maxpt"]=[int(x) for x in cv.bounds.maxpt[:3]]
    if not np.allclose(res,[256,256,256],rtol=0,atol=0):
        emit_blocked("FAIL_M3F2A_ROI_VOLUME_METADATA",meta,f"Unexpected ROI resolution {res}")

    node_reports={}
    overall_pass=True
    trees={}
    for apl in APL_IDS:
        tree=parse_main(WORK/f"{apl}.swc"); trees[apl]=tree
        vox=physical_to_roi_vox(tree["xyz_source"],res)
        lab,inside=sample_labels(cv,vox)
        if not np.all(inside):
            overall_pass=False
        counts,unknown=aggregate_counts(lab[inside],labelmap)
        if unknown: overall_pass=False
        enough=all(counts[g]>=100 for g in ("C","V","H"))
        overall_pass=overall_pass and enough
        node_reports[str(apl)]={
            "main_nodes":int(len(vox)),"component_sizes":tree["component_sizes"],
            "in_bounds":int(np.sum(inside)),"out_of_bounds":int(np.sum(~inside)),
            "exact_source_label_counts":exact_name_counts(lab[inside],labelmap),
            "aggregate_counts":counts,
            "aggregate_fractions":{k:float(v/len(vox)) for k,v in counts.items()},
            "unmapped_nonzero_label_ids":unknown,
            "minimum_group_count_requirement_pass":bool(enough),
        }

    kc=load_kc(); d=extract_aplkc(kc)
    syn_reports={}
    for apl in APL_IDS:
        dd=d[(d.body_pre==apl)|(d.body_post==apl)].copy()
        pts=[]; expected=[]
        for _,r in dd.iterrows():
            pg=semantic_group(r["primary_post"])
            if pg is None: continue
            if int(r["body_post"])==apl:
                pts.append([r["x_post"],r["y_post"],r["z_post"]])
            else:
                pts.append([r["x_pre"],r["y_pre"],r["z_pre"]])
            expected.append(pg)
        vox=physical_to_roi_vox(np.asarray(pts,float),res)
        lab,inside=sample_labels(cv,vox)
        confusion={g:{h:0 for h in ("C","V","H","OUTSIDE")} for g in ("C","V","H")}
        agree=0; total=0; unmapped=set()
        for ok,l,e in zip(inside,lab,expected):
            if not ok:
                g="OUTSIDE"
            elif int(l)==0:
                g="OUTSIDE"
            else:
                nm=labelmap.get(int(l))
                if nm is None:
                    unmapped.add(int(l));g="OUTSIDE"
                else:
                    g=semantic_group(nm) or "OUTSIDE"
            confusion[e][g]+=1
            total+=1; agree+=int(g==e)
        syn_reports[str(apl)]={
            "semantic_raw_sites":total,"in_bounds":int(np.sum(inside)),
            "exact_group_agreement":agree,
            "agreement_fraction":float(agree/total) if total else None,
            "confusion":confusion,"unmapped_nonzero_label_ids":sorted(unmapped),
        }

    cls="PASS_M3F2A_OFFICIAL_ROI_SOURCE_MAPPING" if overall_pass else "FAIL_M3F2A_OFFICIAL_ROI_SOURCE_MAPPING"
    report={
        "gate":"V6-M3F2A_OFFICIAL_ROI_SOURCE_MAPPING","classification":cls,
        "source_hashes":{k:sha_file(p) for k,p in [
            ("brain",WORK/"brain.npz"),("syn",WORK/"syn-partners.feather"),
            ("swc_10540",WORK/"10540.swc"),("swc_10977",WORK/"10977.swc")]},
        "metadata":meta,"node_reports":node_reports,"synapse_consistency_diagnostic":syn_reports,
        "guardrails":{"amin_loaded":False,"electrical_transfer_loaded":False,
                      "nearest_synapse_roi_assignment":False,"q_selected":False,"mnq_loaded":False},
    }
    (OUT/"v6_m3f2a_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":cls,"metadata":meta,
        "node_summary":{k:{"aggregate_counts":v["aggregate_counts"],"out_of_bounds":v["out_of_bounds"],
                           "minimum_group_count_requirement_pass":v["minimum_group_count_requirement_pass"]}
                        for k,v in node_reports.items()},
        "synapse_consistency_diagnostic":syn_reports,
        "guardrails":report["guardrails"],
    },indent=2,sort_keys=True))

if __name__=="__main__": main()
