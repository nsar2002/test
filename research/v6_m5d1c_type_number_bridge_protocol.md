# V6-M5D1C — HEMIBRAIN TYPE-NUMBER BRIDGE FOR MBON ACTIVATION VALENCE (S5)

**STATUS: FROZEN BEFORE ANY S5 STATEMENT WAS READ.** From S5, only the list of `MBON…` name tokens and their counts has been seen. From S4 (nomenclature only), only the naming pattern `MBONnn (<compartments>)` has been seen.

## Freeze record

This protocol is committed alone, before the table or verifier, on branch `claude/hello-8eabhu` of `nsar2002/test`. Changes require a separate, dated amendment file.

## Authorization and purpose

V6-M5D1B PASS (run 36252688728; result JSON SHA256 `4ab95b21738fbeb61dbcebe4e647644c02b9d281c01d29ec4f78bb4a3cd38bad`) found that S5 names MBONs only by hemibrain type number. The frozen compartment-name bridge therefore admitted none of S5. M5D1B named a type-number bridge as the next direction.

M5D1C adds that bridge for S5 only, with an automated nomenclature cross-check, and merges the resulting MBON findings into the M5D1B merged table under the unchanged frozen merge rule. DAN records are carried over from M5D1B unchanged.

## Pinned inputs

- S5 `elife-90523-v1.xml`, SHA256 `876ef708f2269ae5c7ea9743d65e4fcffb5e8efb0d69936f7715fe468e5b1f31`: MBON activation-valence evidence.
- S4 `elife-62576-v2.xml`, SHA256 `d26350b4e8dcecfbb88c14e6fb1fc432b4d0dfcdf44483d75241583c1ace54c7`: nomenclature cross-check only.
- Both come from `elifesciences/elife-article-xml` @ `d146492a0d8efed2fc3bb377ef9b22dde455936b`.
- M5D1B anchors:
  - table `research/v6_m5d1b_valence_extension_table.json`, SHA256 `4fb51f577e2136604ee15e5daf0b8d76888c3d601336e4742144c8a76e8dc5ff`;
  - result `research/results/v6_m5d1b_valence_extension_result.json`, SHA256 `4ab95b21738fbeb61dbcebe4e647644c02b9d281c01d29ec4f78bb4a3cd38bad`;
  - verifier `fly_mnq/v6_m5d1b_valence_extension_verifier.py`, SHA256 `e794fbcf1f14951994d00f2d33a279bc226e4172b036e0a8df11ab14f972dd13`.
- M5D1 verifier `fly_mnq/v6_m5d1_valence_source_verifier.py`, SHA256 `e220fc4e16affa742c96b7b3857b93e6f98004f4b42bddbbb0213c3167e87a3a`. Its normalization functions are reused unchanged.
- MaleCNS annotations SHA256 `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2`.

## Frozen type-number scan and bridge

1. **Scan**: the regex `\bMBON\d{2}(?:-like)?\b` over the normalized S5 text. Every distinct match enters `inventory_s5_numbers`.
2. **Type equality**: a scanned name `N` is a candidate for the MaleCNS MBON records whose type string equals `N` exactly (case-sensitive).
3. **Nomenclature cross-check**: a candidate record (type `N`, instance token `k`) is bridged only if the normalized S4 or S5 text contains a match of `N` immediately followed by `\s*\(([^()]{1,40})\)`, where the captured string, normalized by the frozen M5D1 name normalization (γ→y, α→a, β→B, primes → `'`, whitespace removed, casefold), equals `k` casefolded. Each record of a multi-token type must be confirmed separately.
4. A record whose candidate fails the cross-check is not bridged: its S5 finding is `UNTESTED` with no names. Records with no candidate are also `UNTESTED`.

## Evidence rules (inherited)

The MBON label vocabulary and every rule of the frozen M5D1 protocol and its amendment apply to S5, together with M5D1B amendment provisions 1–3. The quote must contain the type-number name `N` verbatim.

`ATTRACTIVE` or `REPULSIVE` require a name-bearing S5 statement that optogenetic activation of that MBON type (or of a driver line that labels it) caused attraction or avoidance, in intact animals. Group or line-level conflicts give `UNRESOLVED` with `conflict: true`.

## Merge (inherited, unchanged)

Each MBON record's merged label is `merge(old, new)`:
- old is the M5D1B merged label. It counts as a conflict when it is `UNRESOLVED` and the underlying M5D1 note cites amendment provision 2;
- new is the S5 type-number finding.

The merge function is imported from the pinned M5D1B verifier. DAN merged labels are copied unchanged from M5D1B.

## Frozen verification criteria

A. **Source parity**: all pinned hashes above.

B. **Completeness**: exactly the 21 DAN records (copied unchanged) and 38 MBON records; each `m5d1b_label` equals the pinned M5D1B merged label; all labels come from the vocabularies.

C. **Evidence integrity**: S5 quotes are verbatim and contain the type-number name; context and alias quotes are verbatim; `conflict: true` requires `UNRESOLVED`; a record with no bridged name must be `UNTESTED`.

D. **Bridge integrity**: the verifier recomputes the type-equality and cross-check bridge exactly.

E. **No outcome contamination.**

F. **Inventory completeness**: `inventory_s5_numbers` equals the frozen scan. Every name that bridges is `used`.

G. **Merge correctness**: every merged label equals `merge(old, new)`.

Diagnostics only: merged counts; per-compartment coverage (whether each compartment has both a signed teaching DAN and a signed plastic MBON); agreement with the valence-balance model (reported, never enforced).

## Formal classification

- `PASS_M5D1C_TYPE_NUMBER_BRIDGE_FROZEN`: A–G all true.
- `FAIL_M5D1C_TYPE_NUMBER_BRIDGE_INTEGRITY`: A true, and any of B–G false.
- `BLOCKED_M5D1C_SOURCE_PARITY`: A false.

## Consequence of PASS

The M5D1C merged labels supersede the M5D1B labels as the only admissible teaching and readout signs for later V6 gates. Nothing here opens MNQ, reward, PnL, strategy, trading or prop-firm evaluation, or selects θ.

## Firewalls

- MNQ/reward/PnL/trading CLOSED.
- θ not selected.
- Synapse coordinates unopened.
- Amin and M4V0 numeric values unopened.
- The PAM/PPL1 cluster approximation is not a source.
