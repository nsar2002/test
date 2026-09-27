# V6-M5B3C1 — MALECNS SYNAPSE ROI LABEL VOCABULARY PROBE (PER-SYNAPSE VALUES CLOSED)

**STATUS: FROZEN BEFORE ANY DICTIONARY BATCH OF EITHER SYNAPSE FILE WAS READ.** The only bytes of the two synapse files read so far are the V6-M5B3C0 trailers and footers.

## Why this gate exists

### Correction of the M5B3C0 consequence text

The M5B3C0 result, `research/v6_m5b3c0_synapse_source_schema_result.md`, says the syn-points `compartment` column provides "the official per-synapse `compartment` label", implying a mushroom-body (MB) compartment label. That reading was an **unverified interpretation of a column name**.

Before this freeze, only nomenclature documentation was consulted, and no additional synapse-file byte was read. The documentation comes from the public bucket `flyem-male-cns` and contains no per-synapse information:

| Object | Generation | SHA256 |
|---|---|---|
| `v1.0/male-cns-v1.0.json` (dataset viewer descriptor) | 1778032077888581 | `390e01b0c78742bb2465f9ec8f89890106c008d6ac1d5b06840b610f532ea754` |
| `rois/malecns-major-compartments-v2/segment_properties/info` | 1758224769290228 | `168202d7c97497d68078e95c7b7331dc84b5547e8356a7df21aacaf0ea7d3c5d` |
| `rois/malecns-subcompartments-v3/segment_properties/info` | 1777786230941991 | `74490670acafe653900b68fa360ab1836a0bdd76678e1a14b65e0dd5092f3f33` |
| `rois/fullbrain-roi-v5/segment_properties/info` | 1779144090259185 | `2c45b2809adab85facc80b89085fcf90e9ad1ab8cdada4f48c1f712847cd4737` |

Contents:
- The descriptor lists separate ROI layers named `major-compartments`, `brain-neuropils` and `brain-neuropil-subcompartments`.
- `major-compartments` has exactly 5 segment names: `CV`, `CentralBrain`, `Optic(L)`, `Optic(R)`, `VNC`.
- `brain-neuropils` has 82 names. Among them are the MB lobes `aL`, `a'L`, `bL`, `b'L`, `gL`, the calyx `CA` and the peduncle `PED`, each with `(L)` and `(R)`.
- `brain-neuropil-subcompartments` has 199 names. Among them are exactly 30 MB lobe-compartment labels: `a1 a2 a3 a'1 a'2 a'3 b1 b2 b'1 b'2 g1 g2 g3 g4 g5`, each with `(L)` and `(R)`. The prime is ASCII U+0027. No subcompartment name contains `ped`.

This suggests that `compartment` holds the major CNS compartment and that MB compartments sit at a finer ROI level. That is documentation, not evidence about the synapse files. **The resolver must not be frozen on either interpretation.** M5B3C1 therefore reads the actual label vocabularies (Arrow dictionaries) of both synapse files.

### Recorded deviation in M5B3C0

The M5B3C0 protocol required recording "the number of dictionary batches". The M5B3C0 probe did not record it. The M5B3C0 classification rule does not depend on that number, so its classification stands. M5B3C1 records the number.

## Sources and source parity with M5B3C0

The two files are the ones probed in M5B3C0 (`v1.0/connectome-data/flat-connectome/`):
- `syn-partners-male-cns-v1.0-minconf-0.5.feather`
- `syn-points-male-cns-v1.0-minconf-0.5.feather`

Source parity is required against the M5B3C0 record `research/results/v6_m5b3c0_synapse_schema_result.json` (SHA256 `4c0f237cf8d270ec6abaebf3926e750e75c8079bda7c1a4da8f6138af7c12c7e`). Each of the following must be equal:
- `Content-Length`;
- `ETag`;
- `x-goog-generation`;
- the number of record-batch blocks in the footer (4,759 and 5,455);
- the ordered schema field names and types (pyarrow rendering) decoded from the schema message.

## Frozen read scope (per file)

1. One `HEAD` request for the headers.
2. The 10-byte trailer, then the footer bytes it points to (as in M5B3C0).
3. The first 8 bytes of the file (leading magic), then the schema message that starts at offset 8. The schema message is metadata only: its header must be `Schema` and its `bodyLength` must be 0.
4. Each dictionary-batch message listed in the footer's `dictionaries` block table, metadata plus body, read as one exact range.

