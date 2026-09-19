#!/usr/bin/env python3
import bz2, json, re, struct, sys, tempfile, time, zlib
from pathlib import Path
from urllib.parse import quote
import pyabf, requests

RECORD_ID=18644411
ARCHIVE_KEY="Ephys_sparse coding.zip"
EXPECTED_SIZE=2287477173
M4A0_PATH="research/results/v6_m4a0_chen_ephys_schema_result.json"
COLLECTION="Ephys_sparse coding/APL_SD_APL_SKRNAi_Fig4H-J/raw/"
GROUPS={"APL_RNAi_ctrl_kk","APL_SK_RNAi_kk"}
TOKENS={"vm","vmem","membranevoltage","membranepotential","vmon","vmonitor"}
OUT="v6_m4a1h_result.json"

def norm(s):
    return re.sub(r"[^a-z0-9]+","",str(s).lower())

def kind(name):
    b=name.rsplit("/",1)[-1].lower()
    if "ic_ahp_2na" in b: return "IC_AHP_2nA"
    if "ic_fp" in b: return "IC_fp"
    return None

def group(name):
    if not name.startswith(COLLECTION): return None
    g=name[len(COLLECTION):].split("/",1)[0]
    return g if g in GROUPS else None

def rr(s,url,a,b):
    for attempt in range(4):
        try:
            with s.get(url,headers={"Range":f"bytes={a}-{b}","Accept-Encoding":"identity"},stream=True,timeout=(30,180),allow_redirects=True) as r:
                if r.status_code!=206: raise RuntimeError(f"status {r.status_code}")
                cr=r.headers.get("Content-Range","")
                if not cr.endswith(f"/{EXPECTED_SIZE}"): raise RuntimeError(f"Content-Range {cr}")
                n=b-a+1
                d=r.raw.read(n,decode_content=False)
                if len(d)!=n: raise RuntimeError(f"bytes {len(d)} != {n}")
                return d
        except Exception:
            if attempt==3: raise
            time.sleep(2**attempt)

def decode(s,url,e,td):
    off=int(e["local_header_offset"])
    h=rr(s,url,off,off+29)
    vals=struct.unpack("<4s5H3L2H",h)
    if vals[0]!=b"PK\x03\x04": raise ValueError("bad local header")
    _,ver,flags,method,mt,md,crc_lh,comp_lh,uncomp_lh,fn,ex=vals
    ve=rr(s,url,off+30,off+30+fn+ex-1) if fn+ex else b""
    enc="utf-8" if flags&0x800 else "cp437"
    local=ve[:fn].decode(enc)
    if local!=e["name"]: raise ValueError("local name mismatch")
    if method!=int(e["compression_method"]): raise ValueError("method mismatch")
    start=off+30+fn+ex
    comp=rr(s,url,start,start+int(e["compressed_size"])-1)
    if method==0: raw=comp
    elif method==8: raw=zlib.decompress(comp,-15)
    elif method==12: raw=bz2.decompress(comp)
    else: raise ValueError(f"unsupported method {method}")
    if len(raw)!=int(e["uncompressed_size"]): raise ValueError("size mismatch")
    crc=zlib.crc32(raw)&0xffffffff
    if f"{crc:08x}"!=str(e["crc32"]).lower(): raise ValueError("CRC mismatch")
    p=Path(td)/f"{crc:08x}.abf"; p.write_bytes(raw); return p

