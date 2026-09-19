# Prototype 1 Homelander — Flight V2 Reproducibility Audit
Date: 2026-09-19
Status: STATIC/CI PASS, DORMANT, NOT LIVE-PROVEN

## Canonical source lineage
- base canonical v016: `030e936dcef1196d51d9adb9c79ea71080a82b23`
- Flight V2 run-1 head: `028190d19c98c2f9060ebfdd95130f832e1e2411`
- Flight V2 run-2 trigger head: `ef3276150e825b8eae0efbf5a3a00de1fc943837`
- run 1: `35419676652` SUCCESS
- run 2: `35419720415` SUCCESS

Both runs passed:
- branch-scope lock against canonical v016
- Lua 5.1 parse
- Win32/i386 ASI build
- no dynamic MinGW runtime DLL dependency
- native Flight V2 wiring checks
- simulation-delta acceleration/braking checks
- single active velocity-submit-site audit
- forbidden mutation/render primitive audit
- read-only ground telemetry audit
- explicit no-guessed-landing-threshold boundary
- internal package SHA256 verification

## Canonical run-2 identities
- `homelander_p1_flight_v2_STAGED.asi`
  - size: 2,226,220 bytes
  - raw SHA256: `b0614eb7c8d4926397c3d9b3a86bf3cf87fc1f0bc730f01293a8513ad35b3b35`
- `homelander_p1_flight_v2_SOURCE.cpp`
  - SHA256: `4d7888c15205c819431935b8e84993d5d07b4b33931f531c0c8116601e4a8c00`
- `flight_controller_v2_STAGED.lua`
  - size: 14,640 bytes
  - SHA256: `dc5a9a98f5450893c0689f2dd2b71cbf0aa284f86227935ce3656b5d1b8e2edc`
- `flight_ground_probe_v018_STAGED.lua`
  - size: 4,115 bytes
  - SHA256: `e1a5db65d6de40172c7ea60fcd81ddf6c4e01b8ffedfd520d8d6a9bb714a8ced`
- `P1_FLIGHT_V2_STAGING_20260919.md`
  - SHA256: `5658fd64fa5f13a337d46bf8868413ee2784baaa880f639e9b209cb04f2197cd`

## Reproducibility
Run-1 and run-2 ASIs are both exactly 2,226,220 bytes.

Raw differing byte positions:
- `0x88`
- `0xD8`
- `0xD9`
- `0x116404`

All differences are contained entirely within the three expected PE metadata fields:
- COFF TimeDateStamp
- PE CheckSum
- IMAGE_EXPORT_DIRECTORY TimeDateStamp

After zeroing only those three fields:
- remaining byte differences: 0
- normalized SHA256: `64f5672eda6115f14890d52cd56ff7748ab81a256f91d52dc980d4b3f2612558`

Therefore the Flight V2 code/data output is reproducible; raw hash drift is metadata-only.

## Runtime boundary
This audit does NOT prove flight behavior in Prototype.

Before Flight V2 can replace the older controller, live evidence must demonstrate:
1. sane F4 downward ground telemetry while standing and airborne
2. F5 same-velocity setter echo PASS
3. F6 hover without runaway drift
4. smooth W/A/S/D acceleration
5. release-to-air-brake behavior
6. Shift boost
7. controlled Space/Ctrl vertical movement
8. F7 pre-flight velocity restore
9. focus-loss force-disable
10. no mission/streaming/collision regression

Automatic landing/takeoff assist remains intentionally absent until live ground-distance samples establish safe thresholds.
