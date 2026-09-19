# V6-M4A0 PROTOCOL — ACTIVE-APL ELECTROPHYSIOLOGY SOURCE/SCHEMA GATE

**STATUS: FROZEN BEFORE OPENING OR DECOMPRESSING ANY MEMBER OF THE CHEN 2026 ZENODO ELECTROPHYSIOLOGY ARCHIVE.**

## Why this continuation is allowed
M3F4 formally closed the final Amin A1/B1 source-support refinement under the purely passive M3D operator. The failed passive result may not be repaired by changing source width, q, passive parameters, or support semantics.

A different operator family is scientifically admissible only if motivated by biology independent of the M3F4 residual pattern.

Chen et al. 2026 (Current Biology, DOI 10.1016/j.cub.2026.02.028) was already part of the project before M3F4 through the D4-D9/M3E electrophysiology work. The paper reports that adult APL neurons are non-spiking and graded but also exhibit SK-channel-mediated afterhyperpolarization, and occasional spikelet-like nonlinearities under strong current injection. This predates and is independent of the M3F4 horizontal-support failure pattern.

Therefore the only authorized question at M4A0 is whether the exact public raw electrophysiology source is sufficiently auditable to support a later, prospectively specified active-membrane identifiability test.

This protocol does **not** assume that SK/AHP dynamics explain or repair M3F4. In particular, a post-pulse AHP alone may be irrelevant to the steady/local transfer proposition that failed in M3F4.

## Source status and non-holdout declaration
Chen 2026 is **not a pristine validation source** for V6:
- its published physiology has already been inspected in this project;
- the historical project used Chen electrophysiology for passive/compatibility work;
- input-resistance values are already burned for validation.

Chen may therefore be used only as architecture/calibration/source evidence under explicit preregistration. It cannot serve as the new independent validation source required after the M3F4 passive-architecture failure.

Before any Chen raw trace value is opened for active-model fitting, a separate independent validation source must be reserved prospectively.

## Exact official sources
Paper:
- Chen et al., Current Biology 36(7), 1633-1643.e6 (2026)
- DOI: `10.1016/j.cub.2026.02.028`

Raw-data record:
- Zenodo DOI: `10.5281/zenodo.18644411`
- record/version: v1
- exact electrophysiology archive: `Ephys_sparse coding.zip`
- publisher-displayed size: approximately 2.3 GB
- publisher MD5: `c6d63ac25c504db4fc3ee45578d63169`

No substitute mirror/archive is permitted unless byte identity to the official Zenodo file is proven first.

## M4A0 scope: value-opaque archive qualification only
M4A0 may inspect:
1. Zenodo record metadata;
2. HTTP transport metadata needed to retrieve the exact archive;
3. the ZIP end-of-central-directory / ZIP64 metadata if necessary;
4. ZIP central-directory member metadata only:
   - member path/name;
   - file extension;
   - compressed/uncompressed size;
   - CRC;
   - directory structure.

M4A0 may **not**:
- decompress or open any archive member;
- read trace values, current amplitudes, voltages, timestamps, cell measurements, per-cell tables, or analysis outputs;
- compute electrophysiological parameters;
- fit an active or passive model.

Range requests may be used to read only the bytes required for ZIP directory metadata. If the server does not support a safe value-opaque directory read, the gate is BLOCKED rather than downloading/opening the full archive under this protocol.

## Frozen source/schema acceptance rule
M4A0 returns `PASS_M4A0_CHEN_EPHYS_ARCHIVE_SCHEMA_QUALIFIED` only if all of the following hold:

1. **Provider identity**
   - the source is the exact Zenodo record/file above;
   - provider metadata identifies the expected archive and MD5;
   - transport exposes a stable byte length.

2. **ZIP integrity at metadata level**
   - a valid ZIP/ZIP64 central directory can be parsed without decompressing members;
   - every central-directory entry has a deterministic path and nonnegative size metadata;
   - no path traversal entry is present.

3. **Electrophysiology discoverability**
   - central-directory names/structure contain a deterministic, source-defined electrophysiology organization sufficient to identify a candidate APL current-clamp/raw-recording subset without opening numerical member contents.
   - No fuzzy filename matching selected after seeing values is allowed.

4. **No forbidden data access**
   - zero member payload bytes are decompressed/read;
   - no Amin response value is accessed;
   - no M3F4 violating node/margin is used;
   - no MNQ/reward/PnL/strategy/prop-firm datum is loaded.

If provider identity/ZIP parsing fails:
`BLOCKED_M4A0_CHEN_EPHYS_TRANSPORT_OR_ZIP_SCHEMA`.

If the archive is structurally valid but member metadata cannot deterministically identify the relevant electrophysiology subset:
`BLOCKED_M4A0_CHEN_EPHYS_SCHEMA_NOT_SELF_DESCRIBING`.

## What a PASS authorizes
A PASS authorizes only:
- a separate M4A1 protocol to be frozen from the observed **schema/filenames**, not values;
- prospective reservation of a new independent validation source;
- after both are frozen, narrowly opening the minimum Chen raw electrophysiology subset required by M4A1.

A PASS does **not** authorize:
- an SK conductance parameter;
- a spatial SK distribution;
- a soma-only or uniform-tree SK placement;
- a calcium model;
- any change to Ra/Rm/q;
- any reuse of Amin A1/B1 or A4/B4 as the required new holdout;
- MNQ/market evaluation.

## Required M4A1 scientific question before any active operator is accepted
The later M4A1 protocol must distinguish at least:
- during-stimulus nonlinear/state-dependent membrane behavior;
- post-stimulus AHP only;
- passive leak behavior.

An active production operator can only be considered if the source supports an identifiable effect relevant to the time regime used by the model. A purely post-stimulus AHP finding cannot by itself be claimed to repair a DC spatial-transfer failure.

## Firewall
Amin A1/B1 remains unopened.
Amin A4/B4 remains unopened.
M3F5 remains blocked.
MNQ chronology, reward, PnL, strategy selection and prop-firm evaluation remain CLOSED.
