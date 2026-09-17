from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

OUT = Path('v6_m3a_out')
WORK = Path('v6_m3a_work')
OUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)

BASE = 'https://storage.googleapis.com/flyem-male-cns/v1.0/segmentation/skeletons-malecns/skeletons-swc'
EXPECTED = {
    10540: '22372942488c2e9222a1634a63c980c94d8130f4f497c5c62d4bbda4a784170f',
    10977: '34123fc48a5ffee6b9b29e857219776ccdcb737d885b9de90e2a43d57ecaf9cf',
}


def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def acquire(body: int) -> Path:
    p=WORK/f'{body}.swc'
    url=f'{BASE}/{body}.swc'
    cp=subprocess.run(['curl','--silent','--show-error','--location','--fail-with-body','--retry','3','--retry-delay','1','--max-time','120','--output',str(p),url],text=True,capture_output=True)
    if cp.returncode:
        if p.exists(): p.unlink()
        raise RuntimeError(f'curl failed for body {body}: {cp.stderr[-300:]}')
    return p


def parse_and_audit(p: Path, body: int) -> dict:
    nodes={}
    type_counts=Counter()
    for ln,line in enumerate(p.read_text(errors='strict').splitlines(),1):
        s=line.strip()
        if not s or s.startswith('#'): continue
        parts=s.split()
        if len(parts)!=7:
            raise RuntimeError(f'{p.name}: line {ln} has {len(parts)} fields, expected 7')
        try:
            nid=int(float(parts[0])); typ=int(float(parts[1])); x,y,z,r=map(float,parts[2:6]); parent=int(float(parts[6]))
        except Exception as e:
            raise RuntimeError(f'{p.name}: parse error line {ln}: {e}')
        if float(parts[0])!=nid or float(parts[1])!=typ or float(parts[6])!=parent:
            raise RuntimeError(f'{p.name}: non-integer id/type/parent line {ln}')
        if nid<=0 or nid in nodes: raise RuntimeError(f'{p.name}: invalid/duplicate node id {nid}')
        if not all(math.isfinite(v) for v in (x,y,z,r)): raise RuntimeError(f'{p.name}: nonfinite geometry node {nid}')
        if r<=0: raise RuntimeError(f'{p.name}: nonpositive radius node {nid}: {r}')
        nodes[nid]=(typ,x,y,z,r,parent); type_counts[typ]+=1
    if len(nodes)<100: raise RuntimeError(f'{p.name}: too few nodes: {len(nodes)}')
    roots=[nid for nid,v in nodes.items() if v[5]==-1]
    if len(roots)!=1: raise RuntimeError(f'{p.name}: roots={roots}')
    root=roots[0]
    for nid,v in nodes.items():
        parent=v[5]
        if parent==-1: continue
        if parent==nid: raise RuntimeError(f'{p.name}: self-parent {nid}')
        if parent not in nodes: raise RuntimeError(f'{p.name}: missing parent {parent} for {nid}')
    # Parent-link path audit proves connected acyclic rooted tree.
    for start in nodes:
        seen=set(); cur=start
        while cur!=-1:
            if cur in seen: raise RuntimeError(f'{p.name}: cycle from {start}')
            seen.add(cur)
            cur=nodes[cur][5]
        if root not in seen: raise RuntimeError(f'{p.name}: node {start} does not reach root {root}')
    total=0.0; edges=0
    xs=[];ys=[];zs=[];rs=[]
    for nid,(typ,x,y,z,r,parent) in nodes.items():
        xs.append(x);ys.append(y);zs.append(z);rs.append(r)
        if parent!=-1:
            _,px,py,pz,_,_=nodes[parent]
            d=math.sqrt((x-px)**2+(y-py)**2+(z-pz)**2)
            if not math.isfinite(d) or d<=0: raise RuntimeError(f'{p.name}: invalid edge length {nid}->{parent}: {d}')
            total+=d; edges+=1
    if edges!=len(nodes)-1: raise RuntimeError(f'{p.name}: edge count {edges} != nodes-1')
    rs2=sorted(rs); n=len(rs2)
    med=rs2[n//2] if n%2 else .5*(rs2[n//2-1]+rs2[n//2])
    got=sha256(p)
    if got!=EXPECTED[body]:
        raise RuntimeError(f'{p.name}: D0 parity mismatch got={got} expected={EXPECTED[body]}')
    return {
        'body_id':body,
        'source_url_redacted_to_public_path':f'{BASE}/{body}.swc',
        'sha256':got,
        'd0_expected_sha256':EXPECTED[body],
        'd0_byte_parity':True,
        'nodes':len(nodes),'edges':edges,'root_id':root,
        'type_counts':{str(k):v for k,v in sorted(type_counts.items())},
        'coordinate_source_units':{'x':[min(xs),max(xs)],'y':[min(ys),max(ys)],'z':[min(zs),max(zs)]},
        'radius_source_units':{'min':min(rs),'median':med,'max':max(rs)},
        'total_cable_length_source_units':total,
        'total_cable_length_um':total*0.008,
        'source_coordinate_scale_nm_per_unit':8.0,
        'all_structural_checks_pass':True,
    }


def main():
    audited=[]
    for body in sorted(EXPECTED):
        p=acquire(body)
        audited.append(parse_and_audit(p,body))
    report={
        'gate':'V6-M3A_MALECNS_MORPHOLOGY_PASSIVE_SOURCE_AUDIT',
        'classification':'PASS_M3A_CANONICAL_APL_MORPHOLOGY_AND_PASSIVE_ENVELOPE',
        'male_cns_dataset':'v1.0',
        'official_swc_bucket':'gs://flyem-male-cns/v1.0/segmentation/skeletons-malecns/skeletons-swc/',
        'skeletons':audited,
        'passive_literature_envelope':{
            'source':'Scheffer et al. eLife 2020 DOI 10.7554/eLife.57443 Table 6',
            'Ra_ohm_m':[0.40,4.00],
            'Rm_ohm_per_m2':[0.20,2.64],
            'Cm_F_per_m2':[0.006,0.026],
            'role':'uncertainty_set_not_fit',
            'dc_rule':'Cm_not_used_to_tune_steady_state_attenuation',
        },
        'guardrails':{
            'model_prediction_executed':False,
            'amin_response_loaded':False,
            'm2b_residual_array_loaded':False,
            'v5_lobe_residual_loaded':False,
            'mnq_market_loaded':False,
            'passive_point_selected':False,
        }
    }
    p=OUT/'v6_m3a_morphology_source_audit.json'
    p.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=='__main__': main()
