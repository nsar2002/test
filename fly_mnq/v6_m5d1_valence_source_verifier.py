from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import re
import unicodedata
from pathlib import Path

import pyarrow.feather as feather

SRC = Path("v6_m5d1_work")          # pinned eLife XML sources
ANN = Path("v6_m5b3b_work/body-annotations.feather")
O = Path("v6_m5d1_out")
O.mkdir(exist_ok=True)

PROTOCOL_PATH = "research/v6_m5d1_valence_source_protocol.md"
TABLE_PATH = "research/v6_m5d1_valence_source_table.json"
M5B3B_RESULT = "research/results/v6_m5b3b_compartment_gating_mvp_result.json"
M5B3B_SCRIPT = "fly_mnq/v6_m5b3b_compartment_gating_mvp.py"
ANN_SHA = "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
M5B3B_RESULT_SHA = "1792a7f082cf951db76f98978236d3cc0eed828874922ebde79a98b88aadb1b2"
M5B3B_SCRIPT_SHA = "0a8d6c3fb61e7659fb885433dc0a93998dfa3b1b05397d8310274eb9fe14914b"
ELIFE_COMMIT = "d146492a0d8efed2fc3bb377ef9b22dde455936b"
SOURCES = {
    "S1": ("elife-16135-v2.xml", "b599a442b2fd95bd68066a59319f9eb4fc13a697461729fb3270f6f1b311bad2"),
    "S2": ("elife-04580-v1.xml", "f9ad08a542e03d5594640295db0d8d9583adeea6a0c1ed9ab42366ecb20bcfb4"),
    "S3": ("elife-04577-v1.xml", "c17e5916866a0f54eb5113880abe8cd1230121581e5c4da6f269b3f4f9bfb4dd"),
    "S4": ("elife-62576-v2.xml", "d26350b4e8dcecfbb88c14e6fb1fc432b4d0dfcdf44483d75241583c1ace54c7"),
}
DAN_LABELS = {"APPETITIVE", "AVERSIVE", "NO_SIGNIFICANT_MEMORY", "UNRESOLVED", "UNTESTED"}
MBON_LABELS = {"ATTRACTIVE", "REPULSIVE", "NO_SIGNIFICANT_EFFECT", "UNRESOLVED", "UNTESTED"}
SIGNED = {"APPETITIVE", "AVERSIVE", "ATTRACTIVE", "REPULSIVE"}
FAST_DAN_TYPES = [f"PAM{i:02d}" for i in range(1, 16)] + [f"PPL10{i}" for i in range(1, 7)]
EXPECTED_DAN_RECORDS = 21
EXPECTED_MBON_RECORDS = 38
MAX_QUOTE = 600
BLOCK_TAGS = ("p", "title", "caption", "td", "th", "label", "list-item", "article-title")
NAME_SCAN = re.compile(r"\b(PAM|PPL1|MBON)-[^\s,;:()\[\]]+")
COMP_TOKEN = re.compile(r"pedc|y[1-5]|a'[1-3]|a[1-3]|b'[12]|b[12]")
ELIGIBLE_COMPARTMENTS = ("B'1", "B'2", "B1", "a'1", "a'2", "a'3", "a1", "a2", "a3", "y2", "y4", "y5")


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def normalize_text(s: str) -> str:
    """Frozen M5D1 text normalization (protocol criterion C)."""
    block = "|".join(re.escape(t) for t in BLOCK_TAGS)
    s = re.sub(rf"</?(?:{block})(?:\s[^>]*)?/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", " ", s).strip()


PRIME_CHARS = "′’ʹ‘`´'"


def normalize_name(name: str) -> str:
    """Frozen bridge normalization: drop class prefix/whitespace, Greek -> Latin, primes -> ', casefold."""
    s = unicodedata.normalize("NFKC", name)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"^(MBON|PAM|PPL1)-", "", s)
    s = s.replace("γ", "y").replace("α", "a").replace("β", "B")
    for ch in PRIME_CHARS:
        s = s.replace(ch, "'")
    return s.casefold()


