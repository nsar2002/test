# V6-M5D1 — DAN TEACHING VALENCE AND MBON ACTIVATION VALENCE — LITERATURE SOURCE TABLE

**STATUS: FROZEN BEFORE ANY PINNED SOURCE TEXT WAS READ.** The source files below were acquired and hashed only.

## Freeze record

This protocol is committed alone, before the valence table or any verifier code, on branch `claude/hello-8eabhu` of `nsar2002/test`. There is no canonical private test15 commit, and the public protocol-only commit is the freeze of record. Changes require a separate, dated amendment file.

## Authorization and purpose

V6-M5C PASS (run 36249100776) authorizes freezing "DAN teaching semantics, including any valence assignment from independent sources", still without market data. M5D1 builds a quote-verified valence table covering:
1. the 21 fast-MB DAN types (PAM01–PAM15, PPL101–PPL106);
2. the 37 exact MaleCNS MBON types listed by M5B3B (MBON01–MBON35 with the -like variants, as present in the source annotations).

The table only records what independent primary literature states. It is **not** fitted or chosen from any model, reward, market or PnL outcome, and no such outcome exists yet.

## Pinned sources

All files come from the eLife article XML repository `elifesciences/elife-article-xml` at commit `d146492a0d8efed2fc3bb377ef9b22dde455936b`, path `articles/<file>`. The raw URL uses that commit SHA:
- **S1** `elife-16135-v2.xml`, SHA256 `b599a442b2fd95bd68066a59319f9eb4fc13a697461729fb3270f6f1b311bad2`. Aso & Rubin 2016, eLife 5:e16135, "Dopaminergic neurons write and update memories with cell-type-specific rules". Evidence source for DAN teaching valence.
- **S2** `elife-04580-v1.xml`, SHA256 `f9ad08a542e03d5594640295db0d8d9583adeea6a0c1ed9ab42366ecb20bcfb4`. Aso et al. 2014, eLife 3:e04580, "Mushroom body output neurons encode valence and guide memory-based action selection in Drosophila". Evidence source for MBON activation valence.
- **S3** `elife-04577-v1.xml`, SHA256 `c17e5916866a0f54eb5113880abe8cd1230121581e5c4da6f269b3f4f9bfb4dd`. Aso et al. 2014, eLife 3:e04577. Nomenclature only.
- **S4** `elife-62576-v2.xml`, SHA256 `d26350b4e8dcecfbb88c14e6fb1fc432b4d0dfcdf44483d75241583c1ace54c7`. Li et al. 2020, eLife 9:e62576. Nomenclature only.

S3 and S4 may justify only a name↔compartment correspondence, never a valence label. No other source may supply a valence label. In particular, the PAM = appetitive / PPL1 = aversive cluster approximation is **not** a source, and it is never used to fill a gap.

## Label vocabulary

DAN teaching valence (one label per DAN record):
- `APPETITIVE`: S1 states that pairing an odor with activation of this DAN cell type produced appetitive memory (approach to or preference for the paired odor).
- `AVERSIVE`: S1 states it produced aversive memory (avoidance of the paired odor).
- `NO_SIGNIFICANT_MEMORY`: S1 states the type was tested and produced no significant memory.
- `UNRESOLVED`: S1 statements conflict, or the sign depends on protocol such that no forward-pairing result can be isolated.
- `UNTESTED`: S1 contains no result for the type.

Timing rule: if S1 reports different outcomes for different odor–activation timings, the label uses the outcome for odor presented before or together with DAN activation (forward pairing). This matches the M5C chronology, in which dopamine that follows or coincides with KC activity depresses. If no forward-pairing outcome can be isolated, the label is `UNRESOLVED`.

MBON activation valence (one label per MBON record):
- `ATTRACTIVE`: S2 states that optogenetic activation of this MBON cell type caused attraction.
- `REPULSIVE`: S2 states it caused avoidance or repulsion.
- `NO_SIGNIFICANT_EFFECT`: S2 states the type was tested without a significant effect.
- `UNRESOLVED`: statements conflict.
- `UNTESTED`: S2 contains no result for the type, for example MBON types first described after 2014.

Shared driver lines: if the source attributes an effect to a driver line that labels several cell types, that label is recorded for each of those types with `shared_line: true`. It is `UNRESOLVED` if another statement contradicts it for any included type.

## Frozen nomenclature bridge (source names → MaleCNS types)

Each MaleCNS record is keyed by its type plus the parenthesized instance token from the pinned annotations, with the side suffix removed; for example `MBON03` + `B'2mp` and `PAM07` + `y4<y1y2`. The token is empty if the instance has none (`PPL106`), and such a record can bridge only by the fallback rule.

Name normalization, applied to both sides:
- remove the prefixes `MBON-`, `PAM-`, `PPL1-` and all whitespace;
- map γ→y, α→a, β→B, and any prime or apostrophe character to `'`;
- compare case-insensitively.

