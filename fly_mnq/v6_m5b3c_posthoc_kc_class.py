"""Post-hoc diagnostic for the V6-M5B3C FAIL record (not a gate; no criterion).

KC axons are confined to their lobe system (gamma KCs to the gamma lobe, alpha/beta KCs to the alpha/beta lobes,
alpha'/beta' KCs to the alpha'/beta' lobes). This script measures how often the official `subprimary` label of a
KC->MBON synapse names a compartment outside the lobe system of its presynaptic KC.

Inputs: the M5B3C per-synapse artifact v6_m5b3c_kc_mbon_synapses.npz (SHA256 ae61c997..., byte-identical in the
GitHub Actions run 36294693074 and the local run), the pinned body annotations, and the M5B3B result JSON.
Usage: python fly_mnq/v6_m5b3c_posthoc_kc_class.py <synapses.npz> <body-annotations.feather>
"""
from __future__ import annotations

import hashlib
import json
import sys

import numpy as np
import pandas as pd
import pyarrow.feather as feather

LOBE15 = ("a1", "a2", "a3", "a'1", "a'2", "a'3", "B1", "B2", "B'1", "B'2", "y1", "y2", "y3", "y4", "y5")
SYNAPSES_SHA = "ae61c997cbeb646f3544a5b61b0d21972733279adb2f3d71391876c50179d1e4"
ANN_SHA = "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
M5B3B_RESULT = "research/results/v6_m5b3b_compartment_gating_mvp_result.json"


def lobe_system(code: str) -> str:
    return "gamma" if code.startswith("y") else ("alpha_prime_beta_prime" if "'" in code else "alpha_beta")


def kc_system(kc_type: str) -> str:
    if kc_type.startswith("KCg"):
        return "gamma"
    if kc_type.startswith("KCa'b'"):
        return "alpha_prime_beta_prime"
    if kc_type.startswith("KCab"):
        return "alpha_beta"
    return "unknown"


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main(syn_path, ann_path):
    out = {"inputs_verified": sha256(syn_path) == SYNAPSES_SHA and sha256(ann_path) == ANN_SHA}
    syn = np.load(syn_path)
    ann = feather.read_table(ann_path, columns=["bodyId", "type"]).to_pandas()
    kc_type = dict(zip(ann["bodyId"].astype(np.int64).tolist(), ann["type"].astype(str).tolist()))
    pre, post, code = syn["body_pre"], syn["body_post"], syn["lobe_code"]
    ks = np.array([kc_system(kc_type[int(b)]) for b in pre])
    resolved = code >= 0
    ls = np.array([lobe_system(LOBE15[c]) if c >= 0 else "" for c in code])
    known = resolved & (ks != "unknown")
    out["resolved_synapses"] = int(resolved.sum())
    out["resolved_with_known_kc_class"] = int(known.sum())
    out["kc_class_label_lobe_consistent_fraction"] = float(((ks == ls) & known).sum() / known.sum())
    tab = pd.crosstab(pd.Series(ks[known], name="kc"), pd.Series(ls[known], name="label"))
    out["crosstab_kc_class_by_label_lobe"] = {r: {c: int(tab.loc[r, c]) for c in tab.columns} for r in tab.index}
    ref = json.load(open(M5B3B_RESULT, encoding="utf-8"))["mbon_mapping"]["per_body"]
    nominal = {int(r["bodyId"]): r["compartments"][0] for r in ref if r["status"] == "single_compartment"}
    sel = np.isin(post, np.array(sorted(nominal), dtype=np.int64))
    nom = np.array([LOBE15.index(nominal[int(b)]) for b in post[sel]])
    c = code[sel]
    out["single_compartment_agreement_including_unresolved"] = float((c == nom).mean())
    out["single_compartment_agreement_resolved_only"] = float((c[c >= 0] == nom[c >= 0]).mean())
    nsys = np.array([lobe_system(LOBE15[i]) for i in nom])
    kss = ks[sel]
    out["single_compartment_input_from_other_lobe_system_kcs"] = float(((kss != nsys) & (kss != "unknown")).mean())
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
