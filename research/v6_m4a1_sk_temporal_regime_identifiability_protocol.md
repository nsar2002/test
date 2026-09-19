# V6-M4A1 PROTOCOL — CAUSAL SK TEMPORAL-REGIME IDENTIFIABILITY IN APL

**STATUS: FROZEN BEFORE OPENING OR DECOMPRESSING ANY CHEN 2026 RAW ABF MEMBER PAYLOAD.**

## Scientific question
M3F4 failed a frozen DC passive spatial-transfer proposition. Chen 2026 independently motivates active membrane biology, but an afterhyperpolarization that occurs only after stimulus offset cannot repair a DC spatial-transfer failure.

M4A1 therefore asks one narrow causal question:

**Does APL-specific SK knockdown produce an identifiable effect during the depolarizing stimulus itself, or is the identifiable SK effect confined to the post-stimulus AHP regime?**

M4A1 is a temporal-regime/identifiability gate. It is not a spatial model fit and does not attempt to reproduce Amin.

## Prerequisites
- M4A0 = `PASS_M4A0_CHEN_EPHYS_ARCHIVE_SCHEMA_QUALIFIED`.
- M4V0 independent dSK mechanism source reservation is frozen.
- Amin A1/B1/A4/B4 remains unopened.
- M3F4 residuals may not affect any analysis choice.

## Exact Chen source
Zenodo record `18644411`, exact archive `Ephys_sparse coding.zip`, provider MD5 `c6d63ac25c504db4fc3ee45578d63169`, provider size `2287477173` bytes.

The archive must retain exact M4A0 central-directory identity.

## Frozen raw subset
Use only source-defined collection:
`Ephys_sparse coding/APL_SD_APL_SKRNAi_Fig4H-J/raw/`

Exact groups:
- control: `APL_RNAi_ctrl_kk`
- perturbation: `APL_SK_RNAi_kk`

Use all and only:
- `*_IC_fp_*.abf`: M4A0 schema count 11 control, 8 SK-RNAi;
- `*_IC_AHP_2nA_*.abf` or case-only spelling equivalent `*_IC_AHP_2na_*.abf`: 6 control, 5 SK-RNAi.

Do not use:
- `I0_breakin`;
- NS/SD/RS collection;
- NS8593 pharmacology files;
- imaging files/tables;
- any manually selected or excluded cell based on trace outcome.

If the exact frozen counts are not reproduced from central-directory metadata, BLOCK.

## File extraction
Retrieve only the compressed byte ranges needed for the selected ABF members using ZIP local-header offsets and central-directory sizes already qualified by M4A0. Verify CRC32 after decompression for every selected member.

Do not download/decompress unrelated archive members.

## ABF decoding and unit gate
Use a fixed, version-pinned ABF reader. For every selected file report:
- ABF version;
- channel count;
- sweep count;
- sampling rate;
- recorded voltage unit;
- command current unit;
- command waveform extrema.

Required:
- one unambiguous membrane-voltage recording channel;
- one unambiguous injected-current command waveform;
- compatible physical units convertible to mV and pA.

If channel/command identity or unit conversion is ambiguous, BLOCK rather than infer.

## Published-protocol parity gate
Chen methods state that APL intrinsic recordings use 500-ms current steps and that high-discharge bump/AHP amplitudes are measured from depolarizing current injection during charging and after deactivation. The raw command waveform, not the filename, is authoritative for the actual injected current.

For the AHP subset:
- both groups must use the same command protocol within acquisition precision;
- if the raw pulse amplitude materially differs between groups or the source file label and raw command cannot be reconciled, BLOCK the causal comparison.

No rescaling of current between groups.

## Per-file definitions
All windows are derived from the command waveform, not hand-picked from voltage traces.

For each depolarizing pulse:
1. **Baseline voltage**: median voltage over the final 100 ms immediately before pulse onset, provided that interval is command-stable.
2. **Charging / during-stimulus amplitude**: maximum 20-ms rolling-median voltage during the pulse minus baseline.
3. **Late-pulse amplitude**: median voltage over the final 100 ms before pulse offset minus baseline.
4. **Post-stimulus AHP amplitude**: baseline minus the minimum 20-ms rolling-median voltage after pulse offset and before the next command transition; cap the search at 2.0 s if the inter-command interval is longer.
5. **AHP 70→30 decay time**: time for the post-stimulus deflection to decay from 70% to 30% of its peak AHP amplitude, only when both crossings are uniquely identifiable.

The 20-ms rolling median suppresses single-sample acquisition noise without fitting a membrane model.

For `IC_fp`, apply the same baseline, charging and late-pulse definitions to every positive 500-ms command step. The raw command waveform determines the actual set of current levels.

