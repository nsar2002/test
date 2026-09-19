# Homelander P1 Live Gate Assistant
Date: 2026-09-19
Status: READ-ONLY GAMEPLAY OBSERVER / DOES NOT AUTHORIZE PROMOTION

## Purpose
This companion tool reduces friction during the mandatory live gate chain without weakening the fail-closed promotion policy.

It can:
- validate the currently installed managed ASI and loader chain
- launch prototypef.exe
- display the exact key/evidence sequence for the active stage
- monitor homelander_p1_runtime.log live
- report each required regex as it appears
- fail immediately on forbidden/fatal evidence
- write a non-authoritative candidate JSON snapshot for audit

It cannot:
- press F-keys or inject input
- confirm visual evidence
- write to passedStages
- write authoritative gate receipts
- install or roll back ASIs
- change lua_p1
- call P1_PROMOTION_MANAGER.ps1 -Action Check automatically
- unlock a later stage

## Main usage
After the promotion manager has installed the current stage and archived/reset the old runtime log:

powershell -ExecutionPolicy Bypass -File .\P1_LIVE_GATE_ASSISTANT.ps1 -Action Observe

The assistant launches Prototype and starts monitoring immediately.

When log evidence is complete:
1. it writes an observer candidate under .homelander_promotion\live_observer\candidates
2. it explicitly states that no PASS was recorded
3. close Prototype
4. use the promotion manager Check action
5. for visual gates add -ConfirmVisible only when the required effect was genuinely visible

## Stale-evidence protection
Observe/Launch refuses to start if a non-empty runtime log already exists.
For a retry, use the promotion manager ResetLog action first. That archives the old log and clears the current/later pass state.

## Actions
- Status: current stage, state and current evidence snapshot
- Launch: launch Prototype but do not monitor
- Monitor: monitor an already launched observer session
- Observe: launch + monitor
- Snapshot: one-shot evidence snapshot + non-authoritative candidate JSON
- EvaluateLog: offline regex evaluation of a supplied log
- SelfTest: manifest/order/regex validation without touching Prototype

## Trust boundary
Only P1_PROMOTION_MANAGER.ps1 may create a live PASS receipt and unlock the next build.
The observer's candidate JSON always includes:
- authoritative=false
- visualConfirmed=false

The live gate assistant therefore makes testing easier without changing the engineering evidence standard.
