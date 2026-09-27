from __future__ import annotations

import hashlib
import http.client
import http.server
import importlib.util
import io
import json
import os
import ssl
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.ipc as ipc

W = Path("v6_m5b3b_work")  # pinned body annotations and connectome weights (shared convention)
O = Path("v6_m5b3c_out")

PROTOCOL_PATH = "research/v6_m5b3c_synapse_compartment_resolver_protocol.md"
PROTOCOL_FREEZE_COMMIT = "0627505bbbbcda6a79abc13591b4aea978d739f8"
PROTOCOL_SHA = "013fd988ecb063ee74d9b4487dc08dfdcf4270a2ad3b557ab1c53f58141c9cda"
M5B3B_SCRIPT = "fly_mnq/v6_m5b3b_compartment_gating_mvp.py"
M5B3B_RESULT = "research/results/v6_m5b3b_compartment_gating_mvp_result.json"
C0_RESULT = "research/results/v6_m5b3c0_synapse_schema_result.json"
C1_RESULT = "research/results/v6_m5b3c1_roi_vocabulary_result.json"
C1_SCRIPT = "fly_mnq/v6_m5b3c1_roi_vocabulary_probe.py"  # frozen flatbuffer footer reader
FROZEN_FILES = {
    C1_SCRIPT: "6a88359ea4b0b90f2e615d48cfd21a51b7f188a24c34d51d7cdd0ee6c0419557",
    M5B3B_SCRIPT: "0a8d6c3fb61e7659fb885433dc0a93998dfa3b1b05397d8310274eb9fe14914b",
    M5B3B_RESULT: "1792a7f082cf951db76f98978236d3cc0eed828874922ebde79a98b88aadb1b2",
    C0_RESULT: "4c0f237cf8d270ec6abaebf3926e750e75c8079bda7c1a4da8f6138af7c12c7e",
    C1_RESULT: "4a3d73dac3fd87ed266a8e8003f1f345cf1b06aa0f5e5960d35f8be3e38b21b5",
}
ANN_SHA = "2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2"
WEIGHTS_SHA = "e35da783d1c686b2b58b3b87cd6a403ae43bfcfba8bff28e08ef752c1a56afc1"

BASE = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/"
PARTNERS = "syn-partners-male-cns-v1.0-minconf-0.5.feather"
POINTS = "syn-points-male-cns-v1.0-minconf-0.5.feather"
PINS = {
    PARTNERS: {"size": 6777179098, "etag": '"58efcf712f8c4d4de5f2ad51e97def76"', "generation": "1780494942562468",
               "md5": "58efcf712f8c4d4de5f2ad51e97def76", "record_batches": 4759, "footer_length": 116632},
    POINTS: {"size": 13061489098, "etag": '"c69d08758de07582035cc8843574493a"', "generation": "1780494991007477",
             "md5": "c69d08758de07582035cc8843574493a", "record_batches": 5455, "footer_length": 140760},
}
PARTNER_FIELDS = ["x_post", "y_post", "z_post", "body_pre", "body_post", "conf_pre", "conf_post", "primary_post"]
POINT_FIELDS = ["x", "y", "z", "kind", "body", "compartment", "primary", "subprimary"]

EXPECTED = {"KC": 4064, "MBON": 97, "KC_MBON_EDGES": 61210, "SINGLE": 55, "MULTI": 40, "OUTSIDE": 2}
LOBE15 = ("a1", "a2", "a3", "a'1", "a'2", "a'3", "B1", "B2", "B'1", "B'2", "y1", "y2", "y3", "y4", "y5")
ROI_CODE = ("a1", "a2", "a3", "a'1", "a'2", "a'3", "b1", "b2", "b'1", "b'2", "g1", "g2", "g3", "g4", "g5")
REFERENCE_LABELS = {f"{r}({s})": (i, s) for i, r in enumerate(ROI_CODE) for s in ("L", "R")}
VALIDATION_THRESHOLD = 0.80
UNRESOLVED = -1

# Diagnostic context only: M5D1C admissible signs (research/v6_m5d1c_type_number_bridge_result.md).
SIGNED_DAN = {"PAM01": "APPETITIVE", "PAM02": "APPETITIVE", "PAM11": "APPETITIVE",
              "PPL101": "AVERSIVE", "PPL103": "AVERSIVE", "PPL104": "AVERSIVE", "PPL106": "AVERSIVE"}
SIGNED_MBON = {"MBON11": "ATTRACTIVE", "MBON12": "ATTRACTIVE", "MBON33": "ATTRACTIVE",
               "MBON05": "REPULSIVE", "MBON06": "REPULSIVE", "MBON21": "REPULSIVE", "MBON29": "REPULSIVE"}
MODEL_CONSISTENT = {("AVERSIVE", "ATTRACTIVE"), ("APPETITIVE", "REPULSIVE")}

READ_CHUNK = 16 << 20
MAX_RECONNECTS = 8
RETRY_HTTP = (408, 429, 500, 502, 503, 504)


class PinError(Exception):
    """The served object differs from the pinned object; never retried."""


# ---------------------------------------------------------------- utilities

def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_FB = []


def footer_reader():
    """The frozen M5B3C1 module supplies the read-only flatbuffer footer parser."""
    if not _FB:
        _FB.append(load_module("v6_m5b3c1_frozen", C1_SCRIPT))
    return _FB[0]


def idx_in(sorted_ids: np.ndarray, values: np.ndarray):
    pos = np.searchsorted(sorted_ids, values)
    ok = pos < len(sorted_ids)
    safe = np.minimum(pos, len(sorted_ids) - 1)
    ok &= sorted_ids[safe] == values
    return safe, ok


def ssl_context():
    ca = os.environ.get("SSL_CERT_FILE")
    if not ca:
        try:  # proxy CA bundle of the authoring container; unreadable on GitHub runners
            ca = "/root/.ccr/ca-bundle.crt" if Path("/root/.ccr/ca-bundle.crt").is_file() else None
        except OSError:
            ca = None
    return ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()


def array_digest(arrays: dict) -> str:
    h = hashlib.sha256()
    for name in sorted(arrays):
        a = np.ascontiguousarray(arrays[name])
        h.update(name.encode() + b"\0" + a.dtype.str.encode() + b"\0" + repr(a.shape).encode() + b"\0")
        h.update(a.tobytes())
    return h.hexdigest()


# ---------------------------------------------------------------- pinned sequential object stream

