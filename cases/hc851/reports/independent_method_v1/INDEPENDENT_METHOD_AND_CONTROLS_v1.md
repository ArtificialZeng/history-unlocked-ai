# Independent turning-grille method and software controls v1

**PASS.** This report covers the provided primary ACA worked-example capture and independently generated known-key controls. It does not assess the target source, target grille, corrections, plaintext or historical priority.

The independent module `scripts/independent_grille_v1.py` was written and tested before reading or importing `scripts/grille_v1.py`. The only prior project reads were AGENTS.md, the official-source worked-example capture, and the root synthetic-control summary. The source capture points to the American Cryptogram Association’s `https://www.cryptogram.org/downloads/aca.info/ciphers/Grille.pdf`; no network retrieval was performed in this independent task.

For an even side n, a clockwise quarter-turn maps native zero-indexed grid coordinates `(r,c)` to `(c,n−1−r)`. Every cell has a four-cell orbit: a cell fixed by a nontrivial quarter-turn or half-turn would require the central coordinate `(n−1)/2`, which is not integral when n is even. Selecting one hole per orbit therefore gives exactly n²/4 holes and covers all n² cells once during four turns. The codec explicitly checks that coverage rather than assuming that hole count alone establishes a valid grille.

At each orientation the current holes are visited in row-major order. Four such sorted sets, from the selected start angle and direction, form the payload-to-square permutation. Encryption places successive payload characters into that visitation order and emits the square row-major. Decryption reads the row-major ciphertext square in the same visitation order. Multiple whole square blocks are processed independently. Inputs are preserved exactly: the codec does not remove spaces, change case, guess letters or pad incomplete blocks.

The primary known vector passed both directions:

- side 4; one-indexed holes **1, 8, 10, 12**;
- start angle 0°; clockwise quarter-turns; row-major visits at each orientation;
- payload `THETURNINGGRILLE` → square ciphertext `TILUNRGHGELTENIR`;
- explicit one-indexed visitation order: `1,8,10,12,4,6,14,15,5,7,9,16,2,3,11,13`;
- exact decryption recovers the payload, and the explicit primary visitation vector also matches.

Independent seed **85120261006** generated **100 distinct valid grilles** by choosing one cell from each rotation orbit. The distribution is 4 at side 2 (the complete valid set), then 24 each at sides 4, 6, 8 and 10. This avoids describing repeated 2×2 keys as distinct. Every grille was tested at all four start angles and both turning directions, giving **800 controls** with **4 blocks each**. Every control passed:

1. full n²-cell permutation and unique coverage;
2. exact encryption/decryption roundtrip and forward reproduction;
3. equality between the four-block result and four separate block calls;
4. exact cell placement using n² distinct Unicode symbols, avoiding accidental equality from repeated letters.

All **720 rejection controls** passed: 24 fixed invalid-type/side/start/direction cases; 600 per-grille duplicate, lower/upper out-of-bounds, missing-hole, and encryption/decryption partial-block cases; and 96 distinct-hole sets with same-orbit coverage collisions. Duplicate checks occur before hole-count checks, and full rotation coverage is checked separately. The 2×2 grille has only one orbit, so a distinct-hole same-cardinality collision cannot be constructed there; its bad counts and bounds are still tested. Empty payload is explicitly allowed as zero whole blocks; non-string payloads are rejected.

Artifacts:

- `INDEPENDENT_SOFTWARE_CONTROLS_v1.json`: exact primary vector, per-size counts and all rejected-case reasons.
- `INDEPENDENT_SYNTHETIC_FIXTURES_v1.json`: all 100 independent known-key fixtures, their four-block payloads and all 800 visitation permutations/ciphertext hashes.
- `INDEPENDENT_CODEC_PRECOMPARISON_SEAL_v1.json`: hashes of the code, this report, results, fixtures and supplied baseline records, created before opening the root codec.

The independent source-code SHA-256 is `94b5e3d7a34f60fad1262f8467b67d8a5915cca9c355590b2564d98c58ac35e1`. A later cross-implementation audit, if performed, must be recorded separately and must not rewrite the precomparison seal or change this independent codec.
