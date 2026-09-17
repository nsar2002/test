from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.ipc as ipc
import requests
from cloudvolume import CloudVolume
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

WORK=Path("v6_m3f2b_work"); OUT=Path("v6_m3f2b_out")
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
QGRID=np.exp(np.linspace(np.log(0.40/2.64),np.log(4.00/0.20),33))
GROUPS=("C","V","H")

def sha_file(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(8<<20),b""): h.update(b)
 return h.hexdigest()

def semantic_group(name):
 if name is None:return None
 s=str(name).strip(); u=s.upper().replace(" ","")
 if s.startswith("CA(") or u=="CA" or "CALYX" in u:return "C"
 if s.startswith("aL(") or s.startswith("a'L(") or "ALPHAPRIMELOBE" in u or "ALPHALOBE" in u:return "V"
 if s.startswith("bL(") or s.startswith("b'L(") or s.startswith("gL(") or "BETAPRIMELOBE" in u or "BETALOBE" in u or "GAMMALOBE" in u:return "H"
 return None

def fetch_labelmap():
 r=requests.get(BASE_HTTP+"/info",timeout=60);r.raise_for_status();info=r.json()
 rel=info.get("segment_properties")
 if not rel:raise RuntimeError("official ROI metadata missing segment_properties")
 if rel.startswith("gs://"):
  m=re.match(r"gs://([^/]+)/(.+)",rel);base=f"https://storage.googleapis.com/{m.group(1)}/{m.group(2)}"
 elif rel.startswith("http"):base=rel.rstrip("/")
 else:base=BASE_HTTP.rstrip("/")+"/"+rel.strip("/")
 rr=requests.get(base+"/info",timeout=60);rr.raise_for_status();sp=rr.json()
 inline=sp.get("inline",{});ids=inline.get("ids",[]);props=inline.get("properties",[])
 lp=[p for p in props if p.get("type")=="label" and isinstance(p.get("values"),list)]
 if len(lp)!=1 or len(lp[0]["values"])!=len(ids):raise RuntimeError("official ROI label property unresolved")
 return {int(i):str(v) for i,v in zip(ids,lp[0]["values"])}

def parse_tree(path):
 rows=[]
 for line in open(path):
  s=line.strip()
  if not s or s.startswith("#"):continue
  p=s.split();rows.append((int(p[0]),float(p[2]),float(p[3]),float(p[4]),float(p[5]),int(p[6])))
 ids=np.array([r[0] for r in rows],np.int64); xyz=np.array([[r[1],r[2],r[3]] for r in rows],float)
 rad=np.array([r[4] for r in rows],float); par=np.array([r[5] for r in rows],np.int64)
 im={int(x):i for i,x in enumerate(ids)}; rr=[];cc=[]
 for i,p in enumerate(par):
  j=im.get(int(p))
  if j is not None:rr.extend([i,j]);cc.extend([j,i])
 G=sparse.csr_matrix((np.ones(len(rr),np.int8),(rr,cc)),shape=(len(ids),len(ids)))
 nc,lab=connected_components(G,directed=False,return_labels=True);sizes=np.bincount(lab,minlength=nc)
 win=np.flatnonzero(sizes==sizes.max())
 if len(win)!=1:raise RuntimeError("largest component not unique")
 ml=int(win[0]);gidx=np.flatnonzero(lab==ml);gl2loc=np.full(len(ids),-1,np.int64);gl2loc[gidx]=np.arange(len(gidx))
 parent=np.full(len(gidx),-1,np.int64)
 for li,gi in enumerate(gidx):
  pj=im.get(int(par[gi]))
  if pj is not None and lab[pj]==ml:parent[li]=gl2loc[pj]
 if np.sum(parent<0)!=1:raise RuntimeError("main component not one rooted tree")
 xyz_m=xyz[gidx]*8e-9;rad_m=rad[gidx]*8e-9
 er=[];ec=[];ev=[];area=np.zeros(len(gidx),float)
 for c,p in enumerate(parent):
  if p<0:continue
  p=int(p);L=float(np.linalg.norm(xyz_m[c]-xyz_m[p]));r1=float(rad_m[p]);r2=float(rad_m[c])
  if L<=0 or r1<=0 or r2<=0:raise RuntimeError("invalid geometry")
  g0=math.pi*r1*r2/L
  er.extend([p,c,p,c]);ec.extend([p,c,c,p]);ev.extend([g0,g0,-g0,-g0])
  sl=math.sqrt(L*L+(r1-r2)**2);A=math.pi*(r1+r2)*sl;area[p]+=A/2;area[c]+=A/2
 L0=sparse.coo_matrix((ev,(er,ec)),shape=(len(gidx),len(gidx))).tocsr()
 return {"ids_all":ids,"xyz_all":xyz,"labels":lab,"main_label":ml,"gidx":gidx,"gl2loc":gl2loc,
         "ids_main":ids[gidx],"xyz_main":xyz[gidx],"L0":L0,"area":area,
         "component_sizes":[int(x) for x in sizes]}

