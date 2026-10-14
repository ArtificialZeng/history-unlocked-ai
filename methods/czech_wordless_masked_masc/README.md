# Czech wordless masked substitution controls

This portable module preserves a fixed synthetic benchmark on six fresh modern Czech development documents. ASCII-26 excerpts of **400, 400, 500, 500, 600 and 600 original characters** receive seeded bijective substitutions after word boundaries are removed. Each excerpt has **13 unknown runs of length 2–5 and 17 singleton masks**. Every run collapses to one sentinel 26. The sentinel is an **unknown gap**, with its original length retained in gold; it is not a word boundary or a certified single ciphertext unit.

The original run recovered **5/6 exact known-position streams, 2,612/2,613 known characters and 136/137 observed mappings**. The train-frequency baseline recovered **575/2,613** known characters and no exact stream. **P05 has one retained character and mapping error.** The 387 unknown original characters were neither reconstructed nor graded. Candidate/key forward consistency is **2,613/2,613**; the separate gold-recovery forward check is **2,612/2,613**. Key/output compatibility alone does not establish recovery.

There are six positives and three seeded negatives that exactly preserve observed-symbol histograms and gap-marker positions. All nine original runs used **18 restarts × 100,000 loop iterations**, retaining all **162 trials**. Three negatives do not estimate significance or historical success probability. The unchanged generic C++ core has SHA-256 `651b888047c939dd0ce6e0d84805b8a4beba45eb6b0d8ebfe3ab43eb60681276`.

## Offline verification

From the repository root, with Python 3.9+ and no compiler or network:

```sh
python3 methods/czech_wordless_masked_masc/verify_frozen.py
```

The standard-library checker verifies the complete module manifest, original byte equality, fixed configuration and seeds, masks and actual unknown-run lengths, original-coordinate maps and known-position denominators, all nine controls and all 162 retained trial renderings/scores, constant sentinel penalties, exact histogram/gap-preserving shuffles, the baseline, both forward metrics and the P05 failure. It performs no new inference. It cannot re-audit the omitted full raw corpus or attest to unrecorded reads.

The original separate AI-assisted referee passed **3,156 checks with zero failures**, rebuilt the train-only model and fixtures, and reviewed code and retained invocation records. It did not compile or replay the solver. This was an independent workflow within the project, with no external human expert confirmation. The producer and referee original manifests contained 80 and 13 files; their exact bytes and hashes were checked before packaging. Recorded first-safe lateness of **146.531442 seconds** for the producer and **40.326905 seconds** for the referee remains administrative provenance and does not alter the scientific result.

## Fresh bounded replay

A C++17 compiler is required. The default P05 replay deliberately includes the retained failure:

```sh
python3 methods/czech_wordless_masked_masc/run_inference.py --output ../history-unlocked-masked-replay --controls P05
python3 methods/czech_wordless_masked_masc/grade_controls.py --results ../history-unlocked-masked-replay
```

The output directory must be new and outside the module. Keep all generated artifacts outside the checkout so the repository manifest remains valid. Use `--controls all` to replay the nine fixed controls at their original budget. A selected P05 replay does not re-test the full six-positive profile. New compilation/replay receipts and `REPLAY_METRICS.json` are labelled separately from `frozen/` originals. Compiler or C++ library differences may change seeded stochastic trajectories; cross-platform byte identity is not promised. Original no-rerun declarations concern the original experiment, while these public commands perform explicitly separate replays without tuning.

Packaging validation performed one fresh compiled P05 replay at the fixed budget. Its output was byte identical to the retained original and reproduced **537/538** known characters, **23/24** observed mappings and the single error. A separate deterministic rebuild matched the model, frequency ordering and all nine cipher files byte for byte, with identical gold/selection/mask data after excluding timestamps. [PACKAGING_CHECK_SUMMARY.json](provenance/PACKAGING_CHECK_SUMMARY.json) records these checks separately from the original referee audit; the private replay executable and raw corpus are omitted.

Inference reads only configuration and pins, train-only model, masked ciphertext, frequency order, seeds and unchanged core. It receives no original-coordinate map, unknown lengths, corpus or gold values. Grading reads gold after recorded completion of all selected replay processes. Folder separation is not an OS-enforced access barrier. Synthetic answers are public in this release, and agent-wide blindness is not claimed.

## Deterministic source rebuild

The large raw corpus files are omitted. This optional acquisition downloads four files from the pinned UD_Czech-PDTC commit, verifies their SHA-256 values and rebuilds the model and fixtures:

```sh
python3 methods/czech_wordless_masked_masc/fetch_corpus.py --output ../history-unlocked-masked-corpus
python3 methods/czech_wordless_masked_masc/build_synthetic.py --corpus-dir ../history-unlocked-masked-corpus --output ../history-unlocked-masked-built
python3 methods/czech_wordless_masked_masc/run_inference.py --bundle ../history-unlocked-masked-built --output ../history-unlocked-masked-built-replay --controls P05
python3 methods/czech_wordless_masked_masc/grade_controls.py --bundle ../history-unlocked-masked-built --results ../history-unlocked-masked-built-replay
```

Construction uses integer-ID `FORM` rows, NFKD then lowercase ASCII `a`–`z`, excluding range and empty-node rows and removing boundaries. Training uses only `cs_pdtc-ud-train-la.conllu`, document-concatenated wordless quadgrams and add-0.01 log10 smoothing. The original 27⁴ float32 model is little endian; every sentinel-containing quadgram receives a constant floor penalty. Score-per-quadgram denominators include those windows, which provide no word-boundary evidence.

Selection reproduces the original first-eligible development-document order. Six distinct IDs exclude train IDs and the previous six public control IDs in `REBUILD_EXCLUSIONS.json`. Complete selected normalized sentences and whole-excerpt matches in training documents are rejected exactly as in the original construction. Shared authors, genre, collection and near duplicates remain unchecked. Rebuilds write new timestamps and manifests; they do not overwrite original scores or claims.

## Provenance and scope

`frozen/` retains original corpus-derived inputs, gold, masks, results, failure and metric/configuration records. Its corpus-derived baselines and `INFERENCE_PINS.json` are added public packaging artifacts. `provenance/ORIGINAL_ARTIFACT_HASHES.json` records original relative artifact names, hashes and explicit byte-equality/adaptation declarations. The separate audit summary preserves aggregate results and original hashes. Absolute private paths, administrative payloads, raw full corpus and executables are omitted. `MODULE_SHA256.json` hashes every portable file except itself.

This is synthetic error-profile resource qualification. It solves no historical cipher, admits no historical target, certifies no historical segmentation or cipher family, and supplies no historical success probability. Historical source quality, spelling, alphabet, noise profile and method relevance require separate qualification. Quadgram scores are heuristic log scores, not probabilities. Unobserved key symbols are excluded from the 137-mapping denominator.

## Licence

Code and new documentation are [MIT](licenses/MIT.txt). The UD-derived model, excerpts, ciphertexts, gold, masks, frequencies, metrics and retained/generated results remain **[CC BY-NC-SA 4.0](licenses/CC-BY-NC-SA-4.0.txt)**. The MIT code grant does not permit commercial reuse of those linguistic data. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for source attribution, immutable upstream pins, modifications and exact licence texts.
