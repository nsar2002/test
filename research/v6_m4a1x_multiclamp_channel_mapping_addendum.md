# V6-M4A1X ADDENDUM — INDEPENDENT MULTICLAMP/pCLAMP CHANNEL MAPPING

**STATUS: FROZEN BEFORE THE M4A1 RESPONSE-METRIC RERUN.**

## Trigger
M4A1H correctly blocked because the ABF header signal names `IN 0` and `I_MTest 1` did not match the prospectively frozen semantic voltage-name tokens, and one acquisition encoded both ADC units as mV.

No voltage-response shape, amplitude, variance, AHP, bump, or group effect is used in this addendum.

## Independent source chain

### Experimental hardware/software
Chen et al. 2026 published methods state that whole-cell recordings were made with:
- MultiClamp 700B amplifier;
- CV-7B headstage;
- Digidata 1550B digitizer;
- pCLAMP 10;
- APL electrophysiology recorded in current-clamp for the relevant intrinsic/AHP protocols.

Source: Chen et al., Current Biology 36(7), DOI `10.1016/j.cub.2026.02.028`.

### Manufacturer mapping
Molecular Devices' official *Setting Up Clampex Software for Data Acquisition* guide states for the MultiClamp sequence:
- the amplifier Primary Output is connected to digitizer Analog IN #0;
- current-clamp membrane potential is measured on that primary output;
- sequencing key `I-Clamp IN 0` uses that same input channel;
- `IN 0` explicitly refers to Analog IN #0.

The official pCLAMP user guide separately documents `I_MTest 0` as the Membrane Test **input current** signal (pA), not the current-clamp membrane-potential signal.

This provides an independent acquisition-semantic mapping that does not use Chen voltage samples.

## Frozen channel rule
For every one of the exact 30 M4A1 ABF files:

1. Normalize ADC names only by trimming surrounding whitespace and case-folding.
2. Require exactly one ADC whose normalized name is exactly `in 0`.
3. Require that `in 0` has a voltage-convertible unit (`V`, `mV`, or `uV`).
4. Use that ADC as the membrane-voltage channel.
5. Never use any ADC whose normalized name starts with `i_mtest` as membrane voltage, irrespective of a malformed/stale unit string.
6. If `in 0` is absent, duplicated, or non-voltage-scaled in any selected file, return `BLOCKED_M4A1X_CHANNEL_MAPPING_PARITY`.
7. No fallback by trace amplitude, variance, shape, correlation, or response direction is permitted.

## Scope
This addendum changes only ADC identity resolution. It does not alter:
- the exact 30-file source subset;
- group labels;
- current-waveform parsing;
- pulse windows;
- AHP/current level selection;
- bootstrap seeds/count;
- equivalence band;
- classification rules;
- bump diagnostic;
- M4V0 holdout;
- any spatial/passive parameter.

## Authorization
If all 30 ABFs satisfy the exact `IN 0` rule, M4A1 may be rerun unchanged except for deterministic voltage-channel selection.

M4V0 numerical holdout remains unopened.
Amin A1/B1/A4/B4 remains unopened.
M3F4 passive architecture remains failed and closed.
MNQ/reward/PnL/strategy/prop-firm evaluation remains CLOSED.