## Cell/file aggregation
Each ABF file is one experimental unit unless file metadata proves multiple independent cells, in which case BLOCK rather than split post hoc.

For each file:
- AHP protocol: aggregate repeated identical depolarizing pulses separately by exact command-current level; the **largest positive command-current level common to every AHP file in both groups** is the frozen primary AHP level. This level is selected from the command waveform only, never from a voltage response. Lower common AHP levels, if present, remain secondary diagnostics.
- IC_fp: compute charging and late-pulse amplitudes at each positive current level; preserve the complete current-response curve.

No sweep/cell may be dropped because of bump size, apparent noise, sign, or group effect.

## Primary causal contrasts
Group labels are fixed by source path and never inferred from voltage values.

### A. Post-stimulus SK effect
Primary contrast:
`Delta_AHP = median(control AHP amplitude) - median(SK-RNAi AHP amplitude)`.

Use an exact/permutation two-group test over file-level AHP amplitudes and a deterministic 100,000-resample bootstrap of the median difference, PCG64 seed `2026091901`, percentile 95% interval.

### B. During-stimulus SK effect
At the exact common command-current levels present in every AHP file, compute separately:
- charging amplitude;
- late-pulse amplitude.

For each observable and current level:
`Delta_during = median(control) - median(SK-RNAi)`.

Use the same deterministic bootstrap design with seeds `2026091902` for charging and `2026091903` for late-pulse effects.

For IC_fp curves, report group median curves and bootstrap median-difference intervals at current levels common to all files in both groups. These are corroborative and may not override the AHP-protocol primary comparison.

## Measurement-derived practical-equivalence band
M4A1 must not declare 'no during effect' from a nonsignificant p-value alone.

For each file, estimate baseline voltage noise as:
`sigma_baseline = 1.4826 * MAD(V - median(V))`
over the frozen 100-ms pre-pulse window.

For each group/current/observable, define the practical-equivalence half-width as:
`E = 2 * median(sigma_baseline across all AHP files)`.

A between-group during-stimulus effect is practically equivalent to zero only if its 95% bootstrap interval lies entirely inside `[-E, +E]`.

This threshold is measurement-noise-derived, not chosen from the observed group difference.

## Frozen classifications
### `PASS_M4A1_SK_POST_ONLY_IDENTIFIED`
Requires:
1. `Delta_AHP > 0` and its 95% bootstrap lower bound > 0;
2. both primary during-stimulus observables at every exact common AHP current level have 95% intervals entirely within their measurement-derived equivalence bands;
3. source/unit/protocol parity gates pass.

Consequence: SK is causally identifiable in the post-stimulus AHP regime but not as a detectable steady/during-pulse conductance effect at the sensitivity of these recordings. This **does not authorize SK to repair M3F4 DC spatial transfer**.

### `PASS_M4A1_SK_DURING_STIMULUS_EFFECT_IDENTIFIED`
Requires:
1. source/unit/protocol parity gates pass;
2. at least one primary during-stimulus observable has a 95% interval wholly outside its measurement-derived equivalence band at a common current level;
3. the direction is reproduced by the IC_fp corroborative curve at an overlapping current level if such overlap exists.

Consequence: a separately frozen active-operator identification phase may be considered. It still may not tune spatial SK distribution, Ra/Rm/q, or Amin.

### `NO_IDENTIFIABLE_M4A1_SK_TEMPORAL_EFFECT`
If neither post-only nor during-stimulus criteria are met and the source is otherwise valid.

### `BLOCKED_M4A1_SOURCE_OR_PROTOCOL_PARITY`
For source-count, CRC, ABF channel/unit, or current-protocol mismatch.

## Strong-current bump diagnostic
The paper reports occasional spikelet-like bumps under strong depolarization. M4A1 may report a source-defined diagnostic:
- count files/sweeps in which a within-pulse local maximum exceeds the surrounding 20-ms rolling-median trajectory by more than `5 * sigma_baseline`.

This diagnostic may not change the SK classification because the bump is not established as SK-mediated. It may only motivate a future independently sourced voltage-gated-channel investigation.

## Prohibited
- fitting any active conductance;
- fitting calcium dynamics;
- choosing a spatial SK distribution;
- selecting Ra/Rm/q;
- changing M3F4 support geometry;
- using M4V0 numeric values;
- opening Amin A1/B1/A4/B4;
- opening MNQ/reward/PnL/strategy/prop-firm output.

## Firewall
M4A1 ends at electrophysiological temporal-regime identifiability. Any active spatial operator requires a new frozen protocol after M4A1.