No other bytes are read. In particular, **no byte of any record-batch block listed in the footer is read**. The probe logs every range read and checks each against every record-batch block interval `[offset, offset + metaDataLength + bodyLength)`.

## Frozen decoding method

The footer, schema and message metadata are parsed with a minimal read-only flatbuffer reader.

Dictionary contents are decoded by pyarrow 17.0.0. It replays, as an Arrow IPC stream:
- the file's own schema message;
- all dictionary messages, in footer order;
- a locally generated **zero-row** record batch of the same schema, which contains no source values;
- the end-of-stream marker.

The decoded dictionaries are read from that zero-row batch.

### Decoder self-test (run before the probe, same workflow)

The self-test generates synthetic files locally. They contain no MaleCNS data:
- pandas-written Feather files with LZ4, ZSTD and no compression;
- a pyarrow-written IPC file with dictionary deltas.

For every file, it requires:
- the decoded dictionaries equal those from a full pyarrow read;
- no read intersects a record-batch block.

The decoder was validated on these cases before this freeze.

## Recorded outputs

For each file:
- the server headers;
- the footer version and length;
- the count of dictionary blocks and of record-batch blocks;
- the schema fields with dictionary id, index bit width, signedness and ordered flag;
- for every dictionary message: id, `isDelta`, compression codec, dictionary length, and block offset and lengths;
- the full read log with the firewall check.

Decoded vocabularies:
- Recorded in full: `primary_post` (syn-partners); `kind`, `compartment`, `major`, `primary`, `superprimary`, `subprimary` (syn-points).
- The 12 optic-lobe column and layer dictionaries: size and SHA256 of the canonical JSON list only. Canonical JSON is `json.dumps(list, ensure_ascii=False, separators=(",", ":"))`, UTF-8 encoded.

## Frozen reference labels

These are the 30 documented MB lobe-compartment labels, compared as exact strings:
`a1(L) a1(R) a2(L) a2(R) a3(L) a3(R) a'1(L) a'1(R) a'2(L) a'2(R) a'3(L) a'3(R) b1(L) b1(R) b2(L) b2(R) b'1(L) b'1(R) b'2(L) b'2(R) g1(L) g1(R) g2(L) g2(R) g3(L) g3(R) g4(L) g4(R) g5(L) g5(R)`.

They correspond to the M5B3B vocabulary as nomenclature: gamma `y`→`g`, beta `B`→`b`, alpha and primes unchanged. This correspondence is declared here for use by M5B3C and is not tested here.

## Frozen classification

**`BLOCKED_M5B3C1_SOURCE`** if any of these occurs:
- the self-test fails;
- any HTTP or parse failure;
- any source-parity mismatch with M5B3C0;
- any read intersects a record-batch block;
- the schema message is not a `Schema` header with `bodyLength` 0;
- a dictionary message's metadata `bodyLength` differs from its footer block;
- a message in the dictionary block table is not a `DictionaryBatch`;
- a dictionary-encoded field has no dictionary message;
- more than one non-delta dictionary message has the same id.

**`PASS_M5B3C1_MB_COMPARTMENT_COLUMN_IDENTIFIED`**: no BLOCKED condition, and at least one dictionary-encoded column in either file whose vocabulary contains all 30 reference labels. All qualifying columns are listed.

**`FAIL_M5B3C1_MB_COMPARTMENT_COLUMN_NOT_FOUND`**: no BLOCKED condition, and no column qualifies.

Diagnostics, never criteria:
- for each fully recorded column, the reference labels present and absent;
- whether the `compartment` vocabulary equals the 5 documented major-compartment names as a set;
- whether `PED(L)` and `PED(R)` occur in each fully recorded vocabulary;
- whether `primary_post` equals `primary` as a set;
- local and GitHub Actions byte parity of the result JSON.

## Firewalls

- Per-synapse values stay closed: no body IDs, coordinates, confidences, point IDs or per-synapse ROI assignments. Only label vocabularies (Arrow dictionaries) are read. A vocabulary lists possible labels and carries no per-synapse information.
- No resolver design is selected here. M5B3C freezes the resolver after this record.
- MNQ/reward/PnL/strategy/trading/prop-firm evaluation CLOSED.
- θ not selected.
- Amin and M4V0 numeric values unopened.
