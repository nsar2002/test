from __future__ import annotations

import hashlib
import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

DOI = 'doi:10.5061/dryad.bk3j9kdd1'
API = 'https://datadryad.org/api/v2'
TARGET = 'APL_PN_connectivity_table_(Figure_1D).xlsx'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/152 Safari/537.36'
OUT = Path('v6_m2a_assembly_out')
WORK = Path('v6_m2a_assembly_work')
OUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={'Accept':'application/json','X-API-Version':'2.1.0','User-Agent':UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()


def resolve_target() -> tuple[int, dict]:
    enc=urllib.parse.quote(DOI,safe='')
    ds=get_json(f'{API}/datasets/{enc}')
    href=(ds.get('_links') or {}).get('stash:version',{}).get('href')
    m=re.search(r'/versions/(\d+)(?:$|[/?#])',str(href))
    if not m: raise RuntimeError('cannot resolve Dryad version id')
    vid=int(m.group(1))
    url=f'{API}/versions/{vid}/files?per_page=100'
    matches=[]
    seen=set()
    count=0
    while url:
        if url in seen: raise RuntimeError('pagination loop')
        seen.add(url)
        obj=get_json(url)
        files=obj.get('_embedded',{}).get('stash:files',[])
        count += len(files)
        for f in files:
            if str(f.get('path','')).split('/')[-1]==TARGET:
                matches.append(f)
        nxt=(obj.get('_links') or {}).get('next')
        href=nxt.get('href') if isinstance(nxt,dict) else None
        url=href if (href and href.startswith('http')) else ('https://datadryad.org'+href if href else '')
    if len(matches)!=1: raise RuntimeError(f'exact target count={len(matches)}')
    return vid,matches[0]


def curl_get(url: str, dest: Path, accept: str | None = None) -> dict:
    hdr=OUT/(dest.name+'.headers.txt')
    cmd=['curl','--silent','--show-error','--location','--fail-with-body','--max-time','60','--retry','2','--retry-delay','1','--user-agent',UA]
    if accept: cmd += ['--header',f'Accept: {accept}']
    cmd += ['--dump-header',str(hdr),'--output',str(dest),url]
    cp=subprocess.run(cmd,text=True,capture_output=True)
    rawhdr=hdr.read_text(errors='replace') if hdr.exists() else ''
    # never persist presigned query material if a Location header is present
    redacted=re.sub(r'(?im)^(location:\s*[^?\r\n]+)\?[^\r\n]*$',r'\1?[REDACTED_QUERY]',rawhdr)
    hdr.write_text(redacted)
    ctype=None
    for line in reversed(redacted.splitlines()):
        if line.lower().startswith('content-type:'):
            ctype=line.split(':',1)[1].strip(); break
    return {'exit_code':cp.returncode,'stderr_tail':cp.stderr[-500:],'bytes':dest.stat().st_size if dest.exists() else None,'content_type':ctype,'headers_redacted_tail':redacted[-2000:]}


def main() -> None:
    vid,meta=resolve_target()
    expected_sha=str(meta.get('digest') or '').lower()
    expected_size=int(meta.get('size'))
    if str(meta.get('digestType') or '').lower() not in {'sha-256','sha256'}:
        raise RuntimeError('Dryad target digest is not SHA-256')

    endpoint_candidates=[
        f'https://datadryad.org/downloads/zip_assembly_info/{vid}.json',
        f'https://datadryad.org/stash/downloads/zip_assembly_info/{vid}.json',
    ]
    endpoint_attempts=[]
    success=None
    target_info_summary=None
    for i,u in enumerate(endpoint_candidates,1):
        dest=WORK/f'assembly_{i}.bin'
        r=curl_get(u,dest,'application/json')
        r['url_path']=urllib.parse.urlsplit(u).path
        r['body_sha256']=sha256(dest) if dest.exists() and dest.stat().st_size else None
        parsed=None
        if r['exit_code']==0 and dest.exists():
            try:
                parsed=json.loads(dest.read_text(errors='strict'))
            except Exception:
                parsed=None
        r['json_array']=isinstance(parsed,list)
        r['json_entries']=len(parsed) if isinstance(parsed,list) else None
        if isinstance(parsed,list):
            exact=[x for x in parsed if isinstance(x,dict) and str(x.get('filename','')).split('/')[-1]==TARGET]
            r['exact_target_count']=len(exact)
            if len(exact)==1:
                x=exact[0]
                signed=x.get('url')
                target_info_summary={'filename':x.get('filename'),'size':x.get('size'),'url_present':isinstance(signed,str) and signed.startswith('http')}
                if target_info_summary['url_present']:
                    file_dest=WORK/'target.xlsx.bytes'
                    fr=curl_get(signed,file_dest,None)
                    local_sha=sha256(file_dest) if file_dest.exists() and file_dest.stat().st_size else None
                    fr['local_sha256']=local_sha
                    fr['matches_dryad_sha256']=bool(local_sha and local_sha.lower()==expected_sha)
                    fr['matches_dryad_size']=bool(file_dest.exists() and file_dest.stat().st_size==expected_size)
                    fr['signed_url_host']=urllib.parse.urlsplit(signed).hostname
                    fr['signed_url_path']=urllib.parse.urlsplit(signed).path
                    r['target_fetch']=fr
                    if fr['exit_code']==0 and fr['matches_dryad_sha256'] and fr['matches_dryad_size']:
                        success=i
        endpoint_attempts.append(r)
        # assembly response may contain signed credentials; remove it immediately
        if dest.exists(): dest.unlink()
        if success: break

    status='PASS_DRYAD_ASSEMBLY_HASH_IDENTICAL_TRANSPORT' if success else 'FAIL_DRYAD_ASSEMBLY_TRANSPORT'
    report={
        'gate':'V6-M2A_DRYAD_ZIP_ASSEMBLY_TRANSPORT_ONLY',
        'status':status,
        'dryad_version_id':vid,
        'target':TARGET,
        'expected_size':expected_size,
        'expected_sha256':expected_sha,
        'successful_endpoint_attempt':success,
        'target_info_summary':target_info_summary,
        'endpoint_attempts':endpoint_attempts,
        'guardrails':{
            'assembly_signed_queries_persisted_or_logged':False,
            'workbook_opened':False,
            'response_values_read':False,
            'parameters_fit':False,
            'v6_prediction_loaded':False,
            'amin_response_values_loaded':False,
            'mnq_or_market_loaded':False,
        },
    }
    (OUT/'v6_m2a_zip_assembly_transport_probe.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True))
    if status!='PASS_DRYAD_ASSEMBLY_HASH_IDENTICAL_TRANSPORT': raise SystemExit(2)

if __name__=='__main__': main()
