# V6-M5D1 — AMENDMENT 2026-09-26 — DEFINITIONAL GAPS FOUND DURING EXTRACTION

This amendment accompanies the frozen protocol `research/v6_m5d1_valence_source_protocol.md` (freeze commit `f29b87c90bfc5c831fa505ee8cbf3b20d8ba55ce`, SHA256 `e1f1bbd0be4bcee86c2be3d20b3796e4deb84c5f0cdfb04699d5403f81de3f90`). The frozen file is not edited.

It is written after reading S1 and S2 and before the valence table is committed. Every provision below either **withholds** a sign or bridges a name under the frozen normalization unchanged. No provision can create or change a signed label beyond what the frozen rules already allow, and no criterion or tolerance changes.

## Gaps and conservative resolutions

1. **Result without a name-bearing sign.** The source reports a result for a cell type, but no statement that names the type also states the sign. Example: a legend titled "Additional drivers that induced weak, but significant, memory" that names `PAM-β1` without a sign. Resolution: `UNRESOLVED`, so no sign is assigned. The frozen vocabulary had no exact label for this case. `UNTESTED` would falsely deny that a result exists, and signing the type would require evidence the rule does not accept.

2. **Line-level contradiction.** The source attributes a sign to a driver line, and also states that another line labeling the same cell type (per the source's own driver table) gave no significant effect. Example: S2 reports that MB011B produced a significant aversive effect "but not" MB210B or MB002B. Resolution: `UNRESOLVED` for every cell type that the conflicting lines share. Group-level results for which S2 states that subsets had weak effects, significant only with the group driver, are treated the same way (V2 cluster via MB052B).

3. **Context quotes.** A record may carry `context_quotes`: verbatim source text that supports an `UNRESOLVED` decision but does not name the cell type, such as a sentence naming only driver lines. The verifier checks that each context quote occurs verbatim in the named source's normalized text. Context quotes do not count toward criterion C's requirement of at least one name-bearing quote.

4. **Names containing whitespace.** A source cell-type name that occurs verbatim but contains spaces, such as `PAM-γ4 < γ1γ2`, is not captured by the frozen scan regex. Such a name may be listed in a record's `source_names` and is bridged with the frozen normalization, which removes whitespace. It is not added to the scan inventory, which stays exactly equal to the frozen scan.

5. **Names from nomenclature or driver listings only.** A bridged name that occurs only in a nomenclature table or a driver listing, with no activation or memory result in the text, gives `UNTESTED` while keeping `source_names`. The frozen protocol already permits this.

## Effect

These provisions can only turn a potential sign into no sign, or record an unsigned bridge. Downstream gates therefore receive fewer signed labels than a looser reading would give, never more.
