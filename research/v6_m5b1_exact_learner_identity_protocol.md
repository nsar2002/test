# V6-M5B1 — exact learner identity and KC hemisphere freeze

STATUS: FROZEN BEFORE M5B1 ID/side result.

Prerequisite: PASS_M5B0_MALECNS_LEARNER_SCHEMA_QUALIFIED.

Exact identity rules from the official MaleCNS annotation class field:
- KC: class exactly Kenyon_Cell
- DAN: class exactly DAN
- MBON: class exactly MBON

No fuzzy type matching, synaptic-degree threshold, connectivity ranking, lobe performance, V5/V6 residual, model output or market outcome may include/exclude a body.

Required parity counts inherited from the already observed M5B0 source-schema result:
- KC = 4064
- DAN = 340
- MBON = 97

KC hemisphere rule:
- every retained KC must have official somaSide exactly L or R;
- missing, empty or M somaSide for any KC blocks use of this identity manifest by M4B0;
- no coordinate-based or instance-name fallback is permitted.

DAN and MBON identities remain all exact-class bodies regardless of somaSide. Their somaSide/rootSide/type/instance metadata are recorded but cannot be used for exclusion in M5B1.

Output one deterministic bodyId-sorted identity manifest containing bodyId, learner_class, somaSide, rootSide, instance, type, flywireType and hemibrainType for all retained KC/DAN/MBON bodies.

PASS_M5B1_EXACT_LEARNER_IDENTITIES_FROZEN requires exact source hash parity, exact class counts, unique bodyIds, and all 4064 KCs assigned source somaSide L/R.

BLOCKED_M5B1_KC_HEMISPHERE_IDENTITY if any KC lacks L/R somaSide.
BLOCKED_M5B1_SOURCE_PARITY for any other source/count/identity mismatch.

This gate does not inspect the synapse table, learner topology, model states, plasticity, reward, MNQ, PnL, Amin values or M4V0 values.

On PASS, M4B0 may use the exact KC IDs and somaSide assignments for no-market sparsifier unit parity, and M5B2 may inspect only the exact KC/DAN/MBON induced synaptic topology.
