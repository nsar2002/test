from __future__ import annotations

import calendar
import datetime as dt
import hashlib
import importlib.util
import io
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PROTOCOL_PATH = "research/v6_m6a0_mnq_walkforward_protocol.md"
PROTOCOL_SHA = "893e5b5d459610a595cf1352b5e429916ec0d921cf5e2417e14bae891078d561"
PROTOCOL_FREEZE_COMMIT = "c767d89"
MANIFEST_PATH = "research/v6_m6a0_mnq_file_manifest.json"
MANIFEST_SHA = "5cf3d0f2aba4bfea2951c60e953e246ee28b7c6b9fc8cb98bdf3115b5b90d6fe"
M5F0_SCRIPT = "fly_mnq/v6_m5f0_dan_teaching_semantics.py"
M5F0_SHA = "ca3a573c96b0f257b685cb42f9eff427197ecef8c7e5fb895fcc1db452f39afd"
M5G0_RESULT = "research/results/v6_m5g0_theta_selection_result.json"
M5G0_PASS = "PASS_M5G0_THETA_SELECTED"
DATA = Path("v6_m6a0_data")
O = Path("v6_m6a0_out")

NAME_RE = re.compile(r"^MNQ (03|06|09|12)-(\d\d)\.Last\.txt$")
BAR_S = 15 * 60
GAP_MAX_S = 60 * 60
LAGS = (1, 2, 4, 8, 16, 32, 92)
FEATURES = ("r1", "r2", "r4", "r8", "r16", "r32", "r92", "hl", "vr", "lv", "tod_sin", "tod_cos")
STD_HALFLIFE = 500
MIN_SEEN = 50
RIDGE_LAMBDA = 1.0
RIDGE_HALFLIFE = 5000
PERM_SEED = 20261002
BURN_CONTRACTS = 2
BLOCK = 1000
ALPHA = 0.01
POINT_VALUE = 2.0
COST_PER_SIDE = 1.50
ENCODE_CHUNK = 5000

PASS = "PASS_M6A0_CONNECTOME_LEARNS_MNQ"
FAIL = "FAIL_M6A0_NO_CONNECTOME_ADVANTAGE"
BLOCKED = "BLOCKED_M6A0_DATA"


class DataError(Exception):
    pass


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


# ---------------------------------------------------------------- data (fail closed, no repair)

def parse_last_file(path):
    raw = Path(path).read_bytes()
    try:  # amendment A1: ASCII, UTF-8 (optional BOM) or UTF-16 with BOM, decoded strictly
        text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DataError(f"{Path(path).name}: undecodable bytes") from exc
    if not text.isascii():
        raise DataError(f"{Path(path).name}: non-ASCII characters")
    df = pd.read_csv(io.StringIO(text), sep=";", header=None, dtype=str, skip_blank_lines=True)
    if df.shape[1] != 6 or df.isna().any().any() or len(df) == 0:
        raise DataError(f"{Path(path).name}: not 6 fields per line")
    ts, px, vol = df[0], df[[1, 2, 3, 4]], df[5]
    if not ts.str.fullmatch(r"\d{8} \d{6}").all():
        raise DataError(f"{Path(path).name}: timestamp format")
    if not all(px[c].str.fullmatch(r"\d+(\.\d+)?").all() for c in px) or not vol.str.fullmatch(r"\d+").all():
        raise DataError(f"{Path(path).name}: numeric format")
    t = pd.to_datetime(ts, format="%Y%m%d %H%M%S").to_numpy().astype("datetime64[s]").astype(np.int64)
    p = px.to_numpy(dtype=np.float64)
    o_, h_, l_, c_ = p.T
    if not (p > 0).all() or not (np.abs(p * 4 - np.round(p * 4)) < 1e-9).all():
        raise DataError(f"{Path(path).name}: price not a positive multiple of 0.25")
    if not ((h_ >= np.maximum(o_, c_)) & (l_ <= np.minimum(o_, c_))).all():
        raise DataError(f"{Path(path).name}: OHLC inconsistent")
    if not (np.diff(t) > 0).all():
        raise DataError(f"{Path(path).name}: timestamps not strictly increasing")
    return t, o_, h_, l_, c_, vol.to_numpy(dtype=np.int64)


def contract_roll(name):
    m = NAME_RE.match(name)
    month, year = int(m.group(1)), 2000 + int(m.group(2))
    fridays = [d for d in calendar.Calendar().itermonthdates(year, month) if d.month == month and d.weekday() == 4]
    expiry = fridays[2]
    return expiry, expiry - dt.timedelta(days=8)