class PinnedHttpStream(io.RawIOBase):
    """Reads one whole object strictly in order; SHA256 and MD5 cover every byte exactly once.

    Every (re)connection is `Range: bytes=<pos>-` and must return 206 with the exact Content-Range and the
    pinned ETag and generation. Transport errors resume at the current offset; a pin mismatch is fatal.
    """

    def __init__(self, url, pin, ctx=None, timeout=120, max_reconnects=MAX_RECONNECTS, backoff=True):
        self.url, self.pin, self.ctx, self.timeout = url, pin, ctx, timeout
        self.size = pin["size"]
        self.max_reconnects = max_reconnects
        self.backoff = backoff
        self.pos = 0
        self.sha256 = hashlib.sha256()
        self.md5 = hashlib.md5(usedforsecurity=False)
        self.resp = None
        self.connect_offsets = []
        self.reconnects = 0

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def _connect(self):
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-"})
        r = urllib.request.urlopen(req, context=self.ctx, timeout=self.timeout)
        want = f"bytes {self.pos}-{self.size - 1}/{self.size}"
        if r.status != 206 or (r.headers.get("Content-Range") or "") != want:
            r.close()
            raise PinError(f"unexpected response at offset {self.pos}: status {r.status}, range {r.headers.get('Content-Range')}")
        if r.headers.get("ETag") != self.pin["etag"] or r.headers.get("x-goog-generation") != self.pin["generation"]:
            r.close()
            raise PinError(f"served object differs from pin at offset {self.pos}")
        self.connect_offsets.append(self.pos)
        self.resp = r

    def readinto(self, b):
        if self.pos >= self.size:
            return 0
        want = min(len(b), self.size - self.pos)
        attempt = 0
        while True:
            try:
                if self.resp is None:
                    self._connect()
                data = self.resp.read(want)
                if not data:
                    raise IOError(f"connection ended at offset {self.pos}")
                break
            except PinError:
                raise
            except (OSError, http.client.HTTPException) as exc:
                if isinstance(exc, urllib.error.HTTPError) and exc.code not in RETRY_HTTP:
                    raise
                if self.resp is not None:
                    try:
                        self.resp.close()
                    except Exception:
                        pass
                    self.resp = None
                self.reconnects += 1
                attempt += 1
                if self.reconnects > self.max_reconnects:
                    raise
                if self.backoff:
                    time.sleep(min(2 ** attempt, 30))
        n = len(data)
        b[:n] = data
        self.sha256.update(data)
        self.md5.update(data)
        self.pos += n
        return n

    def close(self):
        if self.resp is not None:
            self.resp.close()
            self.resp = None
        super().close()


def stream_file(raw, pin, included, on_batch, fb):
    """Parse the Arrow IPC stream inside an IPC file read strictly sequentially from `raw`.

    Exactly pin['record_batches'] record batches are parsed (projected to `included` field indices). The bytes
    after the last parsed batch (end-of-stream gap, footer, trailer) are captured from the same stream and the
    footer is parsed with the frozen M5B3C1 flatbuffer reader `fb`.
    """
    buf = io.BufferedReader(raw, buffer_size=READ_CHUNK)
    if buf.read(8) != b"ARROW1\x00\x00":
        raise ValueError("leading Arrow magic missing")
    reader = ipc.open_stream(pa.PythonFile(buf, mode="r"), options=ipc.IpcReadOptions(included_fields=included))
    for _ in range(pin["record_batches"]):
        on_batch(reader.read_next_batch())
    end = buf.tell()
    footer_start = pin["size"] - 10 - pin["footer_length"]
    tail = {"end_of_last_parsed_batch": end, "footer_start": footer_start, "gap_length": footer_start - end}
    if 0 <= footer_start - end <= 64:
        rest = buf.read(pin["size"] - end)
        gap, footer, trailer = rest[: footer_start - end], rest[footer_start - end: -10], rest[-10:]
        blocks = fb.blocks(fb.root(footer), 3)
        tail.update({
            "gap_hex": gap.hex(),
            "trailer_ok": trailer[4:] == b"ARROW1" and int.from_bytes(trailer[:4], "little", signed=True) == pin["footer_length"],
            "footer_record_batch_blocks": len(blocks),
            "footer_last_block_end": max(b["offset"] + b["metadata_length"] + b["body_length"] for b in blocks) if blocks else None,
        })
    while buf.read(READ_CHUNK):
        pass
    return tail


def tail_ok(tail, pin):
    """All footer-listed record batches were parsed in order and only an end-of-stream marker precedes the footer."""
    return bool(tail.get("trailer_ok") and tail.get("footer_record_batch_blocks") == pin["record_batches"]
                and tail.get("footer_last_block_end") == tail["end_of_last_parsed_batch"]
                and (tail["gap_length"], tail.get("gap_hex")) in {(0, ""), (4, "00000000"), (8, "ffffffff00000000")})


# ---------------------------------------------------------------- collection

class Collector:
    """Keeps projected rows passing `keep`, checks dictionaries against pinned vocabularies, counts nulls."""

    def __init__(self, fields, dict_refs, keep):
        self.fields = fields
        self.dict_refs = {k: pa.array(v, type=pa.string()) for k, v in dict_refs.items()}
        self.keep = keep
        self.parts = {f: [] for f in fields}
        self.batches = 0
        self.rows = 0
        self.kept = 0
        self.dictionary_mismatch_batches = 0
        self.kept_nulls = 0
        self.key_nulls = 0

    def __call__(self, batch):
        self.batches += 1
        self.rows += batch.num_rows
        for name, ref in self.dict_refs.items():
            if not batch.column(name).dictionary.equals(ref):
                self.dictionary_mismatch_batches += 1
        mask = self.keep(self, batch)
        if not mask.any():
            return
        sub = batch.filter(pa.array(mask))
        self.kept += sub.num_rows
        for f in self.fields:
            col = sub.column(f)
            self.kept_nulls += col.null_count
            if pa.types.is_dictionary(col.type):
                col = col.indices
            self.parts[f].append(col.to_numpy(zero_copy_only=False))

    def arrays(self):
        return {f: (np.concatenate(v) if v else np.array([], dtype=np.int64)) for f, v in self.parts.items()}


def filled(col, fill):
    if col.null_count:
        return pc.fill_null(col, fill).to_numpy()
    return col.to_numpy()


