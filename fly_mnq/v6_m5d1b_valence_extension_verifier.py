from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pyarrow.feather as feather

SRC = Path("v6_m5d1_work")          # pinned eLife XML sources S1-S6
ANN = Path("v6_m5b3b_work/body-annotations.feather")
O = Path("v6_m5d1b_out")
O.mkdir(exist_ok=True)

PROTOCOL_PATH = "research/v6_m5d1b_valence_extension_protocol.md"
AMENDMENT_PATH = "research/v6_m5d1b_valence_extension_protocol_amendment_20260926.md"
TABLE_PATH = "research/v6_m5d1b_valence_extension_table.json"
M5D1_VERIFIER = "fly_mnq/v6_m5d1_valence_source_verifier.py"
ANCHORS = {
    M5D1_VERIFIER: "e220fc4e16affa742c96b7b3857b93e6f98004f4b42bddbbb0213c3167e87a3a",
    "research/v6_m5d1_valence_source_table.json": "72804479baeea2c2c81f11d6344ca3b6616b7e0f2d1a60da9030fc47ae5fee42",
    "research/results/v6_m5d1_valence_source_result.json": "996070bbd217195dac39600eaa90fa5a44d3ce3902aa2ded12b2eab161c8679d",
    "research/v6_m5d1_valence_source_protocol_amendment_20260926.md": "e86079975e3ec08db2a231cffc1414bfcf415dd14deec406ab787f0340e79e5a",
    PROTOCOL_PATH: "6499ce037b98643c8110e59677e569d799ecca2c13e0f0abd246a4b2f5b3fdd3",
}
NEW_SOURCES = {
    "S5": ("elife-90523-v1.xml", "876ef708f2269ae5c7ea9743d65e4fcffb5e8efb0d69936f7715fe468e5b1f31"),
    "S6": ("elife-49257-v3.xml", "f1166b0c679009497f5c52b38cb12cfe1646375e33183c87e7376a5fa3131496"),
}
NEW_EVIDENCE_SOURCE = {"DAN": "S6", "MBON": "S5"}
SIGNS = {"APPETITIVE": ("DAN", +1), "AVERSIVE": ("DAN", -1), "ATTRACTIVE": ("MBON", +1), "REPULSIVE": ("MBON", -1)}
NOSIG = {"NO_SIGNIFICANT_MEMORY", "NO_SIGNIFICANT_EFFECT"}
CONFLICT_MARK = "Amendment provision 2"


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def classify(label, conflict):
    if label in SIGNS:
        return "signed"
    if label in NOSIG:
        return "nosig"
    if label == "UNRESOLVED":
        return "conflict" if conflict else "gap"
    return "untested"


def merge(cls, old_label, old_conflict, new_label, new_conflict):
    """Frozen M5D1B merge rule (protocol section 'Frozen merge rule')."""
    kinds = [classify(old_label, old_conflict), classify(new_label, new_conflict)]
    if "conflict" in kinds:
        return "UNRESOLVED"
    signs = {l for l in (old_label, new_label) if l in SIGNS}
    if len({SIGNS[l][1] for l in signs}) > 1:
        return "UNRESOLVED"
    if len(signs) == 1:
        return "UNRESOLVED" if "nosig" in kinds else next(iter(signs))
    if "nosig" in kinds:
        return "NO_SIGNIFICANT_MEMORY" if cls == "DAN" else "NO_SIGNIFICANT_EFFECT"
    return "UNRESOLVED" if "gap" in kinds else "UNTESTED"


