# V6-M5B3C1 formal result

Classification: **PASS_M5B3C1_MB_COMPARTMENT_COLUMN_IDENTIFIED**

The only qualifying column is `subprimary` in `syn-points-male-cns-v1.0-minconf-0.5.feather`, which contains all 30 documented MB lobe-compartment labels.

## Provenance

- **Protocol:** `research/v6_m5b3c1_roi_label_vocabulary_protocol.md`, SHA256 `26fda91338840b86e9dce0f35e1fcfe931072504597232c7e140bf4873047ade`. Frozen in the protocol-only commit `8d72bb5` before any dictionary batch was read.
- **Implementation:** commit `dbbdbaa0dc8ea8b55007e45bf6c460f26a39b593`, `fly_mnq/v6_m5b3c1_roi_vocabulary_probe.py`, SHA256 `6a88359ea4b0b90f2e615d48cfd21a51b7f188a24c34d51d7cdd0ee6c0419557`.
- **GitHub Actions:**
  - run 36293331100, job 108547444253, head `b51845c034fb221b850ce6621d094b2218e36903`;
  - artifact 10923525057, digest `sha256:90cd76245d661b1be24c77324979cc3a2b0d07d1d5b348338ba5d7cb0b0ad648`;
  - result commit `6831e02154d42f9dc004e834843f1eeb8dabe2a4`.
- **Result JSON:** SHA256 `4a3d73dac3fd87ed266a8e8003f1f345cf1b06aa0f5e5960d35f8be3e38b21b5`. It is **byte-identical** to the independent local execution.

## Controls

- The decoder self-test passed in CI and locally. It covers synthetic Feather files (LZ4, ZSTD, uncompressed) and an IPC file with dictionary deltas. In every case the decoded dictionaries equal a full read, and no record-batch bytes were read.
- Local deliberate-mutant controls, before the formal run: 13 mutants were rejected and 4 clean controls accepted. The mutants were:
  - a read of a record-batch body, or of its metadata prefix;
  - a missing dictionary id;
  - a repeated non-delta dictionary;
  - one missing reference label;
  - a spacing variant or a Unicode-prime variant of a label;
  - an ETag, generation, content-length, record-batch-count or schema-type change;
  - a server that ignores `Range`.
- Source parity with M5B3C0 held for both files: Content-Length, ETag, `x-goog-generation`, record-batch count and schema.

## Firewall evidence

| File | Range reads | Bytes read | File size | Reads intersecting a record-batch block |
|---|---|---|---|---|
| syn-partners | 6 | 120,602 | 6,777,179,098 | 0 |
| syn-points | 23 | 202,266 | 13,061,489,098 | 0 |

The reads covered only the trailer, the footer, the leading magic, the schema message and the dictionary batches. No body ID, coordinate, confidence, point ID or per-synapse label was read.

This also records the dictionary-batch count that M5B3C0 omitted:
- syn-partners has 1 dictionary block;
- syn-points has 18;
- all are non-delta and LZ4_FRAME compressed.

## Vocabularies (key columns)

| File:column | Size | Content |
|---|---|---|
| points:`kind` | 2 | `PostSyn`, `PreSyn` |
| points:`compartment` | 5 | `unknown`, `axon`, `dendrite`, `linker`, `cell-body-fiber` |
| points:`major` | 6 | `<unspecified>`, `CentralBrain`, `Optic(L)`, `Optic(R)`, `CV`, `VNC` |
| points:`superprimary` | 13 | includes `MB(L)`, `MB(R)` |
| points:`primary` | 146 | neuropils, including `CA`, `PED`, `aL`, `a'L`, `bL`, `b'L`, `gL` per side |
| partners:`primary_post` | 146 | identical set to points:`primary` |
| points:`subprimary` | 204 | the 30 MB compartments, `gL-unspecified(L)`, `gL-unspecified(R)`, `<unspecified>`, plus AL glomeruli and CX/LX subdivisions |

No subprimary label exists for the peduncle or the calyx. `PED(L)` and `PED(R)` exist only at the `primary` level.

## Corrections on the record

1. **M5B3C0's interpretation was wrong.** The M5B3C0 result text read the syn-points `compartment` column as "the official per-synapse compartment label", meaning an MB compartment. In fact `compartment` is the **neuronal compartment of the synapse point**: axon, dendrite, linker, cell-body fiber or unknown. It is not a brain region.
2. **The documentation-based expectation in this gate's own protocol was also wrong.** That expectation was "major CNS compartment". The major CNS compartment is carried by `major`, not by `compartment`.
3. **Why neither error affected a result.** The M5B3C1 protocol refused to freeze the resolver on either interpretation. This gate is the evidence that resolves the question.
4. **M5B3C0's classification stands.** Its frozen criterion (identifiers plus coordinates) did not depend on the column's meaning.

## Consequences for M5B3C (resolver)

- The MB compartment of a KC→MBON synapse is **not** in syn-partners. It must come from syn-points `subprimary`, joined through the postsynaptic point: body and x, y, z.
- `primary_post` (syn-partners) and `primary` (syn-points) share one vocabulary. Their agreement on every joined synapse is an independent check of the join.
- The `compartment` column gives a second diagnostic: postsynaptic points of KC→MBON synapses are expected on MBON dendrites.
- Peduncle synapses cannot be assigned to `pedc` from `subprimary`. Treating `PED` as `pedc` would repeat the generic-`ped` conflation that M5B3B explicitly refused.

MNQ reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED. θ is not selected.
