from __future__ import annotations

import hashlib
import json
import os
import ssl
import struct
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.feather as feather
import pyarrow.ipc as ipc

O = Path("v6_m5b3c1_out")
BASE = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/"
PARTNERS = "syn-partners-male-cns-v1.0-minconf-0.5.feather"
POINTS = "syn-points-male-cns-v1.0-minconf-0.5.feather"
FULL_VOCAB = {
    PARTNERS: ["primary_post"],
    POINTS: ["kind", "compartment", "major", "primary", "superprimary", "subprimary"],
}
PROTOCOL = Path("research/v6_m5b3c1_roi_label_vocabulary_protocol.md")
C0_RESULT = Path("research/results/v6_m5b3c0_synapse_schema_result.json")
C0_RESULT_SHA = "4c0f237cf8d270ec6abaebf3926e750e75c8079bda7c1a4da8f6138af7c12c7e"
PARITY_HEADERS = ("ETag", "x-goog-generation")
MB_CODES = ["a1", "a2", "a3", "a'1", "a'2", "a'3", "b1", "b2", "b'1", "b'2", "g1", "g2", "g3", "g4", "g5"]
REFERENCE_LABELS = [c + s for c in MB_CODES for s in ("(L)", "(R)")]
MAJOR_COMPARTMENTS = ["CV", "CentralBrain", "Optic(L)", "Optic(R)", "VNC"]

MAGIC = b"ARROW1"
EOS = b"\xff\xff\xff\xff\x00\x00\x00\x00"
HEADER_SCHEMA, HEADER_DICTIONARY = 1, 2
CODECS = ("LZ4_FRAME", "ZSTD")


# ---------------------------------------------------------------- byte sources

def ssl_context():
    ca = os.environ.get("SSL_CERT_FILE")
    if not ca:
        try:  # proxy CA bundle of the authoring container; unreadable on GitHub runners
            ca = "/root/.ccr/ca-bundle.crt" if Path("/root/.ccr/ca-bundle.crt").is_file() else None
        except OSError:
            ca = None
    return ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()


class HttpSource:
    """Exact HTTP range reads; refuses any response that is not the requested 206 range."""

    def __init__(self, url):
        self.url = url
        self.ctx = ssl_context()
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, context=self.ctx, timeout=60) as r:
            self.size = int(r.headers["Content-Length"])
            self.headers = {k: r.headers.get(k) for k in ("ETag", "x-goog-hash", "x-goog-generation", "Last-Modified")}
        self.log = []

    def read(self, off, n):
        if off < 0 or n <= 0 or off + n > self.size:
            raise ValueError(f"range outside file: {off}+{n}")
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={off}-{off + n - 1}"})
        with urllib.request.urlopen(req, context=self.ctx, timeout=120) as r:
            if r.status != 206 or not (r.headers.get("Content-Range") or "").startswith(f"bytes {off}-{off + n - 1}/"):
                raise IOError(f"server did not honour range {off}+{n}: status {r.status}")
            data = r.read(n + 1)
        if len(data) != n:
            raise IOError(f"short or long range read {off}+{n}: {len(data)}")
        self.log.append((off, n))
        return data


class LocalSource:
    def __init__(self, path):
        self.path = path
        self.size = os.path.getsize(path)
        self.headers = {}
        self.log = []

    def read(self, off, n):
        with open(self.path, "rb") as f:
            f.seek(off)
            data = f.read(n)
        if len(data) != n:
            raise IOError(f"short local read {off}+{n}")
        self.log.append((off, n))
        return data


# ---------------------------------------------------------------- flatbuffer metadata

def _u(fmt, b, p):
    return struct.unpack_from(fmt, b, p)[0]


