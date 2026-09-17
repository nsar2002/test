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
WORK = Path('v6_m2a_ui_transport_work')
OUT = Path('v6_m2a_ui_transport_out')
WORK.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/152 Safari/537.36'


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


def file_id(meta: dict) -> int:
    for rel in ('self','stash:download'):
        x=(meta.get('_links') or {}).get(rel)
        href=x.get('href') if isinstance(x,dict) else None
        if href:
            m=re.search(r'/files/(\d+)(?:/download)?(?:$|[/?#])', href)
            if m:
                return int(m.group(1))
    raise RuntimeError('no Dryad file id in HAL links')


def resolve() -> tuple[int, dict]:
    enc=urllib.parse.quote(DOI,safe='')
    ds=get_json(f'{API}/datasets/{enc}')
    href=(ds.get('_links') or {}).get('stash:version',{}).get('href')
    m=re.search(r'/versions/(\d+)(?:$|[/?#])',str(href))
    if not m: raise RuntimeError('no version id')
    vid=int(m.group(1))
    obj=get_json(f'{API}/versions/{vid}/files?per_page=100')
    files=[]
    while True:
        files += obj.get('_embedded',{}).get('stash:files',[])
        n=(obj.get('_links') or {}).get('next')
        href=n.get('href') if isinstance(n,dict) else None
        if not href: break
        url=href if href.startswith('http') else 'https://datadryad.org'+href
        obj=get_json(url)
    matches=[f for f in files if str(f.get('path','')).split('/')[-1]==TARGET]
    if len(matches)!=1: raise RuntimeError(f'exact target count={len(matches)}')
    return vid,matches[0]


def curl_download(url: str, dest: Path) -> dict:
    headers=OUT/(dest.name+'.headers.txt')
    cp=subprocess.run([
        'curl','--silent','--show-error','--location','--fail-with-body',
        '--max-time','60','--retry','2','--retry-delay','1',
        '--user-agent',UA,'--dump-header',str(headers),'--output',str(dest),url
    ],text=True,capture_output=True)
    return {
        'url_path': urllib.parse.urlsplit(url).path,
        'exit_code': cp.returncode,
        'stderr_tail': cp.stderr[-500:],
        'bytes': dest.stat().st_size if dest.exists() else None,
        'sha256': sha256(dest) if dest.exists() and dest.stat().st_size else None,
        'header_text_redacted': headers.read_text(errors='replace')[-2000:] if headers.exists() else None,
    }


def curl_headers(url: str) -> dict:
    cp=subprocess.run([
        'curl','--silent','--show-error','--head','--max-time','30',
        '--user-agent',UA,'--dump-header','-','--output','/dev/null',url
    ],text=True,capture_output=True)
    # redact query strings in Location so no presigned credentials enter artifacts
    txt=re.sub(r'(?im)^(location:\s*[^?\r\n]+)\?[^\r\n]*$',r'\1?[REDACTED_QUERY]',cp.stdout)
    return {'exit_code':cp.returncode,'headers_redacted':txt[-3000:],'stderr_tail':cp.stderr[-500:]}


def main() -> None:
    vid,meta=resolve()
    fid=file_id(meta)
    expected=str(meta.get('digest') or '').lower()
    size=int(meta.get('size')) if meta.get('size') is not None else None
    paths=[
        f'https://datadryad.org/downloads/file_stream/{fid}',
        f'https://datadryad.org/stash/downloads/file_stream/{fid}',
    ]
    attempts=[]
    success=None
    for i,u in enumerate(paths,1):
        dest=WORK/f'attempt_{i}.bin'
        r=curl_download(u,dest)
        r['matches_dryad_sha256']=bool(r['sha256'] and r['sha256'].lower()==expected)
        r['matches_dryad_size']=bool(size is not None and r['bytes']==size)
        attempts.append(r)
        if r['exit_code']==0 and r['matches_dryad_sha256'] and r['matches_dryad_size']:
            success=i
            break
    enc=urllib.parse.quote(DOI,safe='')
    dataset_header_probe=curl_headers(f'{API}/datasets/{enc}/download')
    status='PASS_PUBLIC_DRYAD_UI_BYTE_TRANSPORT' if success else 'FAIL_PUBLIC_DRYAD_UI_BYTE_TRANSPORT'
    report={
        'gate':'V6-M2A_PUBLIC_DRYAD_UI_TRANSPORT_ONLY',
        'status':status,
        'dryad_version_id':vid,
        'target':TARGET,
        'dryad_file_id':fid,
        'expected_sha256':expected,
        'expected_size':size,
        'successful_attempt':success,
        'attempts':attempts,
        'dataset_download_header_probe':dataset_header_probe,
        'guardrails':{
            'only_one_preregistered_transport_file_requested':True,
            'workbook_opened':False,
            'response_values_read':False,
            'parameters_fit':False,
            'v6_prediction_loaded':False,
            'amin_response_values_loaded':False,
            'mnq_or_market_loaded':False,
        },
    }
    (OUT/'v6_m2a_dryad_ui_transport_probe.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True))
    if status!='PASS_PUBLIC_DRYAD_UI_BYTE_TRANSPORT': raise SystemExit(2)

if __name__=='__main__': main()
