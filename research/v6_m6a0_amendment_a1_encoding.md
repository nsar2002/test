# V6-M6A0 — AMENDMENT A1 (2026-09-28): FILE ENCODING

**Trigger.** Formal run 36381833974 was classified `BLOCKED_M6A0_DATA` ("MNQ 06-19.Last.txt: non-ASCII bytes"). No criterion was evaluated and no MNQ value was seen. The recorded input SHA256s are 25 distinct hashes.

**Change (format handling only).**
- A Last file may be ASCII, UTF-8 with or without a BOM, or UTF-16 with a BOM.
- It is decoded strictly: UTF-16 if it starts with FF FE or FE FF, otherwise UTF-8 with an optional BOM.
- The decoded text must be pure ASCII and must satisfy the unchanged line-format rules. Anything else → BLOCKED.

**Probe.** The workflow's download step logs, for each file, only its size and a byte-class tag: `html`, `utf8-bom`, `utf16-bom`, `digit` or `other`. It fails the job if any file is an HTML page, i.e. access is not public.

**Unchanged.** Data selection, features, arms, criteria, thresholds and diagnostics.