class Table:
    """Minimal read-only flatbuffer table accessor."""

    def __init__(self, buf, pos):
        self.b = buf
        self.pos = pos
        self.vt = pos - _u("<i", buf, pos)
        self.vtlen = _u("<H", buf, self.vt)

    def _fo(self, idx):
        o = 4 + 2 * idx
        return _u("<H", self.b, self.vt + o) if o < self.vtlen else 0

    def scalar(self, idx, fmt, default):
        o = self._fo(idx)
        return _u(fmt, self.b, self.pos + o) if o else default

    def _ref(self, idx):
        o = self._fo(idx)
        if not o:
            return None
        p = self.pos + o
        return p + _u("<I", self.b, p)

    def table(self, idx):
        p = self._ref(idx)
        return None if p is None else Table(self.b, p)

    def vector(self, idx):
        p = self._ref(idx)
        return (0, None) if p is None else (_u("<I", self.b, p), p + 4)

    def string(self, idx):
        n, start = self.vector(idx)
        return None if start is None else bytes(self.b[start:start + n]).decode("utf-8")

    def tables(self, idx):
        n, start = self.vector(idx)
        return [Table(self.b, start + 4 * i + _u("<I", self.b, start + 4 * i)) for i in range(n)]

    def structs(self, idx, size):
        n, start = self.vector(idx)
        return [start + size * i for i in range(n)]


def root(buf):
    return Table(buf, _u("<I", buf, 0))


def blocks(footer, idx):
    b = footer.b
    return [{"offset": _u("<q", b, p), "metadata_length": _u("<i", b, p + 8), "body_length": _u("<q", b, p + 16)}
            for p in footer.structs(idx, 24)]


def schema_fields(schema_table):
    out = []
    for f in schema_table.tables(1):
        d = f.table(4)
        rec = {"name": f.string(0), "dictionary_id": None}
        if d is not None:
            it = d.table(1)
            rec.update({
                "dictionary_id": d.scalar(0, "<q", 0),
                "index_bit_width": None if it is None else it.scalar(0, "<i", 0),
                "index_signed": None if it is None else bool(it.scalar(1, "<?", False)),
                "ordered": bool(d.scalar(2, "<?", False)),
            })
        out.append(rec)
    return out


def message_prefix(prefix8):
    """(flatbuffer length, flatbuffer start) of an encapsulated IPC message."""
    if _u("<I", prefix8, 0) == 0xFFFFFFFF:
        return _u("<i", prefix8, 4), 8
    return _u("<i", prefix8, 0), 4  # legacy framing without continuation marker


def parse_message(meta):
    n, start = message_prefix(meta[:8])
    m = root(meta[start:start + n])
    rec = {"version": m.scalar(0, "<h", 0), "header_type": m.scalar(1, "<B", 0), "body_length": m.scalar(3, "<q", 0)}
    h = m.table(2)
    if rec["header_type"] == HEADER_DICTIONARY and h is not None:
        rb = h.table(1)
        comp = None if rb is None else rb.table(3)
        rec.update({
            "dictionary_id": h.scalar(0, "<q", 0),
            "is_delta": bool(h.scalar(2, "<?", False)),
            "dictionary_length": None if rb is None else rb.scalar(0, "<q", 0),
            "compression_codec": None if comp is None else CODECS[comp.scalar(0, "<b", 0)],
        })
    if rec["header_type"] == HEADER_SCHEMA and h is not None:
        rec["fields"] = schema_fields(h)
    return rec


def read_footer(src):
    tail = src.read(src.size - 10, 10)
    if tail[4:] != MAGIC:
        raise ValueError("trailing Arrow magic missing")
    flen = _u("<i", tail, 0)
    ft = root(src.read(src.size - 10 - flen, flen))
    return {
        "footer_length": flen,
        "version": ft.scalar(0, "<h", 0),
        "fields": schema_fields(ft.table(1)),
        "dictionary_blocks": blocks(ft, 2),
        "record_batch_blocks": blocks(ft, 3),
    }


def read_schema_message(src):
    if src.read(0, 8)[:6] != MAGIC:
        raise ValueError("leading Arrow magic missing")
    prefix = src.read(8, 8)
    n, start = message_prefix(prefix)
    return prefix + src.read(16, start + n - 8)


