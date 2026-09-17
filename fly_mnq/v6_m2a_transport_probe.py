from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

DOI = 'doi:10.5061/dryad.bk3j9kdd1'
DRYAD_API = 'https://datadryad.org/api/v2'
ZENODO_RECORD = 'https://zenodo.org/api/records/5904586'
OUT = Path('v6_m2a_transport_out')
WORK = Path('v6_m2a_transport_work')
OUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)

TARGETS = [
    'APL_PN_connectivity_table_(Figure_1D).xlsx',
    'APL_KC_connectivity_table_(Figure_1E).xlsx',
    'APL_GCaMP6m_Mch_vs_Oct_peaks_(Figure_2D).xlsx',
    'APL_GCaMP6m_DL_vs_Oct_peaks_(Figure_2G).xlsx',
    'GH146-GCaMP6m_Mch_vs_Oct_AL_average_activity_(Figure_3-figure_supplement_2B).xlsx',
    'GH146-GCaMP6m_DL_vs_Oct_AL_average_activity_(Figure_3-figure_supplement_2D).xlsx',
    'MB247-homer-GCaMP3_Mch_vs_Oct_average_response_(Figure_3F-H).xlsx',
    'APL-TNT_MB247-homer-GCaMP3_Mch_vs_Oct_(Figure_4B_and_4D).xlsx',
    'Inter-odour_delta_among_conditions_-_Figure_4-figure_supplement_1.xlsx',
    'APL_locality_PA_MP_vs_FA_MP_(Figure_5C).xlsx',
    'APL_locality_PA_FA_vs_MP_FA_(Figure_5-figure_supplement_1B).xlsx',
    'MB247-homer-GCaMP3_locality_of_MGs_responses_(Figure_5-figure_supplement_1A).xlsx',
    'NP225_Syp-GCaMP3_Mch_vs_Oct_all_boutons_peaks_(Figure_3C).xlsx',
    'MB247-homer-GCaMP3_Mch_vs_Oct_all_MG_peaks_(Figure_3G).xlsx',
    'APL-TNT_MB247-homer-GCaMP3_Mch_vs_Oct_all_MG_peaks_(Figure_4E_and_4F).xlsx',
]


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={
        'Accept': 'application/json',
        'X-API-Version': '2.1.0',
        'User-Agent': 'v6-m2a-transport-audit/1.0',
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={'User-Agent': 'v6-m2a-transport-audit/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r, dest.open('wb') as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def dryad_files() -> tuple[int, list[dict]]:
    encoded = urllib.parse.quote(DOI, safe='')
    ds = get_json(f'{DRYAD_API}/datasets/{encoded}')
    href = ds.get('_links', {}).get('stash:version', {}).get('href')
    m = re.search(r'/versions/(\d+)(?:$|[/?#])', str(href))
    if not m:
        raise RuntimeError(f'cannot parse Dryad version from {href!r}')
    vid = int(m.group(1))
    url = f'{DRYAD_API}/versions/{vid}/files?per_page=100'
    out: list[dict] = []
    seen: set[str] = set()
    while url:
        if url in seen:
            raise RuntimeError('Dryad pagination loop')
        seen.add(url)
        obj = get_json(url)
        out.extend(obj.get('_embedded', {}).get('stash:files', []))
        nxt = obj.get('_links', {}).get('next', {})
        href = nxt.get('href') if isinstance(nxt, dict) else None
        url = href if (href and href.startswith('http')) else ('https://datadryad.org' + href if href else '')
    return vid, out


def zenodo_download_url(f: dict) -> str | None:
    links = f.get('links') or {}
    for key in ('content', 'self'):
        u = links.get(key)
        if isinstance(u, str) and u.startswith('http'):
            return u
    return None


def main() -> None:
    vid, dfs = dryad_files()
    dryad = {str(f.get('path', '')).split('/')[-1]: f for f in dfs}
    missing_dryad = [n for n in TARGETS if n not in dryad]
    if missing_dryad:
        raise RuntimeError(f'Dryad target names missing: {missing_dryad}')

    z = get_json(ZENODO_RECORD)
    zfiles = z.get('files', [])
    zenodo = {str(f.get('key') or f.get('filename') or '').split('/')[-1]: f for f in zfiles}
    missing_zenodo = [n for n in TARGETS if n not in zenodo]

    rows = []
    mismatches = []
    for name in TARGETS:
        d = dryad[name]
        zd = zenodo.get(name)
        row = {
            'filename': name,
            'dryad_size': d.get('size'),
            'dryad_digest_type': d.get('digestType'),
            'dryad_sha256': d.get('digest'),
            'zenodo_present': zd is not None,
        }
        if zd is not None:
            u = zenodo_download_url(zd)
            row['zenodo_size'] = zd.get('size')
            row['zenodo_checksum_metadata'] = zd.get('checksum')
            row['zenodo_download_url_present'] = bool(u)
            if not u:
                mismatches.append({'filename': name, 'reason': 'NO_ZENODO_DOWNLOAD_URL'})
            else:
                dest = WORK / name
                download(u, dest)
                local = sha256(dest)
                row['local_bytes'] = dest.stat().st_size
                row['local_sha256'] = local
                expected = str(d.get('digest') or '').lower()
                dtype = str(d.get('digestType') or '').lower()
                ok = dtype in {'sha-256', 'sha256'} and expected and local.lower() == expected
                row['matches_dryad_sha256'] = bool(ok)
                if d.get('size') is not None:
                    row['matches_dryad_size'] = int(d['size']) == dest.stat().st_size
                    ok = ok and row['matches_dryad_size']
                if not ok:
                    mismatches.append({'filename': name, 'reason': 'BYTE_IDENTITY_MISMATCH'})
        rows.append(row)

    status = 'PASS_HASH_IDENTICAL_ZENODO_TRANSPORT' if not missing_zenodo and not mismatches else 'FAIL_NO_HASH_IDENTICAL_ZENODO_TRANSPORT'
    report = {
        'gate': 'V6-M2A_TRANSPORT_ONLY',
        'status': status,
        'dryad_version_id': vid,
        'dryad_total_files_seen': len(dfs),
        'zenodo_record_id': z.get('id'),
        'zenodo_doi': z.get('doi'),
        'zenodo_total_files_seen': len(zfiles),
        'missing_zenodo_targets': missing_zenodo,
        'mismatches': mismatches,
        'files': rows,
        'guardrails': {
            'workbooks_opened': False,
            'response_values_read': False,
            'parameters_fit': False,
            'v6_prediction_loaded': False,
            'amin_response_values_loaded': False,
            'mnq_or_market_loaded': False,
            'dryad_sha256_is_authority': True,
        },
    }
    (OUT / 'v6_m2a_transport_probe.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report, indent=2, sort_keys=True))
    if status != 'PASS_HASH_IDENTICAL_ZENODO_TRANSPORT':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