Bridge rules, in order:
1. **Primary**: a source cell-type name bridges to a MaleCNS record whose instance token equals the normalized name exactly.
2. **Fallback**: only for a record that no source name matches under rule 1, a source name whose parsed compartment set is non-empty bridges by exact compartment-set equality. This uses the frozen M5B3B sets (γ→y etc., subzone suffixes dropped, `pedc` only when explicit, the DAN modulatory side before `<`, the MBON dendritic side before `>`). The same class and, for DANs, the same cluster (PAM or PPL1) are required. The fallback applies only if exactly one MaleCNS type of that class and cluster has that set, and that type has no primary match.
3. Otherwise there is no bridge. A MaleCNS record with no bridged source name is labeled `UNTESTED`.

Collapsed subzones are therefore never merged, and a newer type is never labeled from an older, differently named type. If a record bridges to several source names with different labels, it is `UNRESOLVED`.

MBON records: 37 types. MBON25-like carries two distinct instance tokens (`y1y2`, `y2`), so it has two records, for 38 MBON records in total. DAN records: 21 types.

## Table format (authored after this freeze)

`research/v6_m5d1_valence_source_table.json` contains:
- `dan_records`: 21 records (type, instance token), each with `label`, `source_names`, `bridge_rule` (`primary`/`fallback`/`none`), `shared_line` and `evidence`;
- `mbon_records`: 38 records with the same fields;
- `inventory`: every distinct cell-type name found in S1 and S2 by the frozen name scan below, each with a `disposition`: `used` (it appears in some record's `source_names`) or `unused` with a free-text reason.

Frozen name scan: `\b(PAM|PPL1|MBON)-[^\s,;:()\[\]]+` over the normalized text, with trailing `.` removed. DAN names come from S1 and MBON names from S2.

A record may keep `source_names` and still be `UNTESTED` only when the source names that cell type without reporting an activation or memory result for it. That case is auditable through the quotes, not scored.

Every evidence item is `{source: S1|S2|S3|S4, quote: <verbatim text>}`.

## Frozen verification criteria

A verifier script, written after this freeze, decides the classification.

A. **Source parity**: the four files are downloaded from the pinned commit URLs, and each SHA256 matches.

B. **Completeness**: exactly the 21 DAN records and 38 MBON records defined above exist, each with exactly one label from its vocabulary.

C. **Evidence integrity**: every label other than `UNTESTED` has at least one evidence quote, of at most 600 characters, that occurs verbatim in the named source's normalized text.

   The normalized text is built as follows: tags of the block elements p, title, caption, td, th, label, list-item and article-title are replaced by one space; all other XML tags are removed; XML/HTML entities are unescaped; Unicode is NFKC-normalized; whitespace runs are collapsed to one space. Quotes are normalized the same way before matching.
   - DAN records' quotes must come from S1, and MBON records' quotes from S2.
   - Each quote must contain at least one of the record's `source_names` verbatim, after the same normalization.
   - A record with no bridged source name must be `UNTESTED`.

D. **Bridge integrity**: the verifier recomputes the bridge from the pinned annotation instance tokens and the frozen M5B3B compartment sets. Every record's `source_names` and `bridge_rule` must agree with the frozen rules above, including the uniqueness condition of the fallback.

F. **Inventory completeness**: the verifier re-runs the frozen name scan. Every name it finds (DAN names in S1, MBON names in S2) is in `inventory`, and no inventory name is missing from the scan. Every inventory name that bridges to a MaleCNS record under the frozen rules has disposition `used` and appears in that record's `source_names`.

E. **No outcome contamination**: the table and verifier load no market, reward, PnL, model-output, Amin or M4V0 data. The verifier's input manifest is limited to the four pinned sources, this protocol, the table, the M5B3B frozen result JSON and the pinned MaleCNS annotation file (SHA256 `2177e246113e4cfbf1e7772ec37c6da1955ff22e8063d0b1f833101f99a9a3b2`), which supplies the instance tokens.

Diagnostics only (no criterion):
- label counts;
- for each of the 12 eligible compartments, whether at least one gate DAN type carries a signed teaching label and whether its single-compartment MBONs carry signed activation labels;
- agreement with the cluster approximation (reported, never enforced).

## Formal classification

- `PASS_M5D1_VALENCE_SOURCE_TABLE_FROZEN`: A–F all true.
- `FAIL_M5D1_VALENCE_SOURCE_INTEGRITY`: A true, and any of B–F false.
- `BLOCKED_M5D1_SOURCE_PARITY`: A false.

Coverage is reported, not required. A PASS with low coverage is still a valid, honest table.

## Consequence of PASS

Later V6 gates may take teaching signs and readout signs only from this table:
- `APPETITIVE`/`AVERSIVE` DAN labels become teaching signs;
- `ATTRACTIVE`/`REPULSIVE` MBON labels become readout signs;
- every other label carries no sign. A DAN type without a signed label receives no reward-driven activity, and an MBON type without a signed label contributes no signed action evidence, unless a later protocol adds independent evidence.

PASS does not define the reward→DAN mapping, the MBON→action mapping or θ. It does not open MNQ, reward, PnL, strategy, trading or prop-firm evaluation.

## Firewalls

- MNQ/reward/PnL/trading CLOSED.
- θ not selected.
- Synapse coordinates unopened.
- Amin and M4V0 numeric values unopened.
