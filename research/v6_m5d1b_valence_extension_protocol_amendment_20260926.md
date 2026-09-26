# V6-M5D1B — AMENDMENT 2026-09-26 — SCOPE CLARIFICATIONS FOUND WHILE READING S5 AND S6

This amendment accompanies the frozen protocol `research/v6_m5d1b_valence_extension_protocol.md` (freeze commit `d823e04bc67285cbccc027786925b576ad85c757`, SHA256 `6499ce037b98643c8110e59677e569d799ecca2c13e0f0abd246a4b2f5b3fdd3`). The frozen file is not edited.

**Full disclosure:** this amendment was written after reading S5 and S6 and before the extension table was built. Provisions 1 and 2 withhold signs. Provision 3 is a scope clarification that can preserve signs relative to a literal reading. It is disclosed as such, and its effect is reported record by record in the result.

## Observations that triggered the amendment

- **S5** refers to MBONs only by hemibrain type number (for example `MBON21`, `MBON33`), never in the `MBON-<compartments>` form. The inherited bridge matches compartment-style names to MaleCNS instance tokens, so S5 yields **no** bridged MBON name. No provision below changes that. A type-number bridge would add signs, so it needs its own separately frozen protocol.
- **S6** reports memories under intact conditions and also under manipulated conditions: TH-null (dopamine-deficient) mutants, ectopic NOS expression, NOS RNAi, L-NNA feeding and Gycβ100B knockdown. In manipulated backgrounds the memory valence deliberately inverts or disappears; that is the paper's subject, co-transmitter action without dopamine. S6 also uses "positive-valence" and "negative-valence memory" as its terms for appetitive and aversive memory.

## Provisions

1. **Alias-identified contradiction (withholds a sign).** Suppose a pinned source names a cell type through an alias, and a nomenclature source (S3 or S4) explicitly confirms that alias. If the statement says that type cannot induce memory by itself, or gave no significant memory, the new finding for that type is `UNRESOLVED` with `conflict: true`. Both the alias statement and the S3/S4 nomenclature text are recorded verbatim as `alias_quotes` and verified. Applied case: S6 "PPL1-α′2/α′2 (MB-V1) … cannot induce aversive memory by itself"; S3 lists `PPL1-α′2α2 PPL1-05 1 MB058B MB-V1`.

2. **Wording equivalence.** "positive-valence memory" is read as appetitive memory (preference for the paired odor), and "negative-valence memory" as aversive memory. This follows directly from the frozen label definitions.

3. **Genotype scope (clarification).** Teaching valence refers to the physiological sign of a DAN cell type. Only statements about animals with intact dopamine synthesis and no manipulation of the cell type's signaling count as sign or conflict evidence. That is the condition of every S1 statement to which the inherited rules were fitted. Statements about manipulated backgrounds (TH-null, ectopic NOS, NOS RNAi, L-NNA, Gycβ100B or other knockdowns) are recorded as `context_quotes` only; they never create a sign or a conflict.

   Disclosed effect: under a literal reading, manipulated-background statements would mark PPL101, PPL103, PPL106, PAM01 and PAM02 as internally conflicting in S6 purely because of the manipulations. Provision 3 prevents that. It cannot create a sign that intact-animal statements do not support, and the frozen merge rule still lets any S1/S2 conflict override.

## Unchanged

The criteria, tolerances, merge rule, vocabularies and inventory requirements are unchanged. The verifier checks every `alias_quotes` entry verbatim in its named source (the pinned S3/S4 or the evidence source).