def to_15min(t, o_, h_, l_, c_, v):
    b = -(-t // BAR_S) * BAR_S
    start = np.flatnonzero(np.r_[True, b[1:] != b[:-1]])
    end = np.r_[start[1:], len(b)] - 1
    return (b[start], o_[start], np.maximum.reduceat(h_, start), np.minimum.reduceat(l_, start), c_[end],
            np.add.reduceat(v, start))


def ew_var(x, halflife):
    a = 1.0 - 0.5 ** (1.0 / halflife)
    out = np.full(len(x), np.nan)
    m = v = None
    for i, xi in enumerate(x):
        if np.isnan(xi):
            continue
        if m is None:
            m, v = xi, 0.0
        else:
            d = xi - m
            m += a * d
            v = (1 - a) * (v + a * d * d)
        out[i] = v
    return out


def contract_features(tb, h_, l_, c_, v):
    lc = np.log(c_)
    cols = []
    for k in LAGS:
        r = np.full(len(lc), np.nan)
        r[k:] = lc[k:] - lc[:-k]
        cols.append(r)
    r1 = cols[0]
    cols.append(np.log(h_ / l_))
    v8, v184 = ew_var(r1, 8), ew_var(r1, 184)
    with np.errstate(divide="ignore", invalid="ignore"):
        vr = np.where((v8 > 0) & (v184 > 0), 0.5 * np.log(v8 / v184), np.nan)
    cols.append(vr)
    cols.append(np.log1p(v.astype(np.float64)))
    minute = (tb % 86400) // 60
    cols.append(np.sin(2 * np.pi * minute / 1440))
    cols.append(np.cos(2 * np.pi * minute / 1440))
    x = np.column_stack(cols)
    outcome = np.full(len(lc), np.nan)
    ok = (tb[1:] - tb[:-1]) <= GAP_MAX_S
    outcome[:-1] = np.where(ok, lc[1:] - lc[:-1], np.nan)
    c_next = np.full(len(lc), np.nan)
    c_next[:-1] = np.where(ok, c_[1:], np.nan)
    return x, outcome, c_next


def build_series(files):
    """Active-contract 15-minute series with features, outcomes and prices (calendar roll, causal)."""
    rows = []
    for f in files:
        expiry, roll = contract_roll(f.name)
        rows.append((expiry, roll, f))
    rows.sort()
    parts, facts = [], []
    prev_roll = None
    for k, (expiry, roll, f) in enumerate(rows):
        t, o_, h_, l_, c_, v = parse_last_file(f)
        tb, bo, bh, bl, bc, bv = to_15min(t, o_, h_, l_, c_, v)
        x, outcome, c_next = contract_features(tb, bh, bl, bc, bv)
        day = (tb // 86400).astype("datetime64[D]")
        lo = np.datetime64(prev_roll) if prev_roll is not None else day.min()
        act = (day >= lo) & (day < np.datetime64(roll))
        prev_roll = roll
        if not act.any():
            raise DataError(f"{f.name}: no bars in its active window")
        parts.append({"x": x[act], "o": outcome[act], "c": bc[act], "c_next": c_next[act], "tb": tb[act],
                      "k": np.full(int(act.sum()), k)})
        facts.append({"file": f.name, "sha256": sha256(f), "minute_lines": int(len(t)), "bars_15m": int(len(tb)),
                      "active_bars": int(act.sum()), "active_with_outcome": int(np.isfinite(outcome[act]).sum()),
                      "expiry": expiry.isoformat(), "roll": roll.isoformat()})
    series = {key: np.concatenate([p[key] for p in parts]) for key in parts[0]}
    if not (np.diff(series["tb"]) > 0).all():
        raise DataError("active series timestamps not strictly increasing across rolls")
    return series, facts


def standardize(x):
    a = 1.0 - 0.5 ** (1.0 / STD_HALFLIFE)
    n, f = x.shape
    z = np.zeros((n, f))
    m, v, seen = np.zeros(f), np.zeros(f), np.zeros(f, dtype=np.int64)
    for t in range(n):
        xt = x[t]
        ok = np.isfinite(xt)
        use = ok & (seen >= MIN_SEEN) & (v > 0)
        z[t, use] = (xt[use] - m[use]) / np.sqrt(v[use])
        first = ok & (seen == 0)
        upd = ok & (seen > 0)
        m[first] = xt[first]
        d = xt[upd] - m[upd]
        m[upd] += a * d
        v[upd] = (1 - a) * (v[upd] + a * d * d)
        seen[ok] += 1
    return z


# ---------------------------------------------------------------- arms

def ridge_arm(u, o):
    x = np.column_stack([np.ones(len(u)), u])
    beta = 0.5 ** (1.0 / RIDGE_HALFLIFE)
    p = np.zeros((x.shape[1], x.shape[1]))
    q = np.zeros(x.shape[1])
    lam = RIDGE_LAMBDA * np.eye(x.shape[1])
    s = np.zeros(len(u))
    for t in range(len(u)):
        s[t] = x[t] @ np.linalg.solve(p + lam, q)  # read before write
        if np.isfinite(o[t]):
            p = beta * p + np.outer(x[t], x[t])
            q = beta * q + x[t] * o[t]
    return s


def fly_arm(m5f0, world, arm, theta, u, teach):
    enc = world["encoders"][arm]
    codes = np.concatenate([enc.encode(u[i:i + ENCODE_CHUNK])[0] for i in range(0, len(u), ENCODE_CHUNK)])
    ones = np.ones(len(world["S"].edge_comp), dtype=np.float64)
    naive = np.stack([m5f0.M5D0.raw_drive(world["S"], world["RW"], ones, codes[t]) for t in range(len(codes))])
    r = m5f0.run_learner(world["S"], world["RW"], theta, codes, teach, world["teacher"], naive,
                         world["app_idx"], world["av_idx"])
    return r["s"], int(r["zero_steps"]), float(codes.mean())


# ---------------------------------------------------------------- evaluation

def corr(a, b):
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def one_sided(x):
    x = np.asarray(x, dtype=np.float64)
    res = stats.ttest_1samp(x, 0.0, alternative="greater")
    return {"mean": float(x.mean()), "sd": float(x.std(ddof=1)), "n_blocks": int(len(x)), "t": float(res.statistic),
            "p": float(res.pvalue)}


def trading(s, series, ev):
    pos = np.where(ev, np.sign(s), 0.0)
    dc = np.where(ev, series["c_next"] - series["c"], 0.0)
    gross = pos * dc * POINT_VALUE
    cost = COST_PER_SIDE * np.abs(np.diff(np.r_[0.0, pos]))
    net = gross - cost
    idx = np.flatnonzero(ev)
    years = (series["tb"][idx[-1]] - series["tb"][idx[0]]) / (365.25 * 86400)
    per_bar = net[idx[0]: idx[-1] + 1]
    eq = np.cumsum(per_bar)
    traded = (pos != 0) & (dc != 0)
    year_of = (series["tb"] // 86400).astype("datetime64[D]").astype("datetime64[Y]").astype(int) + 1970
    by_year = {}
    for y in np.unique(year_of[idx]):
        sel = (year_of == y)
        by_year[str(int(y))] = {"net_pnl": float(net[sel].sum()), "gross_pnl": float(gross[sel].sum())}
    return {"gross_pnl": float(gross.sum()), "costs": float(cost.sum()), "net_pnl": float(net.sum()),
            "sharpe_annualized": float(per_bar.mean() / per_bar.std() * np.sqrt(len(per_bar) / years)) if per_bar.std() > 0 else 0.0,
            "max_drawdown": float((np.maximum.accumulate(np.r_[0.0, eq]) - np.r_[0.0, eq]).max()),
            "hit_rate": float((np.sign(pos[traded]) == np.sign(dc[traded])).mean()) if traded.any() else 0.0,
            "turnover_per_bar": float(np.abs(np.diff(np.r_[0.0, pos])).sum() / len(idx)), "by_year": by_year}


# ---------------------------------------------------------------- formal execution

def main():
    out = {"protocol": {"path": PROTOCOL_PATH, "sha256": PROTOCOL_SHA, "freeze_commit": PROTOCOL_FREEZE_COMMIT}}
    try:
        run(out)
    except DataError as exc:
        finish(out, BLOCKED, f"data: {exc}")
    except Exception as exc:  # recorded, never silent
        finish(out, BLOCKED, f"execution error: {exc!r}")


def run(out):
    t0 = time.time()
    O.mkdir(exist_ok=True)
    pins = {"protocol": Path(PROTOCOL_PATH).is_file() and sha256(PROTOCOL_PATH) == PROTOCOL_SHA,
            "m5f0_script": Path(M5F0_SCRIPT).is_file() and sha256(M5F0_SCRIPT) == M5F0_SHA,
            "manifest": Path(MANIFEST_PATH).is_file() and sha256(MANIFEST_PATH) == MANIFEST_SHA}
    out["pins"] = pins
    out["code_sha256"] = sha256(__file__)
    if not all(pins.values()):
        raise DataError("pinned protocol or M5F0 script hash mismatch")
    manifest = json.loads(Path(MANIFEST_PATH).read_text(encoding="utf-8"))
    present = sorted(f.name for f in DATA.iterdir())
    if present != sorted(manifest["used"]) or set(present) & set(manifest["reserved_holdout_not_downloaded"]):
        raise DataError("data directory does not hold exactly the manifest's used files")
    files = [DATA / n for n in present]
    series, facts = build_series(files)
    out["data"] = {"files": facts, "active_bars": int(len(series["o"]))}
    u = standardize(series["x"])
    o = series["o"]

    m5f0 = load_module("v6_m5f0_frozen_for_m6a0", M5F0_SCRIPT)
    pre = {}
    world = m5f0.build(pre)
    out["m5f0_prerequisites_all_true"] = bool(world is not None and all(pre["prerequisites"].values()))
    if world is None:
        raise DataError("frozen M5F0 prerequisite chain failed")
    theta_pt, theta_src = dict(m5f0.M5C.REFERENCE_POINT), "M5C_REFERENCE_POINT"
    if Path(M5G0_RESULT).is_file():
        g = json.loads(Path(M5G0_RESULT).read_text(encoding="utf-8"))
        out["m5g0_classification"] = g.get("classification")
        if g.get("classification") == M5G0_PASS:
            theta_pt, theta_src = dict(g["theta_star"]), "M5G0_THETA_STAR"
    out["theta"] = {"point": theta_pt, "source": theta_src}
    theta = m5f0.theta_of(theta_pt)

    teach = np.nan_to_num(o, nan=0.0)
    idx = np.flatnonzero(np.isfinite(o))
    perm = np.random.Generator(np.random.PCG64(PERM_SEED)).permutation(len(idx))
    teach_c = np.zeros(len(o))
    teach_c[idx] = o[idx][perm]
    s, info = {}, {}
    for arm, enc_arm, tch in (("A_connectome", "connectome", teach), ("B_rewired", "rewired", teach),
                              ("C_shuffled_teaching", "connectome", teach_c)):
        ta = time.time()
        s[arm], zero_steps, density = fly_arm(m5f0, world, enc_arm, theta, u, tch)
        info[arm] = {"zero_score_bars": zero_steps, "kc_code_density": density, "seconds": round(time.time() - ta, 1)}
        print(arm, info[arm], flush=True)
    s["D_linear_ridge"] = ridge_arm(u, o)

    ev = (series["k"] >= BURN_CONTRACTS) & np.isfinite(o)
    eidx = np.flatnonzero(ev)
    nb = len(eidx) // BLOCK
    blocks = [eidx[i * BLOCK:(i + 1) * BLOCK] for i in range(nb)]
    rho_b = {a: np.array([corr(v[b], o[b]) for b in blocks]) for a, v in s.items()}
    crit_stats = {"H1_learns_MNQ": one_sided(rho_b["A_connectome"]),
                  "H2_connectome_beats_rewired": one_sided(rho_b["A_connectome"] - rho_b["B_rewired"]),
                  "H3_teaching_specific": one_sided(rho_b["A_connectome"] - rho_b["C_shuffled_teaching"])}
    criteria = {k: bool(v["p"] < ALPHA and v["mean"] > 0) for k, v in crit_stats.items()}
    out.update({
        "criteria": criteria, "criteria_stats": crit_stats,
        "evaluation": {"eval_bars": int(len(eidx)), "blocks": nb, "burn_in_contracts": BURN_CONTRACTS,
                       "first_eval_contract": facts[BURN_CONTRACTS]["file"]},
        "diagnostics": {
            "whole_window_rho": {a: corr(v[eidx], o[eidx]) for a, v in s.items()},
            "mean_block_rho": {a: float(r.mean()) for a, r in rho_b.items()},
            "D_linear_ridge": one_sided(rho_b["D_linear_ridge"]),
            "A_minus_D": one_sided(rho_b["A_connectome"] - rho_b["D_linear_ridge"]),
            "arm_run_info": info,
            "trading": {a: trading(v, series, ev) for a, v in s.items()},
        },
        "elapsed_s": round(time.time() - t0, 1),
    })
    if all(criteria.values()):
        return finish(out, PASS, "H1, H2 and H3 hold")
    return finish(out, FAIL, "failed: " + ", ".join(k for k, v in criteria.items() if not v))


def finish(out, classification, reason):
    out.update({"classification": classification, "reason": reason})
    O.mkdir(exist_ok=True)
    (O / "v6_m6a0_result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out.get(k) for k in ("classification", "reason", "criteria", "theta")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
