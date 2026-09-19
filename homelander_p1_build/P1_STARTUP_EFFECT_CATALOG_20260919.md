# Prototype 1 Homelander — startup_effects Exact Effect Catalog Audit
Date: 2026-09-19
Status: STATIC ASSET PROOF / NO RUNTIME SPAWN CLAIM

## Source identity
The already-existing Drive staging copy of the user's `art.rcf` was materialized read-only.
- staged art.rcf size: 496,846,408 bytes
- staged art.rcf SHA256: `38bd7664d5b709d8d9a2fc07e3a68dffbca75a9871e5ae0c2cf1cab0fd7ba94e`
- source RCF entry: `\\art\\startup_effects.p3d.rz`
- RCF entry offset: 480,409,600
- compressed entry size: 3,120,855 bytes
- compressed RZ SHA256: `1388eae833f58c5a03a6263c8f2c6668b0f04171273e59efac27c8b83bf48568`
- RZ header uncompressed-size field: 10,467,955 bytes
- decompressed Pure3D size: 10,467,955 bytes
- decompressed Pure3D SHA256: `7359617402d7f9da2475f69d841e8b341e3b9cf45e9eea88fcd76e559ab37230`

## Pure3D structural proof
The decompressed file parses recursively with the standard 12-byte Pure3D chunk header:
- uint32 chunkType
- uint32 dataSize
- uint32 totalSize

The complete tree parses without a boundary error:
- total chunks: 29,455
- maximum nesting depth: 8
- top-level effect-object chunks of type `0x23000`: 131

The effect names below are therefore not loose text hits. Each is the encoded name of a real top-level `0x23000` effect-object chunk.

## Exact relevant effect objects
| Effect object | Decompressed offset | Chunk total | Intended staged use |
| --- | ---: | ---: | --- |
| `missileImpact001` | `0x78C5AA` | 518 | generic fallback; already selected by F18 |
| `squibMetal001` | `0x78EB2E` | 351 | primary small metal hit candidate |
| `debrisSparks001` | `0x787AE1` | 355 | secondary/larger metal spark candidate |
| `debrisMetal001` | `0x786BA0` | 355 | metal debris candidate, not first impact choice |
| `squibBlood001` | `0x78E2F0` | 351 | primary small organic hit candidate |
| `squibAlexFlesh001` | `0x78E181` | 367 | flesh-specific candidate; do not route generically yet |
| `goreBloodGush001` | `0x78A769` | 355 | stronger organic candidate |
| `goreBloodGush002` | `0x78A8CC` | 355 | stronger organic candidate |
| `goreBloodGush003` | `0x78AA2F` | 355 | stronger organic candidate |
| `goreBloodMistFanOut001` | `0x78AB92` | 379 | secondary organic mist candidate |
| `headLight001` | `0x78AD0D` | 514 | eye/beam polish research |
| `lightGlowRed` | `0x78B759` | 347 | red glow research |
| `flare001` | `0x78A14D` | 331 | glow/flare research |
| `fireGlow001` | `0x789FF6` | 343 | glow research |
| `glow001` | `0x78A61E` | 331 | generic glow research |

## Important negative finding: fire_scorch
`fire_scorch` exists in startup_effects, but it is NOT a top-level `0x23000` effect object.
Observed occurrences are in other chunk classes including `0x11015` and `0x10020`, consistent with decal/resource usage.

Therefore:
- do not pass `fire_scorch` to `em_AddWorldEffect` as an allowlisted effect name
- scorch/decal integration must use a separately proven API/path later

This corrects the earlier broad candidate note that listed `fire_scorch` alongside world effects.

## Conservative target-specific candidate policy
These are static candidate mappings only; no runtime spawnability is claimed.

- HELICOPTER_METAL
  - primary: `squibMetal001`
  - secondary: `debrisSparks001`
  - fallback: `missileImpact001`

- INFECTED_ORGANIC_UNRESOLVED
  - primary: `squibBlood001`
  - secondary: `goreBloodMistFanOut001`
  - fallback: `missileImpact001`

- MILITARY_UNRESOLVED
  - primary/fallback: `missileImpact001`
  - reason: faction alone does not prove human vs vehicle vs structure

- GENERIC
  - primary/fallback: `missileImpact001`

## Runtime boundary
A real effect route is not runtime-proven until the exact effect name has been submitted and visibly observed in-game through an independent one-shot gate.
