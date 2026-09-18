# Prototype 1 Homelander — v005 Dual-Eye Free-Aim Render Gate
Date: 2026-09-18
Status: DORMANT / STAGED / RUNTIME NOT PROMOTED

## Purpose
This stage does NOT change the active game.
It prepares two explicit gates after v003 F9 and v004 F10 have passed in real runtime logs:

- F11: READ-ONLY EYEPOINT verification.
- F12: ONE-SHOT RENDER-ONLY dual-eye ai_Laser call.

Damage, DOT, world effects, velocity and physics mutation are absent.

## Source eye contract
The active prototypeenginef.dll contains exactly one registration-name occurrence each for:
- go_GetJointPosition
- ai_Laser
- EYEPOINT

F11 accepts only the concrete EYEPOINT semantic. It does not silently fall back to "head".
It stores the verified joint name/position only after go_GetJointPosition(player, "EYEPOINT") succeeds.

## Critical target coordinate-space rule
F10 computes HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET in the TARGET OBJECT BASE TRANSFORM.

Therefore F12 MUST call:
    ai_Laser(player, "EYEPOINT", sourceOffset,
             target, "", HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET)

The target joint string MUST remain empty.
Using "head" or "EYEPOINT" as targetJoint would reinterpret the F10 object-local offset in a joint-local coordinate space and is not equivalent.

## F12 prerequisites
F12 fails closed unless:
- HOMELANDER_PLAYER is valid.
- F11 verified EYEPOINT for that same player.
- current EYEPOINT lookup still succeeds.
- HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_GOH is valid and not player.
- HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET exists.
- HOMELANDER_FREEAIM_TARGET_LOCAL_OFFSET_ERROR is numeric.
- current HOMELANDER_FREEAIM_HIT equals the F10 target GOH.

The eye half-separation defaults to 0.035 and is clamped to <= 0.25.

## Mutation boundary
F12 calls ai_Laser exactly twice, once with local source X=-sep and once with X=+sep.
This is a render-only mutation gate.
No go_ApplyDamage, go_ApplyDamageAndHit, em_AddWorldEffect*, velocity setter, or physics setter occurs in the v007 script.

## Promotion order
Active runtime order remains:
1. v003 BOOT -> F4 -> F9
2. v004 F10 read-only local-offset roundtrip
3. v005 F11 read-only EYEPOINT
4. v005 F12 one-shot dual-eye render only
5. only after visible/logged F12 success may continuous heat vision be designed
6. damage / impacts remain separate later gates