def main():
    parity = {"table_present": Path(TABLE_PATH).is_file(), "amendment_present": Path(AMENDMENT_PATH).is_file()}
    for path, want in ANCHORS.items():
        parity["sha256:" + path] = Path(path).is_file() and sha256(path) == want
    base = {"source_parity": parity}
    if not all(parity.values()):
        write_result({"classification": "BLOCKED_M5D1B_SOURCE_PARITY", "reason": "frozen anchor mismatch", **base})
        return
    v = load_module("v6_m5d1_frozen_verifier", M5D1_VERIFIER)
    sources = dict(v.SOURCES)
    sources.update(NEW_SOURCES)
    for sid, (fname, want) in sources.items():
        p = SRC / fname
        parity[f"{sid}_sha256"] = p.is_file() and sha256(p) == want
    parity["annotations_sha256"] = ANN.is_file() and sha256(ANN) == v.ANN_SHA
    parity["m5b3b_result_sha256"] = sha256(v.M5B3B_RESULT) == v.M5B3B_RESULT_SHA
    parity["m5b3b_script_sha256"] = sha256(v.M5B3B_SCRIPT) == v.M5B3B_SCRIPT_SHA
    base.update({"table_sha256": sha256(TABLE_PATH), "amendment_sha256": sha256(AMENDMENT_PATH)})
    if not all(parity.values()):
        write_result({"classification": "BLOCKED_M5D1B_SOURCE_PARITY", "reason": "pinned source mismatch", **base})
        return

    texts = {sid: v.normalize_text((SRC / f).read_text(encoding="utf-8")) for sid, (f, _) in sources.items()}
    table = json.loads(Path(TABLE_PATH).read_text(encoding="utf-8"))
    m5d1 = json.loads(Path("research/v6_m5d1_valence_source_table.json").read_text(encoding="utf-8"))
    m5b3b = v.load_module("v6_m5b3b_frozen", v.M5B3B_SCRIPT)
    m5b3b_result = json.loads(Path(v.M5B3B_RESULT).read_text(encoding="utf-8"))

    ann = feather.read_table(ANN, columns=["bodyId", "class", "type", "instance"]).to_pandas()
    records = {"DAN": {}, "MBON": {}}
    for _, row in ann[ann["class"] == "DAN"].iterrows():
        typ = m5b3b.norm(row["type"])
        if typ in v.FAST_DAN_TYPES:
            _, tok = v.instance_token(m5b3b.norm(row["instance"]))
            records["DAN"][(typ, tok)] = {"cluster": "PAM" if typ.startswith("PAM") else "PPL1", "set": frozenset(m5b3b.DAN_MAP[typ])}
    per_body = {int(b["bodyId"]): b for b in m5b3b_result["mbon_mapping"]["per_body"]}
    for _, row in ann[ann["class"] == "MBON"].iterrows():
        typ = m5b3b.norm(row["type"])
        _, tok = v.instance_token(m5b3b.norm(row["instance"]))
        records["MBON"][(typ, tok)] = {"cluster": None, "set": frozenset(per_body[int(row["bodyId"])]["compartments"] or [])}

    checks, fails = {}, []

    def check(name, ok, detail=None):
        ok = bool(ok)
        checks[name] = checks.get(name, True) and ok
        if not ok and len(fails) < 300:
            fails.append({"criterion": name, "detail": detail})

    old = {"DAN": {(r["type"], r["token"]): r for r in m5d1["dan_records"]},
           "MBON": {(r["type"], r["token"]): r for r in m5d1["mbon_records"]}}
    tab = {"DAN": {(r["type"], r["token"]): r for r in table.get("dan_records", [])},
           "MBON": {(r["type"], r["token"]): r for r in table.get("mbon_records", [])}}
    vocab = {"DAN": v.DAN_LABELS, "MBON": v.MBON_LABELS}

    # B. Completeness and M5D1 label parity.
    for cls in ("DAN", "MBON"):
        check("B_completeness", set(tab[cls]) == set(records[cls]) == set(old[cls]), {"class": cls})
        listed = len(table.get("dan_records" if cls == "DAN" else "mbon_records", []))
        check("B_completeness", listed == len(tab[cls]), {"class": cls, "duplicates": listed - len(tab[cls])})
        for key, r in tab[cls].items():
            o = old[cls].get(key)
            nf = r.get("new_finding", {})
            check("B_completeness", o is not None and r.get("m5d1_label") == o["label"], {"record": list(key)})
            check("B_completeness", nf.get("label") in vocab[cls] and r.get("merged_label") in vocab[cls], {"record": list(key)})

    # D. Bridge integrity of new findings (per new source).
    bridged = {"DAN": {k: [] for k in records["DAN"]}, "MBON": {k: [] for k in records["MBON"]}}
    rule_of = {"DAN": {}, "MBON": {}}
    inv_key = {"DAN": "inventory_s6", "MBON": "inventory_s5"}
    for cls in ("DAN", "MBON"):
        names = sorted(set([i["name"] for i in table.get(inv_key[cls], [])] +
                           [n for r in tab[cls].values() for n in r.get("new_finding", {}).get("source_names", [])]))
        parsed = {}
        for n in names:
            c, cluster = v.name_class(n)
            if c != cls:
                continue
            nn = v.normalize_name(n)
            parsed[n] = (cluster, nn)
            for key, rec in records[cls].items():
                if cls == "DAN" and rec["cluster"] != cluster:
                    continue
                if key[1] and key[1].casefold() == nn:
                    bridged[cls][key].append(n)
                    rule_of[cls][key] = "primary"
        primary_types = {k[0] for k, r in rule_of[cls].items() if r == "primary"}
        for n, (cluster, nn) in parsed.items():
            s = v.parse_set(nn, cls)
            if not s:
                continue
            cands = [k for k, rec in records[cls].items() if rec["set"] == s and (cls == "MBON" or rec["cluster"] == cluster)]
            types = sorted(set(k[0] for k in cands))
            if len(types) != 1 or types[0] in primary_types:
                continue
            for k in cands:
                bridged[cls][k].append(n)
                rule_of[cls][k] = "fallback"
        for key, r in tab[cls].items():
            nf = r.get("new_finding", {})
            want = sorted(set(bridged[cls][key]))
            check("D_bridge_integrity", want == sorted(set(nf.get("source_names", []))) and nf.get("bridge_rule") == rule_of[cls].get(key, "none"),
                  {"record": list(key), "expected": want, "got": nf.get("source_names"), "rule": nf.get("bridge_rule")})

    # C. Evidence integrity of new findings.
    for cls in ("DAN", "MBON"):
        src = NEW_EVIDENCE_SOURCE[cls]
        for key, r in tab[cls].items():
            nf = r.get("new_finding", {})
            label, names = nf.get("label"), nf.get("source_names", [])
            if not names:
                check("C_evidence_integrity", label == "UNTESTED", {"record": list(key), "reason": "no bridged name but labeled"})
            if label != "UNTESTED":
                check("C_evidence_integrity", len(nf.get("evidence", [])) > 0, {"record": list(key), "reason": "no evidence"})
            if nf.get("conflict"):
                check("C_evidence_integrity", label == "UNRESOLVED", {"record": list(key), "reason": "conflict requires UNRESOLVED"})
            for e in nf.get("evidence", []):
                q = v.normalize_text(e.get("quote", ""))
                ok = e.get("source") == src and 0 < len(q) <= v.MAX_QUOTE and q in texts[src] and any(v.normalize_text(n) in q for n in names)
                check("C_evidence_integrity", ok, {"record": list(key), "quote_start": q[:80]})
            for e in nf.get("context_quotes", []):
                q = v.normalize_text(e.get("quote", ""))
                check("C_evidence_integrity", e.get("source") == src and 0 < len(q) <= v.MAX_QUOTE and q in texts[src],
                      {"record": list(key), "context_quote_start": q[:80]})
            for e in nf.get("alias_quotes", []):  # M5D1B amendment provision 1
                q = v.normalize_text(e.get("quote", ""))
                ok = e.get("source") in ("S3", "S4", src) and 0 < len(q) <= v.MAX_QUOTE and q in texts[e.get("source")] and nf.get("conflict") is True
                check("C_evidence_integrity", ok, {"record": list(key), "alias_quote_start": q[:80]})

    # F. Inventory completeness (S5 MBON names, S6 DAN names).
    for cls in ("DAN", "MBON"):
        src = NEW_EVIDENCE_SOURCE[cls]
        scanned = set()
        for m in v.NAME_SCAN.finditer(texts[src]):
            n = m.group(0).rstrip(".")
            if v.name_class(n)[0] == cls:
                scanned.add(n)
        inv = {i["name"]: i for i in table.get(inv_key[cls], [])}
        check("F_inventory_completeness", set(inv) == scanned, {"class": cls, "missing": sorted(scanned - set(inv))[:40], "extra": sorted(set(inv) - scanned)[:40]})
        used = {n for r in tab[cls].values() for n in r.get("new_finding", {}).get("source_names", [])}
        for n, i in inv.items():
            if any(n in b for b in bridged[cls].values()):
                check("F_inventory_completeness", i.get("disposition") == "used" and n in used, {"name": n})
            else:
                check("F_inventory_completeness", i.get("disposition") in ("used", "unused") and (i.get("disposition") != "used" or n in used), {"name": n})

    # E. No outcome contamination.
    forbidden = re.compile(r"mnq|pnl|reward_value|market|price", re.IGNORECASE)
    check("E_no_outcome_contamination", not forbidden.search(json.dumps(sorted(table.keys()))), sorted(table.keys()))

    # G. Merge correctness.
    for cls in ("DAN", "MBON"):
        for key, r in tab[cls].items():
            o = old[cls][key]
            old_conflict = o["label"] == "UNRESOLVED" and CONFLICT_MARK in o.get("note", "")
            nf = r.get("new_finding", {})
            want = merge(cls, o["label"], old_conflict, nf.get("label"), bool(nf.get("conflict")))
            check("G_merge_correctness", r.get("merged_label") == want, {"record": list(key), "expected": want, "got": r.get("merged_label")})

    # Diagnostics.
    counts = {cls: {} for cls in tab}
    for cls in tab:
        for r in tab[cls].values():
            counts[cls][r["merged_label"]] = counts[cls].get(r["merged_label"], 0) + 1
    gates = m5b3b_result["fast_dan"]["gate_population_by_compartment"]
    dan_type_of = {int(row["bodyId"]): m5b3b.norm(row["type"]) for _, row in ann[ann["class"] == "DAN"].iterrows()}
    dan_label = {k[0]: r["merged_label"] for k, r in tab["DAN"].items()}
    coverage, closed = {}, []
    for c in v.ELIGIBLE_COMPARTMENTS:
        gtypes = sorted(set(dan_type_of[b] for b in gates[c]))
        mb = [(b["type"], v.instance_token(b["instance"])[1]) for b in m5b3b_result["mbon_mapping"]["per_body"]
              if b["status"] == "single_compartment" and b["compartments"] == [c]]
        mlabels = sorted(set(tab["MBON"][k]["merged_label"] for k in mb))
        dsigned = sorted(set(dan_label[t] for t in gtypes if dan_label.get(t) in SIGNS))
        msigned = [l for l in mlabels if l in SIGNS]
        coverage[c] = {"gate_dan_merged": {t: dan_label.get(t) for t in gtypes}, "single_compartment_mbon_merged": mlabels,
                       "signed_teaching": dsigned, "signed_mbon": msigned}
        if dsigned and msigned:
            closed.append(c)

    criteria = {"A_source_parity": True}
    for name in ("B_completeness", "C_evidence_integrity", "D_bridge_integrity", "E_no_outcome_contamination",
                 "F_inventory_completeness", "G_merge_correctness"):
        criteria[name] = checks.get(name, False)
    passed = all(criteria.values())
    write_result({
        "classification": "PASS_M5D1B_VALENCE_EXTENSION_FROZEN" if passed else "FAIL_M5D1B_VALENCE_EXTENSION_INTEGRITY",
        "reason": "all frozen extension criteria held" if passed else "at least one frozen extension criterion failed",
        **base,
        "criteria": criteria,
        "failure_records": fails,
        "merged_label_counts": counts,
        "compartment_coverage": coverage,
        "compartments_with_signed_teaching_and_signed_plastic_mbon": closed,
        "guardrails": {"market_reward_pnl_opened": False, "model_outcome_used": False,
                       "cluster_prior_used_as_source": False, "amin_numeric_opened": False, "m4v0_numeric_opened": False},
    })


def write_result(result):
    (O / "v6_m5d1b_valence_extension_result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: result.get(k) for k in ("classification", "reason", "criteria", "merged_label_counts",
                                                  "compartments_with_signed_teaching_and_signed_plastic_mbon")},
                     indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