def partner_keep(kc_sorted, mbon_sorted):
    def keep(c, batch):
        pre, post = batch.column("body_pre"), batch.column("body_post")
        c.key_nulls += pre.null_count + post.null_count
        return idx_in(kc_sorted, filled(pre, -1))[1] & idx_in(mbon_sorted, filled(post, -1))[1]
    return keep


def point_keep(mbon_sorted, post_kind_index):
    def keep(c, batch):
        kind, body = batch.column("kind"), batch.column("body")
        c.key_nulls += kind.null_count + body.null_count
        return (filled(kind.indices, -1) == post_kind_index) & idx_in(mbon_sorted, filled(body, -1))[1]
    return keep


# ---------------------------------------------------------------- resolver logic (pure)

def label_codes(subprimary_vocab):
    """Map subprimary dictionary index -> (LOBE15 code index or -1, side or '')."""
    code = np.full(len(subprimary_vocab), UNRESOLVED, dtype=np.int64)
    side = np.array([""] * len(subprimary_vocab), dtype="U1")
    for i, lab in enumerate(subprimary_vocab):
        if lab in REFERENCE_LABELS:
            code[i], side[i] = REFERENCE_LABELS[lab]
    return code, side


def join_labels(p, q):
    """Join partner post points to PostSyn points on (body, x, y, z).

    p: dict body, x, y, z; q: dict body, x, y, z, sub, prim, comp. Returns per partner row: n matches,
    sub, prim, comp (of the matched group, -1 if unmatched) and whether all matches agree on sub and prim.
    """
    order = np.lexsort((q["comp"], q["prim"], q["sub"], q["z"], q["y"], q["x"], q["body"]))
    b, x, y, z = (q[k][order] for k in ("body", "x", "y", "z"))
    s, pr, c = (q[k][order] for k in ("sub", "prim", "comp"))
    new = np.ones(len(order), dtype=bool)
    new[1:] = (b[1:] != b[:-1]) | (x[1:] != x[:-1]) | (y[1:] != y[:-1]) | (z[1:] != z[:-1])
    starts = np.flatnonzero(new)
    ends = np.r_[starts[1:], len(order)] - 1
    groups = pd.DataFrame({
        "body": b[starts], "x": x[starts], "y": y[starts], "z": z[starts], "n": ends - starts + 1,
        "sub_f": s[starts], "sub_l": s[ends], "prim_f": pr[starts], "prim_l": pr[ends], "comp_f": c[starts],
    })
    left = pd.DataFrame({"row": np.arange(len(p["body"])), "body": p["body"], "x": p["x"], "y": p["y"], "z": p["z"]})
    m = left.merge(groups, on=["body", "x", "y", "z"], how="left", validate="many_to_one").sort_values("row")
    if len(m) != len(left):
        raise AssertionError("join changed the partner row count")
    n = m["n"].fillna(0).to_numpy().astype(np.int64)
    matched = n > 0
    sub_f = m["sub_f"].fillna(-1).to_numpy().astype(np.int64)
    sub_l = m["sub_l"].fillna(-1).to_numpy().astype(np.int64)
    prim_f = m["prim_f"].fillna(-1).to_numpy().astype(np.int64)
    prim_l = m["prim_l"].fillna(-1).to_numpy().astype(np.int64)
    comp = m["comp_f"].fillna(-1).to_numpy().astype(np.int64)
    consistent = matched & (sub_f == sub_l) & (prim_f == prim_l)
    return {"n": n, "sub": np.where(consistent, sub_f, -1), "prim": np.where(consistent, prim_f, -1),
            "comp": comp, "matched": matched, "consistent": consistent,
            "duplicate_point_groups": int((groups["n"] > 1).sum())}


def aggregate_parity(syn_pre, syn_post, w_pre, w_post, w_weight):
    a = pd.DataFrame({"pre": syn_pre, "post": syn_post}).groupby(["pre", "post"]).size().rename("count").reset_index()
    wdf = pd.DataFrame({"pre": w_pre, "post": w_post, "weight": w_weight})
    dup_w = int(wdf.duplicated(["pre", "post"]).sum())
    m = a.merge(wdf, on=["pre", "post"], how="outer", indicator=True)
    both = m[m["_merge"] == "both"]
    rec = {
        "synapse_rows": int(len(syn_pre)),
        "synapse_pairs": int(len(a)),
        "weight_pairs": int(len(wdf)),
        "weight_sum": int(wdf["weight"].sum()),
        "duplicate_weight_pairs": dup_w,
        "pairs_only_in_synapses": int((m["_merge"] == "left_only").sum()),
        "pairs_only_in_weights": int((m["_merge"] == "right_only").sum()),
        "pairs_with_unequal_count": int((both["count"] != both["weight"]).sum()),
    }
    rec["exact"] = (dup_w == 0 and rec["pairs_only_in_synapses"] == 0 and rec["pairs_only_in_weights"] == 0
                    and rec["pairs_with_unequal_count"] == 0 and rec["synapse_rows"] == rec["weight_sum"])
    return rec


def validate_semantics(syn_post, code, single_nominal):
    """single_nominal: {mbon body: LOBE15 index}. Pooled agreement and per-body unique plurality."""
    per_body, agree_total, n_total = [], 0, 0
    for body in sorted(single_nominal):
        nominal = single_nominal[body]
        c = code[syn_post == body]
        n, agree = int(len(c)), int((c == nominal).sum())
        resolved = c[c >= 0]
        counts = np.bincount(resolved, minlength=len(LOBE15))
        top = int(counts.max()) if len(resolved) else 0
        plural = int(np.argmax(counts)) if top > 0 and int((counts == top).sum()) == 1 else None
        per_body.append({
            "bodyId": int(body), "nominal": LOBE15[nominal], "kc_synapses": n, "agree": agree,
            "unresolved": int((c < 0).sum()),
            "plurality": None if plural is None else LOBE15[plural],
            "plurality_matches": plural == nominal,
            "resolved_counts": {LOBE15[i]: int(v) for i, v in enumerate(counts) if v},
        })
        agree_total += agree
        n_total += n
    pooled = agree_total / n_total if n_total else 0.0
    return {"pooled_agreement": pooled, "pooled_agree": agree_total, "pooled_n": n_total,
            "pooled_pass": bool(n_total > 0 and pooled >= VALIDATION_THRESHOLD),
            "every_body_plurality_matches": bool(per_body and all(r["plurality_matches"] for r in per_body)),
            "per_body": per_body}