def decode_dictionaries(schema_msg, dict_msgs):
    """Replay schema + dictionary messages + a local zero-row batch as an IPC stream; return decoded dictionaries."""
    schema = ipc.read_schema(pa.py_buffer(schema_msg))
    empty = pa.record_batch([pa.array([], type=f.type) for f in schema], schema=schema)
    stream = b"".join([schema_msg, *dict_msgs, empty.serialize().to_pybytes(), EOS])
    batch = ipc.open_stream(pa.py_buffer(stream)).read_next_batch()
    if batch.num_rows != 0:
        raise ValueError("synthetic batch is not empty")
    return schema, {f.name: batch.column(i).dictionary.to_pylist()
                    for i, f in enumerate(schema) if pa.types.is_dictionary(f.type)}


# ---------------------------------------------------------------- checks

def dictionary_problems(fields, dict_recs):
    problems = []
    needed = {f["dictionary_id"] for f in fields if f["dictionary_id"] is not None}
    missing = sorted(needed - {r["dictionary_id"] for r in dict_recs})
    if missing:
        problems.append(f"dictionary ids without a dictionary message: {missing}")
    non_delta = [r["dictionary_id"] for r in dict_recs if not r["is_delta"]]
    repeated = sorted({i for i in non_delta if non_delta.count(i) > 1})
    if repeated:
        problems.append(f"repeated non-delta dictionary ids: {repeated}")
    return problems


def intersecting_reads(log, record_batch_blocks):
    starts = np.array([b["offset"] for b in record_batch_blocks], dtype=np.int64)
    ends = starts + np.array([b["metadata_length"] + b["body_length"] for b in record_batch_blocks], dtype=np.int64)
    return [(o, n) for o, n in log if bool(np.any((starts < o + n) & (ends > o)))]


def qualifying_columns(vocabs):
    ref = set(REFERENCE_LABELS)
    return [{"file": name, "column": col} for name in (PARTNERS, POINTS)
            for col, voc in vocabs.get(name, {}).items() if ref <= set(voc)]


def blocked_reasons(problems, parity):
    reasons = [f"{n}: {p}" for n, ps in problems.items() for p in ps]
    return reasons + [f"{n}: parity {k}" for n, d in parity.items() for k, v in d.items() if not v]


def source_parity(rec, ref):
    return {
        "content_length": rec["content_length"] == ref["content_length"],
        "headers": all(rec["server_headers"].get(h) == ref["server_headers"].get(h) for h in PARITY_HEADERS),
        "record_batch_count": rec["record_batch_block_count"] == ref["num_record_batches"],
        "schema": [(f["name"], f["type"]) for f in rec["schema"]] == [(c["name"], c["type"]) for c in ref["schema"]],
    }


# ---------------------------------------------------------------- probe

def probe_source(src):
    """Footer, schema message and dictionary messages only. Returns (record, vocab, problems)."""
    problems = []
    ft = read_footer(src)
    schema_msg = read_schema_message(src)
    sm = parse_message(schema_msg)
    if sm["header_type"] != HEADER_SCHEMA or sm["body_length"] != 0:
        problems.append("schema message is not a Schema header with bodyLength 0")
    elif [(f["name"], f["dictionary_id"]) for f in sm["fields"]] != [(f["name"], f["dictionary_id"]) for f in ft["fields"]]:
        problems.append("schema message fields differ from footer schema fields")
    dict_msgs, dict_recs = [], []
    for b in ft["dictionary_blocks"]:
        raw = src.read(b["offset"], b["metadata_length"] + b["body_length"])
        rec = parse_message(raw[: b["metadata_length"]])
        if rec["header_type"] != HEADER_DICTIONARY:
            problems.append(f"block at {b['offset']} is not a DictionaryBatch")
        elif rec["body_length"] != b["body_length"]:
            problems.append(f"dictionary bodyLength mismatch at {b['offset']}")
        dict_recs.append({**b, **{k: rec.get(k) for k in ("dictionary_id", "is_delta", "dictionary_length", "compression_codec")}})
        dict_msgs.append(raw)
    problems += dictionary_problems(ft["fields"], dict_recs)
    schema, vocab = decode_dictionaries(schema_msg, dict_msgs)
    intersecting = intersecting_reads(src.log, ft["record_batch_blocks"])
    if intersecting:
        problems.append("a read intersected a record-batch block")
    record = {
        "content_length": src.size,
        "server_headers": src.headers,
        "footer_version": ft["version"],
        "footer_length": ft["footer_length"],
        "dictionary_block_count": len(ft["dictionary_blocks"]),
        "record_batch_block_count": len(ft["record_batch_blocks"]),
        "schema": [{"name": f.name, "type": str(f.type)} for f in schema],
        "fields": ft["fields"],
        "schema_message_version": sm["version"],
        "dictionary_messages": dict_recs,
        "range_reads": [{"offset": o, "length": n} for o, n in src.log],
        "reads_intersecting_record_batch_blocks": intersecting,
    }
    return record, vocab, problems


