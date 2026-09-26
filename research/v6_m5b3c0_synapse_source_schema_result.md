# V6-M5B3C0 formal result

Classification: PASS_M5B3C0_SYNAPSE_SCHEMA_RESOLVER_FEASIBLE

## Provenance

- Protocol: `research/v6_m5b3c0_synapse_source_schema_protocol.md`, frozen in the protocol-only commit `d54f5d8c47b4d6a7bdd36afffdd1de4e5246a6fc` before either schema was read.
- The first CI run, 36253500067 (result commit a05eae7), recorded **BLOCKED_M5B3C0_SOURCE_SCHEMA** with `PermissionError(13)`. Cause: an executor bug. The probe's check for the authoring container's CA bundle under `/root` raised EACCES on the GitHub runner. The fix is executor-only (commit 21fa753) and changes no protocol, criterion or source. The BLOCKED record stays in git history.
- Formal run after the fix: run 36253567413; job 108436010896; artifact 10909592746 (digest sha256:b9a5484abab297caf7623923821100bd08aa6d59fb3b9e1c246f50c1c2c4ca96); result commit 2c992780da1e4818313b0024a788f36fc3e47441; result JSON SHA256 4c0f237cf8d270ec6abaebf3926e750e75c8079bda7c1a4da8f6138af7c12c7e.

## Firewall evidence

Each file was read with exactly two HTTP range reads: the 10-byte trailer and the Arrow footer (116,642 and 140,770 bytes from the end). No record-batch or dictionary body was read. No body IDs, coordinates, ROI labels or confidence values were opened.

## Source identities (server-reported)

| File | Bytes | Arrow record batches | ETag | crc32c |
|---|---|---|---|---|
| syn-partners-male-cns-v1.0-minconf-0.5.feather | 6,777,179,098 | 4,759 | 58efcf712f8c4d4de5f2ad51e97def76 | jTlNIA== |
| syn-points-male-cns-v1.0-minconf-0.5.feather | 13,061,489,098 | 5,455 | c69d08758de07582035cc8843574493a | 1E7gRw== |

## Schemas (names and types only)

- **syn-partners**: `x_pre, y_pre, z_pre` (int32), `body_pre` (int64), `conf_pre` (float), `x_post, y_post, z_post` (int32), `body_post` (int64), `conf_post` (float), `primary_post` (dictionary<string>).
- **syn-points**: `z, y, x` (int32), `kind` (dict), `conf` (float), `sv` (int64), `body` (int64), **`compartment` (dict)**, `major`/`primary`/`superprimary`/`subprimary` ROI labels (dict), optic-lobe column/layer labels, `point_id` (uint64).

## Consequence

A synapse-level compartment resolver is feasible from the official sources. Each KC→MBON synapse in `syn-partners` can be joined to its postsynaptic point in `syn-points` by coordinates and body, to obtain the official per-synapse `compartment` label. The per-point `compartment` column was not anticipated in the protocol text; the frozen criterion passed through the coordinate route.

This authorizes **M5B3C**: a frozen resolver protocol that opens only the KC→MBON synapse rows and their compartment labels, pinned by full-file SHA256, to derive compartment-specific plastic sub-edges for multi-compartment MBONs (MBON11, MBON12, MBON21, MBON29, MBON33 carry signed valence).

MNQ reward, PnL, strategy, trading and prop-firm evaluation remain CLOSED.
