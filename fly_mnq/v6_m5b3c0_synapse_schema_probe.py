from __future__ import annotations

import io
import json
import os
import ssl
import urllib.request
from pathlib import Path

import pyarrow as pa
import pyarrow.ipc as ipc

O = Path("v6_m5b3c0_out")
O.mkdir(exist_ok=True)
BASE = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/"
FILES = [
    "syn-partners-male-cns-v1.0-minconf-0.5.feather",
    "syn-points-male-cns-v1.0-minconf-0.5.feather",
]
FOOTER_SPAN_LIMIT = 16 << 20  # any read deeper than this from the file end would indicate body access


def ssl_context():
    ca = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if Path("/root/.ccr/ca-bundle.crt").is_file() else None)
    return ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()


class RangeFile(io.RawIOBase):
    """Read-only seekable HTTP file using Range requests; logs every range read (offset, length)."""

    def __init__(self, url):
        self.url = url
        self.ctx = ssl_context()
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, context=self.ctx, timeout=60) as r:
            self.size = int(r.headers["Content-Length"])
            self.headers = {k: r.headers.get(k) for k in ("ETag", "x-goog-hash", "x-goog-generation", "Last-Modified")}
        self.pos = 0
        self.log = []

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if n <= 0:
            return b""
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"})
        with urllib.request.urlopen(req, context=self.ctx, timeout=120) as r:
            data = r.read()
        self.log.append((self.pos, len(data)))
        self.pos += len(data)
        return data

    def readinto(self, b):
        data = self.read(len(b))
        b[: len(data)] = data
        return len(data)


def probe(name):
    f = RangeFile(BASE + name)
    reader = ipc.open_file(pa.PythonFile(f, mode="r"))
    schema = reader.schema
    cols = [{"name": fld.name, "type": str(fld.type), "dictionary": pa.types.is_dictionary(fld.type)} for fld in schema]
    body_reads = [(o, l) for o, l in f.log if o < f.size - FOOTER_SPAN_LIMIT and o >= 8]
    return {
        "file": name,
        "content_length": f.size,
        "server_headers": f.headers,
        "num_record_batches": reader.num_record_batches,
        "schema": cols,
        "schema_metadata_keys": sorted(k.decode() for k in (schema.metadata or {}).keys()),
        "range_reads": [{"offset": o, "length": l, "distance_from_end": f.size - o} for o, l in f.log],
        "body_reads_detected": body_reads,
    }


def main():
    out = {"probes": [], "firewall": "footer/schema only; no record-batch or dictionary bodies read"}
    try:
        for name in FILES:
            out["probes"].append(probe(name))
    except Exception as exc:
        out.update({"classification": "BLOCKED_M5B3C0_SOURCE_SCHEMA", "reason": repr(exc)})
        write(out)
        return
    no_body = all(not p["body_reads_detected"] for p in out["probes"])
    names = {n for p in out["probes"] for n in (c["name"].lower() for c in p["schema"])}
    has_pre_post = any("pre" in n for n in names) and any("post" in n for n in names)
    has_roi = any("roi" in n for n in names)
    has_xyz = {"x", "y", "z"} <= names or any(n.endswith(("_x", "x_pre", "x_post")) for n in names)
    feasible = has_pre_post and (has_roi or has_xyz)
    out["checks"] = {"footers_parsed": True, "no_body_reads": no_body, "pre_post_identifiers": has_pre_post,
                     "roi_column": has_roi, "xyz_columns": has_xyz}
    if not no_body:
        out.update({"classification": "BLOCKED_M5B3C0_SOURCE_SCHEMA", "reason": "a body read was detected; firewall integrity not demonstrated"})
    elif feasible:
        out.update({"classification": "PASS_M5B3C0_SYNAPSE_SCHEMA_RESOLVER_FEASIBLE", "reason": "schemas expose pre/post identifiers and ROI or coordinates"})
    else:
        out.update({"classification": "FAIL_M5B3C0_RESOLVER_INFEASIBLE_FROM_SCHEMA", "reason": "schemas lack identifiers or ROI/coordinates"})
    write(out)


def write(out):
    (O / "v6_m5b3c0_synapse_schema_result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: out.get(k) for k in ("classification", "reason", "checks")}, indent=2, sort_keys=True))
    for p in out.get("probes", []):
        print(p["file"], p["content_length"], "batches", p["num_record_batches"])
        for c in p["schema"]:
            print("   ", c["name"], c["type"])


if __name__ == "__main__":
    main()
