from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pyarrow.feather as feather

SRC = Path("v6_m5d1_work")
ANN = Path("v6_m5b3b_work/body-annotations.feather")
O = Path("v6_m5d1c_out")
O.mkdir(exist_ok=True)

PROTOCOL_PATH = "research/v6_m5d1c_type_number_bridge_protocol.md"
TABLE_PATH = "research/v6_m5d1c_type_number_bridge_table.json"
M5D1_VERIFIER = "fly_mnq/v6_m5d1_valence_source_verifier.py"
M5D1B_VERIFIER = "fly_mnq/v6_m5d1b_valence_extension_verifier.py"
M5D1B_TABLE = "research/v6_m5d1b_valence_extension_table.json"
ANCHORS = {
    PROTOCOL_PATH: "ca531a8ec50192f8252c2a7a980a6c5c69108f5daf89cdb6946f39c83eaa1b06",
    M5D1_VERIFIER: "e220fc4e16affa742c96b7b3857b93e6f98004f4b42bddbbb0213c3167e87a3a",
    M5D1B_VERIFIER: "e794fbcf1f14951994d00f2d33a279bc226e4172b036e0a8df11ab14f972dd13",
    M5D1B_TABLE: "4fb51f577e2136604ee15e5daf0b8d76888c3d601336e4742144c8a76e8dc5ff",
    "research/results/v6_m5d1b_valence_extension_result.json": "4ab95b21738fbeb61dbcebe4e647644c02b9d281c01d29ec4f78bb4a3cd38bad",
    "research/v6_m5d1_valence_source_table.json": "72804479baeea2c2c81f11d6344ca3b6616b7e0f2d1a60da9030fc47ae5fee42",
}
S4 = ("elife-62576-v2.xml", "d26350b4e8dcecfbb88c14e6fb1fc432b4d0dfcdf44483d75241583c1ace54c7")
S5 = ("elife-90523-v1.xml", "876ef708f2269ae5c7ea9743d65e4fcffb5e8efb0d69936f7715fe468e5b1f31")
TYPE_SCAN = re.compile(r"\bMBON\d{2}(?:-like)?\b")


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


def confirmed(v, texts, type_name, token):
    """Frozen cross-check: '<type> (<x>)' in S4 or S5 with normalize_name(x) == token (casefold)."""
    pat = re.compile(re.escape(type_name) + r"(?![\w-])\s*\(([^()]{1,40})\)")
    for t in texts:
        for m in pat.finditer(t):
            if v.normalize_name(m.group(1)) == token.casefold():
                return True
    return False