def sample_labels(cv,pts):
 pts=np.asarray(pts,np.int64);lo=np.asarray(cv.bounds.minpt[:3],np.int64);hi=np.asarray(cv.bounds.maxpt[:3],np.int64)
 if not np.all(np.all((pts>=lo)&(pts<hi),axis=1)):raise RuntimeError("official ROI lookup out of bounds")
 uniq,inv=np.unique(pts,axis=0,return_inverse=True);out=np.empty(len(uniq),np.int64)
 for a in range(0,len(uniq),20000):
  p=uniq[a:a+20000];keys=[tuple(map(int,x)) for x in p];got=cv.scattered_points(keys,mip=0)
  for j,k in enumerate(keys):out[a+j]=int(got[k])
 return out[inv]

def load_kc():
 b=np.load(WORK/"brain.npz",allow_pickle=False);ids=np.asarray(b["ids"],np.int64);ct=np.asarray(b["cell_type"]).astype(str)
 kc=np.sort(ids[np.char.startswith(ct,"KC")])
 if len(kc)!=4064:raise RuntimeError("KC count")
 return kc

def extract(kc):
 src=pa.memory_map(str(WORK/"syn-partners.feather"),"r");rd=ipc.open_file(src);sc=rd.schema
 req=["body_pre","body_post","x_pre","y_pre","z_pre","x_post","y_post","z_post","primary_post"]
 kcset=pa.array(kc);aplset=pa.array(np.array(APL_IDS,np.int64));chunks=[]
 for bi in range(rd.num_record_batches):
  b=rd.get_batch(bi);pre=b.column(sc.get_field_index("body_pre"));post=b.column(sc.get_field_index("body_post"))
  mask=pc.or_(pc.and_(pc.is_in(pre,value_set=kcset),pc.is_in(post,value_set=aplset)),
              pc.and_(pc.is_in(pre,value_set=aplset),pc.is_in(post,value_set=kcset)))
  bb=b.filter(mask)
  if bb.num_rows:chunks.append(bb.select(req).to_pandas())
 d=pd.concat(chunks,ignore_index=True)
 if len(d)!=406552:raise RuntimeError(f"raw rows {len(d)}")
 return d

def map_output(tree,pts):
 kd=cKDTree(tree["xyz_all"]);_,gi=kd.query(np.asarray(pts,float),k=1,workers=-1)
 if not np.all(tree["labels"][gi]==tree["main_label"]):raise RuntimeError("output site outside main component")
 li=tree["gl2loc"][gi]
 if np.any(li<0):raise RuntimeError("output mapping")
 return li

def output_weights(tree,d,apl):
 rout=d[d.body_pre==apl].copy();W=np.zeros((len(tree["gidx"]),3),float);counts={}
 for j,g in enumerate(GROUPS):
  sub=rout[rout["primary_post"].map(semantic_group).eq(g)]
  if len(sub)==0:raise RuntimeError(f"empty output {g}")
  li=map_output(tree,sub[["x_pre","y_pre","z_pre"]].to_numpy(float))
  cnt=np.bincount(li,minlength=len(tree["gidx"])).astype(float);W[:,j]=cnt/cnt.sum();counts[g]=int(len(li))
 return W,counts

