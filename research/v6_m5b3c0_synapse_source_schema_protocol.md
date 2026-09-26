# V6-M5B3C0 — MALECNS SYNAPSE-LEVEL SOURCE SCHEMA PROBE (VALUES CLOSED)

**STATUS: FROZEN BEFORE THE SCHEMA OF EITHER FILE WAS READ.** Only the bucket listing (file names and sizes) has been seen.

## Authorization and purpose

M5B3B froze KC input to multi-compartment MBONs "until a separately validated synapse-level compartment resolver exists". V6-M5D1C (run 36253035242) found that every signed MBON facing a signed DAN is multi-compartment (MBON11, MBON12, MBON21, MBON29, MBON33). So the resolver, planned as M5B3C, is now the single blocker for a closed, valence-consistent learning loop.

M5B3C0 is the source-schema step only. It establishes whether the official MaleCNS v1.0 synapse files support a compartment resolver, **without reading any synapse value**: no body IDs, coordinates, ROI labels or confidences.

## Sources (official public bucket `flyem-male-cns`, `v1.0/connectome-data/flat-connectome/`)

- `syn-partners-male-cns-v1.0-minconf-0.5.feather`: listed size 6,777.2 MB.
- `syn-points-male-cns-v1.0-minconf-0.5.feather`: listed size 13,061.5 MB.

## Frozen method

- Read only the Arrow IPC file footer of each file, via HTTP range requests: the trailing magic, the footer length and the footer flatbuffer. From it, record:
  - the schema (column names, Arrow types, schema metadata keys);
  - the number of record batches;
  - the number of dictionary batches.
- No record-batch body is read. Dictionary-encoded columns are reported as types only; dictionary contents are **not** read.
- Record the exact byte size (`Content-Length`) and the ETag or `x-goog-hash` headers as provided by the server. Full-file SHA256 pinning is deferred to the gate that opens values.

## Frozen qualification rule

`PASS_M5B3C0_SYNAPSE_SCHEMA_RESOLVER_FEASIBLE` requires that both footers parse, and that the schemas together expose:
- (a) per-synapse or per-connection presynaptic and postsynaptic body identifiers;
- (b) either a per-synapse region/ROI column, or per-point x/y/z coordinates that can be joined to the partner rows.

Otherwise:
- `BLOCKED_M5B3C0_SOURCE_SCHEMA`, if a footer cannot be read;
- `FAIL_M5B3C0_RESOLVER_INFEASIBLE_FROM_SCHEMA`, if the schemas lack (a) or (b).

This gate selects no resolver design and opens no values.

## Firewalls

- Synapse values remain unopened: no body IDs, coordinates, ROI labels or confidence values are read.
- MNQ/reward/PnL/trading CLOSED.
- θ not selected.
- Amin and M4V0 numeric values unopened.
