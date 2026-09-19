# V6-M4A1H PROTOCOL — ABF CHANNEL-SCHEMA DISAMBIGUATION

**STATUS: FROZEN AFTER M4A1 BLOCKED ON ADC AMBIGUITY AND BEFORE ANY CHANNEL CHOICE IS MADE FOR THE AMBIGUOUS FILES.**

## Trigger
The first frozen M4A1 execution returned `BLOCKED_M4A1_SOURCE_OR_PROTOCOL_PARITY` because at least one selected ABF exposed two ADC channels whose physical unit is `mV`. The frozen M4A1 rule required exactly one unambiguous voltage channel and therefore correctly blocked.

No M4A1 scientific classification was produced and no channel was selected from voltage traces.

## Scope
M4A1H is a **header/schema-only repair gate**. It may inspect only ABF metadata from the exact 30 already-frozen M4A1 members:
- ADC names and units;
- ADC channel numbers/indexes;
- DAC names and units;
- protocol/path name;
- ABF version;
- sweep count;
- sampling rate metadata if exposed without selecting/reading a sweep.

M4A1H may not read or summarize:
- voltage sample arrays;
- command waveform arrays;
- current-step amplitudes;
- AHP amplitudes;
- bumps;
- any response-derived quality metric.

## Frozen acceptance semantics
M4A1H may authorize a deterministic channel rule only if header metadata itself provides a source-semantic distinction that is consistent across all 30 files.

Permitted channel rule:
1. Normalize each ADC name by Unicode-lowercasing and removing every non-alphanumeric character.
2. The frozen membrane-voltage semantic tokens are exactly: `vm`, `vmem`, `membranevoltage`, `membranepotential`, `vmon`, `vmonitor`.
3. A file passes only if exactly one ADC name equals one of those tokens and its unit is voltage-convertible (`V`, `mV`, or `uV`).
4. The same normalized semantic name must identify the membrane channel across all 30 files. An exact index may then be fixed only if that same semantic ADC name occupies the same index in every selected file.
5. Unit alone is insufficient when multiple ADCs share a voltage unit.

No substring matching, trace inspection, amplitude comparison, variance comparison, or response-shape inference is permitted.

If channel names are generic/duplicated/empty such that membrane voltage cannot be identified independently of trace behavior, return:
`BLOCKED_M4A1H_ADC_IDENTITY_NOT_SELF_DESCRIBING`.

If a unique, consistent source-semantic membrane-voltage channel is identifiable:
`PASS_M4A1H_DETERMINISTIC_ADC_IDENTITY`.

No response values may be used to decide between channels.

## Consequence
PASS authorizes a narrow M4A1 protocol addendum that fixes the exact channel-name rule and reruns the original frozen M4A1 metrics unchanged.

BLOCK closes this Chen raw route unless an independent source document describing the acquisition channel mapping is found. It does not authorize trace-based channel picking.

## Firewalls
M4V0 numeric holdout remains blind.
Amin remains blind.
M3F4 residuals may not guide this repair.
MNQ/reward/PnL/strategy/prop-firm evaluation remains CLOSED.