def main():
    m=json.load(open(M4A0_PATH,encoding="utf-8"))
    selected=[e for e in m["members"] if group(e["name"]) and kind(e["name"])]
    expected={("APL_RNAi_ctrl_kk","IC_fp"):11,("APL_SK_RNAi_kk","IC_fp"):8,
              ("APL_RNAi_ctrl_kk","IC_AHP_2nA"):6,("APL_SK_RNAi_kk","IC_AHP_2nA"):5}
    counts={}
    for e in selected: counts[(group(e["name"]),kind(e["name"]))]=counts.get((group(e["name"]),kind(e["name"])),0)+1
    if counts!=expected or len(selected)!=30:
        raise RuntimeError(f"source count mismatch {counts}")
    url=f"https://zenodo.org/records/{RECORD_ID}/files/{quote(ARCHIVE_KEY)}?download=1"
    s=requests.Session(); s.headers.update({"User-Agent":"fly-mnq-v6-m4a1h-header-schema/1.0","Accept-Encoding":"identity"})
    rows=[]
    with tempfile.TemporaryDirectory(prefix="m4a1h_") as td:
        for i,e in enumerate(sorted(selected,key=lambda x:x["name"]),1):
            p=decode(s,url,e,td)
            a=pyabf.ABF(str(p),loadData=False)
            names=list(a.adcNames); units=list(a.adcUnits)
            candidates=[]
            for idx,(name,u) in enumerate(zip(names,units)):
                nu=str(u).replace("µ","u").lower()
                if norm(name) in TOKENS and nu in {"v","mv","uv"}:
                    candidates.append({"index":idx,"name":name,"normalized":norm(name),"unit":u})
            rows.append({
                "source_name":e["name"],"group":group(e["name"]),"kind":kind(e["name"]),
                "abf_version":str(a.abfVersionString),
                "adc_names":names,"adc_units":units,
                "adc_count":int(a.channelCount),"semantic_candidates":candidates,
                "dac_names":list(getattr(a,"dacNames",[])),
                "dac_units":list(getattr(a,"dacUnits",[])),
                "sweep_count":int(a.sweepCount),
                "data_rate_hz":float(a.dataRate),
            })
            print(f"HEADER {i:02d}/30 adc={list(zip(names,units))} candidates={candidates}")
    one=all(len(r["semantic_candidates"])==1 for r in rows)
    semantic_names={r["semantic_candidates"][0]["normalized"] for r in rows if len(r["semantic_candidates"])==1}
    indexes={r["semantic_candidates"][0]["index"] for r in rows if len(r["semantic_candidates"])==1}
    if one and len(semantic_names)==1:
        cls="PASS_M4A1H_DETERMINISTIC_ADC_IDENTITY"
        reason="exactly one frozen semantic membrane-voltage ADC token is present in every selected ABF"
    else:
        cls="BLOCKED_M4A1H_ADC_IDENTITY_NOT_SELF_DESCRIBING"
        reason="ABF headers do not provide one consistent membrane-voltage ADC under the frozen exact-name rule"
    out={
        "classification":cls,"reason":reason,
        "frozen_tokens":sorted(TOKENS),
        "semantic_names":sorted(semantic_names),
        "semantic_indexes":sorted(indexes),
        "files":rows,
        "guardrails":{
            "voltage_samples_read":False,"command_waveform_samples_read":False,
            "response_metric_computed":False,"m4v0_numeric_values_opened":False,
            "amin_loaded":False,"mnq_loaded":False,
        }
    }
    json.dump(out,open(OUT,"w",encoding="utf-8"),indent=2,sort_keys=True)
    print(json.dumps({"classification":cls,"reason":reason,"semantic_names":sorted(semantic_names),"semantic_indexes":sorted(indexes),
                      "unique_adc_schemas":sorted({str(list(zip(r["adc_names"],r["adc_units"]))) for r in rows}),
                      "guardrails":out["guardrails"]},indent=2))
    return 0

if __name__=="__main__":
    try: sys.exit(main())
    except Exception as e:
        out={"classification":"BLOCKED_M4A1H_ADC_IDENTITY_NOT_SELF_DESCRIBING","reason":f"{type(e).__name__}: {e}",
             "guardrails":{"voltage_samples_read":False,"command_waveform_samples_read":False,"response_metric_computed":False,
                           "m4v0_numeric_values_opened":False,"amin_loaded":False,"mnq_loaded":False}}
        json.dump(out,open(OUT,"w"),indent=2,sort_keys=True); print(json.dumps(out,indent=2)); sys.exit(0)
