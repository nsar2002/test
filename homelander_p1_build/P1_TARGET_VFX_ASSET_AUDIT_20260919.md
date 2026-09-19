# Prototype 1 Homelander — Target VFX Asset Audit
Date: 2026-09-19
Status: STATIC ASSET PROOF / NO RUNTIME SPAWN CLAIM

## Source identity
Analysis source is the user's unchanged Prototype 1 `art.rcf`:
- source Drive file ID: 1PjLfd4jfdGcE_3sjOhMRHM14MEWpsz4_
- size: 496,846,408 bytes

A server-side staging copy was materialized only for analysis. The original game file was not modified.

Known archive entry:
- path: `\art\startup_effects.p3d.rz`
- RCF offset: 480,409,600
- compressed entry size: 3,120,855 bytes
- RZ header size: 16 bytes
- RZ entry SHA256: `1388eae833f58c5a03a6263c8f2c6668b0f04171273e59efac27c8b83bf48568`
- decompressed Pure3D size: 10,467,955 bytes
- decompressed SHA256: `7359617402d7f9da2475f69d841e8b341e3b9cf45e9eea88fcd76e559ab37230`

The decompressed root begins with the Pure3D root chunk and recursively parses into 29,455 valid chunks using:
`uint32 chunkId, uint32 dataSize, uint32 totalSize`, where sizes include the 12-byte chunk header.

## Effect-candidate registration evidence
The following identifiers occur as direct data of TOP-LEVEL Pure3D chunk ID `0x23000`.
This is the same top-level registration chunk class used by the already staged generic and metal effect candidates. Each listed organic candidate also owns `0x23001` children including a matching `_ptcsys` child.

| Candidate | 0x23000 offset | dataSize | totalSize | direct name offset | direct children |
| --- | ---: | ---: | ---: | ---: | --- |
| missileImpact001 | 7,914,922 | 45 | 518 | +13 | missileImpact001; missileImpact001_flare_glows; missileImpact001_ptcsys |
| debrisSparks001 | 7,895,777 | 45 | 355 | +13 | debrisSparks001; debrisSparks001_ptcsys |
| squibBlood001 | 7,922,416 | 45 | 351 | +13 | squibBlood001; squibBlood001_ptcsys |
| goreBloodGush001 | 7,907,177 | 45 | 355 | +13 | goreBloodGush001; goreBloodGush001_ptcsys |
| goreBloodGush002 | 7,907,532 | 45 | 355 | +13 | goreBloodGush002; goreBloodGush002_ptcsys |
| goreBloodGush003 | 7,907,887 | 45 | 355 | +13 | goreBloodGush003; goreBloodGush003_ptcsys |
| goreBloodMistFanOut001 | 7,908,242 | 53 | 379 | +13 | goreBloodMistFanOut001; goreBloodMistFanOut001_ptcsys |

Additional top-level `0x23000` blood/toxin candidates confirmed:
- `bloodToxCloud001`
- `bloodToxSpray001`

## Engineering interpretation
This upgrades the previous evidence from:
"goreBlood-family resource strings exist"
to:
"exact organic identifiers exist as the same top-level 0x23000 registration-chunk class as missileImpact001/debrisSparks001 and own matching particle-system children."

This is STATIC asset evidence only.

It does NOT prove that:
- `em_AddWorldEffect("squibBlood001", ...)` will visibly spawn in this build,
- the effect is appropriate at every scale or surface,
- the object is preloaded in every gameplay state,
- the effect is safe for repeated per-tick use.

Each new identifier still needs an independent one-shot visible in-game runtime gate before it can be called runtime-proven.

## Candidate choice for heat-vision contact
For the first organic contact candidate, use:
- primary: `squibBlood001`
- alternate: `goreBloodMistFanOut001`
- high-intensity alternate: `goreBloodGush001`

Reason for primary selection:
- "squib" semantically indicates a compact impact-like blood effect and is a closer first probe for a beam contact point than a gush or fan-out mist.
- it is structurally the same top-level 0x23000 registration class as the existing generic and metal candidates.
- this is a staging choice, not a claim that the visual result is already known.

Do not promote `goreBloodGush002/003`, bloodTox effects, decals, or other resources automatically. Their exact intended visual semantics remain unverified at runtime.
