Homelander Prototype 1 — v003 FreeAimGate transfer
Date: 2026-09-18

WHAT THIS PACKAGE DOES
- Promotes the currently confirmed v001 Homelander ASI to v003.
- Keeps the already-installed verified Ultimate ASI Loader unchanged.
- Keeps the five canonical v001 Lua files, verifies their hashes, and adds freeaim_probe_v004_STAGED.lua.
- F9 is READ-ONLY: camera frame + line-of-sight + hitpoint/normal + hit-GOH diagnostics only.
- No heat-vision damage, world VFX, health mutation, or flight-physics mutation is added to F9.

HARD GATES
- Active source ASI must be v001 SHA256 577BE0AD57823B8CF562BEE014D2656819FF5C4159EF74B3C195E842D747B104
- Payload v003 ASI must be SHA256 1845AFF900E77F7C98E1EF0B37A2EA83C1C293AD74D01DC8FB136A198C9027C2
- Active loader must be SHA256 BC48BAB2CF07EAF616E23BA9EEF1922EA5E8590F722B6657A8F2ED986FE6F20E
- Preserved original binkw32Hooked.dll must be SHA256 DBA257F26517D57ECF3C62ACA7CCCFABBAD868DDF97160F71C9AB81D37A8627
- Every baseline Lua hash must match before installation.
- Prototype must be closed.
- Backup must verify before v003 is written.

HOW TO USE
1. Keep this extracted package intact.
2. Right-click PowerShell / Terminal in this package folder and run:
   powershell -ExecutionPolicy Bypass -File .\INSTALL_V003_FREEAIM_GATE.ps1
   The script auto-detects the sibling Prototype folder when run from the synced Homelander workspace.
3. Launch Prototype.
4. First boot: do NOT test damage/VFX. Reach free roam and ensure the game is stable.
5. Press F4 once to establish the verified player/camera baseline.
6. Aim directly at a nearby wall/vehicle/NPC and press F9 once.
7. Exit Prototype and run:
   powershell -ExecutionPolicy Bypass -File .\CHECK_V003_GATE.ps1
8. If boot crashes or the checker reports fatal/resolution errors, run:
   powershell -ExecutionPolicy Bypass -File .\ROLLBACK_V003_TO_V001.ps1

F9 PASS EVIDENCE NEEDED
- READY build=P1_RuntimeProbe_003_FREEAIM_STAGED_20260918
- F9 dispatch
- CAMERA line with axis scores and non-degenerate winner/margin
- HIT or MISS line
- For a deliberate hit: fraction, hit position, normal, and preferably a valid hitGOH/debug name
- END — READ ONLY

Only after this gate passes should free-aim be wired into the already-proved dual-eye ai_Laser render path.