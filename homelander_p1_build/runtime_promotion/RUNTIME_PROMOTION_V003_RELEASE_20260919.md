# Homelander P1 Runtime Promotion Pack v003 — Live Evidence Release
Date: 2026-09-19
Status: VALIDATED / FAIL-CLOSED / ACTIVE GAME ROOT UNCHANGED

## New component
v003 adds a read-only live evidence exporter to the already validated v002 promotion + observer pack.

Validated exporter:
- source branch: homelander-p1-live-gate-assistant-20260919
- validated source head: 550a24938c7ce1811435d27fa78de587541a31cf
- Windows CI run: 35419355934 SUCCESS
- artifact ID: 10576674744
- artifact digest: sha256:cc660916a45fc82ea0daea65db51995d52baee03f7f0f0e77ec2dd4ff956b73c

CI passed:
- PowerShell AST parse
- evidence ZIP round-trip SelfTest
- read-only promotion boundary audit
- evidence-scope audit
- rollback-backup exclusion audit
- CMD launcher audit
- validated artifact assembly

## Exported evidence
After Prototype is closed, P1_EXPORT_LIVE_EVIDENCE.cmd creates one audit ZIP under:
.homelander_promotion\evidence_exports

The audit ZIP can contain:
- homelander_p1_runtime.log
- state.json
- authoritative receipt JSON files
- live-observer session/candidate JSON files
- EVIDENCE_SUMMARY.json
- hashes/metadata for prototypef.exe, prototypeenginef.dll, homelander_p1.asi, binkw32.dll and binkw32Hooked.dll

The exporter does not:
- write or alter passedStages
- invoke promotion-manager Check/Install/Rollback/ResetLog
- launch Prototype
- modify homelander_p1.asi or lua_p1
- copy rollback backups
- create or imply a PASS

## Combined v003 pack identity
- base v002 SHA256: 455d85be240dceb5aa9cf2a1a03461209891c9cebd88c4e5e72b1b4a62f4a111
- filename: Homelander_P1_RuntimePromotionPack_v003_LiveEvidence_VALIDATED.zip
- size: 9,635,965 bytes
- SHA256: 72c750c54f867789f26a7febacc0a35e3aae2dd1aa98c2111cf7f5e6c9381e26
- Drive folder ID: 183DHfFNKBXgc_bc8ktcYSlikgmsKzR03
- Drive file ID: 1Qw_fhCOVHGJrPvo5dzAqUI-BgSS_xPgc
- Drive round-trip download reproduced the exact same size and SHA256

Unchanged from v002:
- all 13 canonical stage ZIPs
- P1_PROMOTION_MANAGER.ps1
- promotion_manifest.json
- P1_LIVE_GATE_ASSISTANT.ps1
- START_V003_LIVE_TEST.ps1 / .cmd

## Current live workflow
1. START_V003_LIVE_TEST.cmd
2. in Prototype: F4 -> aim at nearby NPC/vehicle -> F9
3. observer waits for complete v003/F9 log evidence
4. close Prototype
5. authoritative P1_PROMOTION_MANAGER.ps1 -Action Check -Stage v003
6. P1_EXPORT_LIVE_EVIDENCE.cmd
7. only after a valid v003 PASS receipt may v004 be installed

No active game-root file was changed during cloud-side assembly or validation.