def evaluate(tree,source_group,W):
 idx={g:i for i,g in enumerate(GROUPS)};reps={}
 overall=True
 for g,others in (("H",("C","V")),("V",("C","H"))):
  nodes=np.flatnonzero(source_group==g)
  if len(nodes)==0:raise RuntimeError(f"empty official source {g}")
  worst={"margin":float("inf"),"q":None,"node_id":None,"best_distant":None,"local":None,"distant":None}
  total_bad=0;qmins=[]
  for q in QGRID:
   A=(tree["L0"]+sparse.diags(q*tree["area"],format="csr")).tocsc();phi=splu(A,permc_spec="COLAMD").solve(W)
   loc=phi[nodes,idx[g]];a=phi[nodes,idx[others[0]]];b=phi[nodes,idx[others[1]]];best=np.maximum(a,b);margin=loc-best
   bad=int(np.sum(margin<=0));total_bad+=bad
   mi=int(np.argmin(margin));m=float(margin[mi]);which=others[0] if a[mi]>=b[mi] else others[1]
   qmins.append({"q":float(q),"min_margin":m,"violating_nodes":bad})
   if m<worst["margin"]:
    worst={"margin":m,"q":float(q),"node_id":int(tree["ids_main"][nodes[mi]]),"best_distant":which,
           "local":float(loc[mi]),"distant":float(best[mi])}
  passed=total_bad==0;overall=overall and passed
  reps[g]={"source_nodes":int(len(nodes)),"violating_node_q_instances":int(total_bad),"passed":passed,"worst":worst,"q_minima":qmins}
 return overall,reps

def main():
 for k,p in [("brain",WORK/"brain.npz"),("syn",WORK/"syn-partners.feather"),
             ("swc_10540",WORK/"10540.swc"),("swc_10977",WORK/"10977.swc")]:
  if sha_file(p)!=EXPECTED[k]:raise RuntimeError(f"{k} hash")
 labelmap=fetch_labelmap();cv=CloudVolume(BASE_CV,use_https=True,bounded=True,fill_missing=True,progress=False,mip=0)
 res=np.asarray(cv.resolution,float)
 if not np.allclose(res,[256,256,256],rtol=0,atol=0):raise RuntimeError(f"resolution {res}")
 kc=load_kc();d=extract(kc);reports={};allpass=True
 for apl in APL_IDS:
  tree=parse_tree(WORK/f"{apl}.swc")
  vox=np.floor((tree["xyz_main"]*VOXEL_NM)/res).astype(np.int64);labs=sample_labels(cv,vox)
  sg=np.array([semantic_group(labelmap.get(int(x))) if int(x)!=0 else None for x in labs],object)
  W,outcounts=output_weights(tree,d,apl);passed,ev=evaluate(tree,sg,W);allpass=allpass and passed
  exact={}
  for x in labs:
   nm="BACKGROUND" if int(x)==0 else labelmap.get(int(x),f"UNMAPPED_{int(x)}");exact[nm]=exact.get(nm,0)+1
  reports[str(apl)]={"component_sizes":tree["component_sizes"],
    "official_source_counts":{"C":int(np.sum(sg=="C")),"V":int(np.sum(sg=="V")),"H":int(np.sum(sg=="H")),"OUTSIDE":int(np.sum([x is None for x in sg]))},
    "exact_roi_label_counts":dict(sorted(exact.items(),key=lambda z:(-z[1],z[0]))),
    "output_site_counts":outcounts,"evaluation":ev,"passed":passed}
 cls="PASS_M3F2B_OFFICIAL_ROI_HV_ORDINAL_ELIGIBILITY" if allpass else "NO_ROBUST_M3F2B_OFFICIAL_ROI_HV_ORDINAL_PREDICTION"
 report={"gate":"V6-M3F2B_OFFICIAL_ROI_HV_ORDINAL_ELIGIBILITY","classification":cls,
  "q_grid":[float(x) for x in QGRID],"reports":reports,
  "guardrails":{"amin_loaded":False,"q_restricted":False,"source_node_trimmed":False,"optical_mapping_fit":False,"mnq_loaded":False}}
 (OUT/"v6_m3f2b_result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"classification":cls,"summary":{k:{"official_source_counts":v["official_source_counts"],"evaluation":{g:{"source_nodes":x["source_nodes"],"violating_node_q_instances":x["violating_node_q_instances"],"passed":x["passed"],"worst":x["worst"]} for g,x in v["evaluation"].items()}} for k,v in reports.items()},"guardrails":report["guardrails"]},indent=2,sort_keys=True))

if __name__=="__main__":main()
