# Post-seal root implementation comparison v1

**PASS.** The root codec was opened and imported only after the independent codec, known-vector results, 100 synthetic fixtures and method report were sealed. The precomparison seal is `INDEPENDENT_CODEC_PRECOMPARISON_SEAL_v1.json`, SHA-256 `0d5ac5ffce2de3963dae6e3b45d4544c662d975ea4242254925c08c2fee2a825`.

The post-seal checker converted the independent one-indexed row-major holes to the root codec's zero-indexed `(row,column)` coordinates. It compared the root's output directly with the **already sealed** visitation permutations and ciphertext hashes, rather than creating a new root-derived reference for the independent code.

All **800 start-angle/direction cases** across the **100 distinct grilles** agree exactly in visit permutation, full four-block ciphertext and recovered known payload. The root also passes the ACA example in both directions and rejects all **696** core negative cases: duplicate holes, both out-of-bounds directions, missing holes, same-orbit coverage collisions and incomplete encryption/decryption blocks.

The root source-code SHA-256 is `127ff0b8748728882cd5ab1024e28254ab054be77ff264be61ee5384f73ee757`, agreeing with the previously supplied root-control summary. The independent source-code SHA-256 remains `94b5e3d7a34f60fad1262f8467b67d8a5915cca9c355590b2564d98c58ac35e1`. All four precomparison-sealed artifacts were checked unchanged both before and after the root comparison.

Canonical starts 0, 1, 2, 3 and directions ±1 agree. The root interface accepts modulo-four starting turns, while the independent public interface explicitly rejects noncanonical starts. The independent implementation's stricter invalid-type tests are separate contract checks; identical root behavior for those types is not claimed.

The reproducible comparison script is `postseal_root_crosscheck_v1.py`; detailed case records are in `POSTSEAL_ROOT_CROSSCHECK_v1.json`. Neither implementation comparison consulted target input, target grille holes, source corrections, key interpretation, candidate or target output. This establishes the documented mechanism and software agreement on known controls. Target source geometry and any complete-reading claim require their separate source and all-occurrence audits.
