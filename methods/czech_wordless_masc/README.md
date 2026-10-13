# Czech wordless monoalphabetic substitution controls

This portable module records a fixed synthetic software benchmark: six modern Czech ASCII-26 texts, of lengths 200, 200, 400, 400, 600 and 600, encrypted with seeded bijective substitutions after removing word boundaries. It tests one generic simulated-annealing solver with a train-only quadgram model. No historical cipher is assigned or solved by this module.

The original frozen run recovered **6/6 exact texts, 2,400/2,400 characters and 132/132 observed symbol mappings**. Candidate-key forward reconstruction and separate gold-key reconstruction both matched 2,400/2,400 characters. The training-letter-frequency baseline matched **596/2,400 characters and 0/6 exact texts**. Three seeded frequency-preserving shuffles are descriptive controls; they do not supply a significance test, success probability or historical language/family identification.

A separate AI-assisted audit passed **156 checks**: it rebuilt the language model, replayed source selection and enciphering, checked all 162 retained restart outputs, recomputed scores and metrics, and recompiled the unchanged solver for one P06 replay. That replay matched the retained P06 output byte for byte. This is an independent workflow within the project, with no external human expert or catalogue confirmation implied.

## Offline check

From the repository root, using Python 3.9+ and no network or compiler:

```sh
python3 methods/czech_wordless_masc/verify_frozen.py
```

The checker verifies module hashes, all nine retained controls, all 162 retained trials, exact scores, frequency baselines, seeded shuffles, candidate and gold forward reconstruction, observed-mapping denominators and aggregate metrics. Its current verification count differs from the original audit's 156 checks. It does not re-audit the omitted full raw corpus or prove that unrecorded manual reads never occurred.

## Fresh compilation and bounded replay

A C++17 compiler is required. These commands compile the byte-identical generic core and replay only P06 with its original seed, **18 restarts × 100,000 steps**, then grade it:

```sh
python3 methods/czech_wordless_masc/run_inference.py --output ../history-unlocked-wordless-replay --controls P06
python3 methods/czech_wordless_masc/grade_controls.py --results ../history-unlocked-wordless-replay
```

Keep generated files outside the checkout, as in the sibling directory above, so the repository's complete-file manifest stays valid. The output directory must be new. `REPLAY_METRICS.json` identifies the result as a new public replay and reports only the selected controls. For the fixed full set, replace `P06` with `all`; all nine controls use the same original budget. C++ library/compiler differences can change seeded stochastic trajectories, so cross-platform byte identity is not promised. The inference wrapper reads model, ciphertext, training-frequency order, seeds and configuration only. Grading reads gold after recorded inference completion. Folder separation is not an OS-enforced access barrier, and this public release already contains the synthetic answers.

## Rebuild the inputs from pinned upstream data

The two large raw CoNLL-U files are omitted. This optional acquisition downloads them and their notices from an immutable upstream commit, checks their recorded SHA-256 hashes, then rebuilds the model and seeded fixtures:

```sh
python3 methods/czech_wordless_masc/fetch_corpus.py --output ../history-unlocked-wordless-corpus
python3 methods/czech_wordless_masc/build_synthetic.py --corpus-dir ../history-unlocked-wordless-corpus --output ../history-unlocked-wordless-built
python3 methods/czech_wordless_masc/run_inference.py --bundle ../history-unlocked-wordless-built --output ../history-unlocked-wordless-built-replay --controls P06
python3 methods/czech_wordless_masc/grade_controls.py --bundle ../history-unlocked-wordless-built --results ../history-unlocked-wordless-built-replay
```

Construction retains integer-ID `FORM` rows, normalizes NFKD and lowercase, keeps ASCII `a`–`z`, removes boundaries and excludes range/empty-node rows. Training is confined to `cs_pdtc-ud-train-la.conllu`; selected development excerpts have distinct document IDs, no exact selected full sentence in the training file, and no whole-excerpt substring in a training document. The source checks do not exclude shared author, genre, collection or near duplicates. A new construction writes new timestamps and relative manifests; it does not overwrite or silently recompute original frozen claims.

## Files and provenance

- `generic_solver.cpp` is unchanged: SHA-256 `651b888047c939dd0ce6e0d84805b8a4beba45eb6b0d8ebfe3ab43eb60681276`.
- `frozen/` contains original corpus-derived inputs, gold, retained inference outputs, original configuration and metrics. Only path-bearing manifests/gold source paths are adapted to relative names; original hashes and byte-equality declarations are in `provenance/ORIGINAL_ARTIFACT_HASHES.json`.
- `provenance/INDEPENDENT_AUDIT_SUMMARY.json` records the original separate audit's actual scope, counts, aggregate results, limitations and hashes. Original administrative/controller files and executables are omitted.
- `MODULE_SHA256.json` pins the portable release, independently of the original private artifact hashes.

These six fixed-seed idealized substitutions do not qualify historical transcription, spelling, errors, alphabet identity or cipher family; a matched source and method assessment remains necessary for a historical case. Quadgram scores are heuristic log scores, not probabilities. Unobserved key symbols are excluded from the 132-mapping denominator.

## Licence

Code and newly written documentation are MIT, subject to the repository's original-contribution scope. The model, transformed Czech excerpts, synthetic ciphertexts, gold, corpus-derived retained outputs and frequency data remain **CC BY-NC-SA 4.0**. The MIT grant does not permit commercial reuse of those linguistic data. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution, upstream pins, modifications and the full licence texts.
