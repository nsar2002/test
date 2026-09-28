from __future__ import annotations

import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

PROTOCOL_PATH = "research/v6_m5g0_nonmarket_theta_selection_protocol.md"
PROTOCOL_FREEZE_COMMIT = "2c7dcc8"
PROTOCOL_SHA = "efe42171b6e7e306f4ecd56ecd45dd91907f44203a64c94e784dbd499971b8fd"
M5F0_RESULT = "research/results/v6_m5f0_teaching_result.json"
M5F0_PASS = "PASS_M5F0_TEACHING_SEMANTICS_QUALIFIED"
WORLDS = ("PLANTED:connectome", "PLANTED:rewired", "AR(+0.3):connectome", "AR(-0.3):connectome")
PARAMS = ("eta_minus", "eta_plus", "lam_K", "lam_D", "g_max")
# M5C GRID as frozen (values in listed order); its product order is the tie order.
GRID_LEVELS = ((0.05, 0.5), (0.05, 0.5), (0.0, 0.5, 0.9), (0.0, 0.5, 0.9), (1.5, 2.0))
THRESHOLD = 0.0691
O = Path("v6_m5g0_out")


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def select(m5f0):
    grid = m5f0["diagnostics"]["grid"]
    rows = {w: grid[w] for w in WORLDS}
    expected = list(itertools.product(*GRID_LEVELS))
    if any(len(rows[w]) != len(expected) for w in WORLDS):
        raise ValueError("grid does not have the frozen 72 points in every world")
    points = []
    for i, key in enumerate(expected):
        if any(tuple(rows[w][i][p] for p in PARAMS) != key for w in WORLDS):
            raise ValueError(f"grid point {i} is not in frozen M5C product order")
        rhos = {w: rows[w][i]["rho_os"] for w in WORLDS}
        if not all(isinstance(v, float) and math.isfinite(v) for v in rhos.values()):
            raise ValueError(f"grid point {i} has a non-finite rho_os")
        points.append({"order": i, "theta": dict(zip(PARAMS, key)), "rho_os": rhos, "worst": min(rhos.values())})
    best = max(p["worst"] for p in points)
    star = min((p for p in points if p["worst"] == best), key=lambda p: p["order"])
    return points, star


def main(result_path=M5F0_RESULT):
    O.mkdir(exist_ok=True)
    out = {"protocol": {"path": PROTOCOL_PATH, "sha256": PROTOCOL_SHA, "freeze_commit": PROTOCOL_FREEZE_COMMIT},
           "threshold": THRESHOLD}
    proto_ok = Path(PROTOCOL_PATH).is_file() and sha256(PROTOCOL_PATH) == PROTOCOL_SHA
    try:
        m5f0 = json.loads(Path(result_path).read_text(encoding="utf-8"))
        out["m5f0_result"] = {"path": str(result_path), "sha256": sha256(result_path), "classification": m5f0.get("classification")}
        if not proto_ok or m5f0.get("classification") != M5F0_PASS:
            return finish(out, "BLOCKED_M5G0_PREREQUISITE", "protocol hash mismatch or M5F0 not PASS")
        points, star = select(m5f0)
    except Exception as exc:
        return finish(out, "BLOCKED_M5G0_PREREQUISITE", f"M5F0 result missing or malformed: {exc!r}")
    ranked = sorted(points, key=lambda p: (-p["worst"], p["order"]))
    marg = {}
    for p in PARAMS:
        levels = sorted({pt["theta"][p] for pt in points})
        marg[p] = {str(v): sum(pt["worst"] for pt in points if pt["theta"][p] == v) / sum(1 for pt in points if pt["theta"][p] == v)
                   for v in levels}
    out.update({"theta_star": star["theta"], "theta_star_rho_os": star["rho_os"], "theta_star_worst": star["worst"],
                "diagnostics": {"top10": ranked[:10], "marginal_mean_worst": marg,
                                "fraction_wrong_sign_momentum": sum(1 for pt in points if pt["rho_os"]["AR(+0.3):connectome"] < 0) / len(points)}})
    if star["worst"] > THRESHOLD:
        return finish(out, "PASS_M5G0_THETA_SELECTED", "theta* learns all four worlds above the threshold")
    return finish(out, "FAIL_M5G0_NO_THETA_LEARNS_ALL_WORLDS", "no grid point learns all four worlds above the threshold")


def finish(out, classification, reason):
    out.update({"classification": classification, "reason": reason})
    (O / "v6_m5g0_theta_selection_result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out.get(k) for k in ("classification", "reason", "theta_star", "theta_star_rho_os", "theta_star_worst")},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main(*sys.argv[1:])