def build_learner_edges(syn_pre, syn_post, code, mbon_status, mbon_named, gated):
    """Frozen M5B3C edge rule. Returns plastic (pre, post, comp, weight) and nonplastic (pre, post, weight, reason).

    single_compartment MBON: the whole aggregate edge is plastic in its compartment (M5B3B, unchanged).
    multi_compartment MBON: a synapse whose resolved code is one of the MBON's named lobe compartments and is gated
    by at least one fast DAN joins the plastic sub-edge (pre, post, code); any other synapse joins the nonplastic
    remainder ('offmap', 'ungated' or 'unresolved').
    outside_fast_lobe_map MBON: nonplastic ('outside').
    """
    status = np.array([mbon_status[int(b)] for b in syn_post])
    comp = np.full(len(syn_pre), UNRESOLVED, dtype=np.int64)
    reason = np.array([""] * len(syn_pre), dtype="U10")
    single = status == "single_compartment"
    comp[single] = np.array([mbon_named[int(b)][0] for b in syn_post[single]], dtype=np.int64)
    multi = status == "multi_compartment"
    named = np.array([code[i] in mbon_named[int(syn_post[i])] if multi[i] else False for i in range(len(syn_pre))], dtype=bool)
    is_gated = np.isin(code, np.array(sorted(gated), dtype=np.int64))
    inmap = multi & named & (code >= 0) & is_gated
    comp[inmap] = code[inmap]
    reason[multi & named & (code >= 0) & ~is_gated] = "ungated"
    reason[multi & ~named & (code >= 0)] = "offmap"
    reason[multi & (code < 0)] = "unresolved"
    reason[status == "outside_fast_lobe_map"] = "outside"
    plastic = comp >= 0
    pl = pd.DataFrame({"pre": syn_pre[plastic], "post": syn_post[plastic], "comp": comp[plastic]})
    pl = pl.groupby(["pre", "post", "comp"]).size().rename("weight").reset_index().sort_values(["pre", "post", "comp"])
    npl = pd.DataFrame({"pre": syn_pre[~plastic], "post": syn_post[~plastic], "reason": reason[~plastic]})
    npl = npl.groupby(["pre", "post", "reason"]).size().rename("weight").reset_index().sort_values(["pre", "post", "reason"])
    return {
        "plastic_pre": pl["pre"].to_numpy(np.int64), "plastic_post": pl["post"].to_numpy(np.int64),
        "plastic_comp": np.array([LOBE15[i] for i in pl["comp"]], dtype="U4"),
        "plastic_weight": pl["weight"].to_numpy(np.int64),
        "nonplastic_pre": npl["pre"].to_numpy(np.int64), "nonplastic_post": npl["post"].to_numpy(np.int64),
        "nonplastic_reason": npl["reason"].to_numpy().astype("U10"),
        "nonplastic_weight": npl["weight"].to_numpy(np.int64),
    }


# ---------------------------------------------------------------- self-test (synthetic data only)

class _RangeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        s = self.server
        s.calls += 1
        rng = self.headers.get("Range", "")
        if s.ignore_range or not rng.startswith("bytes="):
            body = s.data
            self.send_response(200)
        else:
            start = int(rng[6:].split("-")[0])
            body = s.data[start:]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(s.data) - 1}/{len(s.data)}")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("ETag", s.etag if (s.calls == 1 or s.etag_after_first is None) else s.etag_after_first)
        self.send_header("x-goog-generation", s.generation)
        self.end_headers()
        try:
            if s.cut_after is not None and s.calls == 1:
                self.wfile.write(body[: s.cut_after])
                self.wfile.flush()
                self.close_connection = True
                return
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):  # the client is expected to abandon rejected responses
            self.close_connection = True


