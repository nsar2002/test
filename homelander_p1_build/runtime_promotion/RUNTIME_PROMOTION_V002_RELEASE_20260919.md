# Homelander P1 Runtime Promotion Pack v002 — Live Assistant Release
Date: 2026-09-19
Status: VALIDATED / FAIL-CLOSED / ACTIVE GAME ROOT UNCHANGED

## Components
This v002 release combines, without modifying their authoritative logic:
- the validated v001 runtime promotion manager
- all 13 canonical staged build ZIPs: v003, v004, v005, v006, v007, v009-v016
- the validated read-only Live Gate Assistant
- the validated v003 first-live-test launcher

## Promotion-manager identity
Base release:
- file: `Homelander_P1_RuntimePromotionPack_v001_VALIDATED.zip`
- SHA256: `ef252888f167757204e5bcd409c87120011ba8533c1b03c2fbe81497ed8d2637`

The following files are byte-identical to the validated v001 pack:
- `P1_PROMOTION_MANAGER.ps1`
- `promotion_manifest.json`
- all 13 files under `packages/`

## Live Gate Assistant identity
- branch: `homelander-p1-live-gate-assistant-20260919`
- head: `62eb397d60275ad5c0c4095b8cbc5ca140ba1b2f`
- Windows CI run: `35418657837`
- CI result: SUCCESS
- GitHub artifact digest: `sha256:2b7d484c264732e84cedaeddcec9c22d0a956efd369bd6ec4b3e17a7062551a3`

CI passed:
- PowerShell AST parse
- observer SelfTest
- positive v003 evidence fixture
- incomplete v003 fail-closed fixture
- forbidden/fatal evidence hard-block fixture
- non-authoritative trust-boundary audit
- launch/monitor semantics
- first-live-test launcher validation
- validated artifact assembly

## Observer trust boundary
The observer may:
- launch `prototypef.exe`
- validate current stage and loader hashes
- monitor `homelander_p1_runtime.log`
- report exact missing/found evidence
- write non-authoritative candidate snapshots

The observer may NOT:
- press or inject F-keys
- confirm visual evidence
- write `passedStages`
- write authoritative PASS receipts
- install or roll back a stage
- unlock v004 or any later stage

Only `P1_PROMOTION_MANAGER.ps1 -Action Check` may record a live gate PASS.

## First-live-test launcher
`START_V003_LIVE_TEST.cmd` / `START_V003_LIVE_TEST.ps1`:
- permits only v001 -> v003 or already-installed v003
- refuses any later active stage
- refuses stale non-empty runtime logs
- launches the read-only observer
- never records PASS

Required manual in-game action remains:
`F4 -> aim at nearby NPC/vehicle -> F9`

## Combined v002 release
- filename: `Homelander_P1_RuntimePromotionPack_v002_LiveAssistant_VALIDATED.zip`
- size: 9,630,115 bytes
- SHA256: `455d85be240dceb5aa9cf2a1a03461209891c9cebd88c4e5e72b1b4a62f4a111`
- Drive file ID: `1bUtHpCnCm1d17Hxh5O_ocxkgfS_NAXC4`
- Drive folder ID: `183DHfFNKBXgc_bc8ktcYSlikgmsKzR03`
- Drive round-trip download reproduced the same size and SHA256.

## Current boundary
The active Prototype game root was not modified while preparing or validating this release.
The first authorized runtime mutation remains installation of v003 through the promotion manager.
No static CI result authorizes skipping the live gate chain.