def main():
    parity = {"table_present": Path(TABLE_PATH).is_file()}
    for path, want in ANCHORS.items():
        parity["sha256:" + path] = Path(path).is_file() and sha256(path) == want
    base = {"source_parity": parity}
    if not all(parity.values()):
        write_result({"classification": "BLOCKED_M5D1C_SOURCE_PARITY", "reason": "frozen anchor mismatch", **base})
        return
    v = load_module("v6_m5d1_frozen_verifier", M5D1_VERIFIER)
    x = load_module("v6_m5d1b_frozen_verifier", M5D1B_VERIFIER)
    for sid, (fname, want) in (("S4", S4), ("S5", S5)):
        p = SRC / fname
        parity[f"{sid}_sha256"] = p.is_file() and sha256(p) == want
    parity["annotations_sha256"] = ANN.is_file() and sha256(ANN) == v.ANN_SHA
    base["table_sha256"] = sha256(TABLE_PATH)
    if not all(parity.values()):
        write_result({"classification": "BLOCKED_M5D1C_SOURCE_PARITY", "reason": "pinned source mismatch", **base})
        return

    t4 = v.normalize_text((SRC / S4[0]).read_text(encoding="utf-8"))
    t5 = v.normalize_text((SRC / S5[0]).read_text(encoding="utf-8"))
    table = json.loads(Path(TABLE_PATH).read_text(encoding="utf-8"))
    prev = json.loads(Path(M5D1B_TABLE).read_text(encoding="utf-8"))
    m5d1 = json.loads(Path("research/v6_m5d1_valence_source_table.json").read_text(encoding="utf-8"))
    m5b3b = v.load_module("v6_m5b3b_frozen", v.M5B3B_SCRIPT)
    m5b3b_result = json.loads(Path(v.M5B3B_RESULT).read_text(encoding="utf-8"))

    ann = feather.read_table(ANN, columns=["bodyId", "class", "type", "instance"]).to_pandas()
    mbon_records = set()
    for _, row in ann[ann["class"] == "MBON"].iterrows():
        typ = m5b3b.norm(row["type"])
        mbon_records.add((typ, v.instance_token(m5b3b.norm(row["instance"]))[1]))

    checks, fails = {}, []

    def check(name, ok, detail=None):
        ok = bool(ok)
        checks[name] = checks.get(name, True) and ok
        if not ok and len(fails) < 300:
            fails.append({"criterion": name, "detail": detail})

    prev_d = {(r["type"], r["token"]): r for r in prev["dan_records"]}
    prev_m = {(r["type"], r["token"]): r for r in prev["mbon_records"]}
    old_m5d1 = {(r["type"], r["token"]): r for r in m5d1["mbon_records"]}
    tab_d = {(r["type"], r["token"]): r for r in table.get("dan_records", [])}
    tab_m = {(r["type"], r["token"]): r for r in table.get("mbon_records", [])}

    # B. Completeness and parity with M5D1B merged labels.
    check("B_completeness", set(tab_d) == set(prev_d) and len(table.get("dan_records", [])) == len(prev_d) == 21, "dan set")
    check("B_completeness", set(tab_m) == set(prev_m) == mbon_records and len(table.get("mbon_records", [])) == 38, "mbon set")
    for k, r in tab_d.items():
        check("B_completeness", r.get("merged_label") == prev_d[k]["merged_label"], {"dan": list(k)})
    for k, r in tab_m.items():
        f = r.get("s5_finding", {})
        check("B_completeness", r.get("m5d1b_label") == prev_m[k]["merged_label"] and f.get("label") in v.MBON_LABELS
              and r.get("merged_label") in v.MBON_LABELS, {"mbon": list(k)})

    # D. Bridge integrity: exact type equality + frozen cross-check.
    scanned = sorted(set(TYPE_SCAN.findall(t5)))
    expected_names = {}
    for k in mbon_records:
        typ, tok = k
        expected_names[k] = [typ] if (typ in scanned and confirmed(v, (t4, t5), typ, tok)) else []
    for k, r in tab_m.items():
        f = r.get("s5_finding", {})
        want = expected_names[k]
        check("D_bridge_integrity", sorted(f.get("source_names", [])) == want
              and f.get("bridge_rule") == ("type_number" if want else "none"),
              {"record": list(k), "expected": want, "got": f.get("source_names"), "rule": f.get("bridge_rule")})

    # C. Evidence integrity (S5).
    for k, r in tab_m.items():
        f = r.get("s5_finding", {})
        label, names = f.get("label"), f.get("source_names", [])
        if not names:
            check("C_evidence_integrity", label == "UNTESTED", {"record": list(k)})
        if label != "UNTESTED":
            check("C_evidence_integrity", len(f.get("evidence", [])) > 0, {"record": list(k), "reason": "no evidence"})
        if f.get("conflict"):
            check("C_evidence_integrity", label == "UNRESOLVED", {"record": list(k)})
        for e in f.get("evidence", []):
            q = v.normalize_text(e.get("quote", ""))
            ok = (e.get("source") == "S5" and 0 < len(q) <= v.MAX_QUOTE and q in t5
                  and any(re.search(re.escape(n) + r"(?![\w-])", q) for n in names))
            check("C_evidence_integrity", ok, {"record": list(k), "quote_start": q[:80]})
        for e in f.get("context_quotes", []):
            q = v.normalize_text(e.get("quote", ""))
            check("C_evidence_integrity", e.get("source") == "S5" and 0 < len(q) <= v.MAX_QUOTE and q in t5, {"record": list(k)})

    # F. Inventory completeness.
    inv = {i["name"]: i for i in table.get("inventory_s5_numbers", [])}
    check("F_inventory_completeness", sorted(inv) == scanned, {"missing": sorted(set(scanned) - set(inv)), "extra": sorted(set(inv) - set(scanned))})
    used = {n for r in tab_m.values() for n in r.get("s5_finding", {}).get("source_names", [])}
    bridging = {n for names in expected_names.values() for n in names}
    for n, i in inv.items():
        if n in bridging:
            check("F_inventory_completeness", i.get("disposition") == "used" and n in used, {"name": n})
        else:
            check("F_inventory_completeness", i.get("disposition") == "unused" and n not in used, {"name": n})

    # E. No outcome contamination.
    forbidden = re.compile(r"mnq|pnl|reward_value|market|price", re.IGNORECASE)
    check("E_no_outcome_contamination", not forbidden.search(json.dumps(sorted(table.keys()))), sorted(table.keys()))

    # G. Merge correctness (frozen M5D1B merge function, old = M5D1B merged label).
    for k, r in tab_m.items():
        old_label = prev_m[k]["merged_label"]
        old_conflict = old_label == "UNRESOLVED" and x.CONFLICT_MARK in old_m5d1[k].get("note", "")
        f = r.get("s5_finding", {})
        want = x.merge("MBON", old_label, old_conflict, f.get("label"), bool(f.get("conflict")))
        check("G_merge_correctness", r.get("merged_label") == want, {"record": list(k), "expected": want, "got": r.get("merged_label")})

    # Diagnostics: coverage with plastic (single-compartment) MBONs.
    gates = m5b3b_result["fast_dan"]["gate_population_by_compartment"]
    dan_type_of = {int(row["bodyId"]): m5b3b.norm(row["type"]) for _, row in ann[ann["class"] == "DAN"].iterrows()}
    dan_label = {k[0]: r["merged_label"] for k, r in tab_d.items()}
    coverage, closed = {}, []
    for c in v.ELIGIBLE_COMPARTMENTS:
        gtypes = sorted(set(dan_type_of[b] for b in gates[c]))
        mb = [(b["type"], v.instance_token(b["instance"])[1]) for b in m5b3b_result["mbon_mapping"]["per_body"]
              if b["status"] == "single_compartment" and b["compartments"] == [c]]
        dsigned = sorted(set(dan_label[t] for t in gtypes if dan_label.get(t) in x.SIGNS))
        msigned = sorted(set(tab_m[k]["merged_label"] for k in mb if tab_m[k]["merged_label"] in x.SIGNS))
        coverage[c] = {"signed_teaching": dsigned, "signed_plastic_mbon": msigned}
        if dsigned and msigned:
            closed.append(c)
    signed_multi = sorted(f"{k[0]}({k[1]})={r['merged_label']}" for k, r in tab_m.items()
                          if r["merged_label"] in x.SIGNS and not any(b["type"] == k[0] and b["status"] == "single_compartment"
                                                                        for b in m5b3b_result["mbon_mapping"]["per_body"]))
    counts = {}
    for r in tab_m.values():
        counts[r["merged_label"]] = counts.get(r["merged_label"], 0) + 1

    criteria = {"A_source_parity": True}
    for name in ("B_completeness", "C_evidence_integrity", "D_bridge_integrity", "E_no_outcome_contamination",
                 "F_inventory_completeness", "G_merge_correctness"):
        criteria[name] = checks.get(name, False)
    passed = all(criteria.values())
    write_result({
        "classification": "PASS_M5D1C_TYPE_NUMBER_BRIDGE_FROZEN" if passed else "FAIL_M5D1C_TYPE_NUMBER_BRIDGE_INTEGRITY",
        "reason": "all frozen type-number bridge criteria held" if passed else "at least one frozen criterion failed",
        **base,
        "criteria": criteria,
        "failure_records": fails,
        "mbon_merged_label_counts": counts,
        "bridged_types": sorted({n for names in expected_names.values() for n in names}),
        "compartment_coverage": coverage,
        "compartments_with_signed_teaching_and_signed_plastic_mbon": closed,
        "signed_multi_compartment_mbons_nonplastic_under_m5b3b": signed_multi,
        "guardrails": {"market_reward_pnl_opened": False, "model_outcome_used": False, "cluster_prior_used_as_source": False},
    })


def write_result(result):
    (O / "v6_m5d1c_type_number_bridge_result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: result.get(k) for k in ("classification", "reason", "criteria", "mbon_merged_label_counts", "bridged_types",
                                                  "compartments_with_signed_teaching_and_signed_plastic_mbon",
                                                  "signed_multi_compartment_mbons_nonplastic_under_m5b3b")},
                     indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