def _serve(data, **kw):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _RangeHandler)
    srv.data, srv.calls, srv.etag, srv.generation = data, 0, '"t"', "7"
    srv.cut_after, srv.etag_after_first, srv.ignore_range = None, None, False
    for k, v in kw.items():
        setattr(srv, k, v)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _selftest_stream():
    rng = np.random.default_rng(11)
    n = 30000
    vocab = ["<unspecified>", "PED(R)", "gL(R)", "aL(L)"]
    df = pd.DataFrame({
        "x_pre": rng.integers(0, 50000, n, dtype=np.int32), "x_post": rng.integers(0, 50000, n, dtype=np.int32),
        "y_post": rng.integers(0, 50000, n, dtype=np.int32), "z_post": rng.integers(0, 50000, n, dtype=np.int32),
        "body_pre": rng.integers(1, 1000, n, dtype=np.int64), "conf_pre": rng.random(n).astype(np.float32),
        "body_post": rng.integers(1, 1000, n, dtype=np.int64), "conf_post": rng.random(n).astype(np.float32),
        "primary_post": pd.Categorical(rng.choice(vocab, n), categories=vocab, ordered=True),
    })
    cases = {}
    os.environ["NO_PROXY"] = os.environ["no_proxy"] = "127.0.0.1,localhost"
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "s.feather")
        feather.write_feather(df, path, compression="lz4", chunksize=2500)
        data = Path(path).read_bytes()
        pin = {"size": len(data), "etag": '"t"', "generation": "7", "md5": hashlib.md5(data, usedforsecurity=False).hexdigest(),
               "record_batches": ipc.open_file(path).num_record_batches,
               "footer_length": int.from_bytes(data[-10:-6], "little", signed=True)}
        names = list(df.columns)
        fields = ["x_post", "y_post", "z_post", "body_pre", "body_post", "primary_post"]
        included = sorted(names.index(f) for f in fields)
        keep_small = lambda c, b: (filled(b.column("body_pre"), -1) < 500)  # noqa: E731

        srv = _serve(data, cut_after=len(data) // 3)
        try:
            raw = PinnedHttpStream(f"http://127.0.0.1:{srv.server_address[1]}/s", pin, backoff=False)
            col = Collector(fields, {"primary_post": vocab}, keep_small)
            tail = stream_file(raw, pin, included, col, footer_reader())
            got = col.arrays()
            want = df[df["body_pre"] < 500]
            cases["resume_after_disconnect"] = bool(
                raw.pos == len(data) and raw.sha256.hexdigest() == hashlib.sha256(data).hexdigest()
                and raw.md5.hexdigest() == pin["md5"] and raw.reconnects == 1 and len(raw.connect_offsets) == 2
                and col.batches == pin["record_batches"] and col.dictionary_mismatch_batches == 0 and col.kept_nulls == 0
                and tail_ok(tail, pin)
                and all(np.array_equal(got[f], want[f].cat.codes.to_numpy() if f == "primary_post" else want[f].to_numpy())
                        for f in fields))
        finally:
            srv.shutdown()

        def expect_pin_error(**kw):
            s = _serve(data, **kw)
            try:
                r = PinnedHttpStream(f"http://127.0.0.1:{s.server_address[1]}/s", pin, backoff=False)
                stream_file(r, pin, included, Collector(fields, {"primary_post": vocab}, keep_small), footer_reader())
                return False
            except PinError:
                return True
            finally:
                s.shutdown()

        cases["object_change_on_reconnect_rejected"] = expect_pin_error(cut_after=len(data) // 3, etag_after_first='"other"')
        cases["range_ignored_rejected"] = expect_pin_error(ignore_range=True)
        wrong_vocab = Collector(fields, {"primary_post": vocab[::-1]}, keep_small)
        s = _serve(data)
        try:
            stream_file(PinnedHttpStream(f"http://127.0.0.1:{s.server_address[1]}/s", pin, backoff=False), pin, included, wrong_vocab,
                        footer_reader())
        finally:
            s.shutdown()
        cases["dictionary_mismatch_detected"] = wrong_vocab.dictionary_mismatch_batches == pin["record_batches"]
    return cases


def _selftest_logic():
    cases = {}
    i32 = lambda v: np.array(v, dtype=np.int32)  # noqa: E731
    i64 = lambda v: np.array(v, dtype=np.int64)  # noqa: E731
    q = {"body": i64([1, 1, 1, 1, 2]), "x": i32([1, 1, 2, 2, 1]), "y": i32([1, 1, 2, 2, 1]), "z": i32([1, 1, 2, 2, 1]),
         "sub": i64([5, 5, 5, 6, 7]), "prim": i64([2, 2, 2, 2, 3]), "comp": i64([0, 0, 1, 1, 2])}
    p = {"body": i64([1, 1, 2, 2, 1]), "x": i32([1, 2, 1, 9, 1]), "y": i32([1, 2, 1, 9, 1]), "z": i32([1, 2, 1, 9, 1])}
    j = join_labels(p, q)
    cases["join"] = bool(
        j["n"].tolist() == [2, 2, 1, 0, 2] and j["matched"].tolist() == [True, True, True, False, True]
        and j["consistent"].tolist() == [True, False, True, False, True] and j["sub"].tolist() == [5, -1, 7, -1, 5]
        and j["prim"].tolist() == [2, -1, 3, -1, 2] and j["duplicate_point_groups"] == 2)
    pre, post = i64([10, 10, 10, 11, 11]), i64([1, 1, 2, 1, 1])
    ok = aggregate_parity(pre, post, i64([10, 10, 11]), i64([1, 2, 1]), i64([2, 1, 2]))
    bad_w = aggregate_parity(pre, post, i64([10, 10, 11]), i64([1, 2, 1]), i64([2, 1, 3]))
    extra = aggregate_parity(pre, post, i64([10, 10, 11, 12]), i64([1, 2, 1, 1]), i64([2, 1, 2, 1]))
    missing = aggregate_parity(pre, post, i64([10, 11]), i64([1, 1]), i64([2, 2]))
    cases["parity"] = bool(ok["exact"] and not bad_w["exact"] and not extra["exact"] and not missing["exact"])
    code = i64([0, 0, 0, -1, 1, 3, 3, 4, 4])
    post9 = i64([1, 1, 1, 1, 1, 2, 2, 2, 2])
    v_ok = validate_semantics(post9[:5], code[:5], {1: 0})
    v_tie = validate_semantics(post9, code, {1: 0, 2: 3})
    cases["validation"] = bool(
        v_ok["pooled_agree"] == 3 and v_ok["pooled_n"] == 5 and not v_ok["pooled_pass"] and v_ok["every_body_plurality_matches"]
        and v_tie["per_body"][1]["plurality"] is None and not v_tie["every_body_plurality_matches"]
        and validate_semantics(i64([1] * 5), i64([0, 0, 0, 0, -1]), {1: 0})["pooled_pass"])
    status = {1: "single_compartment", 2: "multi_compartment", 3: "outside_fast_lobe_map"}
    named = {1: (0,), 2: (10, 11), 3: ()}
    spre = i64([7, 7, 7, 8, 8, 8, 8, 9])
    spost = i64([1, 1, 2, 2, 2, 2, 3, 2])
    scode = i64([5, -1, 10, 11, 12, -1, 10, 10])
    e = build_learner_edges(spre, spost, scode, status, named, set(range(len(LOBE15))))
    plastic = sorted(zip(e["plastic_pre"].tolist(), e["plastic_post"].tolist(), e["plastic_comp"].tolist(), e["plastic_weight"].tolist()))
    nonpl = sorted(zip(e["nonplastic_pre"].tolist(), e["nonplastic_post"].tolist(), e["nonplastic_reason"].tolist(), e["nonplastic_weight"].tolist()))
    e2 = build_learner_edges(spre, spost, scode, status, named, set(range(len(LOBE15))) - {11})
    nonpl2 = sorted(zip(e2["nonplastic_pre"].tolist(), e2["nonplastic_post"].tolist(), e2["nonplastic_reason"].tolist(), e2["nonplastic_weight"].tolist()))
    cases["edges"] = bool(
        plastic == [(7, 1, "a1", 2), (7, 2, "y1", 1), (8, 2, "y2", 1), (9, 2, "y1", 1)]
        and nonpl == [(8, 2, "offmap", 1), (8, 2, "unresolved", 1), (8, 3, "outside", 1)]
        and int(e["plastic_weight"].sum() + e["nonplastic_weight"].sum()) == len(spre)
        and (8, 2, "ungated", 1) in nonpl2 and int(e2["plastic_weight"].sum()) == 4)
    return cases


def selftest():
    cases = {}
    try:
        cases.update(_selftest_stream())
    except Exception as exc:
        cases["stream_exception"] = repr(exc)
    try:
        cases.update(_selftest_logic())
    except Exception as exc:
        cases["logic_exception"] = repr(exc)
    return {"passed": all(v is True for v in cases.values()) and len(cases) == 8, "cases": cases}


# ---------------------------------------------------------------- formal execution

BLOCKED = "BLOCKED_M5B3C_SOURCE"
FAIL = "FAIL_M5B3C_RESOLVER_VALIDATION"
PASS = "PASS_M5B3C_COMPARTMENT_RESOLVER_VALIDATED"
TRANSPORT = {}


def run_stream(name, included, collector, ctx):
    pin = PINS[name]
    raw = PinnedHttpStream(BASE + name, pin, ctx=ctx)
    t0 = time.time()
    tail = stream_file(raw, pin, sorted(included), collector, footer_reader())
    TRANSPORT[name] = {"seconds": round(time.time() - t0, 1), "reconnects": raw.reconnects, "connect_offsets": raw.connect_offsets}
    print(name, "streamed", raw.pos, "bytes in", TRANSPORT[name]["seconds"], "s; reconnects", raw.reconnects, flush=True)
    rec = {
        "bytes": raw.pos, "sha256": raw.sha256.hexdigest(), "md5": raw.md5.hexdigest(),
        "bytes_match_pin": raw.pos == pin["size"], "md5_matches_pin": raw.md5.hexdigest() == pin["md5"],
        "record_batches_parsed": collector.batches, "record_batches_pin": pin["record_batches"],
        "rows_total": collector.rows, "rows_kept": collector.kept,
        "dictionary_mismatch_batches": collector.dictionary_mismatch_batches,
        "kept_row_nulls": collector.kept_nulls, "key_column_nulls": collector.key_nulls,
        "tail": tail, "tail_ok": tail_ok(tail, pin),
    }
    rec["integrity_ok"] = bool(rec["bytes_match_pin"] and rec["md5_matches_pin"] and collector.batches == pin["record_batches"]
                               and collector.dictionary_mismatch_batches == 0 and collector.kept_nulls == 0 and rec["tail_ok"])
    return rec


def kc_mbon_weights(path, kc_sorted, mbon_sorted):
    table = feather.read_table(path, columns=["body_pre", "body_post", "weight"], memory_map=True)
    parts = ([], [], [])
    for batch in table.to_batches(max_chunksize=4_000_000):
        pre = batch.column(0).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        post = batch.column(1).to_numpy(zero_copy_only=False).astype(np.int64, copy=False)
        take = idx_in(kc_sorted, pre)[1] & idx_in(mbon_sorted, post)[1]
        if take.any():
            parts[0].append(pre[take].copy())
            parts[1].append(post[take].copy())
            parts[2].append(batch.column(2).to_numpy(zero_copy_only=False)[take].astype(np.int64))
    return tuple(np.concatenate(p) for p in parts)


def main():
    out = {}
    try:
        run(out)
    except Exception as exc:  # any execution error prevents evaluation: recorded, never silent
        finish(out, BLOCKED, f"execution error: {exc!r}")


def run(out):
    O.mkdir(exist_ok=True)
    out.update({"protocol": {"path": PROTOCOL_PATH, "expected_sha256": PROTOCOL_SHA, "freeze_commit": PROTOCOL_FREEZE_COMMIT,
                             "sha256": sha256_file(PROTOCOL_PATH) if Path(PROTOCOL_PATH).is_file() else None},
                "validation_threshold": VALIDATION_THRESHOLD, "pins": PINS})
    st = selftest()
    out["selftest"] = st
    if not st["passed"]:
        return finish(out, BLOCKED, "self-test failed on synthetic data")

    prereq = {"protocol_sha256": out["protocol"]["sha256"] == PROTOCOL_SHA}
    for path, want in FROZEN_FILES.items():
        prereq[f"sha256:{path}"] = Path(path).is_file() and sha256_file(path) == want
    ann_path, w_path = W / "body-annotations.feather", W / "connectome-weights.feather"
    prereq["annotations_sha256"] = ann_path.is_file() and sha256_file(ann_path) == ANN_SHA
    prereq["weights_sha256"] = w_path.is_file() and sha256_file(w_path) == WEIGHTS_SHA
    out["prerequisites"] = prereq
    if not all(prereq.values()):
        return finish(out, BLOCKED, "frozen file or pinned source hash mismatch")

    # identities and the frozen M5B3B MBON map, reproduced from the pinned annotations
    m5b3b = load_module("v6_m5b3b_frozen", M5B3B_SCRIPT)
    ref = json.loads(Path(M5B3B_RESULT).read_text(encoding="utf-8"))
    ann = feather.read_table(ann_path, columns=["bodyId", "class", "type", "instance", "somaSide"]).to_pandas()
    kc = ann[ann["class"] == "Kenyon_Cell"]
    mb = ann[ann["class"] == "MBON"]
    kc_sorted = np.sort(kc["bodyId"].to_numpy(np.int64))
    mbon_sorted = np.sort(mb["bodyId"].to_numpy(np.int64))
    kc_side = dict(zip(kc["bodyId"].astype(np.int64).tolist(), kc["somaSide"].map(m5b3b.norm).tolist()))
    ref_body = {int(r["bodyId"]): r for r in ref["mbon_mapping"]["per_body"]}
    mbon_status, mbon_named, mbon_type, map_mismatch = {}, {}, {}, []
    for _, row in mb.sort_values("bodyId").iterrows():
        bid, typ, inst = int(row["bodyId"]), m5b3b.norm(row["type"]), m5b3b.norm(row["instance"])
        comps = tuple(m5b3b.mbon_compartments(typ, inst))
        status = ("outside_fast_lobe_map" if not comps else "single_compartment" if len(comps) == 1 else "multi_compartment")
        r = ref_body.get(bid)
        if r is None or list(comps) != r["compartments"] or status != r["status"]:
            map_mismatch.append(bid)
        mbon_status[bid], mbon_type[bid] = status, typ
        mbon_named[bid] = tuple(LOBE15.index(c) for c in comps if c in LOBE15)
    gate_pop = {c: len(v) for c, v in ref["fast_dan"]["gate_population_by_compartment"].items()}
    gated = {i for i, c in enumerate(LOBE15) if gate_pop.get(c, 0) > 0}
    single_nominal = {b: mbon_named[b][0] for b, s in mbon_status.items() if s == "single_compartment"}
    wpre, wpost, ww = kc_mbon_weights(w_path, kc_sorted, mbon_sorted)
    counts = {s: sum(v == s for v in mbon_status.values()) for s in ("single_compartment", "multi_compartment", "outside_fast_lobe_map")}
    identity = {
        "KC": int(len(kc_sorted)), "MBON": int(len(mbon_sorted)), "kc_mbon_edges": int(len(wpre)),
        "kc_mbon_weight_sum": int(ww.sum()), "status_counts": counts, "m5b3b_map_mismatches": map_mismatch,
        "single_bodies_with_one_lobe_compartment": all(len(mbon_named[b]) == 1 for b in single_nominal),
        "gated_lobe_compartments": [LOBE15[i] for i in sorted(gated)],
    }
    out["identity"] = identity
    ident_ok = (identity["KC"] == EXPECTED["KC"] and identity["MBON"] == EXPECTED["MBON"]
                and identity["kc_mbon_edges"] == EXPECTED["KC_MBON_EDGES"] and not map_mismatch
                and counts == {"single_compartment": EXPECTED["SINGLE"], "multi_compartment": EXPECTED["MULTI"],
                               "outside_fast_lobe_map": EXPECTED["OUTSIDE"]}
                and identity["single_bodies_with_one_lobe_compartment"])
    if not ident_ok:
        return finish(out, BLOCKED, "identity or M5B3B map reproduction failed")

    # pinned vocabularies (M5B3C1) and schema positions (M5B3C0)
    c0 = {p["file"]: [c["name"] for c in p["schema"]] for p in json.loads(Path(C0_RESULT).read_text())["probes"]}
    c1 = json.loads(Path(C1_RESULT).read_text())["sources"]
    vocab = {PARTNERS: {"primary_post": c1[PARTNERS]["vocabularies"]["primary_post"]["values"]},
             POINTS: {k: c1[POINTS]["vocabularies"][k]["values"] for k in ("kind", "compartment", "primary", "subprimary")}}

    sources = {}
    try:
        ctx = ssl_context()
        pcol = Collector(PARTNER_FIELDS, vocab[PARTNERS], partner_keep(kc_sorted, mbon_sorted))
        sources[PARTNERS] = run_stream(PARTNERS, [c0[PARTNERS].index(f) for f in PARTNER_FIELDS], pcol, ctx)
        qcol = Collector(POINT_FIELDS, vocab[POINTS], point_keep(mbon_sorted, vocab[POINTS]["kind"].index("PostSyn")))
        sources[POINTS] = run_stream(POINTS, [c0[POINTS].index(f) for f in POINT_FIELDS], qcol, ctx)
    except Exception as exc:
        out["sources"] = sources
        return finish(out, BLOCKED, f"stream failure: {exc!r}")
    out["sources"] = sources
    if not all(s["integrity_ok"] for s in sources.values()):
        return finish(out, BLOCKED, "source integrity check failed")

    P, Q = pcol.arrays(), qcol.arrays()
    parity = aggregate_parity(P["body_pre"], P["body_post"], wpre, wpost, ww)
    j = join_labels({"body": P["body_post"], "x": P["x_post"], "y": P["y_post"], "z": P["z_post"]},
                    {"body": Q["body"], "x": Q["x"], "y": Q["y"], "z": Q["z"],
                     "sub": Q["subprimary"], "prim": Q["primary"], "comp": Q["compartment"]})
    pr_vocab = vocab[POINTS]["primary"]
    pp_to_pr = np.array([pr_vocab.index(v) if v in pr_vocab else -2 for v in vocab[PARTNERS]["primary_post"]], dtype=np.int64)
    prim_agree = j["consistent"] & (j["prim"] == pp_to_pr[P["primary_post"]])
    join_rec = {
        "partner_rows": int(len(P["body_pre"])), "postsyn_points_kept": int(len(Q["body"])),
        "unmatched_rows": int((~j["matched"]).sum()), "inconsistent_rows": int((j["matched"] & ~j["consistent"]).sum()),
        "rows_matching_several_points": int((j["n"] > 1).sum()), "duplicate_point_groups": j["duplicate_point_groups"],
        "primary_disagreements": int((j["consistent"] & ~prim_agree).sum()),
    }
    join_rec["complete_consistent"] = (join_rec["unmatched_rows"] == 0 and join_rec["inconsistent_rows"] == 0
                                       and join_rec["primary_disagreements"] == 0)
    code_of, side_of = label_codes(vocab[POINTS]["subprimary"])
    sub_safe = np.maximum(j["sub"], 0)
    code = np.where(j["consistent"], code_of[sub_safe], UNRESOLVED)
    side = np.where(j["consistent"], side_of[sub_safe], "")
    val = validate_semantics(P["body_post"], code, single_nominal)
    edges = build_learner_edges(P["body_pre"], P["body_post"], code, mbon_status, mbon_named, gated)

    # M5B3B single-compartment eligible set must be reproduced exactly (edge count and weight per compartment)
    single_mask = np.isin(edges["plastic_post"], np.array(sorted(single_nominal), dtype=np.int64))
    repro = {}
    for c in sorted(set(edges["plastic_comp"][single_mask].tolist()) | set(ref["plastic_edges"]["per_compartment"])):
        sel = single_mask & (edges["plastic_comp"] == c)
        want = ref["plastic_edges"]["per_compartment"].get(c, {})
        repro[c] = {"edges": int(sel.sum()), "weight": int(edges["plastic_weight"][sel].sum()),
                    "m5b3b_edges": want.get("edge_count"), "m5b3b_weight": want.get("raw_weight")}
    repro_ok = all(v["edges"] == v["m5b3b_edges"] and v["weight"] == v["m5b3b_weight"] for v in repro.values())

    crit = {
        "A_prerequisites_exact": True,
        "B_source_integrity": True,
        "C_aggregate_parity_exact": bool(parity["exact"] and repro_ok),
        "D_join_complete_consistent": bool(join_rec["complete_consistent"]),
        "E1_pooled_single_compartment_agreement": bool(val["pooled_pass"]),
        "E2_every_single_compartment_body_plurality": bool(val["every_body_plurality_matches"]),
        "F_no_market_valence_theta_criterion": True,
    }
    out.update({"criteria": crit, "aggregate_parity": parity, "m5b3b_single_reproduction": repro, "join": join_rec,
                "validation": val})
    out["diagnostics"] = diagnostics(P, j, code, side, vocab, kc_side, mbon_status, mbon_named, mbon_type, edges, ref, gate_pop)

    arrays = {k: v for k, v in edges.items()}
    out["learner_edges"] = {"file": "v6_m5b3c_learner_edges.npz", "content_digest": array_digest(arrays),
                            "plastic_rows": int(len(edges["plastic_pre"])), "nonplastic_rows": int(len(edges["nonplastic_pre"])),
                            "plastic_weight": int(edges["plastic_weight"].sum()), "nonplastic_weight": int(edges["nonplastic_weight"].sum())}
    np.savez_compressed(O / "v6_m5b3c_learner_edges.npz", **arrays)
    syn = {"body_pre": P["body_pre"], "body_post": P["body_post"], "x_post": P["x_post"], "y_post": P["y_post"],
           "z_post": P["z_post"], "conf_pre": P["conf_pre"], "conf_post": P["conf_post"], "primary_post": P["primary_post"],
           "subprimary": j["sub"], "neuron_part": j["comp"], "lobe_code": code}
    out["synapse_table"] = {"file": "v6_m5b3c_kc_mbon_synapses.npz (artifact only)", "content_digest": array_digest(syn),
                            "rows": int(len(P["body_pre"]))}
    np.savez_compressed(O / "v6_m5b3c_kc_mbon_synapses.npz", **syn)

    if all(crit.values()):
        return finish(out, PASS, "all frozen resolver criteria passed")
    return finish(out, FAIL, "failed: " + ", ".join(k for k, v in crit.items() if not v))


def diagnostics(P, j, code, side, vocab, kc_side, mbon_status, mbon_named, mbon_type, edges, ref, gate_pop):
    d = {}
    d["conf_range"] = {k: [float(P[k].min()), float(P[k].max())] for k in ("conf_pre", "conf_post")} if len(P["conf_pre"]) else {}
    parts = vocab[POINTS]["compartment"]
    matched = j["matched"]
    d["post_point_neuron_part"] = {parts[i]: int(v) for i, v in zip(*np.unique(j["comp"][matched], return_counts=True))}
    res = code >= 0
    kcs = np.array([kc_side.get(int(b), "") for b in P["body_pre"][res]])
    d["side_agreement_resolved"] = {"agree": int((kcs == side[res]).sum()), "disagree": int(((kcs != side[res]) & (kcs != "")).sum()),
                                    "kc_side_missing": int((kcs == "").sum())}
    pp = vocab[PARTNERS]["primary_post"]
    per_multi = []
    for b in sorted(k for k, s in mbon_status.items() if s == "multi_compartment"):
        sel = P["body_post"] == b
        c = code[sel]
        named = mbon_named[b]
        unresolved_primary = pd.Series([pp[i] for i in P["primary_post"][sel][c < 0]], dtype=object).value_counts()
        per_multi.append({
            "bodyId": int(b), "type": mbon_type[b], "named": [LOBE15[i] for i in named], "kc_synapses": int(sel.sum()),
            "in_map": {LOBE15[i]: int((c == i).sum()) for i in named},
            "offmap": {LOBE15[i]: int(v) for i, v in enumerate(np.bincount(c[c >= 0], minlength=15)) if v and i not in named},
            "unresolved": int((c < 0).sum()),
            "unresolved_primary_top": {str(k): int(v) for k, v in unresolved_primary.head(5).items()},
        })
    d["multi_compartment_bodies"] = per_multi
    per_comp = {}
    single_ids = np.array(sorted(b for b, s in mbon_status.items() if s == "single_compartment"), dtype=np.int64)
    for c in LOBE15:
        sel = edges["plastic_comp"] == c
        s1 = sel & np.isin(edges["plastic_post"], single_ids)
        s2 = sel & ~np.isin(edges["plastic_post"], single_ids)
        per_comp[c] = {"gate_dan_bodies": int(gate_pop.get(c, 0)),
                       "single_edges": int(s1.sum()), "single_weight": int(edges["plastic_weight"][s1].sum()),
                       "resolved_subedges": int(s2.sum()), "resolved_weight": int(edges["plastic_weight"][s2].sum()),
                       "resolved_mbon_bodies": int(len(np.unique(edges["plastic_post"][s2])))}
    d["plastic_by_compartment"] = per_comp
    eligible_before = set(ref["plastic_edges"]["per_compartment"])
    d["newly_plastic_compartments"] = [c for c in LOBE15 if c not in eligible_before and per_comp[c]["resolved_weight"] > 0]
    d["nonplastic_by_reason"] = {r: int(edges["nonplastic_weight"][edges["nonplastic_reason"] == r].sum())
                                 for r in sorted(set(edges["nonplastic_reason"].tolist()))}
    m5b3b = load_module("v6_m5b3b_frozen_diag", M5B3B_SCRIPT)
    loops = []
    for c in LOBE15:
        dans = sorted(t for t, comps in m5b3b.DAN_MAP.items() if c in comps and t in SIGNED_DAN)
        if not dans:
            continue
        sel = edges["plastic_comp"] == c
        for mt in sorted(set(mbon_type[int(b)] for b in np.unique(edges["plastic_post"][sel]))):
            if mt not in SIGNED_MBON:
                continue
            ids = np.array([b for b, t in mbon_type.items() if t == mt], dtype=np.int64)
            w = int(edges["plastic_weight"][sel & np.isin(edges["plastic_post"], ids)].sum())
            for dt in dans:
                loops.append({"compartment": c, "mbon_type": mt, "mbon_sign": SIGNED_MBON[mt], "dan_type": dt,
                              "dan_sign": SIGNED_DAN[dt], "plastic_weight": w,
                              "model_consistent": (SIGNED_DAN[dt], SIGNED_MBON[mt]) in MODEL_CONSISTENT})
    d["signed_loops"] = loops
    return d


def finish(out, classification, reason):
    out.update({"classification": classification, "reason": reason})
    O.mkdir(exist_ok=True)
    (O / "v6_m5b3c_resolver_result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (O / "v6_m5b3c_transport_log.json").write_text(json.dumps(TRANSPORT, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out.get(k) for k in ("classification", "reason", "criteria", "aggregate_parity", "join")},
                     indent=2, sort_keys=True))
    v = out.get("validation")
    if v:
        print("pooled agreement", round(v["pooled_agreement"], 6), "=", v["pooled_agree"], "/", v["pooled_n"])
    for r in (out.get("diagnostics") or {}).get("signed_loops", []):
        print("loop", r)


if __name__ == "__main__":
    main()