def name_class(name: str):
    m = re.match(r"^(MBON|PAM|PPL1)-", unicodedata.normalize("NFKC", name).strip())
    if not m:
        return None, None
    return ("MBON", None) if m.group(1) == "MBON" else ("DAN", m.group(1))


def parse_set(norm_name: str, cls: str):
    side = norm_name.split("<")[0] if cls == "DAN" else norm_name.split(">")[0]
    canon = {"b1": "B1", "b2": "B2", "b'1": "B'1", "b'2": "B'2"}
    return frozenset(canon.get(t, t) for t in COMP_TOKEN.findall(side))


def instance_token(instance: str):
    m = re.match(r"^(?P<type>[^()]+?)(?:\((?P<tok>.*)\))?_(?:L|R)$", instance)
    if not m:
        raise ValueError(f"unparseable instance {instance!r}")
    return m.group("type"), (m.group("tok") or "")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    parity = {"protocol_present": Path(PROTOCOL_PATH).is_file(), "table_present": Path(TABLE_PATH).is_file()}
    for sid, (fname, want) in SOURCES.items():
        p = SRC / fname
        parity[f"{sid}_sha256"] = p.is_file() and sha256(p) == want
    parity["annotations_sha256"] = ANN.is_file() and sha256(ANN) == ANN_SHA
    parity["m5b3b_result_sha256"] = sha256(M5B3B_RESULT) == M5B3B_RESULT_SHA
    parity["m5b3b_script_sha256"] = sha256(M5B3B_SCRIPT) == M5B3B_SCRIPT_SHA
    base = {
        "protocol_sha256": sha256(PROTOCOL_PATH) if parity["protocol_present"] else None,
        "table_sha256": sha256(TABLE_PATH) if parity["table_present"] else None,
        "elife_article_xml_commit": ELIFE_COMMIT,
        "source_parity": parity,
    }
    if not all(parity.values()):
        write_result({"classification": "BLOCKED_M5D1_SOURCE_PARITY", "reason": "pinned source/anchor mismatch", **base})
        return

    texts = {sid: normalize_text((SRC / f).read_text(encoding="utf-8")) for sid, (f, _) in SOURCES.items()}
    table = json.loads(Path(TABLE_PATH).read_text(encoding="utf-8"))
    m5b3b = load_module("v6_m5b3b_frozen", M5B3B_SCRIPT)
    m5b3b_result = json.loads(Path(M5B3B_RESULT).read_text(encoding="utf-8"))

    # Frozen MaleCNS records: (type, instance token) with frozen compartment sets.
    ann = feather.read_table(ANN, columns=["bodyId", "class", "type", "instance"]).to_pandas()
    records = {"DAN": {}, "MBON": {}}
    for _, row in ann[ann["class"] == "DAN"].iterrows():
        typ = m5b3b.norm(row["type"])
        if typ not in FAST_DAN_TYPES:
            continue
        itype, tok = instance_token(m5b3b.norm(row["instance"]))
        key = (typ, tok)
        records["DAN"][key] = {"cluster": "PAM" if typ.startswith("PAM") else "PPL1", "set": frozenset(m5b3b.DAN_MAP[typ])}
    per_body = {int(b["bodyId"]): b for b in m5b3b_result["mbon_mapping"]["per_body"]}
    for _, row in ann[ann["class"] == "MBON"].iterrows():
        typ = m5b3b.norm(row["type"])
        itype, tok = instance_token(m5b3b.norm(row["instance"]))
        comps = per_body[int(row["bodyId"])]["compartments"] or []
        records["MBON"][(typ, tok)] = {"cluster": None, "set": frozenset(comps)}

    checks = {}
    fails = []

    def check(name, ok, detail=None):
        ok = bool(ok)
        checks.setdefault(name, True)
        checks[name] &= ok
        if not ok and len(fails) < 300:
            fails.append({"criterion": name, "detail": detail})
        return ok

    # B. Completeness.
    tab = {"DAN": {(r["type"], r["token"]): r for r in table.get("dan_records", [])},
           "MBON": {(r["type"], r["token"]): r for r in table.get("mbon_records", [])}}
    check("B_completeness", len(records["DAN"]) == EXPECTED_DAN_RECORDS, {"dan_records_frozen": len(records["DAN"])})
    check("B_completeness", len(records["MBON"]) == EXPECTED_MBON_RECORDS, {"mbon_records_frozen": len(records["MBON"])})
    for cls, labels in (("DAN", DAN_LABELS), ("MBON", MBON_LABELS)):
        check("B_completeness", set(tab[cls]) == set(records[cls]),
              {"class": cls, "missing": sorted(map(list, set(records[cls]) - set(tab[cls]))),
               "extra": sorted(map(list, set(tab[cls]) - set(records[cls])))})
        n_listed = len(table.get("dan_records" if cls == "DAN" else "mbon_records", []))
        check("B_completeness", n_listed == len(tab[cls]), {"class": cls, "duplicate_records": n_listed - len(tab[cls])})
        for key, r in tab[cls].items():
            check("B_completeness", r.get("label") in labels, {"record": list(key), "label": r.get("label")})

    # D. Bridge integrity: recompute from all source names used or inventoried.
    inventory = table.get("inventory", [])
    all_names = sorted(set([i["name"] for i in inventory] +
                           [n for cls in tab for r in tab[cls].values() for n in r.get("source_names", [])]))
    bridged = {"DAN": {k: [] for k in records["DAN"]}, "MBON": {k: [] for k in records["MBON"]}}
    rule_of = {"DAN": {}, "MBON": {}}
    parsed = {}
    for n in all_names:
        cls, cluster = name_class(n)
        if cls is None:
            continue
        nn = normalize_name(n)
        parsed[n] = (cls, cluster, nn)
        for key in records[cls]:
            if (cls == "DAN" and records[cls][key]["cluster"] != cluster):
                continue
            if key[1] and key[1].casefold() == nn:
                bridged[cls][key].append(n)
                rule_of[cls][key] = "primary"
    primary_types = {cls: {k[0] for k, r in rule_of[cls].items() if r == "primary"} for cls in rule_of}
    for n, (cls, cluster, nn) in parsed.items():
        s = parse_set(nn, cls)
        if not s:
            continue  # fallback requires a non-empty parsed compartment set
        cands = [k for k, v in records[cls].items()
                 if v["set"] == s and (cls == "MBON" or v["cluster"] == cluster)]
        types = sorted(set(k[0] for k in cands))
        if len(types) != 1 or types[0] in primary_types[cls]:
            continue  # fallback only for a unique type with no primary match
        for k in cands:
            bridged[cls][k].append(n)
            rule_of[cls][k] = "fallback"
    for cls in ("DAN", "MBON"):
        for key, r in tab[cls].items():
            want = sorted(set(bridged[cls].get(key, [])))
            got = sorted(set(r.get("source_names", [])))
            want_rule = rule_of[cls].get(key, "none")
            check("D_bridge_integrity", want == got and r.get("bridge_rule") == want_rule,
                  {"record": list(key), "expected_names": want, "table_names": got,
                   "expected_rule": want_rule, "table_rule": r.get("bridge_rule")})

    # C. Evidence integrity.
    for cls, src in (("DAN", "S1"), ("MBON", "S2")):
        for key, r in tab[cls].items():
            label = r.get("label")
            names = r.get("source_names", [])
            ev = r.get("evidence", [])
            if not names:
                check("C_evidence_integrity", label == "UNTESTED", {"record": list(key), "reason": "no bridged name but labeled"})
            if label != "UNTESTED":
                check("C_evidence_integrity", len(ev) > 0, {"record": list(key), "reason": "no evidence"})
            for e in ev:
                q = normalize_text(e.get("quote", ""))
                ok = (e.get("source") == src and 0 < len(q) <= MAX_QUOTE and q in texts[src]
                      and any(normalize_text(n) in q for n in names))
                check("C_evidence_integrity", ok, {"record": list(key), "source": e.get("source"), "quote_start": q[:80]})
            for e in r.get("context_quotes", []):  # amendment 2026-09-26, provision 3
                q = normalize_text(e.get("quote", ""))
                ok = e.get("source") == src and 0 < len(q) <= MAX_QUOTE and q in texts[src] and label == "UNRESOLVED"
                check("C_evidence_integrity", ok, {"record": list(key), "context_quote_start": q[:80]})

    # F. Inventory completeness against the frozen name scan.
    scanned = set()
    for src, cls in (("S1", "DAN"), ("S2", "MBON")):
        for m in NAME_SCAN.finditer(texts[src]):
            n = m.group(0).rstrip(".")
            c, _ = name_class(n)
            if c == cls:
                scanned.add((src, n))
    inv = {(i.get("source"), i.get("name")): i for i in inventory}
    check("F_inventory_completeness", set(inv) == scanned,
          {"missing_from_inventory": sorted(map(list, scanned - set(inv)))[:50],
           "not_found_by_scan": sorted(map(list, set(inv) - scanned))[:50]})
    used_names = {n for cls in tab for r in tab[cls].values() for n in r.get("source_names", [])}
    for (src, n), i in inv.items():
        bridges = any(n in v for cls in bridged for v in bridged[cls].values())
        if bridges:
            check("F_inventory_completeness", i.get("disposition") == "used" and n in used_names,
                  {"name": n, "disposition": i.get("disposition")})
        else:
            check("F_inventory_completeness", i.get("disposition") in ("used", "unused") and (i.get("disposition") != "used" or n in used_names),
                  {"name": n, "disposition": i.get("disposition")})

    # E. No outcome contamination (structural: manifest is fixed; table carries no numeric outcome fields).
    forbidden = re.compile(r"mnq|pnl|reward_value|market|price", re.IGNORECASE)
    check("E_no_outcome_contamination", not forbidden.search(json.dumps(sorted(table.keys()))), sorted(table.keys()))

    # Diagnostics: label counts and per-compartment signed coverage.
    counts = {cls: {} for cls in tab}
    for cls in tab:
        for r in tab[cls].values():
            counts[cls][r["label"]] = counts[cls].get(r["label"], 0) + 1
    gates = m5b3b_result["fast_dan"]["gate_population_by_compartment"]
    dan_type_of = {}
    for _, row in ann[ann["class"] == "DAN"].iterrows():
        dan_type_of[int(row["bodyId"])] = m5b3b.norm(row["type"])
    dan_label = {k[0]: r["label"] for k, r in tab["DAN"].items()}
    coverage = {}
    for c in ELIGIBLE_COMPARTMENTS:
        gate_types = sorted(set(dan_type_of[b] for b in gates[c]))
        mb = [(b["type"], instance_token(b["instance"])[1]) for b in m5b3b_result["mbon_mapping"]["per_body"]
              if b["status"] == "single_compartment" and b["compartments"] == [c]]
        mb_labels = sorted(set(tab["MBON"][k]["label"] for k in mb if k in tab["MBON"]))
        coverage[c] = {
            "gate_dan_types": {t: dan_label.get(t) for t in gate_types},
            "any_signed_teaching_label": any(dan_label.get(t) in SIGNED for t in gate_types),
            "single_compartment_mbon_labels": mb_labels,
            "any_signed_mbon_label": any(l in SIGNED for l in mb_labels),
        }

    criteria = {"A_source_parity": True}
    for name in ("B_completeness", "C_evidence_integrity", "D_bridge_integrity", "E_no_outcome_contamination", "F_inventory_completeness"):
        criteria[name] = checks.get(name, False)
    passed = all(criteria.values())
    write_result({
        "classification": "PASS_M5D1_VALENCE_SOURCE_TABLE_FROZEN" if passed else "FAIL_M5D1_VALENCE_SOURCE_INTEGRITY",
        "reason": "all frozen valence-table integrity criteria held" if passed else "at least one frozen integrity criterion failed",
        **base,
        "criteria": criteria,
        "failure_records": fails,
        "label_counts": counts,
        "compartment_coverage": coverage,
        "inventory_size": len(inv),
        "guardrails": {"market_reward_pnl_opened": False, "model_outcome_used": False,
                       "cluster_prior_used_as_source": False, "amin_numeric_opened": False, "m4v0_numeric_opened": False},
    })


def write_result(result):
    (O / "v6_m5d1_valence_source_result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: result.get(k) for k in ("classification", "reason", "criteria", "label_counts")}, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