def canonical_sha(values):
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- self-test on synthetic files

def selftest():
    cases = []
    rng = np.random.default_rng(7)
    n = 20000
    prim = [f"R{i:03d}(R)" for i in range(300)]
    comp = ["a1(R)", "g5(L)", "b'2(R)", "brain", "vnc"]
    df = pd.DataFrame({
        "z": rng.integers(0, 1000, n, dtype=np.int32),
        "kind": pd.Categorical(rng.choice(["PreSyn", "PostSyn"], n), categories=["PostSyn", "PreSyn"]),
        "conf": rng.random(n).astype(np.float32),
        "body": rng.integers(0, 10**9, n, dtype=np.int64),
        "compartment": pd.Categorical(rng.choice(comp, n), categories=comp),
        "primary": pd.Categorical(rng.choice(prim, n), categories=prim, ordered=True),
        "point_id": rng.integers(0, 2**63, n, dtype=np.uint64),
    })
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for c in ("lz4", "zstd", "uncompressed"):
            p = os.path.join(d, f"pandas_{c}.feather")
            feather.write_feather(df, p, compression=c, chunksize=1500)
            paths.append(p)
        p = os.path.join(d, "deltas.arrow")
        s = pa.schema([("k", pa.dictionary(pa.int8(), pa.string())), ("v", pa.int32())])
        with ipc.new_file(p, s, options=ipc.IpcWriteOptions(emit_dictionary_deltas=True, compression="lz4")) as w:
            for voc in (["a", "b"], ["a", "b", "c"], ["a", "b", "c", "d"]):
                arr = pa.DictionaryArray.from_arrays(pa.array(range(len(voc)), pa.int8()), pa.array(voc))
                w.write_batch(pa.record_batch([arr, pa.array(range(len(voc)), pa.int32())], schema=s))
        paths.append(p)
        for p in paths:
            src = LocalSource(p)
            rec, vocab, problems = probe_source(src)
            reader = ipc.open_file(p)
            full = reader.read_all()
            want = {}
            for name in full.column_names:
                col = full.column(name)
                if pa.types.is_dictionary(col.type):
                    want[name] = col.chunk(col.num_chunks - 1).dictionary.to_pylist()
            cases.append({
                "case": os.path.basename(p),
                "record_batches": rec["record_batch_block_count"],
                "record_batches_match_reader": rec["record_batch_block_count"] == reader.num_record_batches,
                "dictionary_messages": [(m["dictionary_id"], m["is_delta"], m["compression_codec"]) for m in rec["dictionary_messages"]],
                "vocabularies_equal_full_read": vocab == want,
                "no_record_batch_bytes_read": not rec["reads_intersecting_record_batch_blocks"],
                "problems": problems,
            })
    ok = all(c["record_batches_match_reader"] and c["vocabularies_equal_full_read"]
             and c["no_record_batch_bytes_read"] and not c["problems"] for c in cases)
    return {"passed": ok, "cases": cases}


# ---------------------------------------------------------------- main

def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    O.mkdir(exist_ok=True)
    out = {
        "protocol": {"path": str(PROTOCOL), "sha256": sha256_file(PROTOCOL)},
        "reference_labels": REFERENCE_LABELS,
        "firewall": "footers, schema messages and dictionary batches only; no record-batch bytes; no per-synapse values",
    }
    st = selftest()
    out["selftest"] = st
    if not st["passed"]:
        return finish(out, "BLOCKED_M5B3C1_SOURCE", "decoder self-test failed on synthetic files")
    c0_ok = sha256_file(C0_RESULT) == C0_RESULT_SHA
    c0 = {p["file"]: p for p in json.loads(C0_RESULT.read_text())["probes"]} if c0_ok else {}
    out["m5b3c0_record_sha256_match"] = c0_ok
    if not c0_ok:
        return finish(out, "BLOCKED_M5B3C1_SOURCE", "M5B3C0 parity record hash mismatch")
    sources, vocabs, problems, parity = {}, {}, {}, {}
    try:
        for name in (PARTNERS, POINTS):
            src = HttpSource(BASE + name)
            rec, vocab, probs = probe_source(src)
            sources[name], vocabs[name], problems[name] = rec, vocab, probs
            parity[name] = source_parity(rec, c0[name])
    except Exception as exc:
        out.update({"sources": sources, "problems": problems, "parity_with_m5b3c0": parity})
        return finish(out, "BLOCKED_M5B3C1_SOURCE", f"read or parse failure: {exc!r}")

    for name, rec in sources.items():
        rec["vocabularies"] = {}
        for col, voc in vocabs[name].items():
            if col in FULL_VOCAB[name]:
                rec["vocabularies"][col] = {"size": len(voc), "values": voc}
            else:
                rec["vocabularies"][col] = {"size": len(voc), "canonical_json_sha256": canonical_sha(voc)}
    out.update({"sources": sources, "problems": problems, "parity_with_m5b3c0": parity})

    qualifying = qualifying_columns(vocabs)
    out["qualifying_columns"] = qualifying
    diag = {"reference_labels_by_column": {}, "PED_presence": {}}
    for name in (PARTNERS, POINTS):
        for col in FULL_VOCAB[name]:
            voc = set(vocabs[name].get(col, []))
            key = f"{name}:{col}"
            diag["reference_labels_by_column"][key] = {
                "present": [x for x in REFERENCE_LABELS if x in voc],
                "absent": [x for x in REFERENCE_LABELS if x not in voc],
            }
            diag["PED_presence"][key] = {"PED(L)": "PED(L)" in voc, "PED(R)": "PED(R)" in voc}
    diag["compartment_equals_documented_major_compartments"] = set(vocabs[POINTS].get("compartment", [])) == set(MAJOR_COMPARTMENTS)
    diag["primary_post_equals_primary_as_set"] = set(vocabs[PARTNERS].get("primary_post", [])) == set(vocabs[POINTS].get("primary", []))
    out["diagnostics"] = diag

    blocked = blocked_reasons(problems, parity)
    if blocked:
        return finish(out, "BLOCKED_M5B3C1_SOURCE", "; ".join(blocked))
    if qualifying:
        return finish(out, "PASS_M5B3C1_MB_COMPARTMENT_COLUMN_IDENTIFIED",
                      "a dictionary column contains all 30 documented MB lobe-compartment labels")
    return finish(out, "FAIL_M5B3C1_MB_COMPARTMENT_COLUMN_NOT_FOUND",
                  "no dictionary column contains all 30 documented MB lobe-compartment labels")


def finish(out, classification, reason):
    out.update({"classification": classification, "reason": reason})
    (O / "v6_m5b3c1_roi_vocabulary_result.json").write_text(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({k: out.get(k) for k in ("classification", "reason", "qualifying_columns", "parity_with_m5b3c0")},
                     indent=2, sort_keys=True))
    st = out.get("selftest", {})
    print("selftest passed:", st.get("passed"))
    for name, rec in out.get("sources", {}).items():
        print(name, "dictionary blocks", rec["dictionary_block_count"], "record-batch blocks", rec["record_batch_block_count"],
              "reads", len(rec["range_reads"]))
        for col, v in rec.get("vocabularies", {}).items():
            print("   ", col, v["size"], v.get("values") if "values" in v and v["size"] <= 40 else "")


if __name__ == "__main__":
    main()
